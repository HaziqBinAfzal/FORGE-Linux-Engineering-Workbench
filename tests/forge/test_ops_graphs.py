from types import SimpleNamespace
from forge.tui.ops_graphs import braille_chart, format_rate, DiskRates, AlertJournal


def test_graph_is_bounded_and_blank_before_samples():
    assert braille_chart([], width=20, height=4) == 'waiting for samples'
    lines = braille_chart([20, 40, 10, 90], width=20, height=4).splitlines()
    assert len(lines) == 4
    assert all(len(line) == 20 for line in lines)
    assert any(char != ' ' for line in lines for char in line)


def test_graph_filters_bad_values_and_is_deterministic():
    a = braille_chart([1, None, float('nan'), 5], width=12, height=3)
    assert a == braille_chart([1, None, float('nan'), 5], width=12, height=3)


def test_disk_io_reports_real_counter_deltas():
    times = iter([1., 3.])
    tracker = DiskRates(clock=lambda: next(times))
    assert tracker.sample(SimpleNamespace(read_bytes=100, write_bytes=200)) == (None,None)
    assert tracker.sample(SimpleNamespace(read_bytes=1100, write_bytes=600)) == (500., 200.)


def test_disk_counter_reset_clamps_to_zero():
    times = iter([1., 2.])
    tracker = DiskRates(clock=lambda: next(times))
    tracker.sample(SimpleNamespace(read_bytes=900, write_bytes=900))
    assert tracker.sample(SimpleNamespace(read_bytes=10, write_bytes=20)) == (0., 0.)


def test_alert_transitions_and_recovery():
    journal = AlertJournal()
    journal.observe([{'name': 'CPU pressure', 'severity': 'WARNING'}])
    journal.observe([{'name': 'CPU pressure', 'severity': 'WARNING'}])
    assert len(journal.events) == 1
    journal.observe([])
    assert journal.recent(1) == ['RECOVERED: CPU pressure']


def test_units():
    assert format_rate(None) == 'sampling'
    assert format_rate(1024) == '1.0 KiB/s'
