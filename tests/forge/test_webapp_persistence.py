import json

import pytest

from forge.services.linux_lab import LinuxLab
from forge.services.webapp_mission import verify_webapp_setup
from forge.services.webapp_persistence import (
    evidence_path,
    load_webapp_evidence,
    save_webapp_evidence,
)


def test_evidence_survives_restart(tmp_path):
    first = LinuxLab(tmp_path)

    commands = [
        "pwd && ls -R /app",
        "ls -l /app/config.conf",
    ]

    save_webapp_evidence(first, commands)

    restarted = LinuxLab(tmp_path)

    assert load_webapp_evidence(restarted) == commands


def test_evidence_does_not_fake_files(tmp_path):
    lab = LinuxLab(tmp_path)

    commands = [
        "pwd && ls -R /app",
        "ls -l /app/config.conf",
    ]

    save_webapp_evidence(lab, commands)

    report = verify_webapp_setup(
        LinuxLab(tmp_path),
        load_webapp_evidence(LinuxLab(tmp_path)),
    )

    assert not report["verified"]


def test_complete_mission_persists(tmp_path):
    lab = LinuxLab(tmp_path)

    commands = [
        "mkdir -p /app/logs",
        "touch /app/config.conf",
        'echo "Started" > /app/logs/server.log',
        "pwd && ls -R /app",
        "mv /app/logs/server.log /app/logs/server.bak",
        "ls -l /app/config.conf",
    ]

    for command in commands:
        result = lab.execute(command)
        assert not result.startswith("ERROR:"), (command, result)

    save_webapp_evidence(lab, commands)

    restarted = LinuxLab(tmp_path)

    report = verify_webapp_setup(
        restarted,
        load_webapp_evidence(restarted),
    )

    assert report["verified"]
    assert report["completed"] == 6


def test_deleted_file_invalidates_completion(tmp_path):
    lab = LinuxLab(tmp_path)

    commands = [
        "mkdir -p /app/logs",
        "touch /app/config.conf",
        'echo "Started" > /app/logs/server.log',
        "pwd && ls -R /app",
        "mv /app/logs/server.log /app/logs/server.bak",
        "ls -l /app/config.conf",
    ]

    for command in commands:
        assert not lab.execute(command).startswith("ERROR:")

    save_webapp_evidence(lab, commands)

    lab._path("/app/logs/server.bak").unlink()

    report = verify_webapp_setup(
        LinuxLab(tmp_path),
        load_webapp_evidence(LinuxLab(tmp_path)),
    )

    assert not report["verified"]


def test_invalid_evidence_rejected(tmp_path):
    lab = LinuxLab(tmp_path)

    evidence_path(lab).write_text(json.dumps({
        "version": 1,
        "commands": ["sudo rm -rf /"],
    }))

    with pytest.raises(ValueError):
        load_webapp_evidence(lab)


def test_symlink_evidence_rejected(tmp_path):
    lab = LinuxLab(tmp_path)

    target = tmp_path / "target.json"
    target.write_text("{}")

    evidence_path(lab).symlink_to(target)

    with pytest.raises(ValueError):
        load_webapp_evidence(lab)

    with pytest.raises(ValueError):
        save_webapp_evidence(lab, ["pwd"])


def test_only_inspection_commands_are_saved(tmp_path):
    lab = LinuxLab(tmp_path)

    saved = save_webapp_evidence(lab, [
        "mkdir -p /app/logs",
        "pwd",
        "pwd",
        "ls -R /app",
        "ls -l /app/config.conf",
    ])

    assert saved == [
        "pwd",
        "ls -R /app",
        "ls -l /app/config.conf",
    ]
