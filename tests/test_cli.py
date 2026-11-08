
"""Tests for the API Sentinel command-line interface."""

from unittest.mock import patch

import httpx
import pytest

from api_sentinel.cli import main
from api_sentinel.runner import ContractReport


def test_cli_success(fixture_server, capsys):
    """A matching contract returns exit code zero."""
    url = f"{fixture_server}/health"

    exit_code = main([
        "check",
        "--url", url,
        "--status", "200",
    ])

    output = capsys.readouterr()

    assert exit_code == 0
    assert f"PASS | {url}" in output.out
    assert "HTTP status matches expected contract" in output.out


def test_cli_status_mismatch(fixture_server, capsys):
    """An HTTP status mismatch returns exit code one."""
    url = f"{fixture_server}/health"

    exit_code = main([
        "check",
        "--url", url,
        "--status", "201",
    ])

    output = capsys.readouterr()

    assert exit_code == 1
    assert f"FAIL | {url}" in output.out
    assert "Expected HTTP 201, received HTTP 200" in output.out


def test_cli_expected_server_error(fixture_server, capsys):
    """A correctly expected HTTP 500 is a valid contract match."""
    url = f"{fixture_server}/server-error"

    exit_code = main([
        "check",
        "--url", url,
        "--status", "500",
    ])

    output = capsys.readouterr()

    assert exit_code == 0
    assert f"PASS | {url}" in output.out


def test_cli_connection_failure(capsys):
    """Network connection failures return a predictable error."""
    url = "http://127.0.0.1:8765/unreachable"

    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        exit_code = main([
            "check",
            "--url", url,
            "--status", "200",
        ])

    output = capsys.readouterr()

    assert exit_code == 1
    assert f"FAIL | {url}" in output.out
    assert "ERROR: request_error" in output.out


def test_cli_network_timeout(capsys):
    """Network timeouts return a predictable error."""
    url = "http://127.0.0.1:8765/health"

    with patch(
        "api_sentinel.runner.httpx.Client.get",
        side_effect=httpx.ReadTimeout("Timed out"),
    ):
        exit_code = main([
            "check",
            "--url", url,
            "--status", "200",
        ])

    output = capsys.readouterr()

    assert exit_code == 1
    assert f"FAIL | {url}" in output.out
    assert "ERROR: request_timeout" in output.out


@pytest.mark.parametrize("status", ["99", "600"])
def test_cli_invalid_status_rejected_before_network(
    status,
    capsys,
):
    """Invalid contract status codes must not make HTTP requests."""
    with patch(
        "api_sentinel.runner.httpx.Client.get",
    ) as mock_get:
        exit_code = main([
            "check",
            "--url", "http://example.test/health",
            "--status", status,
        ])

        mock_get.assert_not_called()

    output = capsys.readouterr()

    assert exit_code == 2
    assert "INVALID CONTRACT:" in output.err


@pytest.mark.parametrize("timeout", ["0", "-1", "nan"])
def test_cli_invalid_timeout_rejected_before_network(
    timeout,
    capsys,
):
    """Invalid timeouts must be rejected before networking."""
    with patch(
        "api_sentinel.runner.httpx.Client.get",
    ) as mock_get:
        exit_code = main([
            "check",
            "--url", "http://example.test/health",
            "--status", "200",
            "--timeout", timeout,
        ])

        mock_get.assert_not_called()

    output = capsys.readouterr()

    assert exit_code == 2
    assert "INVALID CONTRACT:" in output.err


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["check"],
        ["check", "--status", "200"],
        ["check", "--url", "http://example.test"],
        [
            "check",
            "--url", "http://example.test",
            "--status", "abc",
        ],
    ],
)
def test_cli_argument_errors(argv, capsys):
    """Missing or invalid CLI arguments produce usage errors."""
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    output = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "error:" in output.err


def test_cli_help(capsys):
    """The CLI provides useful help text."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    output = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "usage:" in output.out
    assert "check" in output.out


def test_cli_forwards_timeout_and_url(capsys):
    """The CLI forwards parsed arguments to the contract runner."""
    url = "http://example.test/health"

    fake_report = ContractReport(
        url=url,
        passed=True,
        status_result=None,
        json_results=(),
        error=None,
    )

    with patch(
        "api_sentinel.cli.check_contract",
        return_value=fake_report,
    ) as mock_check:
        exit_code = main([
            "check",
            "--url", url,
            "--status", "200",
            "--timeout", "3.5",
        ])

    capsys.readouterr()

    assert exit_code == 0

    mock_check.assert_called_once_with(
        url=url,
        expected_status=200,
        timeout=3.5,
    )
