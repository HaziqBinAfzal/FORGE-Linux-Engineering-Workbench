from forge.tui.ops_graphs import adaptive_ceiling, compact_plot


def test_idle_cpu_is_not_shown_as_full_scale():
    assert adaptive_ceiling([0.0, 0.2, 0.4], minimum=5, percent=True) == 5
    assert 'idle' in compact_plot([0.0, 0.0], width=20, height=3, ceiling=5)


def test_high_percent_chart_never_exceeds_100():
    assert adaptive_ceiling([98], minimum=5, percent=True) == 100


def test_network_scale_is_adaptive():
    assert adaptive_ceiling([200, 400], minimum=1, percent=False) >= 400


def test_chart_is_real_and_bounded():
    plot = compact_plot([2, 4, 8, 4], width=20, height=3, ceiling=10)
    assert 'newest' in plot
    assert len(plot) < 300
