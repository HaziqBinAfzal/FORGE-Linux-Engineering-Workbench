from forge.services.linux_lab import LinuxLab


def test_pwd(tmp_path):
    lab = LinuxLab(tmp_path)
    assert lab.execute("pwd") == "/"


def test_mkdir_and_cd(tmp_path):
    lab = LinuxLab(tmp_path)
    assert lab.execute("mkdir -p app/logs") == "Directory created"
    assert lab.execute("cd app") == "/app"
    assert lab.execute("pwd") == "/app"


def test_touch_and_ls(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch config.conf")
    assert "config.conf" in lab.execute("ls")


def test_copy_and_move(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch original.txt")
    assert lab.execute("cp original.txt copy.txt") == "File copied"
    assert lab.execute("mv copy.txt backup.txt") == "File moved"
    assert (tmp_path / "backup.txt").exists()


def test_remove_file(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch temp.txt")
    assert lab.execute("rm temp.txt") == "File removed"
    assert not (tmp_path / "temp.txt").exists()


def test_prevent_directory_escape(tmp_path):
    lab = LinuxLab(tmp_path)
    result = lab.execute("cd ../../")
    assert "Access denied" in result


def test_reject_shell_commands(tmp_path):
    lab = LinuxLab(tmp_path)
    result = lab.execute("sudo apt update")
    assert "not supported" in result


def test_reject_recursive_deletion(tmp_path):
    lab = LinuxLab(tmp_path)
    result = lab.execute("rm -rf /")
    assert "disabled" in result
