"""Integration tests for API Sentinel's local fixture server."""

import json

import httpx
import pytest


def test_health_endpoint(fixture_server):
    """Health must return HTTP 200 and the expected JSON."""
    with httpx.Client(timeout=2.0, trust_env=False) as client:
        response = client.get(f"{fixture_server}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_not_found_endpoint(fixture_server):
    """The not-found fixture must return HTTP 404."""
    with httpx.Client(timeout=2.0, trust_env=False) as client:
        response = client.get(f"{fixture_server}/not-found")

    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}


def test_server_error_endpoint(fixture_server):
    """The server-error fixture must return HTTP 500 and expected JSON."""
    with httpx.Client(timeout=2.0, trust_env=False) as client:
        response = client.get(f"{fixture_server}/server-error")

    assert response.status_code == 500
    assert response.json() == {"error": "fixture_failure"}


def test_invalid_json_endpoint(fixture_server):
    """HTTP 200 must not hide an invalid JSON response."""
    with httpx.Client(timeout=2.0, trust_env=False) as client:
        response = client.get(f"{fixture_server}/invalid-json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    with pytest.raises(json.JSONDecodeError):
        response.json()


def test_wrong_type_endpoint(fixture_server):
    """The wrong-type fixture must return a number, not a string."""
    with httpx.Client(timeout=2.0, trust_env=False) as client:
        response = client.get(f"{fixture_server}/wrong-type")

    assert response.status_code == 200

    payload = response.json()

    assert payload == {"status": 123}
    assert type(payload["status"]) is int
    assert not isinstance(payload["status"], str)


def test_slow_endpoint_timeout(fixture_server):
    """A slow response must trigger an HTTP client read timeout."""
    with (
        httpx.Client(timeout=0.5, trust_env=False) as client,
        pytest.raises(httpx.ReadTimeout),
    ):
        client.get(f"{fixture_server}/slow")


def test_redirect_endpoint(fixture_server):
    """Redirect fixture must return HTTP 302 without following it."""
    with httpx.Client(
        timeout=2.0,
        trust_env=False,
        follow_redirects=False,
    ) as client:
        response = client.get(f"{fixture_server}/redirect")

    assert response.status_code == 302
    assert response.headers["location"] == "/health"
    assert response.history == []

