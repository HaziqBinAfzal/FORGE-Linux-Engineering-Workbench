import os
import platform
import socket
import time
from datetime import datetime, timezone

import psutil


def system_snapshot():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    network = psutil.net_io_counters()

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "kernel": platform.release(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": max(
            0, int(time.time() - psutil.boot_time())
        ),
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=0.1),
            "logical_cores": psutil.cpu_count(logical=True),
        },
        "memory": {
            "total_bytes": memory.total,
            "used_bytes": memory.used,
            "available_bytes": memory.available,
            "usage_percent": memory.percent,
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "usage_percent": disk.percent,
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_received": network.bytes_recv,
        },
        "process_count": len(psutil.pids()),
    }


from time import monotonic as _process_clock

# Cached CPU times allow meaningful nonblocking per-process CPU rates.
# The first observation is a baseline, not an estimate of activity.
_PROCESS_CPU_PREVIOUS = {}
_PROCESS_CPU_TIME = None


def top_processes(limit=8):
    """Return memory-ranked processes with measured per-process CPU usage.

    CPU% is relative to one logical CPU, matching psutil's process convention.
    The first sample (or a newly observed process) reports 0 until the next poll.
    PID reuse is guarded by process creation time; disappeared PIDs are purged.
    """
    global _PROCESS_CPU_PREVIOUS, _PROCESS_CPU_TIME

    now = _process_clock()
    elapsed = None if _PROCESS_CPU_TIME is None else now - _PROCESS_CPU_TIME
    current = {}
    processes = []

    for proc in psutil.process_iter(
        ["pid", "name", "memory_percent", "cpu_times", "create_time"]
    ):
        try:
            info = proc.info
            pid = info["pid"]
            times = info.get("cpu_times")
            created = info.get("create_time")
            if times is None:
                continue
            used = float(times.user + times.system)
            previous = _PROCESS_CPU_PREVIOUS.get(pid)
            percent = 0.0
            if (
                previous is not None
                and previous[0] == created
                and elapsed is not None
                and elapsed > 0
            ):
                percent = max(0.0, (used - previous[1]) / elapsed * 100)
            current[pid] = (created, used)
            processes.append({
                "pid": pid,
                "name": info.get("name") or "unknown",
                "cpu_percent": round(percent, 1),
                "memory_percent": round(info.get("memory_percent") or 0, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError, ValueError):
            continue

    _PROCESS_CPU_PREVIOUS = current
    _PROCESS_CPU_TIME = now
    return sorted(
        processes,
        key=lambda item: item["memory_percent"],
        reverse=True,
    )[:max(0, int(limit))]
