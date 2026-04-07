#!/usr/bin/env python3
"""
LGX Ops Bot - NA Inbound GR Data Collector
Fetches data from Snowflake SQ_841_INBOUND_V and stores in local SQLite.

Usage:
    python3 collect_na_inbound_gr.py                  # Default: 30-day lookback
    python3 collect_na_inbound_gr.py --days 90        # Custom lookback
    python3 collect_na_inbound_gr.py --backfill        # Full history backfill
    python3 collect_na_inbound_gr.py --from-csv FILE   # Import from CSV (offline/manual)

This script is designed to be called by a Goose recipe that handles the
Snowflake query execution. The recipe passes results as a CSV file.
"""

import sqlite3
import csv
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'lgx_ops.db')
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# Ensure dirs exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def log(msg: str) -> None:
    """Log to both stdout and log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    log_file = os.path.join(LOG_DIR, 'na_inbound_gr.log')
    with open(log_file, 'a') as f:
        f.write(line + '\n')


def get_db() -> sqlite3.Connection:
    """Get database connection, create tables if needed."""
    # Auto-setup if DB doesn't exist
    if not os.path.exists(DB_PATH):
        log("Database not found, running setup...")
        sys.path.insert(0, SCRIPT_DIR)
        from db_setup import setup_database
        setup_database()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def start_run(conn: sqlite3.Connection) -> int:
    """Record the start of a collection run. Returns the new run_id."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO run_log (source_id, started_at, status)
        VALUES ('na_inbound_gr', datetime('now'), 'running')
    """)
    conn.commit()
    return cursor.lastrowid


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    rows_fetched: int = 0,
    rows_inserted: int = 0,
    rows_updated: int = 0,
    error_message: Optional[str] = None,
) -> None:
    """Record the completion of a collection run."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE run_log SET
            finished_at = datetime('now'),
            status = ?,
            rows_fetched = ?,
            rows_inserted = ?,
            rows_updated = ?,
            error_message = ?,
            duration_secs = ROUND((julianday(datetime('now')) - julianday(started_at)) * 86400, 2)
        WHERE run_id = ?
    """, (status, rows_fetched, rows_inserted, rows_updated, error_message, run_id))

    # Update data source last run info
    if status == 'success':
        cursor.execute("""
            UPDATE data_sources SET
                last_run_at = datetime('now'),
                last_row_count = ?,
                status = 'active',
                updated_at = datetime('now')
            WHERE source_id = 'na_inbound_gr'
        """, (rows_fetched,))

    conn.commit()


def import_from_csv(csv_path: str) -> bool:
    """Import NA Inbound GR data from a CSV file into SQLite."""
    log(f"📥 Importing from CSV: {csv_path}")

    if not os.path.exists(csv_path):
        log(f"❌ CSV file not found: {csv_path}")
        return False

    conn = get_db()
    run_id = start_run(conn)

    try:
        rows_fetched = 0
        rows_inserted = 0
        rows_updated = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                rows_fetched += 1

                # Normalize column names (handle various formats from Snowflake)
                adj_date = row.get('ADJUSTMENT_DATE', row.get('adjustment_date', ''))
                facility = row.get('FACILITY_ID', row.get('facility_id', row.get('FACILILTY_ID', '')))
                item_code = row.get('ITEM_CODE', row.get('item_code', ''))
                item_desc = row.get('ITEM_DESCRIPTION', row.get('item_description', ''))
                product = row.get('PRODUCT_NAME', row.get('product_name', ''))
                client = row.get('CLIENT_CODE', row.get('client_code', ''))
                adj_id = row.get('ADJUSTMENT_ID', row.get('adjustment_id', ''))
                avl_qty = int(float(row.get('AVL_QUANTITY', row.get('avl_quantity', 0)) or 0))
                unavl_qty = int(float(row.get('UNAVL_QUANTITY', row.get('unavl_quantity', 0)) or 0))
                return_qty = int(float(row.get('RETURN_QUANTITY', row.get('return_quantity', 0)) or 0))
                std_cost = float(row.get('STD_COST', row.get('std_cost', 0)) or 0)
                ext_cost = float(row.get('EXTENDED_COST', row.get('extended_cost', 0)) or 0)
                file_name = row.get('FILE_NAME', row.get('file_name', ''))
                proc_flag = row.get('PROCESS_FLAG', row.get('process_flag', ''))

                try:
                    conn.execute("""
                        INSERT INTO na_inbound_gr
                            (adjustment_date, facility_id, item_code, item_description, product_name,
                             client_code, adjustment_id, avl_quantity, unavl_quantity, return_quantity,
                             std_cost, extended_cost, file_name, process_flag)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(adjustment_date, facility_id, item_code, adjustment_id)
                        DO UPDATE SET
                            item_description = excluded.item_description,
                            product_name = excluded.product_name,
                            client_code = excluded.client_code,
                            avl_quantity = excluded.avl_quantity,
                            unavl_quantity = excluded.unavl_quantity,
                            return_quantity = excluded.return_quantity,
                            std_cost = excluded.std_cost,
                            extended_cost = excluded.extended_cost,
                            file_name = excluded.file_name,
                            process_flag = excluded.process_flag,
                            fetched_at = datetime('now')
                    """, (adj_date, facility, item_code, item_desc, product,
                          client, adj_id, avl_qty, unavl_qty, return_qty,
                          std_cost, ext_cost, file_name, proc_flag))

                    # Check if it was an insert or update
                    if conn.execute("SELECT changes()").fetchone()[0] > 0:
                        rows_inserted += 1

                except sqlite3.IntegrityError as e:
                    log(f"   ⚠️ Row {rows_fetched}: {e}")
                    rows_updated += 1

        conn.commit()
        finish_run(conn, run_id, 'success', rows_fetched, rows_inserted, rows_updated)

        log(f"✅ Import complete: {rows_fetched} fetched, {rows_inserted} inserted/updated")

        # Print summary stats
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total, MIN(adjustment_date) as earliest, MAX(adjustment_date) as latest,
                   COUNT(DISTINCT facility_id) as facilities, COUNT(DISTINCT item_code) as skus
            FROM na_inbound_gr
        """)
        stats = cursor.fetchone()
        log(f"📊 Database now has {stats['total']:,} rows | {stats['earliest']} → {stats['latest']} | {stats['facilities']} facilities | {stats['skus']} SKUs")

        conn.close()
        return True

    except Exception as e:
        log(f"❌ Import failed: {e}")
        finish_run(conn, run_id, 'error', error_message=str(e))
        conn.close()
        return False


