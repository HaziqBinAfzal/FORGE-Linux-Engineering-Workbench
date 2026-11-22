"""Read-only Linux signals with rate calculation and bounded alert transitions."""
from collections import deque
from time import monotonic
import psutil


class OperationsMonitor:
    """Collect extra system metrics. Monitoring never runs a shell or changes host state."""
    def __init__(self, history=64, clock=monotonic):
        self.clock = clock
        self.history = {name: deque(maxlen=history) for name in ("cpu", "memory", "disk", "rx", "tx", "read", "write")}
        self.events = deque(maxlen=18)
        self.previous = None
        self.previous_states = {}
        self.samples = 0

    def sample(self, snapshot, *, counters=None, moment=None):
        """Return observed rates and transitions; first sample has unavailable rates."""
        now = self.clock() if moment is None else moment
        if counters is None:
            try:
                disk = psutil.disk_io_counters()
            except (OSError, RuntimeError, PermissionError):
                disk = None
            counters = {
                "read": getattr(disk, "read_bytes", None),
                "write": getattr(disk, "write_bytes", None),
                "rx": snapshot.get("network", {}).get("bytes_received"),
                "tx": snapshot.get("network", {}).get("bytes_sent"),
            }
        rates = {key: None for key in ("rx", "tx", "read", "write")}
        if self.previous:
            elapsed = now - self.previous[0]
            if elapsed > 0:
                for key in rates:
                    old, new = self.previous[1].get(key), counters.get(key)
                    if old is not None and new is not None and new >= old:
                        rates[key] = (new - old) / elapsed
        self.previous = (now, dict(counters))
        self.samples += 1
        for key in ("cpu", "memory", "disk"):
            self.history[key].append(float(snapshot[key]["usage_percent"]))
        for key in rates:
            self.history[key].append(rates[key] or 0)
        alerts = []
        for key in ("cpu", "memory", "disk"):
            value = float(snapshot[key]["usage_percent"])
            level = "critical" if value >= 90 else "warning" if value >= 75 else "normal"
            if self.previous_states.get(key) != level:
                if level != "normal":
                    message = f"{key.upper()} {level.upper()}  {value:.1f}%"
                    self.events.appendleft({"kind": level, "text": message, "sample": self.samples})
                elif self.previous_states.get(key) in ("warning", "critical"):
                    self.events.appendleft({"kind": "recovery", "text": f"{key.upper()} back below 75%  {value:.1f}%", "sample": self.samples})
            self.previous_states[key] = level
            if level != "normal":
                alerts.append({"key": key, "level": level, "value": value})
        return {"rates": rates, "alerts": alerts, "events": list(self.events), "samples": self.samples}
