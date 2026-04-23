"""
LGX-OPS-BOT Configuration — loads from Keywhiz secrets, env vars, or local files.

On SKI: Keywhiz mounts secrets at /config/secrets/<secret-name>
Locally: Falls back to env vars, then hardcoded local paths.
"""

import os
import json
import glob
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Keywhiz mount path (SKI)
SECRETS_DIR = Path("/config/secrets")

# Local credential paths (Mac development)
_LOCAL_KEY_PATTERNS = [
    str(Path.home() / "Desktop" / "Automation" / "lgx-ops-bot" / "credentials" / "LGX_OPS_BOT_private_keys_*.json"),
    str(Path.home() / "Desktop" / "LGX_OPS_BOT_private_keys_*.json"),
]


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
    """Read Snowflake private key from Keywhiz, env, or local JSON file.

    The Keywhiz secret should contain the raw PEM private key.
    The local JSON file contains {"square": {"private_key": "-----BEGIN..."}}.
    """
    # 1. Keywhiz / env var (raw PEM)
    key = _read_secret("lgx-ops-bot-snowflake-key", "SNOWFLAKE_PRIVATE_KEY")
    if key:
        return key

    # 2. Local fallback: read from JSON key file
    for pattern in _LOCAL_KEY_PATTERNS:
        key_files = glob.glob(pattern)
        if key_files:
            try:
                data = json.loads(Path(key_files[0]).read_text())
                # Handle both {"private_key": ...} and {"square": {"private_key": ...}}
                key = data.get("private_key", "")
                if not key and "square" in data:
                    key = data["square"].get("private_key", "")
                if key:
                    logger.info("Loaded Snowflake key from local file: %s", key_files[0])
                    return key
            except Exception as e:
                logger.warning("Failed to read local key file %s: %s", key_files[0], e)
    return ""


# Runtime detection
IS_SKI = SECRETS_DIR.exists() and any(SECRETS_DIR.iterdir()) if SECRETS_DIR.exists() else False

# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------
SLACK_BOT_TOKEN: str = _read_secret(
    "lgx-ops-bot-slack-token", "SLACK_BOT_TOKEN"
)

# Also try .env.local for local development
if not SLACK_BOT_TOKEN:
    _env_path = Path(__file__).resolve().parent.parent / ".env.local"
    if _env_path.exists():
        try:
            for line in _env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "SLACK_BOT_TOKEN":
                        SLACK_BOT_TOKEN = v.strip()
                        logger.info("Loaded SLACK_BOT_TOKEN from .env.local")
                        break
        except Exception as e:
            logger.warning("Failed to read .env.local: %s", e)

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
RETAIL_OPS_HELP_ID: str = "C0AT9NHTR4H"
CHANNEL_OVERRIDES: dict = {
    HARDWAREDELIVERYHELP_ID: {"oscar_cc": True, "disclaimer": True},
}
DEFAULT_CHANNEL_CONFIG: dict = {"oscar_cc": False, "disclaimer": False}

# ---------------------------------------------------------------------------
# Databricks proxy workaround (SKI PrivateLink DNS issue)
# ---------------------------------------------------------------------------
# On SKI, block-lakehouse-production.cloud.databricks.com resolves via
# PrivateLink DNS to 10.172.x.x — unreachable from the staging VPC.
# Route through oregon.cloud.databricks.com with workspace Host header.
DATABRICKS_PROXY_WORKAROUND: bool = os.environ.get(
    "DATABRICKS_PROXY_WORKAROUND", ""
).lower() in ("1", "true", "yes")
_DATABRICKS_WORKSPACE = "block-lakehouse-production.cloud.databricks.com"
_DATABRICKS_PUBLIC = "oregon.cloud.databricks.com"


def databricks_request(method: str, url: str, **kwargs):
    """Make a Databricks API request, routing through public hostname on SKI."""
    import requests as _req
    if DATABRICKS_PROXY_WORKAROUND and _DATABRICKS_WORKSPACE in url:
        url = url.replace(
            f"https://{_DATABRICKS_WORKSPACE}",
            f"https://{_DATABRICKS_PUBLIC}",
        )
        headers = kwargs.get("headers", {})
        headers["Host"] = _DATABRICKS_WORKSPACE
        kwargs["headers"] = headers
    return getattr(_req, method)(url, **kwargs)


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
POLL_INTERVAL: int = int(os.environ.get("POLL_INTERVAL", "10"))
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
