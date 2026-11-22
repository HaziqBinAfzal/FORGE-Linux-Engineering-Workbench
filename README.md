# FORGE — Linux Engineering Workbench

Interactive Linux command-line training for DecodeLabs DevOps Project 1.

## Features
- Isolated Linux command practice
- Official six-step Web App Setup mission
- System overview and process monitoring
- Diagnostics and engineering troubleshooting
- Drift analysis and preflight checks
- Guided engineering missions

## Supported Commands
pwd, cd, ls, mkdir, touch, cp, mv, rm -i, cat, less, head, tail, chmod, chown, whoami, id, ssh

## Installation
    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt

## Launch
    ./forge-run

## Run Tests
    PYTHONPATH=. .venv/bin/python -m pytest tests/forge -q

## Safety
FORGE uses an isolated training filesystem.
SSH and ownership changes are simulated.
Log following is a bounded educational simulation.
Unrestricted destructive deletion is disabled.

## License
Pending selection.
