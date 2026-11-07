
"""Shared pytest fixtures for API Sentinel integration tests."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

SERVER_FILE = Path(__file__).with_name("fixture_server.py")


@pytest.fixture(scope="module")
def fixture_server(tmp_path_factory):
    """Start a local fixture server for integration tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = os.environ.copy()
    env["API_SENTINEL_TEST_PORT"] = str(port)

    log_path = tmp_path_factory.mktemp("server") / "fixture.log"

    with log_path.open("w+b") as log_file:
        server = subprocess.Popen(
            [sys.executable, str(SERVER_FILE)],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

        try:
            deadline = time.monotonic() + 15

            with httpx.Client(
                timeout=2.0,
                trust_env=False,
                follow_redirects=False,
            ) as client:
                while time.monotonic() < deadline:
                    if server.poll() is not None:
                        pytest.fail("Fixture server exited during startup")

                    try:
                        response = client.get(
                            f"http://127.0.0.1:{port}/health"
                        )
                        if response.status_code == 200:
                            break
                    except (httpx.ConnectError, httpx.ConnectTimeout):
                        pass

                    time.sleep(0.2)
                else:
                    pytest.fail("Fixture server did not become ready")

            yield f"http://127.0.0.1:{port}"

        finally:
            if server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)

            log_file.flush()
            if sys.exc_info()[0] is not None:
                print(
                    "\nFixture server log:\n"
                    + log_path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                )
