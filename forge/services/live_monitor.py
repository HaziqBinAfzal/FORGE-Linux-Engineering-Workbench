"""Read-only local host monitoring with bounded measured trend history."""
from collections import deque
from datetime import datetime
from time import monotonic

def sparkline(values, width=30):
    samples = list(values)[-width:]
    if not samples:
        return "waiting for samples"
    ticks = "▁▂▃▄▅▆▇█"
    return "".join(ticks[min(7, max(0, int(float(v) / 100 * 7)))] for v in samples)

class LiveMonitor:
    def __init__(self, history=48, clock=monotonic):
        self.clock = clock
        self.samples = {key: deque(maxlen=history) for key in ("cpu", "memory", "disk")}
        self.previous_network = None
        self.previous_time = None
        self.rx_rate = None
        self.tx_rate = None
        self.last = None

    def update(self, snapshot):
        now = self.clock()
        for key in self.samples:
            self.samples[key].append(min(100, max(0, float(snapshot[key]["usage_percent"]))))
        network = snapshot.get("network", {})
        rx = int(network.get("bytes_received", 0))
        tx = int(network.get("bytes_sent", 0))
        if self.previous_network is not None and self.previous_time is not None:
            elapsed = now - self.previous_time
            if elapsed > 0:
                self.rx_rate = max(0, rx - self.previous_network[0]) / elapsed
                self.tx_rate = max(0, tx - self.previous_network[1]) / elapsed
        self.previous_network = (rx, tx)
        self.previous_time = now
        self.last = snapshot
        return self.assess(snapshot)

    @staticmethod
    def rate(value):
        if value is None:
            return "sampling…"
        for unit in ("B/s", "KiB/s", "MiB/s", "GiB/s"):
            if value < 1024 or unit == "GiB/s":
                return f"{value:.1f} {unit}"
            value /= 1024

    def assess(self, snapshot):
        findings = []
        recommendations = {
            "cpu": ("CPU pressure", "Inspect busy processes: top or ps aux --sort=-%cpu | head"),
            "memory": ("Memory pressure", "Review memory consumers: free -h and ps aux --sort=-%mem | head"),
            "disk": ("Storage pressure", "Inspect filesystem usage: df -h and du -sh <directory>"),
        }
        for key in ("cpu", "memory", "disk"):
            value = float(snapshot[key]["usage_percent"])
            if value >= 90:
                severity = "CRITICAL"
            elif value >= 75:
                severity = "WARNING"
            else:
                continue
            title, suggestion = recommendations[key]
            findings.append({"severity": severity, "name": title, "usage": value, "action": suggestion})
        if any(f["severity"] == "CRITICAL" for f in findings):
            overall = "CRITICAL"
        elif findings:
            overall = "ATTENTION"
        else:
            overall = "HEALTHY"
        return {"health": overall, "findings": findings}
