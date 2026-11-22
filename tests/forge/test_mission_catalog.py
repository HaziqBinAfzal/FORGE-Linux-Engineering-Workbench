import pytest

from forge.services.missions import (
    list_missions,
    inspect_mission,
    verify_diagnosis,
)


@pytest.mark.parametrize(
    "mission_id,answer",
    [
        ("service-recovery", "B"),
        ("disk-exhaustion", "A"),
        ("permission-failure", "C"),
        ("network-failure", "B"),
    ],
)
def test_mission_answers(mission_id, answer):
    mission = inspect_mission(mission_id)

    assert len(mission["evidence"]) >= 3

    result = verify_diagnosis(mission_id, answer)

    assert result["status"] == "PASS"
    assert result["verified"] is True


def test_four_missions_available():
    assert len(list_missions()) == 4
