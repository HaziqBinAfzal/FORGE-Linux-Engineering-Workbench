from forge.services.linux_lab import LinuxLab
from forge.services.webapp_mission import verify_webapp_setup


def test_webapp_initial_state(tmp_path):
    lab = LinuxLab(tmp_path)
    result = verify_webapp_setup(lab)
    assert result["completed"] == 0
    assert not result["verified"]


def test_webapp_complete_mission(tmp_path):
    lab = LinuxLab(tmp_path)

    commands = [
        "mkdir -p /app/logs",
        "touch /app/config.conf",
        "echo Started > /app/logs/server.log",
        "pwd",
        "ls -R /app",
        "mv /app/logs/server.log /app/logs/server.log.bak",
        "ls -l /app/config.conf",
    ]

    for command in commands:
        result = lab.execute(command)
        assert not result.startswith("ERROR:"), (command, result)

    report = verify_webapp_setup(lab, commands)

    assert report["verified"]
    assert report["completed"] == 6
    assert report["percentage"] == 100


def test_webapp_requires_inspection(tmp_path):
    lab = LinuxLab(tmp_path)

    lab.execute("mkdir -p /app/logs")
    lab.execute("touch /app/config.conf")
    lab.execute("echo Started > /app/logs/server.log")
    lab.execute("mv /app/logs/server.log /app/logs/server.log.bak")

    report = verify_webapp_setup(lab)

    assert not report["verified"]
    assert report["completed"] == 4


def test_webapp_blocks_outside_paths(tmp_path):
    lab = LinuxLab(tmp_path)

    result = lab.execute("echo Started > ../../outside.log")

    assert result.startswith("ERROR:")
    assert not (tmp_path.parent.parent / "outside.log").exists()


def test_webapp_rejects_unsupported_ls_options(tmp_path):
    lab = LinuxLab(tmp_path)

    assert lab.execute("ls -R --unknown").startswith("ERROR:")
