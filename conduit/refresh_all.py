#!/usr/bin/env python3
"""
Conduit Pipeline Runner — Refreshes all LGX_OPS_BOT tables from source systems.

Usage:
    python3 refresh_all.py              # Run all pipelines
    python3 refresh_all.py arena        # Run just Arena PLM
    python3 refresh_all.py po           # Run just PO Lines
    python3 refresh_all.py inventory    # Run just Inventory
    python3 refresh_all.py delivery     # Run just Delivery Performance
    python3 refresh_all.py na_inbound   # Run just NA Inbound GR

Requires:
    - LGX_OPS_BOT private key JSON at ~/Desktop/Automation/lgx-ops-bot/credentials/
    - snowflake-connector-python + cryptography packages
"""
import json
import sys
import time
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


# ============================================================================
# CONNECTION
# ============================================================================
def get_connection(role: str = 'LGX_OPS_BOT__SNOWFLAKE__ADMIN') -> snowflake.connector.SnowflakeConnection:
    """Connect to Snowflake using LGX_OPS_BOT key pair auth.

    Supports two modes:
    1. Local: Reads from ~/Desktop/Automation/lgx-ops-bot/credentials/LGX_OPS_BOT_private_keys_*.json
    2. CI/GitHub Actions: Reads from SNOWFLAKE_PRIVATE_KEY env var (base64 encoded)
    """
    import os
    import base64

    # Try environment variables first (GitHub Actions)
    env_key = os.environ.get('SNOWFLAKE_PRIVATE_KEY')
    if env_key:
        key_bytes = base64.b64decode(env_key)
        p_key = serialization.load_pem_private_key(
            key_bytes,
            password=None,
            backend=default_backend()
        )
        account = os.environ.get('SNOWFLAKE_ACCOUNT', 'square')
        user = os.environ.get('SNOWFLAKE_USER', 'LGX_OPS_BOT@squareup.com')
        warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE', 'ETL__MEDIUM')
    else:
        # Local mode: read from JSON file
        key_files = glob.glob(str(Path.home() / 'Desktop' / 'Automation' / 'lgx-ops-bot' / 'credentials' / 'LGX_OPS_BOT_private_keys_*.json'))
        if not key_files:
            key_files = glob.glob(str(Path.home() / 'Desktop' / 'LGX_OPS_BOT_private_keys_*.json'))
        if not key_files:
            raise FileNotFoundError("No LGX_OPS_BOT private key file found.")

        with open(key_files[0]) as f:
            data = json.load(f)

        p_key = serialization.load_pem_private_key(
            data['square']['private_key'].encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        account = data['square'].get('account', 'square')
        user = data['square'].get('robot_user', 'LGX_OPS_BOT') + '@squareup.com'
        warehouse = 'ETL__MEDIUM'

    return snowflake.connector.connect(
        account=account,
        user=user,
        private_key=p_key,
        warehouse=warehouse,
        role=role
    )


# ============================================================================
# PIPELINES
# ============================================================================
PIPELINES: Dict[str, Any] = {}


def pipeline(name: str):
    """Decorator to register a pipeline."""
    def decorator(func):
        PIPELINES[name] = func
        return func
    return decorator


@pipeline('arena')
def sync_arena_plm(cursor) -> int:
    """Arena PLM + Logistics → LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS

    DEDUPLICATES to latest revision per ITEM_NUMBER.
    Source SQ_ARENA_PLM_RAW has ~4.6x duplicates (revision history).
    We take the row with the most recent UPDATED_AT per ITEM_NUMBER.
    """
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS AS
    WITH deduped_plm AS (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY ITEM_NUMBER
                ORDER BY UPDATED_AT DESC NULLS LAST, ID DESC
            ) AS _rn
        FROM ORACLE_ERP.SCM.SQ_ARENA_PLM_RAW
        WHERE ITEM_NUMBER IS NOT NULL
    )
    SELECT
        plm.ID AS ARENA_ID,
        plm.ITEM_NUMBER, plm.ITEM_NAME, plm.ARENA_ITEM_CATEGORY,
        plm.LIFECYCLE_PHASE, plm.REVISION, plm.PRODUCT_FAMILY,
        plm.PRODUCT_SUB_FAMILY, plm.PRODUCTS, plm.COMPATIBLE_WITH,
        plm.PRODUCT_NAME, plm.PACKAGING_TYPE, plm.SKU_VARIATION,
        plm.SELLABLE_COUNTRY, plm.UPC_GTIN, plm.COUNTRY_OF_ORIGIN,
        plm.BATTERY_SHELF_LIFE, plm.SALES_CHANNEL, plm.WAREHOUSE_CODE,
        plm.CREATION_DATE, plm.EFFECTIVITY_DATE, plm.CHANGE_ORDER_NUMBER,
        plm.UPDATED_AT,
        pkg.SERIALIZED_ITEM AS PKG_SERIALIZED_ITEM,
        pkg.COO AS PKG_COO, pkg.ARENA_COO, pkg.WAREHOUSE_CODES,
        pkg.PRODUCT_CATEGORY,
        pkg.SHIPPER_BOX_LENGTH_MM, pkg.SHIPPER_BOX_WIDTH_MM,
        pkg.SHIPPER_BOX_HEIGHT_MM, pkg.SHIPPER_BOX_WEIGHT_KG,
        pkg.INNER_CARTON_SKU, pkg.INNER_CARTON_DESCRIPTION,
        pkg.INNER_CARTON_LENGTH_MM, pkg.INNER_CARTON_WIDTH_MM,
        pkg.INNER_CARTON_HEIGHT_MM, pkg.INNER_CARTON_WEIGHT_KG,
        pkg.UNITS_PER_INNER_CARTON,
        pkg.MASTER_CARTON_SKU, pkg.MASTER_CARTON_DESCRIPTION,
        pkg.MASTER_CARTON_LENGTH_MM, pkg.MASTER_CARTON_WIDTH_MM,
        pkg.MASTER_CARTON_HEIGHT_MM, pkg.MASTER_CARTON_WEIGHT_KG,
        pkg.UNITS_PER_MASTER_CARTON,
        pkg.AIR_PALLET_SKU, pkg.AIR_PALLET_DESCRIPTION,
        pkg.AIR_PALLET_LENGTH_MM, pkg.AIR_PALLET_WIDTH_MM,
        pkg.AIR_PALLET_HEIGHT_MM, pkg.AIR_PALLET_WEIGHT_KG,
        pkg.AIR_PALLET_STACKABLE_PALLET, pkg.UNITS_PER_AIR_PALLET,
        pkg.OCEAN_PALLET_SKU, pkg.OCEAN_PALLET_DESCRIPTION,
        pkg.OCEAN_PALLET_LENGTH_MM, pkg.OCEAN_PALLET_WIDTH_MM,
        pkg.OCEAN_PALLET_HEIGHT_MM, pkg.OCEAN_PALLET_WEIGHT_KG,
        pkg.OCEAN_PALLET_STACKABLE_PALLET, pkg.UNITS_PER_OCEAN_PALLET,
        CURRENT_TIMESTAMP() AS _CONDUIT_SYNCED_AT
    FROM deduped_plm plm
    LEFT JOIN APP_HARDWARE.MART_LOGISTICS.SNAP_SQ_SKU_ARENA_ITEMS pkg
        ON plm.ITEM_NUMBER = pkg.SKU AND pkg.DBT_VALID_TO IS NULL
    WHERE plm._rn = 1
    ORDER BY plm.ITEM_NUMBER
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS")
    return cursor.fetchone()[0]


