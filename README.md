# API Sentinel

**Deterministic API Contract Validation | Python | CLI | Automated QA**

API Sentinel is a local-first Python command-line tool for checking HTTP API responses against explicitly defined contracts.

It verifies HTTP status codes, required JSON fields, JSON value types, and expected values, producing consistent results suitable for manual testing and automated quality assurance workflows.

The project emphasizes predictable behavior, negative testing, structured failure reporting, and evidence-based validation.

## Key Features

- HTTP response status validation
- Required JSON field validation
- JSON data type checking
- Expected JSON value verification
- Reusable JSON contract configuration files
- Human-readable PASS/FAIL output
- Machine-readable JSON reports
- Request timeout and network failure handling
- Invalid contract rejection before network execution
- Deterministic result structures
- Automated regression testing

## Installation

**Requirements:** Python 3.11 or newer (3.13 verified locally).

Clone or download the project, open a terminal inside its root directory, and install it:

```powershell
python -m pip install .
```

Confirm the CLI installation:

```powershell
api-sentinel --help
```

## Usage

### Check an HTTP status code

```powershell
api-sentinel check --url https://example.com --status 200
```

The command compares the actual response status against the expected status.

### Generate a JSON report

```powershell
api-sentinel check --url https://example.com --status 200 --format json
```

The resulting JSON report includes the request URL, overall PASS/FAIL status, HTTP status validation result, JSON validation results, and any categorized request error.

### Use a reusable contract

Create a JSON file such as `contract.json`:

```json
{
  "url": "http://127.0.0.1:8000/health",
  "expected_status": 200,
  "required_fields": {
    "status": "string"
  },
  "expected_values": {
    "status": "ok"
  },
  "timeout": 2.0
}
```

This example expects a locally running API on port 8000 to return HTTP 200 and a JSON object containing `"status": "ok"`.

Run the contract:

```powershell
api-sentinel check --contract contract.json --format json
```

A sample configuration is included in `examples/health_contract.json`.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Contract validation passed |
| `1` | Contract validation failed or request encountered a handled network error |
| `2` | Invalid contract configuration or command-line argument |

These exit codes support integration with scripts and automated quality gates.

## Development and Testing

Install development dependencies:

```powershell
python -m pip install ".[dev]"
```

Run automated tests:

```powershell
python -m pytest -q
```

Run static code-quality checks:

```powershell
python -m ruff check api_sentinel tests
```

## Validation Evidence

At the documented local release-preparation checkpoint:

- **143 automated tests passed**
- Ruff code-quality checks passed
- Separate-environment installation succeeded
- Python wheel build succeeded
- Wheel installation and CLI help smoke test succeeded

These results describe the local validation checkpoint. CI/CD verification, additional compatibility testing, and final publication approval remain separate release gates.

## Scope and Limitations

API Sentinel currently focuses on deterministic HTTP and top-level JSON contract checks.

- JSON validation covers required top-level fields, supported JSON types, and expected values.
- Requests use HTTP GET.
- Redirects are not automatically followed.
- The tool does not currently implement full OpenAPI schema validation, authentication workflows, nested JSON schema validation, or load testing.
- The installed tool requires network access to contact the API endpoint being checked; local testing can use the included fixture server.

## Engineering Approach

This project was developed using a test-driven, evidence-oriented workflow emphasizing:

1. Reproducible validation
2. Explicit expected-versus-actual results
3. Adversarial and negative testing
4. Detection and correction of regressions
5. Structured reports and meaningful exit codes
6. Independent installation verification
7. Human approval before release

**Engineering principle: Test the claim — not just the demo.**

## Release Status

**Version:** 0.1.0

**Status:** Release preparation — final verification pending.

Licensing and public publication will be finalized before release.