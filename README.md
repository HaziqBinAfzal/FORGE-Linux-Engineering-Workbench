# FORGE — Linux Engineering Workbench

**An interactive Linux command-line training and engineering workbench.**

FORGE was developed for **DecodeLabs DevOps Project 1: Linux & Command Line Basics**. It combines guided command-line practice with engineering diagnostics, monitoring, and troubleshooting.

## Features

- Interactive terminal-based interface
- Isolated Linux command training environment
- Guided six-step Web App Setup mission
- System overview and process monitoring
- Diagnostics and engineering troubleshooting
- Drift inspection and preflight checks
- Additional guided engineering missions
- Automated testing and GitHub Actions CI

## Supported Commands

| Category | Commands |
| --- | --- |
| Navigation | `pwd`, `cd`, `ls`, `ls -a`, `ls -l`, `ls -R` |
| Files | `mkdir -p`, `touch`, `cp`, `mv` |
| Inspection | `cat`, `less`, `head`, `tail`, `tail -f` |
| Permissions | `chmod`, `chown` |
| Identity | `whoami`, `id` |
| Safe deletion | `rm -i` |
| Remote access concepts | `ssh` |

## Installation

Requires Python 3, a Linux terminal, and internet access to install dependencies.

1. Clone the repository using your authenticated GitHub account.
2. Open the project directory.
3. Run these commands:

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt

## Launch

    ./forge-run

## Official Web App Setup Mission

Enter these commands inside FORGE's training terminal:

    mkdir -p /app/logs
    touch /app/config.conf
    echo "Started" > /app/logs/server.log
    pwd && ls -R /app
    mv /app/logs/server.log /app/logs/server.bak
    ls -l /app/config.conf

FORGE verifies progress against the isolated training workspace.

## Architecture

- `forge/tui/` — interactive terminal interface
- `forge/services/` — command training, missions, diagnostics, and engineering services
- `forge/api/` — application API
- `forge/web/` — web interface assets
- `scripts/` — operational helper scripts
- `tests/forge/` — automated tests

## Testing

    PYTHONPATH=. .venv/bin/python -m pytest tests/forge -q

The initial release passed **70 automated tests**, including verification in a fresh virtual environment.

GitHub Actions runs automated tests for pushes and pull requests.

## Safety

FORGE's Linux training terminal uses an **isolated filesystem** rather than directly modifying Ubuntu system directories.

- `ssh` is an educational simulation, not a real network connection.
- `chown` simulates ownership changes.
- `tail -f` provides a bounded demonstration rather than continuous streaming.
- Unrestricted destructive deletion is disabled.

The simulated `/app` directory is different from `/app` on the host machine.

FORGE is an educational application, not a production server-management tool.

## Author

**Haziq Afzal**

GitHub: [HaziqBinAfzal](https://github.com/HaziqBinAfzal)

## License

MIT License. See [LICENSE](LICENSE).