@pipeline('po')
def sync_po_lines(cursor) -> int:
    """Oracle PO Details → LGX_OPS_BOT.COST.PO_LINES"""
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.COST.PO_LINES AS
    SELECT
        PO_NUMBER, PO_LINE_NUMBER, PO_HEADER_ID, ITEM_ID, ITEM_NUMBER,
        SUPPLIER_NAME, SUPPLIER_SITE, WAREHOUSE, PO_HEADER_STATUS,
        DESCRIPTION, PO_LINE_QTY, PO_LINE_STATUS, LOCATION_NAME,
        PROCUREMENT_BU, DESTINATION_TYPE_CODE, REQUESTED_DELIVERY_DATE,
        PO_APPRVL_DT, CREATED_AT, UPDATED_AT,
        CURRENT_TIMESTAMP() AS _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.CLOUD_PO_DETAILS
    ORDER BY CREATED_AT DESC
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.COST.PO_LINES")
    return cursor.fetchone()[0]


@pipeline('inventory')
def sync_inventory(cursor) -> int:
    """Inventory EOD → LGX_OPS_BOT.WIGEON.INVENTORY_EOD

    Uses SQ_EOD_ONHAND_INBOUND joined with DEDUPED Arena PLM.
    Arena must be refreshed first to avoid fan-out from duplicate ITEM_NUMBERs.
    """
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.WIGEON.INVENTORY_EOD AS
    SELECT
        e.ID, e.SNAPSHOT_DATE, e.FACILITY, e.ITEM_CODE,
        e.SUB_INVENTORY, e.ONHAND_QUANTITY, e.COMMITED_QUANTITY,
        e.UOM, e.LOCATION, e.CLIENT_CODE, e.DAYS_INVENTORY,
        e.TENANT, e.CREATED_AT, e.UPDATED_AT,
        a.PRODUCT_FAMILY, a.ITEM_NAME AS PRODUCT_NAME,
        a.LIFECYCLE_PHASE, a.PRODUCT_CATEGORY,
        CURRENT_TIMESTAMP() AS _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.SQ_EOD_ONHAND_INBOUND e
    LEFT JOIN LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS a
        ON e.ITEM_CODE = a.ITEM_NUMBER
    WHERE e.SNAPSHOT_DATE >= DATEADD('day', -90, CURRENT_DATE())
    ORDER BY e.SNAPSHOT_DATE DESC, e.FACILITY, e.ITEM_CODE
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.WIGEON.INVENTORY_EOD")
    return cursor.fetchone()[0]


