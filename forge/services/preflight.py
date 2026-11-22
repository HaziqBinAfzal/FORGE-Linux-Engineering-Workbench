import shutil
import subprocess
import sys
from pathlib import Path

import psutil

from forge.services.drift import check_drift

ROOT = Path(__file__).resolve().parents[2]


def result(name, status, detail):
    return {
        "name": name,
        "status": status,
        "detail": detail,
    }


def run_preflight():
    checks = []

    version = sys.version_info
    checks.append(result(
        "Python runtime",
        "PASS" if version >= (3, 12) else "FAIL",
        f"Python {version.major}.{version.minor}.{version.micro}",
    ))

    git = shutil.which("git")

    if git is None:
        checks.append(result(
            "Git availability", "FAIL", "Git executable not found"
        ))
    else:
        try:
            command = subprocess.run(
                [git, "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            valid = command.returncode == 0 and command.stdout.strip() == "true"
            checks.append(result(
                "Git repository",
                "PASS" if valid else "FAIL",
                "Valid Git worktree" if valid else "Not a Git worktree",
            ))
        except (OSError, subprocess.TimeoutExpired):
            checks.append(result(
                "Git repository", "FAIL", "Git verification failed"
            ))

    disk = psutil.disk_usage(str(ROOT))
    free_gb = disk.free / (1024 ** 3)

    checks.append(result(
        "Available disk space",
        "PASS" if free_gb >= 2 else "WARN" if free_gb >= 1 else "FAIL",
        f"{free_gb:.2f} GiB free",
    ))

    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024 ** 3)

    checks.append(result(
        "Available memory",
        "PASS" if available_gb >= 1 else "WARN" if available_gb >= 0.5 else "FAIL",
        f"{available_gb:.2f} GiB available",
    ))

    try:
        drift = check_drift()
        state = drift["status"]

        if state == "clean":
            status, detail = "PASS", "Tracked files match baseline"
        elif state == "no_baseline":
            status, detail = "WARN", "No configuration baseline established"
        else:
            status = "FAIL"
            detail = f"{len(drift['changes'])} configuration changes detected"

        checks.append(result("Configuration integrity", status, detail))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks.append(result(
            "Configuration integrity", "FAIL",
            f"Unable to verify baseline: {type(exc).__name__}",
        ))

    statuses = {check["status"] for check in checks}

    overall = (
        "FAIL" if "FAIL" in statuses
        else "WARN" if "WARN" in statuses
        else "PASS"
    )

    return {
        "overall": overall,
        "checks": checks,
        "checked": len(checks),
    }
