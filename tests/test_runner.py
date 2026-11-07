"""Integration tests for API Sentinel's contract runner."""

import pytest

from api_sentinel.runner import check_contract


def test_valid_contract(fixture_server):
    """A correct response must pass its contract."""
    report = check_contract(
        f"{fixture_server}/health",
        expected_status=200,
        required_fields={"status": "string"},
        expected_values={"status": "ok"},
    )

    assert report.passed is True
    assert report.error is None
    assert report.status_result.passed is True
    assert all(result.passed for result in report.json_results)


def test_status_mismatch(fixture_server):
    """An unexpected HTTP status must fail."""
    report = check_contract(
        f"{fixture_server}/not-found",
        expected_status=200,
    )

    assert report.passed is False
    assert report.status_result.passed is False


def test_expected_server_error(fixture_server):
    """An expected HTTP 500 can satisfy a contract."""
    report = check_contract(
        f"{fixture_server}/server-error",
        expected_status=500,
    )

    assert report.passed is True


def test_invalid_json(fixture_server):
    """Malformed JSON must fail validation."""
    report = check_contract(
        f"{fixture_server}/invalid-json",
        expected_status=200,
        required_fields={"status": "string"},
    )

    assert report.passed is False
    assert report.error == "invalid_json"


def test_wrong_json_type(fixture_server):
    """Incorrect JSON field types must fail."""
    report = check_contract(
        f"{fixture_server}/wrong-type",
        expected_status=200,
        required_fields={"status": "string"},
    )

    assert report.passed is False
    assert any(not result.passed for result in report.json_results)


def test_redirect_without_following(fixture_server):
    """Unexpected redirects must fail."""
    report = check_contract(
        f"{fixture_server}/redirect",
        expected_status=200,
    )

    assert report.passed is False
    assert report.status_result.actual == 302


def test_request_timeout(fixture_server):
    """Slow endpoints must produce a timeout failure."""
    report = check_contract(
        f"{fixture_server}/slow",
        expected_status=200,
        timeout=0.5,
    )

    assert report.passed is False
    assert report.error == "request_timeout"


@pytest.mark.parametrize("timeout", [0, -1])
def test_invalid_timeout_value(timeout):
    """Nonpositive timeouts must be rejected."""
    with pytest.raises(ValueError):
        check_contract(
            "http://127.0.0.1:8765/health",
            expected_status=200,
            timeout=timeout,
        )


@pytest.mark.parametrize("timeout", ["2", None, True])
def test_invalid_timeout_type(timeout):
    """Invalid timeout types must be rejected."""
    with pytest.raises(TypeError):
        check_contract(
            "http://127.0.0.1:8765/health",
            expected_status=200,
            timeout=timeout,
        )