@pipeline('na_inbound')
def sync_na_inbound_gr(cursor) -> int:
    """NA Inbound Goods Receipt → LGX_OPS_BOT.WIGEON.NA_INBOUND_GR"""
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.WIGEON.NA_INBOUND_GR AS
    SELECT
        TO_CHAR(TO_DATE(ADJUSTMENT_DATE), 'YYYY-MM-DD') AS ADJUSTMENT_DATE,
        FACILILTY_ID AS FACILITY_ID,
        ITEM_CODE, ITEM_DESCRIPTION, PRODUCT_NAME, CLIENT_CODE,
        ADJUSTMENT_ID,
        COALESCE(AVL_QUANTITY, 0) AS AVL_QUANTITY,
        COALESCE(UNAVL_QUANTITY, 0) AS UNAVL_QUANTITY,
        COALESCE(RETURN_QUANTITY, 0) AS RETURN_QUANTITY,
        COALESCE(STD_COST, 0) AS STD_COST,
        COALESCE(EXTENDED_COST, 0) AS EXTENDED_COST,
        FILE_NAME, PROCESS_FLAG,
        CURRENT_TIMESTAMP() AS _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.SQ_841_INBOUND_V
    WHERE TENANT IN ('SQ','SQ1')
      AND FACILILTY_ID IN ('CVU', 'IMC', 'IMU')
      AND REMARKS = 'STAT'
    ORDER BY ADJUSTMENT_DATE DESC, FACILILTY_ID, ITEM_CODE
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.WIGEON.NA_INBOUND_GR")
    return cursor.fetchone()[0]


