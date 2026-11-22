from types import SimpleNamespace
from forge.services import telemetry


class FakeProcess:
    def __init__(self, pid, created, cpu, memory=1):
        self.info = {
            "pid": pid, "name": f"proc-{pid}", "create_time": created,
            "cpu_times": SimpleNamespace(user=cpu, system=0),
            "memory_percent": memory,
        }


def test_cpu_rates_are_nonblocking_and_measured(monkeypatch):
    clock = iter([10.0, 12.0])
    frames = iter([
        [FakeProcess(100, 1, 4, 20), FakeProcess(200, 1, 2, 3)],
        [FakeProcess(100, 1, 5, 20), FakeProcess(200, 1, 2.5, 3)],
    ])
    monkeypatch.setattr(telemetry, "_process_clock", lambda: next(clock))
    monkeypatch.setattr(telemetry.psutil, "process_iter", lambda attrs: iter(next(frames)))
    monkeypatch.setattr(telemetry, "_PROCESS_CPU_PREVIOUS", {})
    monkeypatch.setattr(telemetry, "_PROCESS_CPU_TIME", None)
    assert telemetry.top_processes()[0]["cpu_percent"] == 0
    rows = telemetry.top_processes()
    assert rows[0]["cpu_percent"] == 50
    assert rows[1]["cpu_percent"] == 25
    assert rows[0]["memory_percent"] == 20


def test_pid_reuse_and_disappearance_do_not_reuse_old_cpu(monkeypatch):
    clock = iter([10.0, 11.0, 12.0])
    frames = iter([
        [FakeProcess(11, 1, 10)],
        [FakeProcess(11, 2, 15)],
        [],
    ])
    monkeypatch.setattr(telemetry, "_process_clock", lambda: next(clock))
    monkeypatch.setattr(telemetry.psutil, "process_iter", lambda attrs: iter(next(frames)))
    monkeypatch.setattr(telemetry, "_PROCESS_CPU_PREVIOUS", {})
    monkeypatch.setattr(telemetry, "_PROCESS_CPU_TIME", None)
    assert telemetry.top_processes()[0]["cpu_percent"] == 0
    assert telemetry.top_processes()[0]["cpu_percent"] == 0
    assert telemetry.top_processes() == []
    assert telemetry._PROCESS_CPU_PREVIOUS == {}
