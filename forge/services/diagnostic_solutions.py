"""Read-only, evidence-based Linux diagnostics and investigation advice."""

def analyze(snapshot):
    resources = (
        ("cpu", "Identify heavy processes and recheck; one CPU reading cannot prove sustained load.",
         ("top", "ps -eo pid,comm,%cpu --sort=-%cpu | head"), "Compare repeated CPU readings."),
        ("memory", "Inspect available RAM, swap and heavy processes before considering a restart.",
         ("free -h", "ps -eo pid,comm,rss,%mem --sort=-%mem | head"), "Recheck RAM and swap usage."),
        ("disk", "Inspect large directories and logs; do not delete files without review.",
         ("df -h /", "du -sh /var/log 2>/dev/null"), "Recheck free space with df -h /."),
    )
    findings=[]
    for key, solution, commands, verify in resources:
        try:
            value=float(snapshot[key]["usage_percent"])
        except (KeyError, TypeError, ValueError):
            findings.append((key,"UNKNOWN","No valid measurement", "Refresh telemetry", (), "Verify measurement source"))
            continue
        if not 0 <= value <= 100:
            findings.append((key,"UNKNOWN",f"Invalid reading: {value:g}%", "Check telemetry source", (), "Confirm valid percentage"))
        elif value >= 75:
            severity="CRITICAL" if value >= 90 else "WARNING"
            findings.append((key,severity,f"Measured {key} utilization: {value:.1f}%",solution,commands,verify))
    priority={"CRITICAL":0,"WARNING":1,"UNKNOWN":2}
    findings.sort(key=lambda row: priority[row[1]])
    if not findings:
        return [("system","OK","All monitored resources under 75%",
                 "Continue monitoring; one healthy snapshot does not rule out other issues.",
                 ("uptime","free -h","df -h /"),"Refresh and compare readings")]
    return findings