@pipeline('delivery')
def sync_delivery_orders(cursor) -> int:
    """Delivery Performance → LGX_OPS_BOT.WIGEON.DELIVERY_ORDERS

    ORDER-LEVEL rollup: one row per ORDER_NUMBER with full lifecycle dates,
    SKU/item counts, tracking numbers, and computed status.
    Source is line-level (3.6M rows) → rolled up to ~2.7M orders.
    """
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.WIGEON.DELIVERY_ORDERS AS
    SELECT
        ORDER_NUMBER,
        MAX(ORACLE_ORDER_NUMBER) AS ORACLE_ORDER_NUMBER,
        MAX(CUSTOMER_NAME) AS CUSTOMER_NAME,
        MAX(COUNTRY) AS COUNTRY,
        MAX(STATE) AS STATE,
        MAX(CITY) AS CITY,
        LISTAGG(DISTINCT FACILITY, ', ') WITHIN GROUP (ORDER BY FACILITY) AS FACILITIES,
        LISTAGG(DISTINCT CARRIER_CODE, ', ') WITHIN GROUP (ORDER BY CARRIER_CODE) AS CARRIERS,
        MAX(SHIPPING_METHOD) AS SHIPPING_METHOD,
        MAX(ORDER_TYPE) AS ORDER_TYPE,
        MAX(IS_SPLIT_ORDER) AS IS_SPLIT_ORDER,
        -- Lifecycle dates
        MIN(ORDERED_DATE)::DATE AS ORDERED_DATE,
        MIN(SENT_TO_WAREHOUSE_DATE)::DATE AS SENT_TO_WH_DATE,
        MIN(SHIPPED_DATE)::DATE AS FIRST_SHIP_DATE,
        MAX(SHIPPED_DATE)::DATE AS LAST_SHIP_DATE,
        MIN(DELIVERY_DATE)::DATE AS FIRST_DELIVERY_DATE,
        MAX(DELIVERY_DATE)::DATE AS LAST_DELIVERY_DATE,
        MAX(ESTIMATED_DELIVERY_DATE) AS ESTIMATED_DELIVERY_DATE,
        -- Order size
        COUNT(DISTINCT ITEM_NAME) AS UNIQUE_SKUS,
        SUM(QUANTITY) AS TOTAL_ITEMS,
        COUNT(DISTINCT TRACKING_NUMBER) AS SHIPMENT_COUNT,
        LISTAGG(DISTINCT TRACKING_NUMBER, ', ') WITHIN GROUP (ORDER BY TRACKING_NUMBER) AS TRACKING_NUMBERS,
        -- Status
        MAX(DELIVERY_STATUS) AS DELIVERY_STATUS,
        CASE
            WHEN MAX(CANCELLED_FLAG) = 'Y' THEN 'CANCELLED'
            WHEN MIN(CASE WHEN IS_DELIVERED THEN 1 ELSE 0 END) = 1 THEN 'DELIVERED'
            WHEN MAX(CASE WHEN IS_DELIVERED THEN 1 ELSE 0 END) = 1 THEN 'PARTIALLY_DELIVERED'
            WHEN MAX(SHIPPED_DATE) IS NOT NULL THEN 'SHIPPED'
            WHEN MAX(SENT_TO_WAREHOUSE_DATE) IS NOT NULL THEN 'AT_WAREHOUSE'
            ELSE 'ORDERED'
        END AS ORDER_STATUS,
        -- Timing
        MAX(PROCESSING_DAYS) AS PROCESSING_DAYS,
        MAX(TRANSIT_DAYS) AS TRANSIT_DAYS,
        MAX(DAYS_TO_DELIVERY) AS DAYS_TO_DELIVERY,
        -- Metadata
        CURRENT_TIMESTAMP() AS _CONDUIT_SYNCED_AT
    FROM APP_HARDWARE.MART_LOGISTICS.RPT_SQ_DELIVERY_PERFORMANCE
    GROUP BY ORDER_NUMBER
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.WIGEON.DELIVERY_ORDERS")
    return cursor.fetchone()[0]


