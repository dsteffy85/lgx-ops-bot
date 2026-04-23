#!/usr/bin/env python3
"""
LGX-OPS-BOT Slack Listener — polls channels every 10 seconds for new questions,
queries Snowflake, and posts answers via direct Slack API calls.

Usage:
    python3 slack_listener.py                    # Watch all configured channels
    python3 slack_listener.py --test-only        # Watch only #squirt-test
    python3 slack_listener.py --prod-only        # Watch only #hardwaredeliveryhelp

Runs as a persistent background process. Ctrl+C to stop.
"""
import json
import time
import re
import sys
import glob
import os
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

# ============================================================================
# DATABRICKS PROXY WORKAROUND (SKI only)
# ============================================================================
# Workaround is implemented in bot.config.databricks_request().
# When running standalone (not via bot.main), define a local fallback.
try:
    from bot.config import databricks_request as _databricks_request
except ImportError:
    # Standalone mode — define locally
    _DATABRICKS_WORKSPACE = 'block-lakehouse-production.cloud.databricks.com'
    _DATABRICKS_PUBLIC = 'oregon.cloud.databricks.com'
    _USE_DATABRICKS_WORKAROUND = os.environ.get(
        'DATABRICKS_PROXY_WORKAROUND', ''
    ).lower() in ('1', 'true', 'yes')

    def _databricks_request(method: str, url: str, **kwargs) -> requests.Response:
        if _USE_DATABRICKS_WORKAROUND and _DATABRICKS_WORKSPACE in url:
            url = url.replace(
                f'https://{_DATABRICKS_WORKSPACE}',
                f'https://{_DATABRICKS_PUBLIC}',
            )
            headers = kwargs.get('headers', {})
            headers['Host'] = _DATABRICKS_WORKSPACE
            kwargs['headers'] = headers
        return getattr(requests, method)(url, **kwargs)


# ============================================================================
# CONFIG
# ============================================================================
# Channel-specific overrides (special behavior for known channels)
CHANNEL_OVERRIDES = {
    "C2L95G8TF": {  # #hardwaredeliveryhelp
        "oscar_cc": True,
        "disclaimer": True,
    },
}

# Default config for any channel the bot is added to
DEFAULT_CHANNEL_CONFIG = {
    "oscar_cc": False,
    "disclaimer": False,
}

OSCAR_ID = "U02DXNZF8SF"
POLL_INTERVAL = 10  # seconds
BOT_SIGNATURE = "LGX-OPS-BOT"

# Load .env.local if SLACK_BOT_TOKEN not already in environment
if not os.environ.get("SLACK_BOT_TOKEN"):
    _env_path = Path(__file__).resolve().parent.parent / ".env.local"
    if _env_path.exists():
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _key, _val = _line.split("=", 1)
                    os.environ[_key.strip()] = _val.strip()

LGX_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
BOT_USER_ID = "U0ASVFR7NMB"  # @lgxopsbot Slack user ID
ADMIN_USER_ID = "U04RK34LMFG"  # dsteffy — only admin can use learning commands
CHANNEL_REFRESH_INTERVAL = 300  # Re-discover channels every 5 minutes
LEARNED_FACTS_PATH = Path(__file__).parent.parent / 'shared' / 'learned_facts.json'

# Cached channel list: {channel_id: {"name": ..., "oscar_cc": ..., "disclaimer": ...}}
_discovered_channels: Dict[str, Dict] = {}
_last_channel_refresh: float = 0

# Track which messages we've already processed (persists in memory)
processed_threads: set = set()

# Learned facts loaded from shared/learned_facts.json
LEARNED_FACTS: List[Dict] = []
# Users with a pending 'clear memory' confirmation
_pending_clear_confirmations: set = set()

# ============================================================================
# CHANNEL DISCOVERY
# ============================================================================
def discover_channels() -> Dict[str, Dict]:
    """Discover all channels the bot is a member of via Slack API.
    
    Uses users.conversations (Tier 2, 20 req/min) which only returns
    channels the bot is already a member of — much lighter than conversations.list.
    """
    global _discovered_channels, _last_channel_refresh

    now = time.time()
    if _discovered_channels and (now - _last_channel_refresh) < CHANNEL_REFRESH_INTERVAL:
        return _discovered_channels

    channels = {}
    cursor = None
    try:
        while True:
            params = {'types': 'public_channel,private_channel', 'limit': '100', 'exclude_archived': 'true'}
            if cursor:
                params['cursor'] = cursor
            resp = requests.get(
                'https://slack.com/api/users.conversations',
                headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}'},
                params=params,
                timeout=15
            )
            data = resp.json()
            if not data.get('ok'):
                error = data.get('error', 'unknown')
                if error == 'ratelimited':
                    retry_after = int(resp.headers.get('Retry-After', '30'))
                    print(f"  [CHANNELS] Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                print(f"  [CHANNELS] API error: {error}")
                break

            for ch in data.get('channels', []):
                ch_id = ch['id']
                if ch.get('is_im'):
                    other_user = ch.get('user', ch_id)
                    ch_name = f"DM-{other_user}"
                    config = dict(DEFAULT_CHANNEL_CONFIG)
                    config['name'] = ch_name
                    config['is_dm'] = True
                    config['dm_user'] = other_user
                else:
                    ch_name = ch.get('name', ch_id)
                    config = dict(DEFAULT_CHANNEL_CONFIG)
                    config['name'] = ch_name
                    if ch_id in CHANNEL_OVERRIDES:
                        config.update(CHANNEL_OVERRIDES[ch_id])
                channels[ch_id] = config

            cursor = data.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break

        # Separately try to fetch DMs (requires im:read scope — may not be available)
        try:
            im_cursor = None
            while True:
                im_params = {'types': 'im', 'limit': '100'}
                if im_cursor:
                    im_params['cursor'] = im_cursor
                im_resp = requests.get(
                    'https://slack.com/api/users.conversations',
                    headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}'},
                    params=im_params,
                    timeout=15
                )
                im_data = im_resp.json()
                if not im_data.get('ok'):
                    im_error = im_data.get('error', 'unknown')
                    if im_error == 'missing_scope':
                        print("  [CHANNELS] DMs disabled — bot needs im:read scope. Add at https://api.slack.com/apps")
                    else:
                        print(f"  [CHANNELS] DM fetch error: {im_error}")
                    break

                for ch in im_data.get('channels', []):
                    ch_id = ch['id']
                    other_user = ch.get('user', ch_id)
                    ch_name = f"DM-{other_user}"
                    config = dict(DEFAULT_CHANNEL_CONFIG)
                    config['name'] = ch_name
                    config['is_dm'] = True
                    config['dm_user'] = other_user
                    channels[ch_id] = config

                im_cursor = im_data.get('response_metadata', {}).get('next_cursor')
                if not im_cursor:
                    break
        except Exception as e:
            print(f"  [CHANNELS] DM discovery failed: {e}")

        if channels:
            _discovered_channels = channels
            _last_channel_refresh = now
            dm_count = sum(1 for c in channels.values() if c.get('is_dm'))
            ch_count = len(channels) - dm_count
            channel_names = sorted(c['name'] for c in channels.values() if not c.get('is_dm'))
            dm_label = f" + {dm_count} DMs" if dm_count else ""
            print(f"  [CHANNELS] Watching {ch_count} channels{dm_label}: {', '.join(channel_names)}")
        else:
            print("  [CHANNELS] No channels found — is the bot added to any channels?")

    except Exception as e:
        print(f"  [CHANNELS] Discovery failed: {e}")

    # Always return something — cached or empty
    return _discovered_channels


# ============================================================================
# PLAYBOOK (loaded once at startup for #hardwaredeliveryhelp)
# ============================================================================
_playbook_cache: Optional[str] = None

def _load_playbook() -> str:
    """Load the hardwaredeliveryhelp playbook for enriched responses."""
    global _playbook_cache
    if _playbook_cache is not None:
        return _playbook_cache
    playbook_path = Path(__file__).parent.parent / 'docs' / 'hardwaredeliveryhelp-playbook.md'
    if playbook_path.exists():
        _playbook_cache = playbook_path.read_text()
        print(f"  [PLAYBOOK] Loaded {len(_playbook_cache):,} chars from {playbook_path.name}")
    else:
        _playbook_cache = ""
        print(f"  [PLAYBOOK] Not found at {playbook_path}")
    return _playbook_cache

# ============================================================================
# LEARNED FACTS
# ============================================================================
def _load_learned_facts() -> List[Dict]:
    """Load learned facts from disk into LEARNED_FACTS global."""
    global LEARNED_FACTS
    if LEARNED_FACTS_PATH.exists():
        try:
            with open(LEARNED_FACTS_PATH) as f:
                data = json.load(f)
            LEARNED_FACTS = data.get('facts', [])
            print(f"  [MEMORY] Loaded {len(LEARNED_FACTS)} learned fact(s)")
        except Exception as e:
            print(f"  [MEMORY] Failed to load learned facts: {e}")
            LEARNED_FACTS = []
    else:
        LEARNED_FACTS = []
    return LEARNED_FACTS


def _save_learned_facts():
    """Save LEARNED_FACTS to disk and reload global."""
    global LEARNED_FACTS
    LEARNED_FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARNED_FACTS_PATH, 'w') as f:
        json.dump({'facts': LEARNED_FACTS}, f, indent=2)
    _load_learned_facts()


def _get_learned_facts_prompt() -> str:
    """Return formatted learned facts for injection into LLM prompts."""
    if not LEARNED_FACTS:
        return ""
    lines = [f"- {f['fact']}" for f in LEARNED_FACTS]
    return "LEARNED FACTS (from team feedback):\n" + "\n".join(lines)


def _is_learning_command(text: str) -> bool:
    """Check if a message looks like a learning command."""
    t = text.lower().strip()
    return (t.startswith('remember:') or t.startswith('correct:') or
            t.startswith('forget:') or t == 'show memory' or t == 'clear memory')


