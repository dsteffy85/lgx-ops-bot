"""
LGX-OPS-BOT Configuration — loads from Keywhiz secrets, env vars, or local files.

On SKI: Keywhiz mounts secrets at /config/secrets/<secret-name>
Locally: Falls back to env vars, then hardcoded local paths.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Keywhiz mount path (SKI)
SECRETS_DIR = Path("/config/secrets")

# Local credential file (Mac development)
LOCAL_KEY_FILE = Path.home() / "Desktop" / "LGX_OPS_BOT_private_keys_20260408_191019.json"


def _read_secret(keywhiz_name: str, env_var: str = "", default: str = "") -> str:
    """Read a secret from Keywhiz mount, then env var, then default."""
    # 1. Keywhiz (SKI)
    secret_path = SECRETS_DIR / keywhiz_name
    if secret_path.exists():
        try:
            val = secret_path.read_text().strip()
            if val:
                logger.info("Loaded secret from Keywhiz: %s", keywhiz_name)
                return val
        except Exception as e:
            logger.warning("Failed to read Keywhiz secret %s: %s", keywhiz_name, e)
    # 2. Environment variable
    if env_var and os.environ.get(env_var):
        logger.info("Loaded secret from env: %s", env_var)
        return os.environ[env_var]
    # 3. Default
    if default:
        logger.info("Using default for: %s", keywhiz_name)
    return default


def _read_snowflake_key() -> str:
    """Read Snowflake private key from Keywhiz, env, or local JSON file."""
    key = _read_secret("lgx-ops-bot-snowflake-key", "SNOWFLAKE_PRIVATE_KEY")
    if key:
        return key
    # Local fallback: read from JSON key file
    if LOCAL_KEY_FILE.exists():
        try:
            data = json.loads(LOCAL_KEY_FILE.read_text())
            key = data.get("private_key", "")
            if key:
                logger.info("Loaded Snowflake key from local file: %s", LOCAL_KEY_FILE)
                return key
        except Exception as e:
            logger.warning("Failed to read local key file: %s", e)
    return ""


# Runtime detection
IS_SKI = SECRETS_DIR.exists() and any(SECRETS_DIR.iterdir()) if SECRETS_DIR.exists() else False

# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN: str = _read_secret(
    "lgx-ops-bot-slack-token", "SLACK_BOT_TOKEN"
)
BOT_USER_ID: str = "U0ASVFR7NMB"
BOT_SIGNATURE: str = "LGX-OPS-BOT"
OSCAR_ID: str = "U02DXNZF8SF"

# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------
SNOWFLAKE_PRIVATE_KEY: str = _read_snowflake_key()
SNOWFLAKE_ACCOUNT: str = os.environ.get("SNOWFLAKE_ACCOUNT", "square")
SNOWFLAKE_USER: str = os.environ.get("SNOWFLAKE_USER", "LGX_OPS_BOT@squareup.com")
SNOWFLAKE_WAREHOUSE: str = os.environ.get("SNOWFLAKE_WAREHOUSE", "ETL__MEDIUM")
SNOWFLAKE_ROLE: str = os.environ.get("SNOWFLAKE_ROLE", "LGX_OPS_BOT__SNOWFLAKE__ADMIN")

# ---------------------------------------------------------------------------
# Databricks (LLM)
# ---------------------------------------------------------------------------
DATABRICKS_HOST: str = os.environ.get(
    "DATABRICKS_HOST", "https://block-lakehouse-production.cloud.databricks.com"
)
DATABRICKS_ACCESS_TOKEN: str = _read_secret(
    "lgx-ops-bot-databricks-token", "DATABRICKS_ACCESS_TOKEN"
)
DATABRICKS_REFRESH_TOKEN: str = _read_secret(
    "lgx-ops-bot-databricks-refresh", "DATABRICKS_REFRESH_TOKEN"
)

# ---------------------------------------------------------------------------
# Channel config
# ---------------------------------------------------------------------------
HARDWAREDELIVERYHELP_ID: str = "C2L95G8TF"
CHANNEL_OVERRIDES: dict = {
    HARDWAREDELIVERYHELP_ID: {"oscar_cc": True, "disclaimer": True},
}
DEFAULT_CHANNEL_CONFIG: dict = {"oscar_cc": False, "disclaimer": False}

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
POLL_INTERVAL: int = int(os.environ.get("POLL_INTERVAL", "10"))
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
