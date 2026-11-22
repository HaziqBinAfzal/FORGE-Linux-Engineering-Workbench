from dataclasses import dataclass
from typing import Literal

MissionStatus = Literal["PASS", "FAIL"]


@dataclass(frozen=True)
class Mission:
    id: str
    title: str
    scenario: str
    evidence: tuple[str, ...]
    question: str
    expected: str
    explanation: str


MISSIONS = {
    "service-recovery": Mission(
        id="service-recovery",
        title="Service Recovery",
        scenario=(
            "A simulated Linux web service fails to start "
            "after a configuration change."
        ),
        evidence=(
            "systemctl status forge-web: failed (exit-code)",
            "journalctl: configuration validation failed",
            "nginx: [emerg] invalid directive 'listen_port'",
            "nginx -t: configuration test failed",
        ),
        question=(
            "Which root cause best explains the failure?\n"
            "A. Insufficient disk space\n"
            "B. Invalid configuration directive\n"
            "C. Network cable disconnected"
        ),
        expected="B",
        explanation=(
            "The simulated service fails configuration validation "
            "because 'listen_port' is not a valid nginx directive. "
            "The appropriate next step would be to correct the "
            "configuration and validate it before restarting."
        ),
    ),
}


def list_missions():
    return [
        {
            "id": mission.id,
            "title": mission.title,
            "scenario": mission.scenario,
        }
        for mission in MISSIONS.values()
    ]


def inspect_mission(mission_id):
    mission = MISSIONS.get(mission_id)

    if mission is None:
        raise ValueError(f"Unknown mission: {mission_id}")

    return {
        "id": mission.id,
        "title": mission.title,
        "scenario": mission.scenario,
        "evidence": list(mission.evidence),
        "question": mission.question,
    }


def verify_diagnosis(mission_id, answer):
    mission = MISSIONS.get(mission_id)

    if mission is None:
        raise ValueError(f"Unknown mission: {mission_id}")

    normalized = str(answer).strip().upper()

    if normalized not in {"A", "B", "C"}:
        return {
            "status": "FAIL",
            "verified": False,
            "explanation": "Choose A, B, or C.",
        }

    correct = normalized == mission.expected

    return {
        "status": "PASS" if correct else "FAIL",
        "verified": correct,
        "explanation": (
            mission.explanation
            if correct
            else "Diagnosis not verified. Re-examine the evidence."
        ),
    }


MISSIONS.update({
    "disk-exhaustion": Mission(
        id="disk-exhaustion",
        title="Disk Exhaustion",
        scenario=(
            "A Linux application can no longer write logs "
            "or create temporary files."
        ),
        evidence=(
            "df -h: /dev/sda1 100% used",
            "journalctl: No space left on device",
            "df -i: inode usage 24%",
            "systemctl: application failed to write state",
        ),
        question=(
            "What is the most likely root cause?\n"
            "A. Filesystem capacity exhausted\n"
            "B. Incorrect DNS configuration\n"
            "C. Missing execute permission"
        ),
        expected="A",
        explanation=(
            "The filesystem has exhausted its available storage "
            "blocks, while inode capacity remains available. "
            "Investigate disk usage and safely reclaim space."
        ),
    ),

    "permission-failure": Mission(
        id="permission-failure",
        title="Permission Failure",
        scenario=(
            "A deployed application cannot read its "
            "configuration file."
        ),
        evidence=(
            "ls -l: -rw------- root root app.conf",
            "Application runs as user forgeapp",
            "journalctl: Permission denied reading app.conf",
            "File exists and contains valid configuration",
        ),
        question=(
            "What best explains the failure?\n"
            "A. Incorrect DNS records\n"
            "B. Insufficient disk space\n"
            "C. File access permissions"
        ),
        expected="C",
        explanation=(
            "The configuration file is readable only by root, "
            "but the application runs under a different account. "
            "Apply the minimum required permissions or group access."
        ),
    ),

    "network-failure": Mission(
        id="network-failure",
        title="Network Connectivity",
        scenario=(
            "A Linux host can reach an internal service by "
            "IP address but not by hostname."
        ),
        evidence=(
            "ping 10.0.0.20: successful",
            "getent hosts internal.example: no result",
            "resolvectl status: DNS server unavailable",
            "ip route: default route present",
        ),
        question=(
            "Which subsystem should be investigated first?\n"
            "A. Disk storage\n"
            "B. DNS resolution\n"
            "C. CPU scheduling"
        ),
        expected="B",
        explanation=(
            "IP connectivity is working, but hostname resolution "
            "fails. Investigate resolver configuration, DNS server "
            "availability, and name records."
        ),
    ),
})


MISSIONS.update({
    "disk-exhaustion": Mission(
        id="disk-exhaustion",
        title="Disk Exhaustion",
        scenario=(
            "A Linux application can no longer write logs "
            "or create temporary files."
        ),
        evidence=(
            "df -h: /dev/sda1 100% used",
            "journalctl: No space left on device",
            "df -i: inode usage 24%",
            "systemctl: application failed to write state",
        ),
        question=(
            "What is the most likely root cause?\n"
            "A. Filesystem capacity exhausted\n"
            "B. Incorrect DNS configuration\n"
            "C. Missing execute permission"
        ),
        expected="A",
        explanation=(
            "The filesystem has exhausted its available storage "
            "blocks, while inode capacity remains available. "
            "Investigate disk usage and safely reclaim space."
        ),
    ),

    "permission-failure": Mission(
        id="permission-failure",
        title="Permission Failure",
        scenario=(
            "A deployed application cannot read its "
            "configuration file."
        ),
        evidence=(
            "ls -l: -rw------- root root app.conf",
            "Application runs as user forgeapp",
            "journalctl: Permission denied reading app.conf",
            "File exists and contains valid configuration",
        ),
        question=(
            "What best explains the failure?\n"
            "A. Incorrect DNS records\n"
            "B. Insufficient disk space\n"
            "C. File access permissions"
        ),
        expected="C",
        explanation=(
            "The configuration file is readable only by root, "
            "but the application runs under a different account. "
            "Apply the minimum required permissions or group access."
        ),
    ),

    "network-failure": Mission(
        id="network-failure",
        title="Network Connectivity",
        scenario=(
            "A Linux host can reach an internal service by "
            "IP address but not by hostname."
        ),
        evidence=(
            "ping 10.0.0.20: successful",
            "getent hosts internal.example: no result",
            "resolvectl status: DNS server unavailable",
            "ip route: default route present",
        ),
        question=(
            "Which subsystem should be investigated first?\n"
            "A. Disk storage\n"
            "B. DNS resolution\n"
            "C. CPU scheduling"
        ),
        expected="B",
        explanation=(
            "IP connectivity is working, but hostname resolution "
            "fails. Investigate resolver configuration, DNS server "
            "availability, and name records."
        ),
    ),
})
