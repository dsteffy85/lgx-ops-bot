"""
Thin wrapper around scripts/slack_listener.py — bridges into the bot package
without rewriting the existing listener logic.

Patches config values into the listener module, then delegates to slack_listener.main().

On SKI, also monkey-patches get_sf_connection() and _get_databricks_token()
to read secrets from Keywhiz mounts / env vars instead of local file paths.
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


def _make_sf_connection_factory():
    """Create a Snowflake connection factory that uses bot.config secrets."""
    _sf_conn = None

    def get_sf_connection():
        nonlocal _sf_conn
        if _sf_conn is not None:
            try:
                _sf_conn.cursor().execute("SELECT 1")
                return _sf_conn
            except Exception:
                _sf_conn = None

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import snowflake.connector

        key_pem = config.SNOWFLAKE_PRIVATE_KEY
        if not key_pem:
            raise RuntimeError("No Snowflake private key found in config")

        p_key = serialization.load_pem_private_key(
            key_pem.encode() if isinstance(key_pem, str) else key_pem,
            password=None,
            backend=default_backend(),
        )
        _sf_conn = snowflake.connector.connect(
            account=config.SNOWFLAKE_ACCOUNT,
            user=config.SNOWFLAKE_USER,
            private_key=p_key,
            warehouse=config.SNOWFLAKE_WAREHOUSE,
            role=config.SNOWFLAKE_ROLE,
        )
        logger.info("Snowflake connection established (user=%s, wh=%s)",
                     config.SNOWFLAKE_USER, config.SNOWFLAKE_WAREHOUSE)
        return _sf_conn

    return get_sf_connection


def _make_databricks_token_getter():
    """Create a Databricks token getter that uses bot.config secrets."""
    import time
    import json
    import os

    _cached_token: str = ""
    _token_expires: float = 0

    def _get_databricks_token():
        nonlocal _cached_token, _token_expires

        # If we have a cached token that's still valid, return it
        if _cached_token and time.time() < _token_expires:
            return _cached_token

        # Try config (Keywhiz / env var)
        token = config.DATABRICKS_ACCESS_TOKEN
        if token:
            _cached_token = token
            _token_expires = time.time() + 3300  # assume ~1hr, refresh 5min early
            return token

        # Try refreshing with refresh token
        refresh_token = config.DATABRICKS_REFRESH_TOKEN
        if refresh_token:
            try:
                resp = config.databricks_request('post',
                    f'{config.DATABRICKS_HOST}/oidc/v1/token',
                    data={
                        'grant_type': 'refresh_token',
                        'client_id': 'databricks-cli',
                        'refresh_token': refresh_token,
                    },
                    timeout=15,
                )
                if resp.ok:
                    data = resp.json()
                    _cached_token = data['access_token']
                    expires_in = data.get('expires_in', 3600)
                    _token_expires = time.time() + expires_in - 300
                    logger.info("Databricks token refreshed (expires in %ds)", expires_in)
                    return _cached_token
                else:
                    logger.warning("Databricks token refresh failed: %s %s",
                                   resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("Databricks token refresh error: %s", e)

        # Fall back to local file (Mac development)
        import glob
        token_files = glob.glob(os.path.expanduser('~/.config/goose/databricks/oauth/*.json'))
        if token_files:
            try:
                with open(token_files[0]) as f:
                    token_data = json.load(f)
                _cached_token = token_data.get('access_token', '')
                return _cached_token
            except Exception as e:
                logger.warning("Failed to read local Databricks token: %s", e)

        logger.error("No Databricks token available")
        return None

    return _get_databricks_token


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

    # Monkey-patch Snowflake and Databricks functions to use config secrets
    # This ensures SKI Keywhiz secrets are used instead of local file paths
    if config.IS_SKI or config.SNOWFLAKE_PRIVATE_KEY:
        logger.info("Patching Snowflake connection factory (config-based)")
        listener.get_sf_connection = _make_sf_connection_factory()

    if config.IS_SKI or config.DATABRICKS_ACCESS_TOKEN or config.DATABRICKS_REFRESH_TOKEN:
        logger.info("Patching Databricks token getter (config-based)")
        listener._get_databricks_token = _make_databricks_token_getter()

    logger.info("Config patched — Slack token: %s..., Poll: %ds, SKI: %s",
                config.SLACK_BOT_TOKEN[:15] if config.SLACK_BOT_TOKEN else "EMPTY",
                config.POLL_INTERVAL,
                config.IS_SKI)

    # Signal health endpoint that the listener is starting
    mark_listener_ready()
    logger.info("Listener marked ready — entering poll loop")

    listener.main()
