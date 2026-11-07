
"""Verify API Sentinel reports are consistent and deterministic."""

from dataclasses import FrozenInstanceError, asdict
from unittest.mock import patch

import httpx
import pytest

from api_sentinel.runner import ContractReport, check_contract


def test_success_report(fixture_server):
    report = check_contract(
        f"{fixture_server}/health",
        expected_status=200,
        required_fields={"status": "string"},
        expected_values={"status": "ok"},
    )

    assert report.passed is True
    assert report.error is None
    assert report.status_result is not None
    assert report.status_result.passed is True
    assert all(result.passed for result in report.json_results)


def test_status_mismatch_report(fixture_server):
    report = check_contract(
        f"{fixture_server}/health",
        expected_status=201,
    )

    assert report.passed is False
    assert report.error is None
    assert report.status_result is not None
    assert report.status_result.passed is False
    assert report.json_results == ()


def test_json_type_failure_report(fixture_server):
    report = check_contract(
        f"{fixture_server}/wrong-type",
        expected_status=200,
        required_fields={"status": "string"},
    )

    assert report.passed is False
    assert report.error is None
    assert report.status_result is not None
    assert report.status_result.passed is True
    assert any(not result.passed for result in report.json_results)


def test_invalid_json_report(fixture_server):
    report = check_contract(
        f"{fixture_server}/invalid-json",
        expected_status=200,
        required_fields={"status": "string"},
    )

    assert report.passed is False
    assert report.error == "invalid_json"
    assert report.status_result is not None
    assert report.json_results == ()


@pytest.mark.parametrize(
    ("exception", "expected_error"),
    [
        (httpx.ConnectError("Connection refused"), "request_error"),
        (httpx.ConnectTimeout("Timed out"), "request_timeout"),
        (httpx.ReadTimeout("Read timed out"), "request_timeout"),
    ],
)
def test_network_failure_report(exception, expected_error):
    url = "http://127.0.0.1:8765/unreachable"

    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=exception,
    ):
        report = check_contract(url, expected_status=200)

    assert report.url == url
    assert report.passed is False
    assert report.error == expected_error
    assert report.status_result is None
    assert report.json_results == ()


def test_report_is_immutable():
    report = ContractReport(
        url="http://example.test",
        passed=False,
        status_result=None,
        json_results=(),
        error="request_error",
    )

    with pytest.raises(FrozenInstanceError):
        report.passed = True


def test_report_serializes_to_dictionary(fixture_server):
    report = check_contract(
        f"{fixture_server}/health",
        expected_status=200,
        required_fields={"status": "string"},
    )

    result = asdict(report)

    assert isinstance(result, dict)
    assert result["url"] == f"{fixture_server}/health"
    assert result["passed"] is True
    assert result["error"] is None
    assert isinstance(result["status_result"], dict)
    assert isinstance(result["json_results"], tuple)


def test_repeated_requests_produce_consistent_results(fixture_server):
    reports = [
        check_contract(
            f"{fixture_server}/health",
            expected_status=200,
            required_fields={"status": "string"},
            expected_values={"status": "ok"},
        )
        for _ in range(3)
    ]

    assert reports[0] == reports[1] == reports[2]
    assert all(report.passed for report in reports)
