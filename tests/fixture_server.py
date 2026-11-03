
"""Deterministic local HTTP fixtures for API Sentinel tests.

This server is for local testing only, not production deployment.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def respond(self, status, body, content_type="application/json"):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        if self.command != "HEAD":
            self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self.respond(200, json.dumps({"status": "ok"}))

        elif self.path == "/not-found":
            self.respond(404, json.dumps({"error": "not_found"}))

        elif self.path == "/server-error":
            self.respond(500, json.dumps({"error": "fixture_failure"}))

        elif self.path == "/invalid-json":
            self.respond(200, '{"status":', "application/json")

        elif self.path == "/wrong-type":
            self.respond(200, json.dumps({"status": 123}))

        elif self.path == "/slow":
            time.sleep(2)
            self.respond(200, json.dumps({"status": "slow"}))

        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/health")
            self.send_header("Content-Length", "0")
            self.end_headers()

        else:
            self.respond(404, json.dumps({"error": "unknown_fixture"}))

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format_string, *args):
        pass


def main():
    port = int(os.environ.get("API_SENTINEL_TEST_PORT", "8765"))

    server = ThreadingHTTPServer(
        ("127.0.0.1", port),
        FixtureHandler,
    )

    print(
        f"API Sentinel fixture server: http://127.0.0.1:{server.server_port}",
        flush=True,
    )

    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        print("\nFixture server stopping.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