def _handle_learning_command(user_id: str, text: str) -> Optional[str]:
    """Handle admin learning commands. Returns response text or None if not a command."""
    global LEARNED_FACTS, _pending_clear_confirmations

    t = text.strip()
    t_lower = t.lower()

    # Handle pending clear memory confirmation
    if user_id in _pending_clear_confirmations and t_lower == 'yes':
        _pending_clear_confirmations.discard(user_id)
        LEARNED_FACTS = []
        _save_learned_facts()
        return "✅ Memory cleared. All learned facts have been removed."

    if t_lower.startswith('remember:'):
        fact_text = t[len('remember:'):].strip()
        if not fact_text:
            return "Please provide a fact to remember. Usage: `remember: <fact>`"
        next_id = max((f['id'] for f in LEARNED_FACTS), default=0) + 1
        LEARNED_FACTS.append({
            'id': next_id,
            'fact': fact_text,
            'type': 'fact',
            'added_at': datetime.now(timezone.utc).isoformat(),
            'added_by': user_id,
        })
        _save_learned_facts()
        return f"✅ Got it — I'll remember that. (fact #{next_id})"

    elif t_lower.startswith('correct:'):
        rest = t[len('correct:'):].strip()
        if '→' in rest:
            topic = rest.split('→', 1)[0].strip()
        else:
            topic = rest
        next_id = max((f['id'] for f in LEARNED_FACTS), default=0) + 1
        LEARNED_FACTS.append({
            'id': next_id,
            'fact': rest,
            'type': 'correction',
            'added_at': datetime.now(timezone.utc).isoformat(),
            'added_by': user_id,
        })
        _save_learned_facts()
        return f"✅ Correction noted for '{topic}'. I'll use this going forward."

    elif t_lower.startswith('forget:'):
        query = t[len('forget:'):].strip()
        if not query:
            return "Please specify what to forget. Usage: `forget: <N>` or `forget: <search text>`"
        removed = None
        if query.isdigit():
            fact_id = int(query)
            for i, f in enumerate(LEARNED_FACTS):
                if f['id'] == fact_id:
                    removed = LEARNED_FACTS.pop(i)
                    break
        else:
            for i, f in enumerate(LEARNED_FACTS):
                if query.lower() in f['fact'].lower():
                    removed = LEARNED_FACTS.pop(i)
                    break
        if removed:
            _save_learned_facts()
            return f"✅ Forgot: '{removed['fact']}'"
        return f"No fact found matching '{query}'."

    elif t_lower == 'show memory':
        if not LEARNED_FACTS:
            return "No learned facts yet."
        lines = []
        for f in LEARNED_FACTS:
            date_str = f.get('added_at', '')[:10]
            type_tag = '[correction] ' if f.get('type') == 'correction' else ''
            lines.append(f"#{f['id']} [{date_str}] {type_tag}{f['fact']}")
        return "Learned facts:\n" + "\n".join(lines)

    elif t_lower == 'clear memory':
        if not LEARNED_FACTS:
            return "No learned facts to clear."
        _pending_clear_confirmations.add(user_id)
        return f"Are you sure? This will remove all {len(LEARNED_FACTS)} learned facts. Reply 'yes' to confirm."

    return None


# ============================================================================
# SNOWFLAKE CONNECTION
# ============================================================================
_sf_conn = None

def get_sf_connection():
    """Lazy Snowflake connection with reconnect."""
    global _sf_conn
    if _sf_conn is not None:
        try:
            _sf_conn.cursor().execute("SELECT 1")
            return _sf_conn
        except Exception:
            _sf_conn = None

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import snowflake.connector

    key_files = glob.glob(str(Path.home() / 'Desktop' / 'Automation' / 'lgx-ops-bot' / 'credentials' / 'LGX_OPS_BOT_private_keys_*.json'))
    with open(key_files[0]) as f:
        data = json.load(f)
    p_key = serialization.load_pem_private_key(
        data['square']['private_key'].encode(), password=None, backend=default_backend()
    )
    _sf_conn = snowflake.connector.connect(
        account='square',
        user='LGX_OPS_BOT@squareup.com',
        private_key=p_key,
        warehouse='ETL__MEDIUM',
        role='LGX_OPS_BOT__SNOWFLAKE__ADMIN',
    )
    return _sf_conn


def query_sf(sql: str) -> Tuple[List[str], List[tuple]]:
    """Execute a Snowflake query, return (columns, rows)."""
    conn = get_sf_connection()
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return cols, rows


# ============================================================================
# SLACK HELPERS (direct Slack API — no sq agent-tools dependency)
# ============================================================================
def read_channel_api(channel_id: str, count: int = 15) -> List[Dict]:
    """Read recent messages from a channel via Slack conversations.history API.

    Returns a list of Slack message dicts (newest first), each with at least:
      ts, text, user, subtype, reply_count

    # TODO: Add cursor pagination for count > 100 (Slack max per page).
    # Current limit of 15 is well under the threshold.
    """
    try:
        resp = requests.get(
            'https://slack.com/api/conversations.history',
            headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}'},
            params={'channel': channel_id, 'limit': str(count)},
            timeout=15,
        )
        data = resp.json()
        if data.get('ok'):
            return data.get('messages', [])
        error = data.get('error', 'unknown')
        if error == 'ratelimited':
            retry_after = int(resp.headers.get('Retry-After', '30'))
            print(f"  [CHANNELS] Rate limited on history, waiting {retry_after}s...")
            time.sleep(retry_after)
        else:
            print(f"  [CHANNELS] conversations.history error: {error}")
    except Exception as e:
        print(f"  [!] Error reading channel {channel_id}: {e}")
    return []


def read_thread_api(channel_id: str, thread_ts: str, limit: int = 20) -> List[Dict]:
    """Read thread replies via Slack conversations.replies API.

    Returns a list of Slack message dicts (first element is the parent).

    # TODO: Add cursor pagination for threads with > 100 replies.
    # Current limit of 20 is well under the threshold.
    """
    try:
        resp = requests.get(
            'https://slack.com/api/conversations.replies',
            headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}'},
            params={'channel': channel_id, 'ts': thread_ts, 'limit': str(limit)},
            timeout=15,
        )
        data = resp.json()
        if data.get('ok'):
            return data.get('messages', [])
        print(f"  [!] conversations.replies error: {data.get('error', 'unknown')}")
    except Exception as e:
        print(f"  [!] Error reading thread {thread_ts}: {e}")
    return []


def thread_has_bot_reply(channel_id: str, thread_ts: str) -> bool:
    """Check if a thread already has a reply from this bot."""
    replies = read_thread_api(channel_id, thread_ts)
    for reply in replies:
        # Check by bot user ID
        if reply.get('user') == BOT_USER_ID:
            return True
        # Check by signature text in message body
        if BOT_SIGNATURE in reply.get('text', ''):
            return True
    return False


def post_thread(channel_id: str, thread_ts: str, text: str) -> str:
    """Post a threaded reply as the LGX-OPS-BOT Slack app.
    
    NEVER falls back to sq agent-tools — that posts as dsteffy.
    If the bot token is missing or the API call fails, log the error and skip.
    """
    if not LGX_BOT_TOKEN:
        print(f"  [!] SLACK_BOT_TOKEN not set — refusing to post (would appear as dsteffy)")
        return ''
    try:
        resp = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}', 'Content-Type': 'application/json'},
            json={
                'channel': channel_id,
                'thread_ts': thread_ts,
                'text': text,
                'unfurl_links': False,
                'unfurl_media': False,
            },
            timeout=15
        )
        data = resp.json()
        if not data.get('ok'):
            print(f"  [!] Slack API error: {data.get('error', 'unknown')} — skipping (will NOT fall back to sq agent-tools)")
            return ''
        return data.get('ts', '')
    except Exception as e:
        print(f"  [!] Slack post failed: {e} — skipping (will NOT fall back to sq agent-tools)")
        return ''


def post_message(channel_id: str, text: str) -> str:
    """Post a direct message to a channel/DM (no thread_ts — used for DM replies)."""
    if not LGX_BOT_TOKEN:
        print(f"  [!] SLACK_BOT_TOKEN not set — refusing to post")
        return ''
    try:
        resp = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}', 'Content-Type': 'application/json'},
            json={
                'channel': channel_id,
                'text': text,
                'unfurl_links': False,
                'unfurl_media': False,
            },
            timeout=15
        )
        data = resp.json()
        if not data.get('ok'):
            print(f"  [!] Slack API error: {data.get('error', 'unknown')}")
            return ''
        return data.get('ts', '')
    except Exception as e:
        print(f"  [!] Slack post failed: {e}")
        return ''


