from forge.services.linux_lab import LinuxLab


def test_interactive_removal_confirmation(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch example.txt")
    prompt = lab.execute("rm -i example.txt")
    assert "Type yes" in prompt
    assert (tmp_path / "example.txt").exists()
    assert lab.execute("no") == "Deletion cancelled"
    assert (tmp_path / "example.txt").exists()
    lab.execute("rm -i example.txt")
    assert lab.execute("yes") == "File removed after confirmation"
    assert not (tmp_path / "example.txt").exists()


def test_recursive_deletion_disabled(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch example.txt")
    assert lab.execute("rm -rf example.txt").startswith("ERROR:")
    assert (tmp_path / "example.txt").exists()
