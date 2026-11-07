
"""Execute deterministic API contract checks."""

import math
from dataclasses import dataclass
from typing import Any

import httpx

from api_sentinel.json_validator import (
    JsonValidationResult,
    validate_json_contract,
)
from api_sentinel.validator import ValidationResult, validate_status

VALID_JSON_TYPES = frozenset(
    {"string", "number", "integer", "boolean", "null", "array", "object"}
)


@dataclass(frozen=True)
class ContractReport:
    """Structured results from one API contract check."""

    url: str
    passed: bool
    status_result: ValidationResult | None
    json_results: tuple[JsonValidationResult, ...]
    error: str | None


def _validate_contract_definition(
    expected_status: int,
    required_fields: dict[str, str],
    expected_values: dict[str, Any],
    timeout: float,
) -> None:
    """Reject invalid contract definitions before any network request."""
    validate_status(expected_status, expected_status)

    if type(timeout) not in (int, float):
        raise TypeError("timeout must be a number")

    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and greater than zero")

    if not isinstance(required_fields, dict):
        raise TypeError("required_fields must be a dictionary")

    if not isinstance(expected_values, dict):
        raise TypeError("expected_values must be a dictionary")

    for field, expected_type in required_fields.items():
        if not isinstance(field, str):
            raise TypeError("Required field names must be strings")

        if not isinstance(expected_type, str):
            raise TypeError("Expected JSON types must be strings")

        if expected_type not in VALID_JSON_TYPES:
            raise ValueError(f"Unsupported JSON type: {expected_type}")

    for field in expected_values:
        if not isinstance(field, str):
            raise TypeError("Expected value field names must be strings")


def check_contract(
    url: str,
    expected_status: int,
    required_fields: dict[str, str] | None = None,
    expected_values: dict[str, Any] | None = None,
    timeout: float = 2.0,
) -> ContractReport:
    """Request an endpoint and validate its response."""
    if required_fields is None:
        required_fields = {}

    if expected_values is None:
        expected_values = {}

    _validate_contract_definition(
        expected_status,
        required_fields,
        expected_values,
        timeout,
    )

    try:
        with httpx.Client(
            timeout=timeout,
            trust_env=False,
            follow_redirects=False,
        ) as client:
            response = client.get(url)
    except httpx.TimeoutException:
        return ContractReport(
            url=url,
            passed=False,
            status_result=None,
            json_results=(),
            error="request_timeout",
        )
    except httpx.RequestError:
        return ContractReport(
            url=url,
            passed=False,
            status_result=None,
            json_results=(),
            error="request_error",
        )

    status_result = validate_status(
        expected_status,
        response.status_code,
    )

    json_results = ()

    if required_fields or expected_values:
        try:
            payload = response.json()
        except ValueError:
            return ContractReport(
                url=url,
                passed=False,
                status_result=status_result,
                json_results=(),
                error="invalid_json",
            )

        json_results = tuple(
            validate_json_contract(
                payload,
                required_fields,
                expected_values,
            )
        )

    passed = status_result.passed and all(
        result.passed for result in json_results
    )

    return ContractReport(
        url=url,
        passed=passed,
        status_result=status_result,
        json_results=json_results,
        error=None,
    )
