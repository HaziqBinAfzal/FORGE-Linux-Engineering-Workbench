"""Tiny, dependency-free live plots and read-only operational state for FORGE."""
from collections import deque
from math import isfinite
from time import monotonic


def braille_chart(values, *, width=48, height=7, ceiling=100.0):
    """Plot sampled points, without extrapolation, using 2x4 dot braille cells."""
    width = max(4, min(120, int(width)))
    height = max(2, min(24, int(height)))
    raw = list(values)[-width * 2:]
    samples = [float(v) if isinstance(v, (int, float)) and isfinite(v) else 0.0 for v in raw]
    cells = [[0] * width for _ in range(height)]
    if not samples:
        return "waiting for samples"
    scale = max(1.0, float(ceiling), max(samples))
    span = width * 2 - 1
    rows = height * 4 - 1

    def dot(x, y):
        x = max(0, min(span, x))
        y = max(0, min(rows, y))
        bits = ((1, 2, 4, 64), (8, 16, 32, 128))
        cells[y // 4][x // 2] |= bits[x % 2][y % 4]

    # Keep the newest data aligned at the right, as in production resource monitors.
    start = span - (len(samples) - 1)
    previous = None
    for index, sample in enumerate(samples):
        x = start + index
        y = round((1 - max(0.0, min(1.0, sample / scale))) * rows)
        if previous is not None:
            x0, y0 = previous
            steps = max(abs(x-x0), abs(y-y0), 1)
            for k in range(steps + 1):
                dot(round(x0 + (x-x0)*k/steps), round(y0 + (y-y0)*k/steps))
        dot(x, y)
        previous = (x, y)
    return "\n".join("".join(chr(0x2800 + v) if v else " " for v in row) for row in cells)


def format_rate(value):
    if value is None:
        return "sampling"
    value = max(0.0, float(value))
    for unit in ("B/s", "KiB/s", "MiB/s", "GiB/s"):
        if value < 1024 or unit == "GiB/s":
            return f"{value:.1f} {unit}"
        value /= 1024


class DiskRates:
    """Disk I/O counter deltas; first sample is unknown, never a fabricated zero rate."""
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.last = None
        self.last_time = None

    def sample(self, counters):
        if counters is None:
            return None, None
        now = self.clock()
        present = (int(counters.read_bytes), int(counters.write_bytes))
        rates = (None, None)
        if self.last is not None and self.last_time is not None and now > self.last_time:
            dt = now - self.last_time
            rates = (max(0, present[0] - self.last[0])/dt,
                     max(0, present[1] - self.last[1])/dt)
        self.last, self.last_time = present, now
        return rates


class AlertJournal:
    """Track observed alert transitions, not fictional incidents."""
    def __init__(self, limit=40):
        self.events = deque(maxlen=limit)
        self.current = {}

    def observe(self, findings):
        next_state = {finding["name"]: finding["severity"] for finding in findings}
        for name, severity in next_state.items():
            if self.current.get(name) != severity:
                self.events.appendleft(f"{severity}: {name}")
        for name in self.current.keys() - next_state.keys():
            self.events.appendleft(f"RECOVERED: {name}")
        self.current = next_state

    def recent(self, limit=3):
        return list(self.events)[:limit]


def adaptive_ceiling(values, *, minimum=5.0, percent=False):
    """Conservative readable chart scale. Never exaggerate an idle reading as high usage."""
    vals = [float(v) for v in values if isinstance(v, (int, float)) and isfinite(v)]
    peak = max(vals, default=0.0)
    limit = max(float(minimum), peak * 1.25)
    if percent:
        limit = min(100.0, limit)
    if limit <= 10:
        return float(int(limit + 0.999))
    step = 5 if limit <= 50 else 10
    return float(int((limit + step - 0.000001) // step) * step)


def compact_plot(values, *, width, height, ceiling, idle_threshold=0.0):
    """Braille plot with explicitly labelled scale and honest idle/flat interpretation."""
    vals = list(values)
    width = max(4, int(width))
    height = max(2, int(height))
    if not vals:
        return '[#888888]Collecting samples…[/]'
    peak = max(float(v) for v in vals if isinstance(v, (int, float)))
    note = '  /  idle' if peak <= idle_threshold else ''
    plot = braille_chart(vals, width=width, height=height, ceiling=ceiling)
    # Built-in braille is actual sampled history; 0 lies at the bottom of the plot.
    return f'[#777777]{ceiling:g}  ─{note}[/]\n[#A7BAAC]{plot}[/]\n[#777777]0  ─  newest →[/]'
