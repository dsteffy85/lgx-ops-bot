"""
LGX-OPS-BOT — Entry point.

1. Configures structured JSON logging.
2. Starts the health-check HTTP server in a daemon thread.
3. Runs the Slack listener main loop (blocking).
"""

import sys

from bot.config import LOG_LEVEL
from bot.logging_setup import configure_logging

# Set up logging first so every subsequent import gets the JSON formatter
configure_logging(level=LOG_LEVEL)

import logging  # noqa: E402 — must come after configure_logging

from bot.health import start_health_server  # noqa: E402
from bot.listener import run as run_listener  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    import os
    logger.info("LGX-OPS-BOT starting up")

    # Debug: log proxy and secret env vars
    proxy_vars = {k: v for k, v in os.environ.items() if 'PROXY' in k.upper() or 'proxy' in k}
    logger.info("Proxy env vars: %s", proxy_vars if proxy_vars else "NONE SET")
    secret_dir = "/config/secrets"
    if os.path.isdir(secret_dir):
        secrets_found = os.listdir(secret_dir)
        logger.info("Secrets in %s: %s", secret_dir, secrets_found)
    else:
        logger.info("Secrets dir %s does NOT exist", secret_dir)

    # Health / readiness probes (background daemon thread)
    start_health_server(port=8080)

    # Blocking — runs the Slack poll loop
    try:
        run_listener()
    except KeyboardInterrupt:
        logger.info("Received SIGINT — shutting down")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error in listener loop")
        sys.exit(1)


if __name__ == "__main__":
    main()