def import_from_json(json_path: str) -> bool:
    """Import NA Inbound GR data from a JSON file (Snowflake query result format)."""
    log(f"📥 Importing from JSON: {json_path}")

    if not os.path.exists(json_path):
        log(f"❌ JSON file not found: {json_path}")
        return False

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log(f"❌ Failed to parse JSON file: {e}")
        return False

    # Handle Snowflake result format: {"data": [...], "columns": [...]}
    if isinstance(data, dict) and 'data' in data:
        rows = data['data']
    elif isinstance(data, list):
        rows = data
    else:
        log(f"❌ Unexpected JSON format")
        return False

    # Write to temp CSV and use existing import
    temp_csv = os.path.join(DATA_DIR, '_temp_import.csv')
    if rows:
        with open(temp_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        result = import_from_csv(temp_csv)
        os.remove(temp_csv)
        return result

    log("⚠️ No data rows in JSON file")
    return False


def get_latest_date(conn: sqlite3.Connection) -> Optional[str]:
    """Get the most recent adjustment_date in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(adjustment_date) as latest FROM na_inbound_gr")
    row = cursor.fetchone()
    return row['latest'] if row and row['latest'] else None


def query_summary(days: int = 7) -> None:
    """Print a summary of recent data for quick checks."""
    conn = get_db()
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    print(f"\n📊 NA Inbound GR Summary (last {days} days)")
    print("=" * 60)

    # By facility
    cursor.execute("""
        SELECT facility_id,
               COUNT(*) as rows,
               SUM(avl_quantity) as total_avl,
               SUM(unavl_quantity) as total_unavl,
               COUNT(DISTINCT item_code) as unique_skus,
               COUNT(DISTINCT adjustment_date) as days_covered
        FROM na_inbound_gr
        WHERE adjustment_date >= ?
        GROUP BY facility_id
        ORDER BY facility_id
    """, (cutoff,))

    print(f"\n{'Facility':<10} {'Rows':>8} {'AVL Qty':>12} {'UNAVL Qty':>12} {'SKUs':>8} {'Days':>6}")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row['facility_id']:<10} {row['rows']:>8,} {row['total_avl']:>12,} {row['total_unavl']:>12,} {row['unique_skus']:>8} {row['days_covered']:>6}")

    # Top SKUs by volume
    cursor.execute("""
        SELECT item_code, product_name,
               SUM(avl_quantity) as total_avl,
               SUM(unavl_quantity) as total_unavl
        FROM na_inbound_gr
        WHERE adjustment_date >= ?
        GROUP BY item_code, product_name
        ORDER BY total_avl DESC
        LIMIT 10
    """, (cutoff,))

    print(f"\n🔝 Top 10 SKUs by AVL Quantity (last {days} days):")
    print(f"{'Item Code':<20} {'Product':<25} {'AVL':>10} {'UNAVL':>10}")
    print("-" * 70)
    for row in cursor.fetchall():
        product = (row['product_name'] or '')[:24]
        print(f"{row['item_code']:<20} {product:<25} {row['total_avl']:>10,} {row['total_unavl']:>10,}")

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LGX Ops Bot - NA Inbound GR Collector')
    parser.add_argument('--from-csv', type=str, help='Import from CSV file')
    parser.add_argument('--from-json', type=str, help='Import from JSON file')
    parser.add_argument('--days', type=int, default=30, help='Lookback days for Snowflake query (default: 30)')
    parser.add_argument('--summary', action='store_true', help='Print data summary')
    parser.add_argument('--summary-days', type=int, default=7, help='Days for summary (default: 7)')

    args = parser.parse_args()

    if args.summary:
        query_summary(args.summary_days)
    elif args.from_csv:
        import_from_csv(args.from_csv)
    elif args.from_json:
        import_from_json(args.from_json)
    else:
        print("LGX Ops Bot - NA Inbound GR Collector")
        print("=" * 50)
        print(f"Lookback: {args.days} days")
        print()
        print("This script imports data from CSV/JSON files.")
        print("Use the Goose recipe to run the Snowflake query and pass results here.")
        print()
        print("Usage:")
        print("  python3 collect_na_inbound_gr.py --from-csv data/na_inbound_gr_export.csv")
        print("  python3 collect_na_inbound_gr.py --from-json data/na_inbound_gr_export.json")
        print("  python3 collect_na_inbound_gr.py --summary")
        print("  python3 collect_na_inbound_gr.py --summary --summary-days 30")
