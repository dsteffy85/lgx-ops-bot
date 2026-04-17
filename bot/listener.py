"""
Thin wrapper around scripts/slack_listener.py — bridges into the bot package
without rewriting the existing listener logic.

Patches config values into the listener module, then delegates to slack_listener.main().
"""

import importlib.util
import logging
import sys
from pathlib import Path

from bot import config
from bot.health import mark_listener_ready

logger = logging.getLogger(__name__)

# Resolve the path to the original listener script
_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "slack_listener.py"


def _load_listener_module():
    """Dynamically import scripts/slack_listener.py as a module."""
    spec = importlib.util.spec_from_file_location("slack_listener", _SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load listener script: {_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["slack_listener"] = module
    spec.loader.exec_module(module)
    return module


def run() -> None:
    """Load the listener module, patch config, and run its main()."""
    logger.info("Loading slack_listener from %s", _SCRIPT_PATH)
    listener = _load_listener_module()

    # Patch the listener's constants with values from bot.config
    # (the listener uses module-level constants, not env vars)
    listener.LGX_BOT_TOKEN = config.SLACK_BOT_TOKEN
    listener.BOT_USER_ID = config.BOT_USER_ID
    listener.BOT_SIGNATURE = config.BOT_SIGNATURE
    listener.OSCAR_ID = config.OSCAR_ID
    listener.POLL_INTERVAL = config.POLL_INTERVAL
    listener.CHANNEL_OVERRIDES = {
        config.HARDWAREDELIVERYHELP_ID: {
            "oscar_cc": True,
            "disclaimer": True,
        },
    }

    logger.info("Config patched — Slack token: %s..., Poll: %ds",
                config.SLACK_BOT_TOKEN[:15] if config.SLACK_BOT_TOKEN else "EMPTY",
                config.POLL_INTERVAL)

    # Signal health endpoint that the listener is starting
    mark_listener_ready()
    logger.info("Listener marked ready — entering poll loop")

    listener.main()
