
"""Unit tests for API Sentinel JSON contract validation."""

import pytest

from api_sentinel.json_validator import validate_json_contract


def test_valid_json_contract():
    """Matching fields, types, and values must pass."""
    results = validate_json_contract(
        {"status": "ok", "count": 3},
        {"status": "string", "count": "integer"},
        {"status": "ok"},
    )

    assert len(results) == 3
    assert all(result.passed for result in results)


def test_missing_required_field():
    """Missing required fields must fail."""
    results = validate_json_contract(
        {"count": 3},
        {"status": "string"},
    )

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].check == "required_field:status"


def test_incorrect_field_type():
    """Numbers must not satisfy string contracts."""
    results = validate_json_contract(
        {"status": 123},
        {"status": "string"},
    )

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].actual == "number"


def test_incorrect_expected_value():
    """Unexpected values must fail."""
    results = validate_json_contract(
        {"status": "error"},
        {"status": "string"},
        {"status": "ok"},
    )

    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is False


def test_boolean_is_not_integer():
    """Python booleans must not pass integer contracts."""
    results = validate_json_contract(
        {"count": True},
        {"count": "integer"},
    )

    assert results[0].passed is False


def test_boolean_is_not_number():
    """Python booleans must not pass number contracts."""
    results = validate_json_contract(
        {"count": True},
        {"count": "number"},
    )

    assert results[0].passed is False


@pytest.mark.parametrize(
    ("value", "expected_type"),
    [
        ("hello", "string"),
        (42, "integer"),
        (3.14, "number"),
        (True, "boolean"),
        (None, "null"),
        ([1, 2], "array"),
        ({"id": 1}, "object"),
    ],
)
def test_supported_json_types(value, expected_type):
    """Every supported JSON type must validate correctly."""
    results = validate_json_contract(
        {"value": value},
        {"value": expected_type},
    )

    assert len(results) == 1
    assert results[0].passed is True


def test_non_object_payload():
    """A JSON array cannot satisfy an object contract."""
    results = validate_json_contract(
        [1, 2, 3],
        {"status": "string"},
    )

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].check == "json_object"


def test_extra_fields_are_allowed():
    """Additional response fields must not cause failure."""
    results = validate_json_contract(
        {"status": "ok", "extra": "allowed"},
        {"status": "string"},
    )

    assert all(result.passed for result in results)


def test_missing_expected_value_field():
    """Missing fields referenced by expected_values must fail."""
    results = validate_json_contract(
        {},
        {},
        {"status": "ok"},
    )

    assert len(results) == 1
    assert results[0].passed is False


def test_boolean_does_not_equal_integer_value():
    """True must not match an expected integer value of 1."""
    results = validate_json_contract(
        {"enabled": True},
        {"enabled": "boolean"},
        {"enabled": 1},
    )

    assert results[0].passed is True
    assert results[1].passed is False


@pytest.mark.parametrize("invalid_type", ["text", "float", "unknown"])
def test_unsupported_contract_type(invalid_type):
    """Unsupported contract types must be rejected."""
    with pytest.raises(ValueError):
        validate_json_contract(
            {"status": "ok"},
            {"status": invalid_type},
        )


def test_invalid_required_fields_argument():
    """Required field definitions must be dictionaries."""
    with pytest.raises(TypeError):
        validate_json_contract({"status": "ok"}, [])


def test_invalid_expected_values_argument():
    """Expected values must be dictionaries."""
    with pytest.raises(TypeError):
        validate_json_contract(
            {"status": "ok"},
            {},
            ["status"],
        )
