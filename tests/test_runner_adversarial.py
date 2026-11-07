
"""Adversarial tests for API Sentinel's contract runner."""

from unittest.mock import patch

import httpx
import pytest

from api_sentinel.runner import check_contract


def test_connection_failure_returns_structured_report():
    """Connection failures must not crash the contract runner."""
    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        report = check_contract(
            "http://127.0.0.1:8765/unreachable",
            expected_status=200,
        )

    assert report.passed is False
    assert report.error == "request_error"
    assert report.status_result is None
    assert report.json_results == ()


def test_dns_failure_returns_structured_report():
    """DNS failures must produce a request error report."""
    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=httpx.ConnectError("Name resolution failed"),
    ):
        report = check_contract(
            "http://invalid.example.test/health",
            expected_status=200,
        )

    assert report.passed is False
    assert report.error == "request_error"


def test_network_timeout_returns_structured_report():
    """Connection timeouts must produce a timeout failure report."""
    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=httpx.ConnectTimeout("Connection timed out"),
    ):
        report = check_contract(
            "http://127.0.0.1:8765/health",
            expected_status=200,
        )

    assert report.passed is False
    assert report.error == "request_timeout"
    assert report.status_result is None


@pytest.mark.parametrize("invalid_status", [99, 600, True, "200"])
def test_invalid_contract_status_rejected(invalid_status):
    """Invalid expected statuses must be rejected before networking."""
    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        with pytest.raises((TypeError, ValueError)):
            check_contract(
                "http://127.0.0.1:8765/health",
                expected_status=invalid_status,
            )

        mock_get.assert_not_called()


def test_connection_failure_preserves_requested_url():
    """Failure reports must preserve the requested URL."""
    url = "http://127.0.0.1:8765/unreachable"

    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        report = check_contract(url, expected_status=200)

    assert report.url == url
    assert report.passed is False
