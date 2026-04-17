"""
Lightweight HTTP health-check server (runs in a background daemon thread).

Endpoints:
    GET /health  → 200 {"status": "ok", "uptime": <seconds>}
    GET /ready   → 200 if listener is running, 503 otherwise
"""

import json
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

_start_time: float = time.time()
_listener_ready = threading.Event()


def mark_listener_ready() -> None:
    """Called by the listener wrapper once the poll loop is active."""
    _listener_ready.set()


def is_listener_ready() -> bool:
    return _listener_ready.is_set()


class _HealthHandler(BaseHTTPRequestHandler):
    """Minimal request handler — no framework dependency."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._respond(200, {
                "status": "ok",
                "uptime": round(time.time() - _start_time, 1),
            })
        elif self.path == "/ready":
            if is_listener_ready():
                self._respond(200, {"status": "ready"})
            else:
                self._respond(503, {"status": "not_ready"})
        else:
            self._respond(404, {"error": "not_found"})

    def _respond(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args) -> None:  # noqa: A002
        # Suppress default stderr access logs; use structured logging instead
        logger.debug("health probe: %s", args[0] if args else "")


def start_health_server(port: int = 8080) -> threading.Thread:
    """Start the health-check HTTP server in a daemon thread."""
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, name="health-server", daemon=True)
    thread.start()
    logger.info("Health-check server listening on :%d", port)
    return thread
