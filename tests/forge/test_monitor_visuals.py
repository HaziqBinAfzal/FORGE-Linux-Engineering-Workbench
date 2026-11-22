from forge.tui.monitor_visuals import plot, bandwidth_rate, measured_bar


def test_plot_is_multiline_and_does_not_invent_values():
    assert 'waiting for samples' in plot([])
    image = plot([0, 20, 40, 60, 80, 100], width=10, height=4)
    assert len(image.splitlines()) == 4
    assert any('\u2800' <= c <= '\u28ff' for c in image)


def test_bandwidth_rate_handles_absent_and_large_values():
    assert bandwidth_rate(None) == 'sampling'
    assert bandwidth_rate(2048) == '2.0 KiB/s'
    assert bandwidth_rate(-1) == '0.0 B/s'


def test_measured_bar_is_bounded():
    assert len(measured_bar(120,10)) == 10
    assert measured_bar(-5,4) == '────'
