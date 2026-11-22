from forge.services.linux_lab import LinuxLab


def test_lab_identity(tmp_path):
    lab = LinuxLab(tmp_path)
    assert lab.execute("whoami") == "forge"
    assert "uid=1000(forge)" in lab.execute("id")


def test_chmod_permissions(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch config.conf")

    assert lab.execute("chmod 754 config.conf").startswith(
        "Permissions changed"
    )

    result = lab.execute("ls -l config.conf")
    assert "-rwxr-xr--" in result


def test_chmod_rejects_invalid_mode(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch config.conf")
    assert lab.execute("chmod 999 config.conf").startswith("ERROR:")


def test_head_tail_less(tmp_path):
    lab = LinuxLab(tmp_path)
    (tmp_path / "notes.txt").write_text(
        "one\ntwo\nthree\nfour\n"
    )

    assert lab.execute("head -n 2 notes.txt") == "one\ntwo"
    assert lab.execute("tail -n 2 notes.txt") == "three\nfour"
    assert "three" in lab.execute("less notes.txt")


def test_ls_hidden_files(tmp_path):
    lab = LinuxLab(tmp_path)
    lab.execute("touch .env")
    lab.execute("touch visible.txt")

    assert ".env" not in lab.execute("ls")
    assert ".env" in lab.execute("ls -a")


def test_reject_outside_sandbox(tmp_path):
    lab = LinuxLab(tmp_path)
    result = lab.execute("chmod 777 ../../outside.txt")
    assert result.startswith("ERROR:")
