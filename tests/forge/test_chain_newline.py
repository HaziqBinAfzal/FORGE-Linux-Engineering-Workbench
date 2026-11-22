
from forge.services.linux_lab import LinuxLab


def test_chained_commands_use_real_newlines(tmp_path):
    lab = LinuxLab(tmp_path)
    result = lab.execute("pwd && pwd")

    newline = chr(10)
    literal_escape = chr(92) + "n"

    assert result == "/" + newline + "/"
    assert literal_escape not in result


def test_chained_directory_listing_format(tmp_path):
    lab = LinuxLab(tmp_path)

    lab.execute("mkdir -p /app/logs")
    lab.execute("touch /app/config.conf")

    result = lab.execute("pwd && ls -R /app")

    newline = chr(10)
    literal_escape = chr(92) + "n"

    assert result.startswith("/" + newline)
    assert "/app/config.conf" in result
    assert "/app/logs" in result
    assert literal_escape not in result
