from forge.services.operations_monitor import OperationsMonitor


def snapshot(cpu=10, memory=20, disk=30):
    return {"cpu": {"usage_percent":cpu}, "memory": {"usage_percent":memory}, "disk": {"usage_percent":disk}, "network": {"bytes_received":100,"bytes_sent":200}}


def test_rates_begin_unavailable_then_are_measured():
    monitor = OperationsMonitor()
    first = monitor.sample(snapshot(), counters={"rx":100,"tx":200,"read":300,"write":400}, moment=10)
    assert first['rates']['rx'] is None
    second = monitor.sample(snapshot(), counters={"rx":120,"tx":260,"read":340,"write":460}, moment=12)
    assert second['rates'] == {"rx":10,"tx":30,"read":20,"write":30}


def test_alert_transition_avoids_spamming_and_recovers():
    monitor = OperationsMonitor()
    monitor.sample(snapshot(cpu=80), counters={}, moment=1)
    assert len(monitor.events) == 1
    monitor.sample(snapshot(cpu=82), counters={}, moment=2)
    assert len(monitor.events) == 1
    monitor.sample(snapshot(cpu=92), counters={}, moment=3)
    assert len(monitor.events) == 2
    monitor.sample(snapshot(cpu=22), counters={}, moment=4)
    assert len(monitor.events) == 3
    assert monitor.events[0]['kind'] == 'recovery'


def test_reset_counters_not_reported_negative():
    monitor = OperationsMonitor()
    monitor.sample(snapshot(), counters={"rx":100,"tx":30}, moment=1)
    out = monitor.sample(snapshot(), counters={"rx":10,"tx":50}, moment=2)
    assert out['rates']['rx'] is None
    assert out['rates']['tx'] == 20


def test_history_bounded():
    monitor = OperationsMonitor(history=3)
    for i in range(10):
        monitor.sample(snapshot(cpu=i), counters={}, moment=i+1)
    assert list(monitor.history['cpu']) == [7,8,9]