# ============================================================================
# ORDER LOOKUP
# ============================================================================
def lookup_order(order_number: str) -> Dict[str, Any]:
    """Look up an order in DELIVERY_ORDERS, SHIPMENTS, and RPT_SQ_DELIVERY_PERFORMANCE (fallback)."""
    result = {"delivery": None, "shipment": None}

    # Sanitize order number to prevent SQL injection
    safe_order = order_number.replace("'", "''")

    cols, rows = query_sf(f"""
    SELECT ORDER_NUMBER, CUSTOMER_NAME, FACILITIES, CARRIERS,
        ORDERED_DATE, SENT_TO_WH_DATE, FIRST_SHIP_DATE, LAST_SHIP_DATE,
        FIRST_DELIVERY_DATE, LAST_DELIVERY_DATE, ESTIMATED_DELIVERY_DATE,
        UNIQUE_SKUS, TOTAL_ITEMS, SHIPMENT_COUNT, TRACKING_NUMBERS,
        ORDER_STATUS, DELIVERY_STATUS, SHIPPING_METHOD, PROCESSING_DAYS, TRANSIT_DAYS,
        DAYS_TO_DELIVERY, STATE, CITY, COUNTRY
    FROM LGX_OPS_BOT.WIGEON.DELIVERY_ORDERS
    WHERE ORDER_NUMBER = '{safe_order}'
    """)
    if rows:
        result["delivery"] = dict(zip(cols, [str(v) if v is not None else None for v in rows[0]]))

    cols2, rows2 = query_sf(f"""
    SELECT ORDER_TOKEN, ORDER_TYPE, ORDER_TYPE_NAME, FACILITIES, CARRIERS,
        SHIP_METHOD, FIRST_SHIP_DATE, LAST_SHIP_DATE,
        UNIQUE_SKUS, TOTAL_ITEMS, SHIPMENT_COUNT, TRACKING_NUMBERS,
        TOTAL_STD_COST, SERIAL_COUNT, IS_EXPEDITED
    FROM LGX_OPS_BOT.WIGEON.SHIPMENTS
    WHERE ORDER_TOKEN = '{safe_order}'
    """)
    if rows2:
        result["shipment"] = dict(zip(cols2, [str(v) if v is not None else None for v in rows2[0]]))

    # Fallback: check source RPT_SQ_DELIVERY_PERFORMANCE if not in curated tables
    if not result["delivery"] and not result["shipment"]:
        try:
            cols3, rows3 = query_sf(f"""
            SELECT ORDER_NUMBER, CUSTOMER_NAME, FACILITY, CARRIER_CODE,
                ORDERED_DATE, SENT_TO_WAREHOUSE_DATE, SHIPPED_DATE, DELIVERY_DATE,
                ESTIMATED_DELIVERY_DATE, TRACKING_NUMBER, EVENT_CODE,
                DELIVERY_STATUS, ITEM_NAME, COUNTRY, STATE, CITY,
                SHIPPING_METHOD, PROCESSING_DAYS, TRANSIT_DAYS, DAYS_TO_DELIVERY,
                IS_DELIVERED, CANCELLED_FLAG
            FROM APP_HARDWARE.MART_LOGISTICS.RPT_SQ_DELIVERY_PERFORMANCE
            WHERE ORDER_NUMBER = '{safe_order}'
            ORDER BY SHIPPED_DATE DESC NULLS LAST
            LIMIT 5
            """)
            if rows3:
                # Combine line-level data into order-level summary
                first = dict(zip(cols3, [str(v) if v is not None else None for v in rows3[0]]))
                tracking_nums = list(set(str(r[cols3.index('TRACKING_NUMBER')]) for r in rows3 if r[cols3.index('TRACKING_NUMBER')]))
                items = list(set(str(r[cols3.index('ITEM_NAME')]) for r in rows3 if r[cols3.index('ITEM_NAME')]))

                result["delivery"] = {
                    "ORDER_NUMBER": first.get("ORDER_NUMBER"),
                    "CUSTOMER_NAME": first.get("CUSTOMER_NAME"),
                    "FACILITIES": first.get("FACILITY"),
                    "CARRIERS": first.get("CARRIER_CODE"),
                    "ORDERED_DATE": first.get("ORDERED_DATE"),
                    "SENT_TO_WH_DATE": first.get("SENT_TO_WAREHOUSE_DATE"),
                    "FIRST_SHIP_DATE": first.get("SHIPPED_DATE"),
                    "LAST_SHIP_DATE": first.get("SHIPPED_DATE"),
                    "FIRST_DELIVERY_DATE": first.get("DELIVERY_DATE"),
                    "LAST_DELIVERY_DATE": first.get("DELIVERY_DATE"),
                    "ESTIMATED_DELIVERY_DATE": first.get("ESTIMATED_DELIVERY_DATE"),
                    "TRACKING_NUMBERS": ", ".join(tracking_nums),
                    "ORDER_STATUS": "DELIVERED" if first.get("IS_DELIVERED") == "True" else
                                    "CANCELLED" if first.get("CANCELLED_FLAG") == "Y" else
                                    "SHIPPED" if first.get("SHIPPED_DATE") else "PROCESSING",
                    "DELIVERY_STATUS": first.get("DELIVERY_STATUS"),
                    "SHIPPING_METHOD": first.get("SHIPPING_METHOD"),
                    "PROCESSING_DAYS": first.get("PROCESSING_DAYS"),
                    "TRANSIT_DAYS": first.get("TRANSIT_DAYS"),
                    "DAYS_TO_DELIVERY": first.get("DAYS_TO_DELIVERY"),
                    "UNIQUE_SKUS": str(len(items)),
                    "TOTAL_ITEMS": str(len(rows3)),
                    "SHIPMENT_COUNT": str(len(tracking_nums)),
                    "STATE": first.get("STATE"),
                    "CITY": first.get("CITY"),
                    "COUNTRY": first.get("COUNTRY"),
                    "_SOURCE": "RPT_SQ_DELIVERY_PERFORMANCE",
                }
                print(f"  [FALLBACK] Found {order_number} in RPT_SQ_DELIVERY_PERFORMANCE ({len(rows3)} lines)")
        except Exception as e:
            print(f"  [FALLBACK] RPT lookup failed: {e}")

    return result


def format_date(date_str: Optional[str]) -> str:
    """Format a date string to 'Apr 6' style."""
    if not date_str or date_str == 'None':
        return 'n/a'
    try:
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
            try:
                dt = datetime.strptime(date_str.split('.')[0][:19], fmt)
                return dt.strftime('%b %-d')
            except ValueError:
                continue
        return date_str[:10]
    except Exception:
        return date_str[:10] if date_str else 'n/a'


def format_order_response(order_number: str, data: Dict, channel_config: Dict,
                          ticket_text: str = "") -> str:
    """Format an order lookup into a Slack message.

    For #hardwaredeliveryhelp, uses the playbook + LLM to generate an enriched
    response with triage, next steps, and escalation guidance.
    For other channels, uses the original simple format.
    """
    d = data.get("delivery")
    s = data.get("shipment")

    # --- Not found ---
    if not d and not s:
        msg = f"Order `{order_number}` not found in delivery tracking data.\n\n"
        msg += "Possible reasons:\n"
        msg += "• Order was placed very recently and hasn't reached the warehouse yet\n"
        msg += "• Order number may be incorrect — please verify\n"
        msg += "• This may be a *return order* (not an outbound shipment)\n"
        msg += "• For BOPIS orders, this channel cannot assist — please contact the retail team\n"
        if channel_config.get("oscar_cc"):
            msg += f"\ncc <@{OSCAR_ID}> for manual investigation"
        if channel_config.get("disclaimer"):
            msg += f"\n\n_Automated lookup by {BOT_SIGNATURE}._"
        return msg

    # --- Build data summary for LLM ---
    order_data_summary = ""
    if d:
        order_data_summary = (
            f"ORDER_NUMBER: {d.get('ORDER_NUMBER', order_number)}\n"
            f"ORDER_STATUS: {d.get('ORDER_STATUS', 'UNKNOWN')}\n"
            f"CUSTOMER_NAME: {d.get('CUSTOMER_NAME', 'n/a')}\n"
            f"ORDERED_DATE: {d.get('ORDERED_DATE', 'n/a')}\n"
            f"SENT_TO_WH_DATE: {d.get('SENT_TO_WH_DATE', 'n/a')}\n"
            f"FIRST_SHIP_DATE: {d.get('FIRST_SHIP_DATE', 'n/a')}\n"
            f"LAST_SHIP_DATE: {d.get('LAST_SHIP_DATE', 'n/a')}\n"
            f"FIRST_DELIVERY_DATE: {d.get('FIRST_DELIVERY_DATE', 'n/a')}\n"
            f"LAST_DELIVERY_DATE: {d.get('LAST_DELIVERY_DATE', 'n/a')}\n"
            f"ESTIMATED_DELIVERY_DATE: {d.get('ESTIMATED_DELIVERY_DATE', 'n/a')}\n"
            f"FACILITIES: {d.get('FACILITIES', 'n/a')}\n"
            f"CARRIERS: {d.get('CARRIERS', 'n/a')}\n"
            f"SHIPPING_METHOD: {d.get('SHIPPING_METHOD', 'n/a')}\n"
            f"TRACKING_NUMBERS: {d.get('TRACKING_NUMBERS', 'n/a')}\n"
            f"UNIQUE_SKUS: {d.get('UNIQUE_SKUS', 'n/a')}\n"
            f"TOTAL_ITEMS: {d.get('TOTAL_ITEMS', 'n/a')}\n"
            f"SHIPMENT_COUNT: {d.get('SHIPMENT_COUNT', 'n/a')}\n"
            f"PROCESSING_DAYS: {d.get('PROCESSING_DAYS', 'n/a')}\n"
            f"TRANSIT_DAYS: {d.get('TRANSIT_DAYS', 'n/a')}\n"
            f"DAYS_TO_DELIVERY: {d.get('DAYS_TO_DELIVERY', 'n/a')}\n"
            f"CITY: {d.get('CITY', 'n/a')}\n"
            f"STATE: {d.get('STATE', 'n/a')}\n"
            f"COUNTRY: {d.get('COUNTRY', 'n/a')}\n"
        )
    if s and not d:
        order_data_summary = (
            f"ORDER_TOKEN: {s.get('ORDER_TOKEN', order_number)}\n"
            f"ORDER_TYPE: {s.get('ORDER_TYPE', 'n/a')}\n"
            f"FACILITIES: {s.get('FACILITIES', 'n/a')}\n"
            f"CARRIERS: {s.get('CARRIERS', 'n/a')}\n"
            f"SHIP_METHOD: {s.get('SHIP_METHOD', 'n/a')}\n"
            f"FIRST_SHIP_DATE: {s.get('FIRST_SHIP_DATE', 'n/a')}\n"
            f"TRACKING_NUMBERS: {s.get('TRACKING_NUMBERS', 'n/a')}\n"
            f"TOTAL_ITEMS: {s.get('TOTAL_ITEMS', 'n/a')}\n"
        )

    # --- Detect region and enrich ticket context for EU/UK/AU orders ---
    region = _get_region_from_order(order_number)
    if region != 'US':
        parsed = parse_eu_ticket(ticket_text)
        eu_context = ""
        if parsed.get('issue_type'):
            eu_context += f"Issue type: {parsed['issue_type']}\n"
        if parsed.get('details'):
            eu_context += f"Details: {parsed['details']}\n"
        if parsed.get('merchant_token'):
            eu_context += f"Merchant token: {parsed['merchant_token']}\n"
        if parsed.get('team'):
            eu_context += f"Team: {parsed['team']}\n"
        if eu_context:
            ticket_text = eu_context + "\n" + ticket_text
        print(f"  [TRIAGE] {region} order detected: {order_number}")

    # --- For #hardwaredeliveryhelp: use playbook + LLM for enriched response ---
    playbook = _load_playbook()
    if playbook and channel_config.get("oscar_cc"):
        enriched = _generate_playbook_response(order_number, order_data_summary,
                                                ticket_text, playbook, channel_config,
                                                region=region)
        if enriched:
            return enriched

    # --- Fallback: simple formatted response (other channels or LLM failure) ---
    if d:
        status = d.get('ORDER_STATUS', 'UNKNOWN')
        ordered = format_date(d.get('ORDERED_DATE'))
        sent_wh = format_date(d.get('SENT_TO_WH_DATE'))
        shipped = format_date(d.get('FIRST_SHIP_DATE'))
        delivered = format_date(d.get('LAST_DELIVERY_DATE'))
        facility = d.get('FACILITIES', 'n/a')
        carriers = d.get('CARRIERS', 'n/a')
        method = d.get('SHIPPING_METHOD', 'n/a')
        tracking = d.get('TRACKING_NUMBERS', 'n/a')
        skus = d.get('UNIQUE_SKUS', '?')
        items = d.get('TOTAL_ITEMS', '?')
        shipments = d.get('SHIPMENT_COUNT', '?')
        city = d.get('CITY', '')
        state = d.get('STATE', '')
        ship_to = f"{city}, {state}".strip(', ') if city or state else 'n/a'

        msg = f"*Order:* `{order_number}`\n"
        msg += f"*Status:* {status}\n"
        msg += f"*Ordered:* {ordered} → *Sent to WH:* {sent_wh} → *Shipped:* {shipped} → *Delivered:* {delivered}\n"
        msg += f"*Facility:* {facility}\n"
        msg += f"*Carrier:* {carriers} | *Method:* {method}\n"
        msg += f"*Tracking:* {tracking}\n"
        msg += f"*Items:* {skus} SKUs, {items} items across {shipments} shipments\n"
        msg += f"*Ship to:* {ship_to}"
    else:
        msg = f"*Order:* `{order_number}`\n*Shipment data only (no delivery tracking)*"

    if channel_config.get("oscar_cc"):
        msg += f"\n\ncc <@{OSCAR_ID}> for review"
    if channel_config.get("disclaimer"):
        msg += f"\n\n_Automated lookup by {BOT_SIGNATURE}._"

    return msg


