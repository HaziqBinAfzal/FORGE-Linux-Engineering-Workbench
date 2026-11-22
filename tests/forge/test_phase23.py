from forge.services.linux_lab import LinuxLab
from forge.services.webapp_mission import verify_webapp_setup


def test_exact_assignment_commands(tmp_path):
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

    report = verify_webapp_setup(lab, commands)

    assert report["verified"]
    assert report["completed"] == 6
    assert report["percentage"] == 100


def test_chained_commands_return_both_outputs(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("mkdir -p /app/logs")

    result = lab.execute("pwd && ls -R /app")

    assert result.startswith("/")
    assert "/app/logs" in result


def test_chaining_stops_after_error(tmp_path):
    lab = LinuxLab(tmp_path)

    result = lab.execute(
        "cat /missing.txt && touch /should-not-exist.txt"
    )

    assert result.startswith("ERROR:")
    assert not lab._path("/should-not-exist.txt").exists()


def test_chaining_rejects_malformed_input(tmp_path):
    lab = LinuxLab(tmp_path)

    for command in (
        "&& pwd",
        "pwd &&",
        "pwd && && ls",
        "pwd & ls",
    ):
        assert lab.execute(command).startswith("ERROR:")


def test_chaining_stays_inside_sandbox(tmp_path):
    lab = LinuxLab(tmp_path)

    result = lab.execute(
        "pwd && touch ../../outside.txt"
    )

    assert "ERROR:" in result
    assert not (tmp_path.parent.parent / "outside.txt").exists()
