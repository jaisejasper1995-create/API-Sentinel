
"""Tests for machine-readable API Sentinel CLI reports."""

import json
from unittest.mock import patch

import httpx
import pytest

from api_sentinel.cli import main


def test_json_success(fixture_server, capsys):
    """A successful contract produces valid JSON and exit code zero."""
    url = f"{fixture_server}/health"

    exit_code = main([
        "check", "--url", url,
        "--status", "200",
        "--format", "json",
    ])

    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 0
    assert output.err == ""
    assert report["url"] == url
    assert report["passed"] is True
    assert report["error"] is None
    assert report["status_result"]["passed"] is True
    assert report["json_results"] == []


def test_json_status_mismatch(fixture_server, capsys):
    """HTTP mismatches produce structured JSON and exit code one."""
    url = f"{fixture_server}/health"

    exit_code = main([
        "check", "--url", url,
        "--status", "201",
        "--format", "json",
    ])

    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 1
    assert report["passed"] is False
    assert report["error"] is None
    assert report["status_result"]["expected"] == 201
    assert report["status_result"]["actual"] == 200


def test_json_expected_server_error(fixture_server, capsys):
    """HTTP 500 can correctly pass when the contract expects 500."""
    exit_code = main([
        "check",
        "--url", f"{fixture_server}/server-error",
        "--status", "500",
        "--format", "json",
    ])

    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert report["passed"] is True
    assert report["status_result"]["actual"] == 500


@pytest.mark.parametrize(
    ("exception", "expected_error"),
    [
        (httpx.ConnectError("Connection refused"), "request_error"),
        (httpx.ReadTimeout("Timed out"), "request_timeout"),
    ],
)
def test_json_network_failures(exception, expected_error, capsys):
    """Network problems produce JSON failure reports."""
    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=exception,
    ):
        exit_code = main([
            "check",
            "--url", "http://127.0.0.1:8765/unreachable",
            "--status", "200",
            "--format", "json",
        ])

    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 1
    assert report["passed"] is False
    assert report["error"] == expected_error
    assert report["status_result"] is None
    assert report["json_results"] == []


def test_json_invalid_contract(capsys):
    """Invalid contracts keep exit code two and report on stderr."""
    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        exit_code = main([
            "check",
            "--url", "http://example.test",
            "--status", "99",
            "--format", "json",
        ])

        mock_get.assert_not_called()

    output = capsys.readouterr()

    assert exit_code == 2
    assert output.out == ""
    assert "INVALID CONTRACT:" in output.err


def test_explicit_text_format(fixture_server, capsys):
    """Explicit text mode preserves the original readable output."""
    url = f"{fixture_server}/health"

    exit_code = main([
        "check", "--url", url,
        "--status", "200",
        "--format", "text",
    ])

    output = capsys.readouterr()

    assert exit_code == 0
    assert f"PASS | {url}" in output.out


def test_unsupported_format_rejected(capsys):
    """Unknown report formats produce a CLI usage error."""
    with pytest.raises(SystemExit) as exc_info:
        main([
            "check",
            "--url", "http://example.test",
            "--status", "200",
            "--format", "xml",
        ])

    output = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "invalid choice" in output.err


def test_json_output_is_repeatable(fixture_server, capsys):
    """Identical responses produce identical serialized reports."""
    argv = [
        "check",
        "--url", f"{fixture_server}/health",
        "--status", "200",
        "--format", "json",
    ]

    first_exit = main(argv)
    first_output = capsys.readouterr()

    second_exit = main(argv)
    second_output = capsys.readouterr()

    assert first_exit == second_exit == 0
    assert first_output.out == second_output.out
