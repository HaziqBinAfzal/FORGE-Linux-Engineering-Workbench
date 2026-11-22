import pytest

from forge.services.missions import (
    list_missions,
    inspect_mission,
    verify_diagnosis,
)


def test_mission_catalog():
    missions = list_missions()
    assert len(missions) >= 1
    assert missions[0]["id"] == "service-recovery"


def test_mission_has_evidence():
    mission = inspect_mission("service-recovery")
    assert len(mission["evidence"]) >= 3


def test_correct_diagnosis():
    result = verify_diagnosis("service-recovery", "b")
    assert result["status"] == "PASS"
    assert result["verified"] is True


def test_incorrect_diagnosis():
    result = verify_diagnosis("service-recovery", "A")
    assert result["status"] == "FAIL"
    assert result["verified"] is False


def test_invalid_mission():
    with pytest.raises(ValueError):
        inspect_mission("unknown")