@pipeline('shipments')
def sync_shipments(cursor) -> int:
    """856 Outbound Shipments → LGX_OPS_BOT.WIGEON.SHIPMENTS

    ORDER-LEVEL rollup of 856 ASN data. Includes warranty replacements,
    serial numbers, tracking, and carrier info. Joins to DELIVERY_ORDERS
    via ORDER_TOKEN = ORDER_NUMBER.
    Last 2 years of data.
    """
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.WIGEON.SHIPMENTS AS
    SELECT
        ORDER_TOKEN,
        ORDER_NUMBER AS INTERNAL_ORDER_NUMBER,
        MAX(ORDER_TYPE_CODE) AS ORDER_TYPE,
        MAX(ORDER_TYPE_NAME) AS ORDER_TYPE_NAME,
        MAX(EFF_ORDER_TYPE) AS EFF_ORDER_TYPE,
        MAX(SALES_CHANNEL) AS SALES_CHANNEL,
        MAX(COUNTRY) AS COUNTRY,
        MAX(SHIP_TO_NAME) AS SHIP_TO_NAME,
        LISTAGG(DISTINCT FACILITY_ID, ', ') WITHIN GROUP (ORDER BY FACILITY_ID) AS FACILITIES,
        LISTAGG(DISTINCT CARRIER_CODE, ', ') WITHIN GROUP (ORDER BY CARRIER_CODE) AS CARRIERS,
        MAX(SHIP_METHOD) AS SHIP_METHOD,
        MIN(SHIPPING_DATE) AS FIRST_SHIP_DATE,
        MAX(SHIPPING_DATE) AS LAST_SHIP_DATE,
        COUNT(DISTINCT ITEM_CODE) AS UNIQUE_SKUS,
        SUM(QUANTITY) AS TOTAL_ITEMS,
        COUNT(DISTINCT TRACKING_NUMBER) AS SHIPMENT_COUNT,
        LISTAGG(DISTINCT TRACKING_NUMBER, ', ') WITHIN GROUP (ORDER BY TRACKING_NUMBER) AS TRACKING_NUMBERS,
        SUM(NUMBER_PACKAGES) AS TOTAL_PACKAGES,
        SUM(STD_COST) AS TOTAL_STD_COST,
        COUNT(DISTINCT SERIAL_NUMBER) AS SERIAL_COUNT,
        MAX(CLIENT_CODE) AS CLIENT_CODE,
        MAX(PRODUCT_NAME) AS PRODUCT_NAME,
        MAX(PROCESS_FLAG) AS PROCESS_FLAG,
        MAX(IS_EXPEDITED) AS IS_EXPEDITED,
        CURRENT_TIMESTAMP() AS _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.SQ_856_SC_INBOUND_V
    WHERE SHIPPING_DATE >= DATEADD('year', -2, CURRENT_DATE())
    GROUP BY ORDER_TOKEN, ORDER_NUMBER
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.WIGEON.SHIPMENTS")
    return cursor.fetchone()[0]


# ============================================================================
# RUNNER
# ============================================================================
def run_pipelines(targets: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run specified pipelines (or all if none specified)."""
    if targets is None:
        targets = list(PIPELINES.keys())

    conn = get_connection()
    cursor = conn.cursor()

    results: Dict[str, Any] = {}
    total_start = time.time()

    print(f"\n{'='*60}")
    print(f"  CONDUIT PIPELINE RUN — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"   Pipelines: {', '.join(targets)}")
    print(f"   User: LGX_OPS_BOT@squareup.com")
    print(f"   Warehouse: ETL__MEDIUM")
    print()

    for name in targets:
        if name not in PIPELINES:
            print(f"  Unknown pipeline: {name}")
            print(f"   Available: {', '.join(PIPELINES.keys())}")
            continue

        start = time.time()
        try:
            print(f"  {name}...", end=" ", flush=True)
            row_count = PIPELINES[name](cursor)
            elapsed = time.time() - start
            print(f"  {row_count:,} rows in {elapsed:.1f}s")
            results[name] = {"status": "success", "rows": row_count, "duration": elapsed}
        except Exception as e:
            elapsed = time.time() - start
            print(f"  FAILED in {elapsed:.1f}s: {e}")
            results[name] = {"status": "error", "error": str(e), "duration": elapsed}

    conn.close()
    total_elapsed = time.time() - total_start

    # Summary
    total_rows = sum(r.get("rows", 0) for r in results.values())
    successes = sum(1 for r in results.values() if r["status"] == "success")
    failures = sum(1 for r in results.values() if r["status"] == "error")

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"   {successes} succeeded | {failures} failed")
    print(f"   {total_rows:,} total rows | {total_elapsed:.1f}s total")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else None
    run_pipelines(targets)
