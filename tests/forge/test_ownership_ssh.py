from forge.services.linux_lab import LinuxLab


def test_chown_training(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch config.conf")

    result = lab.execute("chown deploy config.conf")

    assert "Training simulation" in result
    assert "deploy" in result
    assert lab._simulated_owners[str(tmp_path / "config.conf")] == "deploy"


def test_chown_missing_file(tmp_path):
    lab = LinuxLab(tmp_path)
    assert lab.execute("chown deploy missing.conf").startswith("ERROR:")


def test_ssh_training(tmp_path):
    lab = LinuxLab(tmp_path)

    result = lab.execute("ssh admin@example.com")

    assert "Training simulation" in result
    assert "No network connection" in result


def test_ssh_invalid_target(tmp_path):
    lab = LinuxLab(tmp_path)
    assert lab.execute("ssh invalid").startswith("ERROR:")
