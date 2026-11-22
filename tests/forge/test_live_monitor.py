from forge.services.live_monitor import LiveMonitor, sparkline

def sample(cpu=10, memory=20, disk=30, rx=0, tx=0):
    return {"cpu": {"usage_percent": cpu},
            "memory": {"usage_percent": memory},
            "disk": {"usage_percent": disk},
            "network": {"bytes_received": rx, "bytes_sent": tx}}

def test_resource_alerts_and_recommendations():
    m=LiveMonitor(clock=lambda: 10)
    out=m.update(sample(cpu=91,memory=82,disk=20))
    assert out["health"]=="CRITICAL"
    assert len(out["findings"])==2
    assert all(item["action"] for item in out["findings"])

def test_healthy_resources():
    m=LiveMonitor(clock=lambda: 10)
    assert m.update(sample())["health"]=="HEALTHY"

def test_network_delta_uses_elapsed_time():
    times=iter([10,12])
    m=LiveMonitor(clock=lambda: next(times))
    m.update(sample(rx=100,tx=200))
    assert m.rx_rate is None
    m.update(sample(rx=2100,tx=1200))
    assert m.rx_rate==1000
    assert m.tx_rate==500

def test_network_counter_reset_never_negative():
    times=iter([10,11])
    m=LiveMonitor(clock=lambda: next(times))
    m.update(sample(rx=5000,tx=5000))
    m.update(sample(rx=200,tx=300))
    assert m.rx_rate==0 and m.tx_rate==0

def test_history_bounded_and_sparkline():
    m=LiveMonitor(history=3,clock=lambda: 10)
    for n in range(6): m.update(sample(cpu=n*10))
    assert len(m.samples["cpu"])==3
    assert len(sparkline(m.samples["cpu"]))==3
