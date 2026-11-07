
"""Deterministic JSON response contract validation for API Sentinel."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JsonValidationResult:
    """Result of validating one JSON response contract."""

    passed: bool
    check: str
    expected: Any
    actual: Any
    message: str


def _type_name(value: Any) -> str:
    """Return a JSON-compatible type name."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_type(value: Any, expected_type: str) -> bool:
    """Check JSON types without treating booleans as numbers."""
    valid_types = {
        "string",
        "number",
        "integer",
        "boolean",
        "null",
        "array",
        "object",
    }

    if expected_type not in valid_types:
        raise ValueError(f"Unsupported JSON type: {expected_type}")

    if expected_type == "integer":
        return type(value) is int

    if expected_type == "number":
        return type(value) in (int, float)

    return _type_name(value) == expected_type


def validate_json_contract(
    payload: Any,
    required_fields: dict[str, str],
    expected_values: dict[str, Any] | None = None,
) -> list[JsonValidationResult]:
    """Validate required fields, their types, and expected values.

    Only top-level fields are supported in this first version.
    Additional response fields are permitted.
    """
    if not isinstance(payload, dict):
        return [
            JsonValidationResult(
                passed=False,
                check="json_object",
                expected="object",
                actual=_type_name(payload),
                message="JSON response must be an object",
            )
        ]

    if not isinstance(required_fields, dict):
        raise TypeError("required_fields must be a dictionary")

    if expected_values is None:
        expected_values = {}

    if not isinstance(expected_values, dict):
        raise TypeError("expected_values must be a dictionary")

    valid_types = {
        "string",
        "number",
        "integer",
        "boolean",
        "null",
        "array",
        "object",
    }

    for field, expected_type in required_fields.items():
        if not isinstance(field, str):
            raise TypeError("Required field names must be strings")

        if not isinstance(expected_type, str):
            raise TypeError("Expected JSON types must be strings")

        if expected_type not in valid_types:
            raise ValueError(f"Unsupported JSON type: {expected_type}")

    for field in expected_values:
        if not isinstance(field, str):
            raise TypeError("Expected value field names must be strings")

    results = []

    for field, expected_type in required_fields.items():
        if field not in payload:
            results.append(
                JsonValidationResult(
                    passed=False,
                    check=f"required_field:{field}",
                    expected=expected_type,
                    actual=None,
                    message=f"Missing required field: {field}",
                )
            )
            continue

        actual_value = payload[field]
        type_passed = _matches_type(actual_value, expected_type)

        results.append(
            JsonValidationResult(
                passed=type_passed,
                check=f"field_type:{field}",
                expected=expected_type,
                actual=_type_name(actual_value),
                message=(
                    f"Field '{field}' has the expected type"
                    if type_passed
                    else (
                        f"Field '{field}' expected type "
                        f"{expected_type}, received "
                        f"{_type_name(actual_value)}"
                    )
                ),
            )
        )

    for field, expected_value in expected_values.items():
        if field not in payload:
            results.append(
                JsonValidationResult(
                    passed=False,
                    check=f"expected_value:{field}",
                    expected=expected_value,
                    actual=None,
                    message=f"Missing field for expected value: {field}",
                )
            )
            continue

        actual_value = payload[field]

        # Python considers True == 1, so compare types too.
        value_passed = (
            type(actual_value) is type(expected_value)
            and actual_value == expected_value
        )

        results.append(
            JsonValidationResult(
                passed=value_passed,
                check=f"expected_value:{field}",
                expected=expected_value,
                actual=actual_value,
                message=(
                    f"Field '{field}' matches expected value"
                    if value_passed
                    else f"Field '{field}' does not match expected value"
                ),
            )
        )

    return results
