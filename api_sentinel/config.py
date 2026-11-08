
"""Load and validate reusable JSON API contracts."""

import json
from pathlib import Path
from typing import Any

from api_sentinel.runner import _validate_contract_definition

ALLOWED_KEYS = {
    "url",
    "expected_status",
    "required_fields",
    "expected_values",
    "timeout",
}

REQUIRED_KEYS = {"url", "expected_status"}


def load_contract(path: str | Path) -> dict[str, Any]:
    """Load a contract and reject malformed definitions."""

    contract_path = Path(path)

    with contract_path.open("r", encoding="utf-8") as file:
        contract = json.load(file)

    if not isinstance(contract, dict):
        raise TypeError("Contract must be a JSON object")

    missing = REQUIRED_KEYS - contract.keys()

    if missing:
        raise ValueError(
            f"Missing contract fields: {', '.join(sorted(missing))}"
        )

    unexpected = contract.keys() - ALLOWED_KEYS

    if unexpected:
        raise ValueError(
            f"Unsupported contract fields: {', '.join(sorted(unexpected))}"
        )

    url = contract["url"]

    if not isinstance(url, str) or not url.strip():
        raise ValueError("Contract URL must be a nonempty string")

    expected_status = contract["expected_status"]
    required_fields = contract.get("required_fields", {})
    expected_values = contract.get("expected_values", {})
    timeout = contract.get("timeout", 2.0)

    # Reuse the runner's validation rules before networking.
    _validate_contract_definition(
        expected_status,
        required_fields,
        expected_values,
        timeout,
    )

    return {
        "url": url,
        "expected_status": expected_status,
        "required_fields": required_fields,
        "expected_values": expected_values,
        "timeout": timeout,
    }
