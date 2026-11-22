from forge.services.linux_lab import LinuxLab


def test_tail_follow_training(tmp_path):
    lab = LinuxLab(tmp_path)
    (tmp_path / "server.log").write_text("Started\\nReady\\n")

    result = lab.execute("tail -f server.log")

    assert "Started" in result
    assert "Ready" in result
    assert "Ctrl+C" in result
    assert "Training simulation" in result


def test_tail_follow_missing_file(tmp_path):
    lab = LinuxLab(tmp_path)
    assert lab.execute("tail -f missing.log").startswith("ERROR:")
