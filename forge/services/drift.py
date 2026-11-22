import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "runtime" / "forge-baseline.json"

TRACKED = (
    "requirements.txt",
    ".gitignore",
    "forge/api/main.py",
    "forge/services/telemetry.py",
    "forge/tui/app.py",
)


def checksum(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def snapshot():
    result = {}

    for name in TRACKED:
        path = ROOT / name

        if path.is_file() and not path.is_symlink():
            result[name] = checksum(path)
        else:
            result[name] = None

    return result


def create_baseline():
    BASELINE.parent.mkdir(parents=True, exist_ok=True)

    if BASELINE.is_symlink():
        raise ValueError("Baseline path must not be a symlink")

    data = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": snapshot(),
    }

    temporary = BASELINE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(BASELINE)

    return data


def check_drift():
    if not BASELINE.is_file() or BASELINE.is_symlink():
        return {
            "status": "no_baseline",
            "changes": [],
        }

    baseline = json.loads(BASELINE.read_text())
    expected = baseline["files"]
    current = snapshot()

    changes = []

    for name in TRACKED:
        before = expected.get(name)
        after = current.get(name)

        if before == after:
            continue

        if before is None:
            state = "ADDED"
        elif after is None:
            state = "MISSING"
        else:
            state = "MODIFIED"

        changes.append({
            "file": name,
            "state": state,
        })

    return {
        "status": "drift_detected" if changes else "clean",
        "changes": changes,
        "checked_files": len(TRACKED),
    }
