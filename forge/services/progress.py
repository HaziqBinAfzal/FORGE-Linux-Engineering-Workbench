import json
from datetime import datetime, timezone
from pathlib import Path

from forge.services.missions import MISSIONS

ROOT = Path(__file__).resolve().parents[2]
PROGRESS_FILE = ROOT / "runtime" / "mission-progress.json"


def load_progress():
    if PROGRESS_FILE.is_symlink():
        raise ValueError("Progress file must not be a symlink")

    if not PROGRESS_FILE.exists():
        return {"completed": {}}

    data = json.loads(PROGRESS_FILE.read_text())

    if not isinstance(data, dict):
        raise ValueError("Invalid progress data")

    completed = data.get("completed", {})

    if not isinstance(completed, dict):
        raise ValueError("Invalid completion records")

    return {"completed": completed}


def save_progress(data):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if PROGRESS_FILE.is_symlink():
        raise ValueError("Progress file must not be a symlink")

    temporary = PROGRESS_FILE.with_suffix(".tmp")

    if temporary.is_symlink():
        raise ValueError("Temporary progress file must not be a symlink")

    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(PROGRESS_FILE)


def record_completion(mission_id):
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")

    data = load_progress()

    if mission_id not in data["completed"]:
        data["completed"][mission_id] = {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "verified": True,
        }

        save_progress(data)

    return progress_summary()


def progress_summary():
    data = load_progress()

    completed = {
        mission_id: record
        for mission_id, record in data["completed"].items()
        if mission_id in MISSIONS
        and isinstance(record, dict)
        and record.get("verified") is True
    }

    total = len(MISSIONS)
    count = len(completed)

    return {
        "total": total,
        "completed": count,
        "remaining": total - count,
        "percentage": round(count / total * 100) if total else 0,
        "missions": completed,
    }
