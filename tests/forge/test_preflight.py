from forge.services.preflight import result, run_preflight


def test_result_structure():
    item = result("Example", "PASS", "Verified")
    assert item == {
        "name": "Example",
        "status": "PASS",
        "detail": "Verified",
    }


def test_preflight_report_structure():
    report = run_preflight()

    assert report["overall"] in {"PASS", "WARN", "FAIL"}
    assert report["checked"] == len(report["checks"])
    assert report["checked"] == 5


def test_preflight_checks_have_valid_statuses():
    report = run_preflight()

    for check in report["checks"]:
        assert check["status"] in {"PASS", "WARN", "FAIL"}
        assert check["name"]
        assert check["detail"]


def test_preflight_overall_matches_checks():
    report = run_preflight()
    statuses = {item["status"] for item in report["checks"]}

    expected = (
        "FAIL" if "FAIL" in statuses
        else "WARN" if "WARN" in statuses
        else "PASS"
    )

    assert report["overall"] == expected
