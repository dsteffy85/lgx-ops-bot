"""
LGX-OPS-BOT Configuration — loads from environment variables and mounted secrets.

Secrets are expected as files mounted from K8s secrets:
  - SNOWFLAKE_PRIVATE_KEY_PATH  → path to PEM file
  - SLACK_BOT_TOKEN             → token string (or path to file via SLACK_BOT_TOKEN_PATH)
  - DATABRICKS_TOKEN_PATH       → path to token file
"""

import os
import logging

logger = logging.getLogger(__name__)


def _read_secret_file(path: str) -> str:
    """Read a secret from a mounted file, stripping whitespace."""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning("Secret file not found: %s", path)
        return ""
    except Exception as e:
        logger.error("Failed to read secret file %s: %s", path, e)
        return ""


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN: str = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_BOT_TOKEN_PATH: str = os.environ.get("SLACK_BOT_TOKEN_PATH", "")
if not SLACK_BOT_TOKEN and SLACK_BOT_TOKEN_PATH:
    SLACK_BOT_TOKEN = _read_secret_file(SLACK_BOT_TOKEN_PATH)

BOT_USER_ID: str = os.environ.get("BOT_USER_ID", "U0ASVFR7NMB")

# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------
SNOWFLAKE_PRIVATE_KEY_PATH: str = os.environ.get(
    "SNOWFLAKE_PRIVATE_KEY_PATH", "/etc/secrets/snowflake/private_key.pem"
)
SNOWFLAKE_ACCOUNT: str = os.environ.get("SNOWFLAKE_ACCOUNT", "square")
SNOWFLAKE_USER: str = os.environ.get(
    "SNOWFLAKE_USER", "LGX_OPS_BOT@squareup.com"
)
SNOWFLAKE_WAREHOUSE: str = os.environ.get("SNOWFLAKE_WAREHOUSE", "ETL__MEDIUM")
SNOWFLAKE_ROLE: str = os.environ.get(
    "SNOWFLAKE_ROLE", "LGX_OPS_BOT__SNOWFLAKE__ADMIN"
)

# ---------------------------------------------------------------------------
# Databricks
# ---------------------------------------------------------------------------
DATABRICKS_HOST: str = os.environ.get(
    "DATABRICKS_HOST",
    "https://block-lakehouse-production.cloud.databricks.com",
)
DATABRICKS_TOKEN_PATH: str = os.environ.get(
    "DATABRICKS_TOKEN_PATH", "/etc/secrets/databricks/token"
)

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
POLL_INTERVAL: int = int(os.environ.get("POLL_INTERVAL", "10"))
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
