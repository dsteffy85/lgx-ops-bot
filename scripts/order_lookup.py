#!/usr/bin/env python3
"""Look up an order in DELIVERY_ORDERS and SHIPMENTS tables."""
import json, sys, glob
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import snowflake.connector

order = sys.argv[1] if len(sys.argv) > 1 else None
if not order:
    print("Usage: python3 order_lookup.py <ORDER_NUMBER>")
    sys.exit(1)

key_files = glob.glob(str(Path.home() / 'Desktop' / 'Automation' / 'lgx-ops-bot' / 'credentials' / 'LGX_OPS_BOT_private_keys_*.json'))
with open(key_files[0]) as f:
    data = json.load(f)
p_key = serialization.load_pem_private_key(data['square']['private_key'].encode(), password=None, backend=default_backend())
conn = snowflake.connector.connect(account='square', user='LGX_OPS_BOT@squareup.com', private_key=p_key, warehouse='ETL__MEDIUM', role='LGX_OPS_BOT__SNOWFLAKE__ADMIN')
cur = conn.cursor()

# Query DELIVERY_ORDERS
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

result = {"delivery": None, "shipment": None}
if row:
    result["delivery"] = dict(zip(cols, [str(v) if v is not None else None for v in row]))

# Query SHIPMENTS (856 data)
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
    print("ORDER_NOT_FOUND")
