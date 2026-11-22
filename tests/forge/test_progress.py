import pytest

from forge.services import progress


@pytest.fixture
def isolated_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(
        progress,
        "PROGRESS_FILE",
        tmp_path / "mission-progress.json",
    )


def test_initial_progress(isolated_progress):
    result = progress.progress_summary()

    assert result["completed"] == 0
    assert result["remaining"] == 4
    assert result["percentage"] == 0


def test_record_completion(isolated_progress):
    result = progress.record_completion("service-recovery")

    assert result["completed"] == 1
    assert result["percentage"] == 25


def test_completion_is_idempotent(isolated_progress):
    progress.record_completion("service-recovery")
    progress.record_completion("service-recovery")

    result = progress.progress_summary()

    assert result["completed"] == 1


def test_multiple_completions(isolated_progress):
    progress.record_completion("service-recovery")
    progress.record_completion("disk-exhaustion")

    result = progress.progress_summary()

    assert result["completed"] == 2
    assert result["percentage"] == 50


def test_unknown_mission_rejected(isolated_progress):
    with pytest.raises(ValueError):
        progress.record_completion("unknown")
