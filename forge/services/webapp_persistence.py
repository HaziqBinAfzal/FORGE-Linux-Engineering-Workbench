"""Persistent evidence for the DecodeLabs Web App Setup mission.

Stores successful inspection commands, never a cached verification result.
The existing verifier always rechecks the live sandbox filesystem.
"""

import json
import os
import tempfile
from pathlib import Path

EVIDENCE_NAME = ".webapp-mission-evidence.json"

ALLOWED_COMMANDS = frozenset({
    "pwd",
    "ls -R /app",
    "pwd && ls -R /app",
    "ls -l /app/config.conf",
})


def evidence_path(lab):
    return Path(lab.root) / EVIDENCE_NAME


def _validate(commands):
    if not isinstance(commands, list):
        raise ValueError("Invalid mission evidence format")

    if len(commands) > 16:
        raise ValueError("Mission evidence exceeds limit")

    if any(
        not isinstance(command, str)
        or command not in ALLOWED_COMMANDS
        for command in commands
    ):
        raise ValueError("Invalid mission evidence command")

    return list(dict.fromkeys(commands))


def load_webapp_evidence(lab):
    """Load previously successful inspection commands."""
    path = evidence_path(lab)

    if path.is_symlink():
        raise ValueError("Mission evidence cannot be a symlink")

    if not path.exists():
        return []

    if not path.is_file() or path.stat().st_size > 8192:
        raise ValueError("Invalid mission evidence file")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported mission evidence version")

    return _validate(data.get("commands"))


def save_webapp_evidence(lab, commands):
    """Atomically save only supported inspection evidence."""
    path = evidence_path(lab)

    if path.is_symlink():
        raise ValueError("Mission evidence cannot be a symlink")

    clean = _validate([
        command
        for command in commands
        if command in ALLOWED_COMMANDS
    ])

    payload = json.dumps({
        "version": 1,
        "commands": clean,
    }, indent=2)

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".webapp-evidence-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)

        os.replace(temporary, path)

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    return clean