def _generate_playbook_response(order_number: str, order_data: str,
                                 ticket_text: str, playbook: str,
                                 channel_config: Dict,
                                 region: str = 'US') -> Optional[str]:
    """Use the playbook + LLM to generate an enriched triage response."""
    try:

        host = os.environ.get('DATABRICKS_HOST', 'https://block-lakehouse-production.cloud.databricks.com')
        token = _get_databricks_token()
        if not token:
            return None

        today = datetime.now().strftime('%Y-%m-%d')

        # Region-specific carrier guidance for the prompt
        region_carrier_notes = {
            'UK': "UK carrier: DPD. B2C=1 attempt then parcel shop 5 days. B2B=2 attempts then RTS. Return location: Coalville.",
            'EU': "EU carrier: UPS. B2C=1 attempt + 5 days at Access Point. B2B=3 attempts then RTS. Return location: Born (FR/ES/IE).",
            'AU': "AU carriers: Australia Post (1 attempt, depot 10 days) or StarTrack (2 attempts). Return location: Villawood.",
        }
        carrier_note = region_carrier_notes.get(region, "")
        is_intl = region != 'US'

        system_prompt = (
            "You are LGX-OPS-BOT, an automated fulfillment triage assistant for #hardwaredeliveryhelp. "
            "You respond to Slack tickets about Square hardware orders.\n\n"
            "RULES:\n"
            "- Lead with the order data (status, dates, tracking) in a clear format\n"
            "- Then provide a *Triage Assessment* — what type of ticket is this and what's the situation\n"
            "- Then provide *Recommended Next Steps* — specific actions based on the playbook\n"
            "- Use Slack formatting: *bold* for labels, `code` for order/tracking numbers, bullet points\n"
            "- Be concise — max 15 lines total\n"
            "- Format dates as 'Apr 6' style\n"
            "- Use emoji: ✅ delivered, 🚚 in transit, ⏳ processing, ⚠️ delayed, 🔴 critical\n"
            "- Do NOT start with bot name or emoji prefix — the Slack app name is shown automatically\n"
            "- Do NOT make up data — only use what's provided\n"
            "- Do NOT promise refunds, generate labels, or take actions — only recommend\n"
            "- If the order is overdue, calculate days overdue from today's date\n"
            "- Always mention tracking number(s) so the submitter can check carrier status\n"
            + (f"- This is a {region} order — apply {region}-specific SLAs, carrier rules, and return locations\n"
               f"- {carrier_note}\n"
               "- Flag for SAS escalation if order value > $200; notify LGX if > $500\n"
               if is_intl else "")
            + f"- Today's date: {today}\n\n"
            "PLAYBOOK REFERENCE (use for triage logic, escalation rules, SLA thresholds, carrier claim windows):\n"
            f"{playbook}\n"
            + (f"\nEU/UK/AU FAQ (SLAs, carrier rules, return flows, escalation thresholds):\n{EU_UK_AU_FAQ}\n"
               if is_intl and EU_UK_AU_FAQ else "")
            + (f"\n{_get_learned_facts_prompt()}\n" if _get_learned_facts_prompt() else "")
        )

        user_msg = f"Ticket text from Slack:\n{ticket_text}\n\nOrder data from Snowflake:\n{order_data}"

        resp = _databricks_request('post',
            f'{host}/serving-endpoints/goose-claude-4-5-haiku/invocations',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg}
                ],
                'max_tokens': 800
            },
            timeout=30
        )

        if resp.ok:
            answer = resp.json()['choices'][0]['message']['content'].strip()
            msg = f"{answer}"
            if channel_config.get("oscar_cc"):
                msg += f"\n\ncc <@{OSCAR_ID}>"
            msg += f"\n\n_Automated triage by {BOT_SIGNATURE}._"
            print(f"  [PLAYBOOK] Generated enriched response ({len(answer)} chars)")
            return msg
        else:
            print(f"  [PLAYBOOK] LLM failed: {resp.status_code} {resp.text[:200]}")
            return None

    except Exception as e:
        print(f"  [PLAYBOOK] Error: {e}")
        return None


# ============================================================================
# GENERAL QUESTION HANDLER
# ============================================================================
def _load_schema_context() -> str:
    """Load SCHEMA_CONTEXT from shared/schema_context.json (single source of truth)."""
    shared_path = Path(__file__).parent.parent / 'shared' / 'schema_context.json'
    with open(shared_path) as f:
        return json.load(f)['schema_context']

SCHEMA_CONTEXT = _load_schema_context()


def _load_logistics_kb() -> str:
    """Load logistics knowledge base from shared/logistics_knowledge_base.md.
    
    Source: https://github.com/squareup/logistics-knowledge-base
    Contains process docs, shipping guides, DRI routing, SLAs, and escalation paths.
    """
    kb_path = Path(__file__).parent.parent / 'shared' / 'logistics_knowledge_base.md'
    if kb_path.exists():
        return kb_path.read_text()
    print("  [!] logistics_knowledge_base.md not found — process questions will fall back to SQL")
    return ""

LOGISTICS_KB = _load_logistics_kb()


def _load_eu_uk_au_faq() -> str:
    """Load EU/UK/AU fulfillment FAQ from shared/eu_uk_au_faq.md."""
    faq_path = Path(__file__).parent.parent / 'shared' / 'eu_uk_au_faq.md'
    if faq_path.exists():
        content = faq_path.read_text()
        print(f"  [EU FAQ] Loaded {len(content):,} chars from {faq_path.name}")
        return content
    print("  [EU FAQ] eu_uk_au_faq.md not found")
    return ""

EU_UK_AU_FAQ = _load_eu_uk_au_faq()

# Prefixes that map to regions
_EU_PREFIXES = {'FR', 'IE', 'ES'}
_UK_PREFIXES = {'GB'}
_AU_PREFIXES = {'AU', 'NZ', 'SG'}


def _get_region_from_order(order_number: str) -> str:
    """Return region string for an order number: 'UK', 'EU', 'AU', or 'US'."""
    prefix = order_number[:2].upper()
    if prefix in _UK_PREFIXES:
        return 'UK'
    if prefix in _EU_PREFIXES:
        return 'EU'
    if prefix in _AU_PREFIXES:
        return 'AU'
    return 'US'


def parse_eu_ticket(text: str) -> Dict[str, str]:
    """Parse a structured EU/UK/AU Request Manager ticket into key fields.

    Handles the structured format posted by the Request Manager bot:
        Order Number
        ES-028968397
        Country
        ES
        Issue with the order
        Order Not Delivered
        ...
    """
    result: Dict[str, str] = {
        'order_number': '',
        'country': '',
        'issue_type': '',
        'details': '',
        'merchant_token': '',
        'team': '',
    }

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Walk lines looking for label → value pairs
    label_map = {
        'order number': 'order_number',
        'country': 'country',
        'issue with the order': 'issue_type',
        'issue with the order (order must be over 200 gbp/eur)': 'issue_type',
        'please provide more details': 'details',
        'please provide more details of your query': 'details',
        'merchant token': 'merchant_token',
        'what team do you belong to?': 'team',
        'what team do you belong to': 'team',
    }

    i = 0
    while i < len(lines):
        key = lines[i].lower().rstrip('?').strip()
        if key in label_map and i + 1 < len(lines):
            field = label_map[key]
            result[field] = lines[i + 1]
            i += 2
        else:
            i += 1

    # Fallback: pull order number from text if not found via label
    if not result['order_number']:
        found = find_order_number(text)
        if found:
            result['order_number'] = found

    return result


