"""Honest terminal-native plots for live measured telemetry."""
from math import isfinite

STEPS = "▁▂▃▄▅▆▇█"


def plot(values, *, width=48, height=7, ceiling=100.0):
    """Plot measured values on a Unicode braille grid. No interpolation or invented data."""
    values = [float(v) for v in values if isinstance(v, (int, float)) and isfinite(v)]
    if not values:
        return "\n".join(["  waiting for samples".ljust(width)] + ["" for _ in range(height-1)])
    width = max(4, width)
    height = max(2, height)
    vals = values[-width * 2:]
    if len(vals) == 1:
        vals = vals * 2
    ceiling = max(1.0, float(ceiling), max(vals))
    dots = [[0 for _ in range(width)] for _ in range(height)]
    n = len(vals)
    for i, value in enumerate(vals):
        x = round(i * (width*2-1) / max(1, n-1))
        y = round((1 - max(0, min(value/ceiling, 1))) * (height*4-1))
        col, row = x//2, y//4
        bit = ((0x01,0x02,0x04,0x40),(0x08,0x10,0x20,0x80))[x%2][y%4]
        dots[row][col] |= bit
    return "\n".join("".join(chr(0x2800+bit) if bit else "·" for bit in row) for row in dots)


def bandwidth_rate(value):
    if value is None:
        return "sampling"
    value = max(0, float(value))
    for unit in ("B/s", "KiB/s", "MiB/s", "GiB/s"):
        if value < 1024 or unit == "GiB/s":
            return f"{value:.1f} {unit}"
        value /= 1024
    return "unavailable"


def measured_bar(value, width=22):
    value = min(100, max(0, float(value)))
    count = round(value / 100 * width)
    return "━" * count + "─" * (width-count)
