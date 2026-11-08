
"""Tests for reusable JSON contract configuration."""

import json
from unittest.mock import patch

import pytest

from api_sentinel.cli import main
from api_sentinel.config import load_contract


def write_contract(tmp_path, payload):
    """Write temporary JSON contract data."""
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def valid_contract(url):
    return {
        "url": url,
        "expected_status": 200,
        "required_fields": {"status": "string"},
        "expected_values": {"status": "ok"},
        "timeout": 2.0,
    }


def test_load_valid_contract(tmp_path):
    path = write_contract(
        tmp_path,
        valid_contract("http://example.test/health"),
    )

    result = load_contract(path)

    assert result["expected_status"] == 200
    assert result["required_fields"] == {"status": "string"}
    assert result["expected_values"] == {"status": "ok"}


def test_default_settings(tmp_path):
    path = write_contract(
        tmp_path,
        {
            "url": "http://example.test/health",
            "expected_status": 200,
        },
    )

    result = load_contract(path)

    assert result["required_fields"] == {}
    assert result["expected_values"] == {}
    assert result["timeout"] == 2.0


@pytest.mark.parametrize(
    "payload",
    [
        [],
        "invalid",
        None,
        {},
        {"url": "http://example.test"},
        {"expected_status": 200},
        {"url": "", "expected_status": 200},
        {"url": 123, "expected_status": 200},
        {"url": "http://example.test", "expected_status": 99},
        {"url": "http://example.test", "expected_status": True},
        {
            "url": "http://example.test",
            "expected_status": 200,
            "unknown_setting": True,
        },
        {
            "url": "http://example.test",
            "expected_status": 200,
            "required_fields": {"status": "unsupported"},
        },
        {
            "url": "http://example.test",
            "expected_status": 200,
            "timeout": -1,
        },
    ],
)
def test_invalid_contract_rejected(tmp_path, payload):
    path = write_contract(tmp_path, payload)

    with pytest.raises((TypeError, ValueError)):
        load_contract(path)


def test_missing_file_rejected(tmp_path):
    with pytest.raises(OSError):
        load_contract(tmp_path / "missing.json")


def test_invalid_json_rejected(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"url":', encoding="utf-8")

    with pytest.raises(ValueError):
        load_contract(path)


def test_cli_contract_success(fixture_server, tmp_path, capsys):
    path = write_contract(
        tmp_path,
        valid_contract(f"{fixture_server}/health"),
    )

    exit_code = main([
        "check",
        "--contract", str(path),
        "--format", "json",
    ])

    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 0
    assert output.err == ""
    assert report["passed"] is True
    assert report["error"] is None
    assert len(report["json_results"]) == 2
    assert all(r["passed"] for r in report["json_results"])


def test_cli_contract_failure(fixture_server, tmp_path, capsys):
    payload = valid_contract(f"{fixture_server}/wrong-type")
    path = write_contract(tmp_path, payload)

    exit_code = main([
        "check",
        "--contract", str(path),
        "--format", "json",
    ])

    report = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert report["passed"] is False
    assert any(not r["passed"] for r in report["json_results"])


def test_invalid_file_causes_no_request(tmp_path, capsys):
    path = write_contract(
        tmp_path,
        {
            "url": "http://example.test",
            "expected_status": 600,
        },
    )

    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        exit_code = main([
            "check",
            "--contract", str(path),
        ])

        mock_get.assert_not_called()

    output = capsys.readouterr()

    assert exit_code == 2
    assert "INVALID CONTRACT:" in output.err


def test_conflicting_arguments_rejected(tmp_path, capsys):
    path = write_contract(
        tmp_path,
        valid_contract("http://example.test"),
    )

    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        exit_code = main([
            "check",
            "--contract", str(path),
            "--status", "200",
        ])

        mock_get.assert_not_called()

    assert exit_code == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_invalid_configuration_does_not_make_request(tmp_path):
    path = write_contract(
        tmp_path,
        {
            "url": "http://example.test",
            "expected_status": 200,
            "required_fields": {"status": "not_a_json_type"},
        },
    )

    with patch("api_sentinel.runner.httpx.Client.get") as mock_get:
        with pytest.raises(ValueError):
            load_contract(path)

        mock_get.assert_not_called()
