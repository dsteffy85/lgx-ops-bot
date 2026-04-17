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
    logger.info("LGX-OPS-BOT starting up")

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
