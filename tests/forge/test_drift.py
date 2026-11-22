from forge.services import drift


def test_snapshot_tracks_expected_files():
    result = drift.snapshot()
    assert set(result) == set(drift.TRACKED)


def test_checksum_is_deterministic(tmp_path):
    target = tmp_path / "example.txt"
    target.write_text("forge")
    assert drift.checksum(target) == drift.checksum(target)


def test_baseline_and_clean_check(tmp_path, monkeypatch):
    monkeypatch.setattr(
        drift, "BASELINE", tmp_path / "baseline.json"
    )

    drift.create_baseline()
    result = drift.check_drift()

    assert result["status"] == "clean"
    assert result["changes"] == []


def test_detects_modified_file(tmp_path, monkeypatch):
    source = tmp_path / "config.txt"
    source.write_text("version=1")

    monkeypatch.setattr(drift, "ROOT", tmp_path)
    monkeypatch.setattr(drift, "TRACKED", ("config.txt",))
    monkeypatch.setattr(
        drift, "BASELINE", tmp_path / "baseline.json"
    )

    drift.create_baseline()
    source.write_text("version=2")

    result = drift.check_drift()

    assert result["status"] == "drift_detected"
    assert result["changes"][0]["state"] == "MODIFIED"
