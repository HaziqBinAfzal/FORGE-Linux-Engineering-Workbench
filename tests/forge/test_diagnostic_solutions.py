from forge.services.diagnostic_solutions import analyze

def sample(cpu=25, memory=40, disk=30):
    return {k: {"usage_percent": v} for k,v in (("cpu",cpu),("memory",memory),("disk",disk))}

def test_healthy_snapshot():
    assert analyze(sample())[0][1] == "OK"

def test_memory_warning_has_guidance():
    row=analyze(sample(memory=80))[0]
    assert row[1] == "WARNING" and "free -h" in row[4] and row[5]

def test_critical_first():
    rows=analyze(sample(cpu=80,disk=96))
    assert rows[0][0] == "disk" and rows[0][1] == "CRITICAL"

def test_bad_telemetry_not_healthy():
    assert analyze(sample(cpu=130))[0][1] == "UNKNOWN"
    assert analyze({"cpu":{},"memory":{},"disk":{}})[0][1] == "UNKNOWN"
