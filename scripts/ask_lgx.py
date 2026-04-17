#!/usr/bin/env python3
"""
Ask LGX-OPS-BOT — runs a natural language question against Snowflake.
Uses the same schema context as the G2 app's Ask LGX OPS BOT feature.

Usage:
    python3 ask_lgx.py "how many orders shipped from CVU yesterday?"
    python3 ask_lgx.py "US-373216476"  # direct order lookup
"""
import json, sys, glob, re
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import snowflake.connector

question = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else None
if not question:
    print("Usage: python3 ask_lgx.py <question>")
    sys.exit(1)

# Connect to Snowflake
key_files = glob.glob(str(Path.home() / 'Desktop' / 'Automation' / 'lgx-ops-bot' / 'credentials' / 'LGX_OPS_BOT_private_keys_*.json'))
with open(key_files[0]) as f:
    data = json.load(f)
p_key = serialization.load_pem_private_key(data['square']['private_key'].encode(), password=None, backend=default_backend())
conn = snowflake.connector.connect(account='square', user='LGX_OPS_BOT@squareup.com', private_key=p_key, warehouse='ETL__MEDIUM', role='LGX_OPS_BOT__SNOWFLAKE__ADMIN')
cur = conn.cursor()

# Check if this is a direct order lookup
order_match = re.search(r'US-\d{6,}', question)
if order_match:
    order = order_match.group()
    result = {"type": "order_lookup", "order": order, "delivery": None, "shipment": None}
    
    cur.execute(f"""
    SELECT ORDER_NUMBER, CUSTOMER_NAME, FACILITIES, CARRIERS,
        ORDERED_DATE, SENT_TO_WH_DATE, FIRST_SHIP_DATE, LAST_SHIP_DATE,
        FIRST_DELIVERY_DATE, LAST_DELIVERY_DATE,
        UNIQUE_SKUS, TOTAL_ITEMS, SHIPMENT_COUNT, TRACKING_NUMBERS,
        ORDER_STATUS, SHIPPING_METHOD, PROCESSING_DAYS, TRANSIT_DAYS,
        STATE, CITY
    FROM LGX_OPS_BOT.WIGEON.DELIVERY_ORDERS
    WHERE ORDER_NUMBER = '{order}'
    """)
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    if row:
        result["delivery"] = dict(zip(cols, [str(v) if v is not None else None for v in row]))

    cur.execute(f"""
    SELECT ORDER_TOKEN, ORDER_TYPE, ORDER_TYPE_NAME, SALES_CHANNEL, COUNTRY,
        SHIP_TO_NAME, FACILITIES, CARRIERS, SHIP_METHOD,
        FIRST_SHIP_DATE, LAST_SHIP_DATE,
        UNIQUE_SKUS, TOTAL_ITEMS, SHIPMENT_COUNT, TRACKING_NUMBERS,
        TOTAL_PACKAGES, TOTAL_STD_COST, SERIAL_COUNT, IS_EXPEDITED
    FROM LGX_OPS_BOT.WIGEON.SHIPMENTS
    WHERE ORDER_TOKEN = '{order}'
    """)
    cols2 = [d[0] for d in cur.description]
    row2 = cur.fetchone()
    if row2:
        result["shipment"] = dict(zip(cols2, [str(v) if v is not None else None for v in row2]))
    
    conn.close()
    if result["delivery"] or result["shipment"]:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"type": "order_lookup", "order": order, "error": "ORDER_NOT_FOUND"}))
else:
    # General question — output the question and schema for the LLM to generate SQL
    result = {
        "type": "general_question",
        "question": question,
        "schema": {
            "PRODUCTS.ARENA_ITEMS": "Product master (1,259 rows). Key cols: ITEM_NUMBER, ITEM_NAME, PRODUCT_FAMILY, LIFECYCLE_PHASE",
            "WIGEON.INVENTORY_EOD": "End-of-day inventory (~448K rows, last 90 days). Key cols: SNAPSHOT_DATE, FACILITY, ITEM_CODE, ONHAND_QUANTITY, PRODUCT_FAMILY",
            "WIGEON.NA_INBOUND_GR": "NA goods receipts (14K rows). Key cols: ADJUSTMENT_DATE, FACILITY_ID, ITEM_CODE, AVL_QUANTITY",
            "WIGEON.EUAPAC_INBOUND_GR": "EU/APAC inbound (518 rows). Key cols: ARRIVAL_DATE, FACILITY, SKU, RECEIVED_QUANTITY",
            "WIGEON.DELIVERY_ORDERS": "Order-level delivery (2.7M rows). Key cols: ORDER_NUMBER, ORDERED_DATE, SENT_TO_WH_DATE, FIRST_SHIP_DATE, LAST_DELIVERY_DATE, ORDER_STATUS, FACILITIES, TRACKING_NUMBERS, UNIQUE_SKUS, TOTAL_ITEMS, CITY, STATE",
            "WIGEON.SHIPMENTS": "856 outbound shipments (1.6M rows). Key cols: ORDER_TOKEN, ORDER_TYPE, FACILITIES, TRACKING_NUMBERS, SHIPPING_DATE, CARRIER_CODE",
            "WIGEON.BLOCK_INVENTORY_DETAIL": "Ingram Micro on-hand (640 rows). Key cols: SKU, LOCATION, AVL, TOTAL",
            "WIGEON.ALL_INBOUND": "Union of NA + EU/APAC inbound (view). Key cols: INBOUND_DATE, FACILITY, SKU, REGION",
            "WIGEON.INBOUND_DISCREPANCIES": "Shipped vs received (view). Key cols: DOC_DATE, ITEM_CODE, SHIPPED_QTY, RECEIVED_QTY, VARIANCE, DISCREPANCY_TYPE",
        },
        "instructions": "Generate a Snowflake SQL query to answer this question. Use fully qualified table names (LGX_OPS_BOT.SCHEMA.TABLE). No semicolons. LIMIT results to 50 rows max."
    }
    print(json.dumps(result, indent=2))

conn.close()
