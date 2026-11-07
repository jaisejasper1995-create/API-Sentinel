
"""Deterministic API contract validation functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """Structured result of one contract validation."""

    passed: bool
    check: str
    expected: int
    actual: int
    message: str


def validate_status(expected: int, actual: int) -> ValidationResult:
    """Compare an expected HTTP status code with the actual code."""
    if type(expected) is not int or type(actual) is not int:
        raise TypeError("HTTP status codes must be integers")

    if not 100 <= expected <= 599:
        raise ValueError("Expected HTTP status must be between 100 and 599")

    if not 100 <= actual <= 599:
        raise ValueError("Actual HTTP status must be between 100 and 599")

    passed = expected == actual

    return ValidationResult(
        passed=passed,
        check="http_status",
        expected=expected,
        actual=actual,
        message=(
            "HTTP status matches expected contract"
            if passed
            else f"Expected HTTP {expected}, received HTTP {actual}"
        ),
    )
