
"""Adversarial tests for malformed API contract definitions."""

from unittest.mock import patch

import pytest

from api_sentinel.runner import check_contract

TEST_URL = "http://127.0.0.1:8765/health"


@pytest.mark.parametrize(
    "invalid_status",
    [99, 600, -1, "200", 200.0, True, None],
)
def test_invalid_status_rejected_before_request(invalid_status):
    """Invalid HTTP status contracts must not trigger networking."""
    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        with pytest.raises((TypeError, ValueError)):
            check_contract(TEST_URL, expected_status=invalid_status)

        mock_get.assert_not_called()


@pytest.mark.parametrize(
    "invalid_timeout",
    [0, -1, "2", None, True, -0.5],
)
def test_invalid_timeout_rejected_before_request(invalid_timeout):
    """Invalid timeout settings must not trigger networking."""
    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        with pytest.raises((TypeError, ValueError)):
            check_contract(
                TEST_URL,
                expected_status=200,
                timeout=invalid_timeout,
            )

        mock_get.assert_not_called()


@pytest.mark.parametrize(
    "invalid_required_fields",
    [
        [],
        "status",
        123,
        {"status": "unsupported"},
        {123: "string"},
        {"status": 123},
    ],
)
def test_malformed_required_fields_rejected_before_request(
    invalid_required_fields,
):
    """Malformed required fields must fail before any HTTP request."""
    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        with pytest.raises((TypeError, ValueError)):
            check_contract(
                TEST_URL,
                expected_status=200,
                required_fields=invalid_required_fields,
            )

        mock_get.assert_not_called()


@pytest.mark.parametrize(
    "invalid_expected_values",
    [
        [],
        "status",
        123,
        {123: "ok"},
    ],
)
def test_malformed_expected_values_rejected_before_request(
    invalid_expected_values,
):
    """Malformed expected values must fail before any HTTP request."""
    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        with pytest.raises((TypeError, ValueError)):
            check_contract(
                TEST_URL,
                expected_status=200,
                expected_values=invalid_expected_values,
            )

        mock_get.assert_not_called()