def _get_databricks_token() -> Optional[str]:
    """Get a valid Databricks access token, refreshing if expired."""

    host = os.environ.get('DATABRICKS_HOST', 'https://block-lakehouse-production.cloud.databricks.com')
    token_files = glob.glob(os.path.expanduser('~/.config/goose/databricks/oauth/*.json'))
    if not token_files:
        print("  [!] No Databricks OAuth token found")
        return None

    token_path = token_files[0]
    with open(token_path) as f:
        token_data = json.load(f)

    # Check if token is expired
    expires_at = token_data.get('expires_at', '')
    is_expired = False
    if expires_at:
        try:
            from datetime import datetime as _dt, timezone as _tz
            exp_ts = _dt.fromisoformat(expires_at.replace('Z', '+00:00')).timestamp()
            # Refresh 5 minutes before expiry
            is_expired = time.time() > (exp_ts - 300)
        except Exception:
            pass

    if is_expired:
        print("  [TOKEN] Refreshing Databricks OAuth token...")
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
            print("  [!] No refresh token available")
            return None
        try:
            resp = _databricks_request('post',
                f'{host}/oidc/v1/token',
                data={
                    'grant_type': 'refresh_token',
                    'client_id': 'databricks-cli',
                    'refresh_token': refresh_token,
                },
                timeout=15
            )
            if resp.ok:
                new_data = resp.json()
                from datetime import datetime as _dt, timezone as _tz, timedelta as _td
                expires_in = new_data.get('expires_in', 3600)
                new_expires = (_dt.now(_tz.utc) + _td(seconds=expires_in)).isoformat()
                save_data = {
                    'access_token': new_data['access_token'],
                    'refresh_token': new_data.get('refresh_token', refresh_token),
                    'expires_at': new_expires,
                }
                with open(token_path, 'w') as f:
                    json.dump(save_data, f)
                print(f"  [TOKEN] Refreshed — expires {new_expires}")
                return new_data['access_token']
            else:
                print(f"  [!] Token refresh failed: {resp.status_code} {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"  [!] Token refresh error: {e}")
            return None

    return token_data['access_token']


def _check_canned_query(question: str) -> Optional[str]:
    """Check if question matches a canned inbound shipment report query.
    
    Returns proven SQL for common report requests instead of LLM-generated SQL.
    Source: shared/inbound_shipment_queries.md
    """
    q = question.lower()

    # All Block inbound shipments
    if any(p in q for p in ['all block shipments', 'all inbound shipments', 'inbound shipment report',
                             'block shipment report', 'all shipments report']):
        return """SELECT ff.SHIPMENT_ID, ff.HOUSE_BOL, ff.MASTER_BOL, ff.INCO_TERM,
            asn_sku.PO_NUMBERS, asn_sku.SKU, asn_sku.TOTAL_SKU_QUANTITY, asn_sku.SHIP_TO_FACILITY,
            ff.FORWARDER, ff.TRANSPORTATION_METHOD AS "Mode", ff.SHIPPER_NAME,
            ff.ORIGIN_COUNTRY, ff.DESTINATION_COUNTRY,
            COALESCE(asn_sku.SHIP_TO_FACILITY, ff.CONSIGNEE_NAME) AS "Destination",
            DATE(ff.BOOKING_DATE) AS "BOOKING_DATE",
            DATE(ff.ESTIMATED_DELIVERY_DATE) AS "ESTIMATED_DELIVERY_DATE",
            DATE(ff.ACTUAL_DELIVERY_DATE) AS "ACTUAL_DELIVERY_DATE",
            ff.PIECES, ff.GROSS_WEIGHT, ff.GROSS_WEIGHT_UOM
        FROM ORACLE_ERP.SCM.SQ_FF_SHIPMENT_INFO ff
        LEFT JOIN (
            SELECT TRACKING_NUMBER, PART_NUMBER AS SKU,
                LISTAGG(DISTINCT PO_NUMBER, ', ') WITHIN GROUP (ORDER BY PO_NUMBER) AS PO_NUMBERS,
                SUM(QUANTITY) AS TOTAL_SKU_QUANTITY, MAX(SHIP_TO_FACILITY) AS SHIP_TO_FACILITY
            FROM ORACLE_ERP.SCM.SQ_CM_ASN_INBOUND WHERE PART_NUMBER IS NOT NULL
            GROUP BY TRACKING_NUMBER, PART_NUMBER
        ) asn_sku ON ff.HOUSE_BOL = asn_sku.TRACKING_NUMBER
        WHERE (ff.BOOKING_DATE >= DATEADD(month, -3, CURRENT_DATE())
            OR (ff.BOOKING_DATE IS NULL AND ff.CREATED_AT >= DATEADD(month, -3, CURRENT_DATE())))
        ORDER BY ff.ESTIMATED_DELIVERY_DATE DESC NULLS LAST, ff.SHIPMENT_ID, asn_sku.SKU
        LIMIT 50"""

    # Wistron shipments
    if any(p in q for p in ['wistron shipment', 'wistron report', 'malaysia shipment',
                             'wistron inbound']):
        return """SELECT ff.SHIPMENT_ID, ff.HOUSE_BOL, ff.INCO_TERM,
            asn_sku.PO_NUMBERS, asn_sku.SKU, asn_sku.TOTAL_SKU_QUANTITY, asn_sku.SHIP_TO_FACILITY,
            ff.FORWARDER, ff.TRANSPORTATION_METHOD AS "Mode", ff.SHIPPER_NAME,
            ff.DESTINATION_COUNTRY,
            COALESCE(asn_sku.SHIP_TO_FACILITY, ff.CONSIGNEE_NAME) AS "Destination",
            DATE(ff.ESTIMATED_DELIVERY_DATE) AS "ESTIMATED_DELIVERY_DATE",
            DATE(ff.ACTUAL_DELIVERY_DATE) AS "ACTUAL_DELIVERY_DATE",
            ff.PIECES, ff.GROSS_WEIGHT
        FROM ORACLE_ERP.SCM.SQ_FF_SHIPMENT_INFO ff
        LEFT JOIN (
            SELECT TRACKING_NUMBER, PART_NUMBER AS SKU,
                LISTAGG(DISTINCT PO_NUMBER, ', ') WITHIN GROUP (ORDER BY PO_NUMBER) AS PO_NUMBERS,
                SUM(QUANTITY) AS TOTAL_SKU_QUANTITY, MAX(SHIP_TO_FACILITY) AS SHIP_TO_FACILITY
            FROM ORACLE_ERP.SCM.SQ_CM_ASN_INBOUND WHERE PART_NUMBER IS NOT NULL
            GROUP BY TRACKING_NUMBER, PART_NUMBER
        ) asn_sku ON ff.HOUSE_BOL = asn_sku.TRACKING_NUMBER
        WHERE (ff.ACTUAL_DELIVERY_DATE IS NULL OR ff.ACTUAL_DELIVERY_DATE >= DATEADD(day, -14, CURRENT_DATE()))
        AND ff.ORIGIN_COUNTRY = 'MY'
        AND (ff.CONSIGNEE_NAME IS NULL OR ff.CONSIGNEE_NAME NOT ILIKE '%Proto%')
        ORDER BY ff.ESTIMATED_DELIVERY_DATE DESC NULLS FIRST, ff.SHIPMENT_ID, asn_sku.SKU
        LIMIT 50"""

    # Proto shipments
    if any(p in q for p in ['proto shipment', 'proto report', 'prototype shipment',
                             'proto inbound']):
        return """SELECT ff.SHIPMENT_ID, ff.HOUSE_BOL, ff.INCO_TERM,
            asn_sku.PO_NUMBERS, asn_sku.SKU, asn_sku.TOTAL_SKU_QUANTITY, asn_sku.SHIP_TO_FACILITY,
            ff.FORWARDER, ff.TRANSPORTATION_METHOD AS "Mode", ff.SHIPPER_NAME,
            ff.ORIGIN_COUNTRY, ff.DESTINATION_COUNTRY,
            COALESCE(asn_sku.SHIP_TO_FACILITY, ff.CONSIGNEE_NAME) AS "Destination",
            DATE(ff.ESTIMATED_DELIVERY_DATE) AS "ESTIMATED_DELIVERY_DATE",
            DATE(ff.ACTUAL_DELIVERY_DATE) AS "ACTUAL_DELIVERY_DATE",
            ff.PIECES, ff.GROSS_WEIGHT
        FROM ORACLE_ERP.SCM.SQ_FF_SHIPMENT_INFO ff
        LEFT JOIN (
            SELECT TRACKING_NUMBER, PART_NUMBER AS SKU,
                LISTAGG(DISTINCT PO_NUMBER, ', ') WITHIN GROUP (ORDER BY PO_NUMBER) AS PO_NUMBERS,
                SUM(QUANTITY) AS TOTAL_SKU_QUANTITY, MAX(SHIP_TO_FACILITY) AS SHIP_TO_FACILITY
            FROM ORACLE_ERP.SCM.SQ_CM_ASN_INBOUND WHERE PART_NUMBER IS NOT NULL
            GROUP BY TRACKING_NUMBER, PART_NUMBER
        ) asn_sku ON ff.HOUSE_BOL = asn_sku.TRACKING_NUMBER
        WHERE (ff.ACTUAL_DELIVERY_DATE IS NULL OR ff.ACTUAL_DELIVERY_DATE >= DATEADD(day, -14, CURRENT_DATE()))
        AND ff.CONSIGNEE_NAME ILIKE '%Proto%'
        ORDER BY ff.ESTIMATED_DELIVERY_DATE DESC NULLS FIRST, ff.SHIPMENT_ID, asn_sku.SKU
        LIMIT 50"""

    return None


def generate_sql_llm(question: str) -> Optional[str]:
    """Use Databricks-hosted LLM to generate SQL for a question."""
    try:

        host = os.environ.get('DATABRICKS_HOST', 'https://block-lakehouse-production.cloud.databricks.com')
        token = _get_databricks_token()
        if not token:
            return None

        resp = _databricks_request('post',
            f'{host}/serving-endpoints/goose-claude-4-5-haiku/invocations',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={
                'messages': [
                    {'role': 'system', 'content': 'You are a SQL expert. Return ONLY a Snowflake SQL query. No explanation, no markdown fences, no comments, no semicolons.'},
                    {'role': 'user', 'content': (
                        f'{SCHEMA_CONTEXT}'
                        + (f'\n\n{_get_learned_facts_prompt()}' if _get_learned_facts_prompt() else '')
                        + f'\n\nQuestion: {question}'
                    )}
                ],
                'max_tokens': 500
            },
            timeout=30
        )

        if resp.ok:
            sql = resp.json()['choices'][0]['message']['content'].strip()
            if sql.startswith('```sql'): sql = sql[6:]
            elif sql.startswith('```'): sql = sql[3:]
            if sql.endswith('```'): sql = sql[:-3]
            sql = sql.strip().rstrip(';')
            if sql.upper().startswith('SELECT'):
                # Log on single line for readability
                print(f"  [LLM] SQL: {' '.join(sql.split())}")
                return sql
            else:
                print(f"  [!] LLM non-SELECT: {sql[:80]}")
        else:
            print(f"  [!] Databricks API {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  [!] LLM failed: {e}")
    return None


def _parse_date_filter(q: str, date_col: str, is_string_date: bool = False) -> str:
    """Parse time references from a question into SQL date filters."""
    if is_string_date:
        # For string date columns like ADJUSTMENT_DATE stored as 'YYYY-MM-DD'
        if 'yesterday' in q:
            return f"{date_col} = TO_CHAR(CURRENT_DATE() - 1, 'YYYY-MM-DD')"
        elif 'today' in q:
            return f"{date_col} = TO_CHAR(CURRENT_DATE(), 'YYYY-MM-DD')"
        elif 'this week' in q:
            return f"{date_col} >= TO_CHAR(DATE_TRUNC('week', CURRENT_DATE()), 'YYYY-MM-DD')"
        elif 'last week' in q:
            return f"{date_col} >= TO_CHAR(DATE_TRUNC('week', CURRENT_DATE()) - 7, 'YYYY-MM-DD') AND {date_col} < TO_CHAR(DATE_TRUNC('week', CURRENT_DATE()), 'YYYY-MM-DD')"
        else:
            return f"{date_col} >= TO_CHAR(CURRENT_DATE() - 7, 'YYYY-MM-DD')"
    else:
        if 'yesterday' in q:
            return f"{date_col}::DATE = CURRENT_DATE() - 1"
        elif 'today' in q:
            return f"{date_col}::DATE = CURRENT_DATE()"
        elif 'this week' in q:
            return f"{date_col}::DATE >= DATE_TRUNC('week', CURRENT_DATE())"
        elif 'last week' in q:
            return f"{date_col}::DATE >= DATE_TRUNC('week', CURRENT_DATE()) - 7 AND {date_col}::DATE < DATE_TRUNC('week', CURRENT_DATE())"
        elif 'last 7 days' in q or 'past week' in q:
            return f"{date_col}::DATE >= CURRENT_DATE() - 7"
        elif 'last 30 days' in q or 'past month' in q:
            return f"{date_col}::DATE >= CURRENT_DATE() - 30"
        else:
            return f"{date_col}::DATE >= CURRENT_DATE() - 7"


def _parse_facility(question: str) -> Optional[str]:
    """Extract a facility code from a question."""
    match = re.search(r'\b(CVU|IMC|IMU|GBR|NLD|ARV|SGU)\b', question, re.IGNORECASE)
    return match.group().upper() if match else None


def _parse_sku(question: str) -> Optional[str]:
    """Extract a SKU from a question."""
    match = re.search(r'\b(A-SKU-\d{3,})\b', question, re.IGNORECASE)
    if match:
        return match.group().upper()
    # Also match raw item numbers like 37952060
    match = re.search(r'\b(\d{8})\b', question)
    if match:
        return match.group()
    return None


def _format_answer_llm(question: str, cols: List[str], rows: List[tuple]) -> Optional[str]:
    """Use LLM to format query results into a natural Slack response."""
    try:

        host = os.environ.get('DATABRICKS_HOST', 'https://block-lakehouse-production.cloud.databricks.com')
        token = _get_databricks_token()
        if not token:
            return None

        # Build a concise data summary for the LLM
        def fmt(v):
            if v is None: return 'null'
            if isinstance(v, (int, float)): return f"{v:,}" if isinstance(v, int) else f"{v:,.2f}"
            return str(v)

        data_lines = []
        for row in rows[:20]:  # Cap at 20 rows for context
            data_lines.append(", ".join(f"{c}={fmt(v)}" for c, v in zip(cols, row)))
        data_str = "\n".join(data_lines)
        total_rows = len(rows)

        resp = _databricks_request('post',
            f'{host}/serving-endpoints/goose-claude-4-5-haiku/invocations',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={
                'messages': [
                    {'role': 'system', 'content': (
                        'Format Snowflake query results as a concise Slack message. Rules:\n'
                        '- Use Slack formatting: *bold*, bullet points with •\n'
                        '- Format numbers with commas, currency with $ prefix\n'
                        '- Format dates as "Apr 6, 2025"\n'
                        '- Keep it under 15 lines total\n'
                        '- Do NOT include any header or bot name — just the answer content\n'
                        '- Do NOT sum or total prices/costs unless explicitly asked for a total\n\n'
                        'FORMAT BY QUESTION TYPE:\n'
                        '- PRICING questions (price, cost, sell price, sales price): List each product with its price. '
                        'Format as a clean price list sorted high to low. Do NOT sum prices into a total.\n'
                        '- COUNT/VOLUME questions (how many, units, shipped, delivered): Start with the key number in bold, '
                        'then add breakdowns.\n'
                        '- STATUS questions (order, tracking): Show status details with dates and tracking.\n'
                        '- LIST questions (show me, what products): Clean bullet list of items.\n'
                    )},
                    {'role': 'user', 'content': f'Question: {question}\n\nColumns: {", ".join(cols)}\nRows ({total_rows} total):\n{data_str}'}
                ],
                'max_tokens': 500
            },
            timeout=15
        )

        if resp.ok:
            answer = resp.json()['choices'][0]['message']['content'].strip()
            return answer
    except Exception as e:
        print(f"  [!] Answer formatting failed: {e}")
    return None


def _is_process_question(question: str) -> bool:
    """Detect if a question is about logistics processes/policy rather than data.
    
    Process questions ask "how do I", "what's the process", "who handles", etc.
    Data questions ask about numbers, counts, orders, inventory levels, etc.
    """
    q = question.lower()

    # Check data signals FIRST — they're more specific and should take priority
    data_signals = [
        'how many', 'how much', 'count', 'total',
        'shipped', 'delivered', 'inventory', 'on hand', 'onhand',
        'units', 'quantity', 'volume',
        'last week', 'this week', 'yesterday', 'today',
        'us-', 'order number', 'tracking',
        'a-sku-', 'sku', 'facility', 'warehouse',
    ]
    if any(signal in q for signal in data_signals):
        return False

    # Process phrase signals (multi-word, safe for substring matching)
    process_phrases = [
        'how do i', 'how to', 'what is the process', "what's the process",
        'who handles', 'who do i', 'who should i', 'who is responsible',
        'where do i', 'where should i', 'where can i',
        'can i ship', 'can we ship', 'can we import', 'can block import', 'import into',
        'what do i need', 'what documents', 'what paperwork',
        'dri for', 'point of contact', 'who owns',
        'hs code', 'tariff', 'customs', 'duty', 'duties',
        'commercial invoice', 'incoterm',
        'export control', 'hand carry', 'hand-carry', 'handcarry',
        'temporary import', 'ata carnet', 'carnet',
        'country of origin', 'marking requirement',
        'de minimis', 'low value',
        'new lane', 'new inbound lane',
        'ship to employee', 'shipping to employee',
        'engage logistics', 'logistics team',
        'classification request', 'classify',
        'importer of record', 'freight forwarder', 'broker',
        'transit time', 'shipping speed',
        'return process', 'how to return',
        'escalat', 'who to escalate',
        'warehouse receiving', 'hot receipt',
        'pallet', 'palletize',
    ]
    if any(signal in q for signal in process_phrases):
        return True

    # Short keywords that need word-boundary matching to avoid false positives
    # e.g., 'ear' in 'year', 'ior' in 'prior', 'sla' in 'slang', 'dap' in 'adapt'
    boundary_keywords = ['ear', 'itar', 'eccn', 'ddp', 'dap', 'ior', 'sla', 'rma']
    if any(re.search(rf'\b{kw}\b', q) for kw in boundary_keywords):
        return True

    return False


def answer_process_question(question: str, channel_config: Dict) -> Optional[str]:
    """Answer a logistics process/policy question using the knowledge base."""
    if not LOGISTICS_KB:
        return None
    
    try:

        host = os.environ.get('DATABRICKS_HOST', 'https://block-lakehouse-production.cloud.databricks.com')
        token = _get_databricks_token()
        if not token:
            return None

        # Truncate KB to ~40K chars to stay within context limits
        kb_context = LOGISTICS_KB[:40000]

        resp = _databricks_request('post',
            f'{host}/serving-endpoints/goose-claude-4-5-haiku/invocations',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={
                'messages': [
                    {'role': 'system', 'content': (
                        "You are LGX-OPS-BOT, a logistics assistant for Block's Hardware Operations team. "
                        "Answer the question using ONLY the knowledge base provided below. "
                        "Rules:\n"
                        "- Be concise — max 8 lines\n"
                        "- Use Slack formatting: *bold* for key terms, bullet points\n"
                        "- Link to go/ links and resources when relevant\n"
                        "- When routing to a person, give their @username from the DRI table\n"
                        "- If the KB doesn't cover the question, say so and suggest who to ask\n"
                        "- Never guess HS codes, tariff rates, or export control classifications\n"
                        "- Do NOT start with bot name — the Slack app name shows automatically\n\n"
                        f"KNOWLEDGE BASE:\n{kb_context}"
                        + (f"\n\n{_get_learned_facts_prompt()}" if _get_learned_facts_prompt() else "")
                    )},
                    {'role': 'user', 'content': question}
                ],
                'max_tokens': 600
            },
            timeout=30
        )

        if resp.ok:
            answer = resp.json()['choices'][0]['message']['content'].strip()
            print(f"  [KB] Process answer ({len(answer)} chars)")
            return answer
        else:
            print(f"  [KB] LLM failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"  [KB] Error: {e}")
    return None


def answer_general_question(question: str, channel_config: Dict) -> Optional[str]:
    """Answer a general data question using LLM-generated SQL + LLM-formatted response."""
    # Check canned queries first (proven SQL for common report requests)
    sql = _check_canned_query(question)
    if sql:
        print(f"  [CANNED] Matched canned query for: {question[:60]}")
    else:
        sql = generate_sql_llm(question)
    if not sql:
        return None

    try:
        print(f"  [EXEC] {' '.join(sql.split())}")
        cols, rows = query_sf(sql)
        print(f"  [RESULT] {len(rows)} rows, cols={cols}")
        if not rows:
            return f"No data found for that query."

        # Use LLM to format a rich answer
        formatted = _format_answer_llm(question, cols, rows)
        if formatted:
            return f"{formatted}"

        # Fallback: simple formatting
        def fmt_val(v):
            if v is None: return 'n/a'
            if isinstance(v, (int, float)): return f"{int(v):,}"
            return str(v)

        if len(cols) == 1 and len(rows) == 1:
            return f"{fmt_val(rows[0][0])}"
        elif len(rows) == 1:
            parts = [f"*{col}:* {fmt_val(v)}" for col, v in zip(cols, rows[0])]
            return "• " + "\n• ".join(parts)
        else:
            lines = [" | ".join(fmt_val(v) for v in row) for row in rows[:10]]
            return f"*{' | '.join(cols)}*\n" + "\n".join(lines)

    except Exception as e:
        error_msg = str(e)
        print(f"  [!] Query failed: {error_msg}")

        # Auto-fix common SQL errors and retry once
        if 'not a valid order by expression' in error_msg.lower() or 'order by' in error_msg.lower():
            # Remove ORDER BY clause and retry
            import re as _re
            fixed_sql = _re.sub(r'\s+ORDER\s+BY\s+[^)]+?(?=\s+LIMIT|\s*$)', '', sql, flags=_re.IGNORECASE)
            if fixed_sql != sql:
                print(f"  [RETRY] Removed ORDER BY, retrying...")
                try:
                    cols, rows = query_sf(fixed_sql)
                    print(f"  [RESULT] {len(rows)} rows (after fix)")
                    if rows:
                        formatted = _format_answer_llm(question, cols, rows)
                        return formatted if formatted else f"Found {len(rows)} results."
                except Exception as e2:
                    print(f"  [!] Retry also failed: {e2}")

        return None


# ============================================================================
# MESSAGE PARSER
# ============================================================================
def normalize_api_messages(api_messages: List[Dict]) -> List[Dict]:
    """Normalize Slack API message dicts into the format process_channel expects.

    Each returned dict has: ts, text, user, subtype, reply_count
    """
    results = []
    for msg in api_messages:
        results.append({
            "ts": msg.get("ts", "0"),
            "text": msg.get("text", ""),
            "user": msg.get("user", ""),
            "subtype": msg.get("subtype"),
            "reply_count": msg.get("reply_count", 0),
        })
    return results


def find_order_number(text: str) -> Optional[str]:
    """Extract an order number from text. Supports all regions: US, CA, GB, IE, FR, ES, AU, NZ, SG, etc."""
    # Broad pattern: 2-letter country prefix + dash + 6-9 digits (with optional -WR suffix)
    match = re.search(r'\b[A-Z]{2}-\d{6,9}(?:-WR)?\b', text, re.IGNORECASE)
    return match.group().upper() if match else None


def is_question(text: str) -> bool:
    """Check if a message is a question we should answer.

    Also detects #hardwaredeliveryhelp ticket patterns from Request Manager bot
    (structured posts with order numbers, issue types like Missing Items, Late Delivery, etc.)
    """
    t = text.lower().strip()
    if not t:
        return False
    # Has a question mark
    if '?' in t:
        return True
    # Starts with question words
    if any(t.startswith(w) for w in ['how ', 'what ', 'when ', 'where ', 'why ', 'show ', 'list ', 'find ',
                                       'look up', 'check ', 'tell ', 'give ', 'get ', 'pull ', 'can you ',
                                       'is there', 'are there', 'do we ', 'did we ', 'has ', 'have ',
                                       'which ', 'who ', 'compare ', 'breakdown', 'details ', 'status ',
                                       'track ', 'price ', 'cost ']):
        return True
    # Contains an order number (US-, CA-, GB- patterns)
    if re.search(r'(?:US|CA|GB)-\d{6,}', text, re.IGNORECASE):
        return True
    if re.search(r'\b\d{8,}\b', text):  # 8+ digit numbers (Oracle order numbers, tracking)
        return True
    if re.search(r'\b[A-Z0-9]{8,}\b', text) and any(w in t for w in ['order', 'track', 'status', 'detail', 'ship', 'deliver']):
        return True
    # Detect #hardwaredeliveryhelp ticket patterns (Request Manager bot posts)
    ticket_keywords = ['missing item', 'late delivery', 'order not shipped', 'address change',
                       'return label', 'return request', 'replacement', 'damaged', 'wrong item',
                       'not received', 'lost package', 'refund', 'delivery issue',
                       'order status', 'tracking', 'where is my']
    if any(kw in t for kw in ticket_keywords):
        return True
    return False


# ============================================================================
# MAIN LOOP
# ============================================================================
def _check_casual_message(text: str) -> Optional[str]:
    """Detect casual/greeting messages and respond with logistics humor."""
    import random
    t = text.lower().strip()
    # Strip @mentions
    t = re.sub(r'<@[A-Z0-9]+>', '', t).strip()

    greetings = ['hi', 'hey', 'hello', 'yo', 'sup', 'howdy', 'heya', 'hiya', 'whats up', "what's up"]
    how_are_you = ['how are you', 'hows it going', "how's it going", 'how you doing', "how's your day",
                   'how are things', 'what are you up to', 'you good', 'how goes it']
    thanks = ['thanks', 'thank you', 'thx', 'appreciate it', 'nice work', 'good job', 'great job', 'well done']
    # 'ty' checked separately with word boundary to avoid matching 'prototype', 'warranty', etc.
    ty_match = bool(re.search(r'\bty\b', t))
    who_are_you = ['who are you', 'what are you', 'what do you do', 'what can you do', 'help']

    if any(t == g or t == g + '!' or t == g + '?' for g in greetings):
        responses = [
            "Hey! 👋 All systems operational — shipments are moving and inventory is stocked. What can I look up for you?",
            "What's up! 📦 I'm here and ready to ship answers. Got an order number or a data question?",
            "Hey there! 🚛 Just finished scanning the warehouse. What do you need?",
            "Hello! I'm running on schedule today — unlike some of our carriers 😏 What can I help with?",
        ]
        return f"{random.choice(responses)}"

    if any(phrase in t for phrase in how_are_you):
        responses = [
            "Running at full capacity! 🏭 All 8 Snowflake pipelines refreshed this morning, inventory is counted, and deliveries are tracked. What's on your mind?",
            "Better than a package with 'Delivered' status! ✅ Everything's flowing — orders, shipments, inventory. What do you need?",
            "I'm doing great — no delays, no exceptions, no backorders on my end 📊 Unlike some of these POs... What can I look up?",
            "Operating within SLA! ⏱️ All data is fresh and I'm ready to query. Fire away!",
            "Smooth sailing — no lost packages today 🚢 What can I track down for you?",
        ]
        return f"{random.choice(responses)}"

    if ty_match or any(phrase in t for phrase in thanks):
        responses = [
            "Happy to help! That's what I'm here for — delivering answers on time, every time 📬",
            "You got it! 🤖 Always here if you need another lookup.",
            "No problem! Consider that query fulfilled and shipped ✅",
            "Anytime! My turnaround time is better than ground shipping 😄",
        ]
        return f"{random.choice(responses)}"

    if any(phrase in t for phrase in who_are_you):
        return (
            "I'm LGX-OPS-BOT — the Hardware Ops data assistant! 🤖📦\n\n"
            "Here's what I can do:\n"
            "• 📋 *Order lookups* — give me a US/CA/GB order number\n"
            "• 🚚 *Shipment data* — volumes, carriers, facilities\n"
            "• 📊 *Inventory levels* — on-hand, aging, by warehouse\n"
            "• 🏷️ *Retail pricing* — Amazon, Best Buy, Walmart orders\n"
            "• 📈 *Delivery performance* — transit times, delays, SLAs\n"
            "• 🔍 *General questions* — ask in plain English, I'll query Snowflake\n\n"
            "Just ask a question or drop an order number and I'll get to work!"
        )

    return None


def process_channel(channel_id: str, name: str, config: Dict):
    """Check a channel for new questions and answer them."""
    api_msgs = read_channel_api(channel_id, 15)
    if not api_msgs:
        return

    messages = normalize_api_messages(api_msgs)
    answered = 0
    is_dm = config.get('is_dm', False)
    dm_user = config.get('dm_user', '')

    # Only process messages from the last 2 hours
    cutoff_ts = time.time() - 7200

    for msg in messages:
        if answered >= 3:
            break
        if float(msg["ts"]) < cutoff_ts:
            continue
        if msg["subtype"] in ("channel_join", "bot_message"):
            continue
        if msg["ts"] in processed_threads:
            continue

        # We have a new message to process!
        text = msg["text"].strip()
        # Strip Slack formatting: _italic_, *bold*, > quotes
        text = re.sub(r'^>\s*', '', text)  # leading quote
        text = re.sub(r'^_|_$', '', text.strip())  # surrounding italics
        text = re.sub(r'^\*|\*$', '', text.strip())  # surrounding bold
        text = text.strip()

        # --- DM: handle learning commands first ---
        if is_dm:
            if dm_user == ADMIN_USER_ID:
                cmd_response = _handle_learning_command(dm_user, text)
                if cmd_response is not None:
                    print(f"  [{name}] Learning command: {text[:60]}...")
                    post_message(channel_id, cmd_response)
                    processed_threads.add(msg["ts"])
                    answered += 1
                    continue
                # Also check for pending 'yes' confirmation
                if dm_user in _pending_clear_confirmations and text.lower().strip() == 'yes':
                    cmd_response = _handle_learning_command(dm_user, text)
                    if cmd_response is not None:
                        post_message(channel_id, cmd_response)
                        processed_threads.add(msg["ts"])
                        answered += 1
                        continue
            elif _is_learning_command(text):
                print(f"  [{name}] Non-admin learning command attempt")
                post_message(channel_id, "Learning commands are admin-only. Ask @dsteffy to add this.")
                processed_threads.add(msg["ts"])
                answered += 1
                continue

        if not is_question(text):
            continue

        # Check thread for existing LGX-OPS-BOT reply (channels only)
        if not is_dm and msg["reply_count"] > 0:
            if thread_has_bot_reply(channel_id, msg["ts"]):
                processed_threads.add(msg["ts"])
                continue

        print(f"  [{name}] New question: {text[:80]}...")

        order = find_order_number(text)
        response = None

        # Order lookup takes priority — tickets with order numbers always get triage
        if order:
            data = lookup_order(order)
            response = format_order_response(order, data, config, ticket_text=text)
        else:
            # Check for casual/greeting messages (only when no order number)
            casual = _check_casual_message(text)
            if casual:
                response = casual
            elif _is_process_question(text):
                # Process/policy question — answer from logistics KB
                print(f"  [{name}] Process question detected")
                response = answer_process_question(text, config)
                if not response:
                    # Fall back to SQL path in case it's a hybrid question
                    response = answer_general_question(text, config)
            else:
                # General data question
                response = answer_general_question(text, config)

        if response:
            print(f"  [{name}] Posting response ({('DM' if is_dm else 'thread')} {msg['ts']})")
            if is_dm:
                post_message(channel_id, response)
            else:
                post_thread(channel_id, msg["ts"], response)
            processed_threads.add(msg["ts"])
            answered += 1
        else:
            # Spicy fallback
            import random
            fallbacks = [
                "That one's outside my shipping zone 📦 I'm built for order lookups, shipment volumes, inventory levels, and delivery status. Hit me with a tracking question!",
                "I'd love to help, but that's not in my warehouse 🏭 Try me on orders, shipments, inventory, or delivery questions — that's where I really deliver.",
                "Hmm, that query didn't clear customs 🛃 I specialize in order tracking, inventory data, shipment volumes, and retail pricing. What can I look up?",
                "That's a bit outside my route 🚚 But ask me about order status, inventory levels, shipping volumes, or delivery performance and I'll get you sorted!",
                "I'm drawing a blank on that one — must be a backorder 😅 I can help with order lookups, inventory, shipments, and delivery tracking though!",
            ]
            fallback = f"{random.choice(fallbacks)}"
            print(f"  [{name}] Posting fallback ({('DM' if is_dm else 'thread')} {msg['ts']})")
            if is_dm:
                post_message(channel_id, fallback)
            else:
                post_thread(channel_id, msg["ts"], fallback)
            processed_threads.add(msg["ts"])


# Track which thread replies we've already processed (ts of the reply, not the parent)
processed_mentions: set = set()


def _get_thread_replies_api(channel_id: str, thread_ts: str, limit: int = 20) -> List[Dict]:
    """Get thread replies via Slack API directly (more structured than sq agent-tools)."""
    try:
        resp = requests.get(
            'https://slack.com/api/conversations.replies',
            headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}'},
            params={'channel': channel_id, 'ts': thread_ts, 'limit': str(limit)},
            timeout=15
        )
        data = resp.json()
        if data.get('ok'):
            return data.get('messages', [])
    except Exception as e:
        print(f"  [!] Thread API error: {e}")
    return []


def check_thread_mentions(channel_id: str, name: str, config: Dict):
    """Check threads in a channel for @LGX-OPS-BOT mentions that need a response.

    Scans recent channel messages that have threads, then checks if any
    thread reply mentions the bot and hasn't been answered yet.
    """

    # Get recent channel messages that have threads
    try:
        resp = requests.get(
            'https://slack.com/api/conversations.history',
            headers={'Authorization': f'Bearer {LGX_BOT_TOKEN}'},
            params={'channel': channel_id, 'limit': '15'},
            timeout=15
        )
        data = resp.json()
        if not data.get('ok'):
            return
    except Exception:
        return

    cutoff_ts = time.time() - 7200  # Last 2 hours
    answered = 0

    for msg in data.get('messages', []):
        if answered >= 2:  # Max 2 mention replies per cycle
            break
        reply_count = msg.get('reply_count', 0)
        if reply_count == 0:
            continue
        thread_ts = msg.get('ts', '')
        if float(thread_ts) < cutoff_ts:
            continue

        # Get thread replies
        replies = _get_thread_replies_api(channel_id, thread_ts)
        if not replies:
            continue

        # Check replies (skip first message which is the parent)
        for reply in replies[1:]:
            reply_ts = reply.get('ts', '')
            reply_user = reply.get('user', '')

            # Skip if already processed or if it's from the bot itself
            if reply_ts in processed_mentions:
                continue
            if reply_user == BOT_USER_ID:
                continue
            if float(reply_ts) < cutoff_ts:
                continue

            reply_text = reply.get('text', '')

            # Check if this reply mentions @LGX-OPS-BOT
            if f'<@{BOT_USER_ID}>' not in reply_text:
                continue

            # Check if the bot already replied AFTER this mention
            already_replied = False
            for later_reply in replies:
                if float(later_reply.get('ts', '0')) > float(reply_ts) and later_reply.get('user') == BOT_USER_ID:
                    already_replied = True
                    break
            if already_replied:
                processed_mentions.add(reply_ts)
                continue

            # We have an unanswered @mention! Process it.
            # Strip the @mention from the text
            clean_text = reply_text.replace(f'<@{BOT_USER_ID}>', '').strip()
            # Also gather thread context (parent message)
            parent_text = msg.get('text', '')
            full_context = f"{parent_text}\n\n{clean_text}" if parent_text else clean_text

            print(f"  [{name}] @mention in thread {thread_ts}: {clean_text[:80]}...")

            order = find_order_number(clean_text) or find_order_number(parent_text)
            response = None

            # Order lookup takes priority — tickets with order numbers always get triage
            if order:
                data_result = lookup_order(order)
                response = format_order_response(order, data_result, config, ticket_text=full_context)
            else:
                # Check casual only when no order number present
                casual = _check_casual_message(clean_text)
                if casual:
                    response = casual
                elif _is_process_question(clean_text):
                    print(f"  [{name}] Process question detected (@mention)")
                    response = answer_process_question(clean_text, config)
                    if not response:
                        response = answer_general_question(clean_text, config)
                else:
                    response = answer_general_question(clean_text, config)

            if not response:
                # Try with full thread context
                if _is_process_question(full_context):
                    response = answer_process_question(full_context, config)
                if not response:
                    response = answer_general_question(full_context, config)

            if response:
                print(f"  [{name}] Replying to @mention in thread {thread_ts}")
                post_thread(channel_id, thread_ts, response)
                processed_mentions.add(reply_ts)
                answered += 1
            else:
                import random
                fallbacks = [
                    "That one's outside my shipping zone 📦 I'm built for order lookups, shipment volumes, inventory levels, and delivery status.",
                    "I'd love to help, but that's not in my warehouse 🏭 Try me on orders, shipments, inventory, or delivery questions!",
                    "Hmm, that query didn't clear customs 🛃 I specialize in order tracking, inventory data, and retail pricing.",
                ]
                fallback = f"{random.choice(fallbacks)}"
                post_thread(channel_id, thread_ts, fallback)
                processed_mentions.add(reply_ts)


def main():
    print(f"\n{'='*50}")
    print(f"  LGX-OPS-BOT Slack Listener")
    print(f"  Mode: Auto-discover all channels bot is a member of")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  Channel refresh: every {CHANNEL_REFRESH_INTERVAL}s")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Load learned facts
    _load_learned_facts()

    # Initial channel discovery
    channels = discover_channels()
    if not channels:
        print("  [!] No channels found on startup. Will retry...")

    while True:
        try:
            # Re-discover channels periodically (picks up new channel invites)
            channels = discover_channels()
            for ch_id, config in channels.items():
                ch_name = config.get('name', ch_id)
                # Process new top-level messages
                process_channel(ch_id, ch_name, config)
                # Check threads for @mentions (channels only — DMs don't have thread mentions)
                if not config.get('is_dm'):
                    check_thread_mentions(ch_id, ch_name, config)
        except KeyboardInterrupt:
            print("\nStopping listener...")
            break
        except Exception as e:
            print(f"  [!] Error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
