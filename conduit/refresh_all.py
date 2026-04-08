#!/usr/bin/env python3
"""
Conduit Pipeline Runner — Refreshes all LGX_OPS_BOT tables from source systems.

Usage:
    python3 refresh_all.py              # Run all pipelines
    python3 refresh_all.py arena        # Run just Arena PLM
    python3 refresh_all.py po           # Run just PO Lines
    python3 refresh_all.py inventory    # Run just Inventory
    python3 refresh_all.py delivery     # Run just Delivery Performance

Requires:
    - LGX_OPS_BOT private key JSON at ~/Desktop/LGX_OPS_BOT_private_keys_*.json
    - snowflake-connector-python + cryptography packages
"""
import json
import sys
import time
import glob
from datetime import datetime
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


# ============================================================================
# CONNECTION
# ============================================================================
def get_connection(role='LGX_OPS_BOT__SNOWFLAKE__ADMIN'):
    """Connect to Snowflake using LGX_OPS_BOT key pair auth.
    
    Supports two modes:
    1. Local: Reads from ~/Desktop/LGX_OPS_BOT_private_keys_*.json
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
        # Local mode: read from JSON file on Desktop
        key_files = glob.glob(str(Path.home() / 'Desktop' / 'LGX_OPS_BOT_private_keys_*.json'))
        if not key_files:
            raise FileNotFoundError("No LGX_OPS_BOT private key file found on Desktop and no SNOWFLAKE_PRIVATE_KEY env var set")
        
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
PIPELINES = {}

def pipeline(name):
    """Decorator to register a pipeline"""
    def decorator(func):
        PIPELINES[name] = func
        return func
    return decorator


@pipeline('arena')
def sync_arena_plm(cursor):
    """Arena PLM + Logistics → LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS"""
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS AS
    SELECT
        plm.ID as ARENA_ID,
        plm.ITEM_NUMBER, plm.ITEM_NAME, plm.ARENA_ITEM_CATEGORY,
        plm.LIFECYCLE_PHASE, plm.REVISION, plm.PRODUCT_FAMILY,
        plm.PRODUCT_SUB_FAMILY, plm.PRODUCTS, plm.COMPATIBLE_WITH,
        plm.PRODUCT_NAME, plm.PACKAGING_TYPE, plm.SKU_VARIATION,
        plm.SELLABLE_COUNTRY, plm.UPC_GTIN, plm.COUNTRY_OF_ORIGIN,
        plm.BATTERY_SHELF_LIFE, plm.SALES_CHANNEL, plm.WAREHOUSE_CODE,
        plm.CREATION_DATE, plm.EFFECTIVITY_DATE, plm.CHANGE_ORDER_NUMBER,
        plm.UPDATED_AT,
        pkg.SERIALIZED_ITEM as PKG_SERIALIZED_ITEM,
        pkg.COO as PKG_COO, pkg.ARENA_COO, pkg.WAREHOUSE_CODES,
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
        CURRENT_TIMESTAMP() as _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.SQ_ARENA_PLM_RAW plm
    LEFT JOIN APP_HARDWARE.MART_LOGISTICS.SNAP_SQ_SKU_ARENA_ITEMS pkg
        ON plm.ITEM_NUMBER = pkg.SKU AND pkg.DBT_VALID_TO IS NULL
    WHERE plm.ITEM_NUMBER IS NOT NULL
    ORDER BY plm.ITEM_NUMBER
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS")
    return cursor.fetchone()[0]


@pipeline('po')
def sync_po_lines(cursor):
    """Oracle PO Details → LGX_OPS_BOT.COST.PO_LINES"""
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.COST.PO_LINES AS
    SELECT
        PO_NUMBER, PO_LINE_NUMBER, PO_HEADER_ID, ITEM_ID, ITEM_NUMBER,
        SUPPLIER_NAME, SUPPLIER_SITE, WAREHOUSE, PO_HEADER_STATUS,
        DESCRIPTION, PO_LINE_QTY, PO_LINE_STATUS, LOCATION_NAME,
        PROCUREMENT_BU, DESTINATION_TYPE_CODE, REQUESTED_DELIVERY_DATE,
        PO_APPRVL_DT, CREATED_AT, UPDATED_AT,
        CURRENT_TIMESTAMP() as _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.CLOUD_PO_DETAILS
    ORDER BY CREATED_AT DESC
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.COST.PO_LINES")
    return cursor.fetchone()[0]


@pipeline('inventory')
def sync_inventory(cursor):
    """Inventory EOD (current) → LGX_OPS_BOT.WIGEON.INVENTORY_EOD
    
    Uses SQ_EOD_ONHAND_INBOUND (8.5M rows, updated daily) joined with
    Arena PLM for product family enrichment. Replaces old SQ_CM_EOD_ONHAND
    which was stale (last data April 2023).
    """
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.WIGEON.INVENTORY_EOD AS
    SELECT
        e.ID, e.SNAPSHOT_DATE, e.FACILITY, e.ITEM_CODE,
        e.SUB_INVENTORY, e.ONHAND_QUANTITY, e.COMMITED_QUANTITY,
        e.UOM, e.LOCATION, e.CLIENT_CODE, e.DAYS_INVENTORY,
        e.TENANT, e.CREATED_AT, e.UPDATED_AT,
        a.PRODUCT_FAMILY, a.ITEM_NAME as PRODUCT_NAME,
        a.LIFECYCLE_PHASE, a.PRODUCT_CATEGORY,
        CURRENT_TIMESTAMP() as _CONDUIT_SYNCED_AT
    FROM ORACLE_ERP.SCM.SQ_EOD_ONHAND_INBOUND e
    LEFT JOIN LGX_OPS_BOT.PRODUCTS.ARENA_ITEMS a 
        ON e.ITEM_CODE = a.ITEM_NUMBER
    WHERE e.SNAPSHOT_DATE >= DATEADD('day', -90, CURRENT_DATE())
    ORDER BY e.SNAPSHOT_DATE DESC, e.FACILITY, e.ITEM_CODE
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.WIGEON.INVENTORY_EOD")
    return cursor.fetchone()[0]


@pipeline('na_inbound')
def sync_na_inbound_gr(cursor):
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
def sync_delivery_performance(cursor):
    """Delivery Performance → LGX_OPS_BOT.WIGEON.DELIVERY_PERFORMANCE"""
    cursor.execute("""
    CREATE OR REPLACE TABLE LGX_OPS_BOT.WIGEON.DELIVERY_PERFORMANCE AS
    SELECT *, CURRENT_TIMESTAMP() as _CONDUIT_SYNCED_AT
    FROM APP_HARDWARE.MART_LOGISTICS.RPT_SQ_DELIVERY_PERFORMANCE
    """)
    cursor.execute("SELECT COUNT(*) FROM LGX_OPS_BOT.WIGEON.DELIVERY_PERFORMANCE")
    return cursor.fetchone()[0]


# ============================================================================
# RUNNER
# ============================================================================
def run_pipelines(targets=None):
    """Run specified pipelines (or all if none specified)"""
    if targets is None:
        targets = list(PIPELINES.keys())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    results = {}
    total_start = time.time()
    
    print(f"\n{'='*60}")
    print(f"🚀 CONDUIT PIPELINE RUN — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"   Pipelines: {', '.join(targets)}")
    print(f"   User: LGX_OPS_BOT@squareup.com")
    print(f"   Warehouse: ETL__MEDIUM")
    print()
    
    for name in targets:
        if name not in PIPELINES:
            print(f"❌ Unknown pipeline: {name}")
            print(f"   Available: {', '.join(PIPELINES.keys())}")
            continue
        
        start = time.time()
        try:
            print(f"⏳ {name}...", end=" ", flush=True)
            row_count = PIPELINES[name](cursor)
            elapsed = time.time() - start
            print(f"✅ {row_count:,} rows in {elapsed:.1f}s")
            results[name] = {"status": "success", "rows": row_count, "duration": elapsed}
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ FAILED in {elapsed:.1f}s: {e}")
            results[name] = {"status": "error", "error": str(e), "duration": elapsed}
    
    conn.close()
    total_elapsed = time.time() - total_start
    
    # Summary
    total_rows = sum(r.get("rows", 0) for r in results.values())
    successes = sum(1 for r in results.values() if r["status"] == "success")
    failures = sum(1 for r in results.values() if r["status"] == "error")
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"   ✅ {successes} succeeded | ❌ {failures} failed")
    print(f"   📊 {total_rows:,} total rows | ⏱️ {total_elapsed:.1f}s total")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else None
    run_pipelines(targets)
