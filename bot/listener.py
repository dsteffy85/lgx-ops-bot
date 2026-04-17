"""
Thin wrapper around scripts/slack_listener.py — bridges into the bot package
without rewriting the existing listener logic.

Sets environment-driven config values, then delegates to slack_listener.main().
"""

import importlib.util
import logging
import os
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


def _inject_env() -> None:
    """Push bot.config values into the environment so the legacy script picks
    them up via its own os.environ / constant reads."""
    env_map = {
        "SLACK_BOT_TOKEN": config.SLACK_BOT_TOKEN,
        "SNOWFLAKE_PRIVATE_KEY_PATH": config.SNOWFLAKE_PRIVATE_KEY_PATH,
        "SNOWFLAKE_ACCOUNT": config.SNOWFLAKE_ACCOUNT,
        "SNOWFLAKE_USER": config.SNOWFLAKE_USER,
        "SNOWFLAKE_WAREHOUSE": config.SNOWFLAKE_WAREHOUSE,
        "SNOWFLAKE_ROLE": config.SNOWFLAKE_ROLE,
        "DATABRICKS_HOST": config.DATABRICKS_HOST,
        "DATABRICKS_TOKEN_PATH": config.DATABRICKS_TOKEN_PATH,
        "POLL_INTERVAL": str(config.POLL_INTERVAL),
        "BOT_USER_ID": config.BOT_USER_ID,
    }
    for key, value in env_map.items():
        if value:
            os.environ.setdefault(key, value)


def run() -> None:
    """Configure environment, load the listener module, and run its main()."""
    logger.info("Injecting config into environment")
    _inject_env()

    logger.info("Loading slack_listener from %s", _SCRIPT_PATH)
    listener = _load_listener_module()

    # Signal health endpoint that the listener is starting
    mark_listener_ready()
    logger.info("Listener marked ready — entering poll loop")

    listener.main()
