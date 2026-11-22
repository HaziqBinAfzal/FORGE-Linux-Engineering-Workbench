"""DecodeLabs Project 1: Web App Setup practical verification."""

from pathlib import Path


STEPS = (
    ("Application logs directory", "mkdir -p /app/logs"),
    ("Configuration file", "touch /app/config.conf"),
    ("Startup log", 'echo "Started" > /app/logs/server.log'),
    ("Directory inspection", "pwd && ls -R /app"),
    ("Log backup", "mv /app/logs/server.log /app/logs/server.bak"),
    ("Configuration audit", "ls -l /app/config.conf"),
)


def verify_webapp_setup(lab, command_history=()):
    """Verify actual files and observed inspection commands."""
    app = lab._path("/app")
    logs = lab._path("/app/logs")
    config = lab._path("/app/config.conf")
    original_log = lab._path("/app/logs/server.log")
    backup = lab._path("/app/logs/server.bak")
    legacy_backup = lab._path("/app/logs/server.log.bak")

    def valid_backup():
        return any(
            path.is_file() and path.read_text().strip() == "Started"
            for path in (backup, legacy_backup)
        )

    history = tuple(command_history)

    checks = (
        logs.is_dir(),
        config.is_file(),
        (
            (original_log.is_file()
             and original_log.read_text().strip() == "Started")
            or
            valid_backup()
        ),
        (
            any(
                command.strip() == "pwd && ls -R /app"
                for command in history
            )
            or (
                "pwd" in history
                and "ls -R /app" in history
            )
        ),
        (
            valid_backup()
            and not original_log.exists()
        ),
        any(
            command == "ls -l /app/config.conf"
            for command in history
        ) and config.is_file(),
    )

    completed = sum(checks)

    return {
        "title": "DecodeLabs Web App Setup",
        "completed": completed,
        "total": len(checks),
        "percentage": round(completed / len(checks) * 100),
        "verified": all(checks),
        "steps": [
            {
                "title": title,
                "command": command,
                "passed": passed,
            }
            for (title, command), passed
            in zip(STEPS, checks)
        ],
    }
