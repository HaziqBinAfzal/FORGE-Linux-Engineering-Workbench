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


def top_processes(limit=8):
    processes = []

    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"] or "unknown",
                "cpu_percent": info["cpu_percent"] or 0,
                "memory_percent": round(
                    info["memory_percent"] or 0, 2
                ),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(
        processes,
        key=lambda item: item["memory_percent"],
        reverse=True,
    )[:limit]
