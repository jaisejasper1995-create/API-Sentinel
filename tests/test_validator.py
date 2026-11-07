
"""Unit tests for API Sentinel's contract validator."""

import pytest

from api_sentinel.validator import validate_status


@pytest.mark.parametrize(
    ("expected", "actual", "should_pass"),
    [
        (200, 200, True),
        (404, 404, True),
        (500, 500, True),
        (200, 404, False),
        (200, 500, False),
        (404, 200, False),
    ],
)
def test_validate_status(expected, actual, should_pass):
    """Status validation must distinguish matches from mismatches."""
    result = validate_status(expected, actual)

    assert result.passed is should_pass
    assert result.check == "http_status"
    assert result.expected == expected
    assert result.actual == actual


@pytest.mark.parametrize("invalid", [99, 600, -1])
def test_reject_out_of_range_status(invalid):
    """Reject HTTP status codes outside the supported range."""
    with pytest.raises(ValueError):
        validate_status(invalid, 200)


@pytest.mark.parametrize("invalid", ["200", 200.0, True, None])
def test_reject_invalid_status_types(invalid):
    """Reject noninteger HTTP status codes, including booleans."""
    with pytest.raises(TypeError):
        validate_status(200, invalid)
