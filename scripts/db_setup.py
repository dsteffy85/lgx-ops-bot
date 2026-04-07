#!/usr/bin/env python3
"""
LGX Ops Bot - Database Setup & Schema Management
Creates and maintains the SQLite database for all collected data.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DB_DIR, 'lgx_ops.db')


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def setup_database() -> str:
    """Create all tables and indexes. Returns the path to the database file."""
    conn = get_connection()
    cursor = conn.cursor()

    # ─── Data Sources Registry ───
    # Tracks what data sources are configured and when they last ran
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_sources (
            source_id       TEXT PRIMARY KEY,
            source_name     TEXT NOT NULL,
            source_type     TEXT NOT NULL CHECK(source_type IN ('snowflake', 'looker', 'gmail', 'gdrive')),
            description     TEXT,
            query_or_config TEXT,
            schedule        TEXT,
            last_run_at     TEXT,
            last_row_count  INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'error')),
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # ─── Run Log ───
    # Tracks every data collection run (success/failure, row counts, timing)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_log (
            run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id       TEXT NOT NULL REFERENCES data_sources(source_id),
            started_at      TEXT NOT NULL,
            finished_at     TEXT,
            status          TEXT DEFAULT 'running' CHECK(status IN ('running', 'success', 'error', 'skipped')),
            rows_fetched    INTEGER DEFAULT 0,
            rows_inserted   INTEGER DEFAULT 0,
            rows_updated    INTEGER DEFAULT 0,
            error_message   TEXT,
            duration_secs   REAL
        )
    """)

    # ─── NA Inbound GR Data ───
    # Goods Receipt data from ORACLE_ERP.SCM.SQ_841_INBOUND_V
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS na_inbound_gr (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            adjustment_date TEXT NOT NULL,
            facility_id     TEXT NOT NULL,
            item_code       TEXT NOT NULL,
            item_description TEXT,
            product_name    TEXT,
            client_code     TEXT,
            adjustment_id   TEXT,
            avl_quantity    INTEGER DEFAULT 0,
            unavl_quantity  INTEGER DEFAULT 0,
            return_quantity INTEGER DEFAULT 0,
            std_cost        REAL DEFAULT 0,
            extended_cost   REAL DEFAULT 0,
            file_name       TEXT,
            process_flag    TEXT,
            fetched_at      TEXT DEFAULT (datetime('now')),
            UNIQUE(adjustment_date, facility_id, item_code, adjustment_id)
        )
    """)

    # ─── Indexes for fast querying ───
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_na_gr_date ON na_inbound_gr(adjustment_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_na_gr_facility ON na_inbound_gr(facility_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_na_gr_item ON na_inbound_gr(item_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_na_gr_date_facility ON na_inbound_gr(adjustment_date, facility_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_na_gr_product ON na_inbound_gr(product_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_log_source ON run_log(source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_log_status ON run_log(status)")

    # ─── Register the NA Inbound GR data source ───
    cursor.execute("""
        INSERT OR IGNORE INTO data_sources (source_id, source_name, source_type, description, schedule)
        VALUES (
            'na_inbound_gr',
            'NA Inbound GR Daily',
            'snowflake',
            'Goods Receipt data from SQ_841_INBOUND_V for CVU/IMC/IMU facilities. STAT remarks only. Rolling 30-day window stored locally, 7-day aggregated pushed to Google Sheets.',
            'daily 4:00 AM PST'
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database ready: {DB_PATH}")
    return DB_PATH


def get_stats() -> None:
    """Print database statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    print("\n📊 LGX Ops Bot - Database Stats")
    print("=" * 50)

    # Data sources
    cursor.execute("SELECT source_id, source_name, source_type, status, last_run_at, last_row_count FROM data_sources")
    sources = cursor.fetchall()
    print(f"\n📁 Data Sources: {len(sources)}")
    for s in sources:
        print(f"   • {s['source_name']} ({s['source_type']}) — {s['status']}")
        print(f"     Last run: {s['last_run_at'] or 'Never'} | Rows: {s['last_row_count']}")

    # NA Inbound GR
    cursor.execute("SELECT COUNT(*) as cnt FROM na_inbound_gr")
    gr_count = cursor.fetchone()['cnt']
    if gr_count > 0:
        cursor.execute("""
            SELECT MIN(adjustment_date) as earliest, MAX(adjustment_date) as latest,
                   COUNT(DISTINCT facility_id) as facilities, COUNT(DISTINCT item_code) as skus
            FROM na_inbound_gr
        """)
        gr = cursor.fetchone()
        print(f"\n📦 NA Inbound GR: {gr_count:,} rows")
        print(f"   Date range: {gr['earliest']} → {gr['latest']}")
        print(f"   Facilities: {gr['facilities']} | SKUs: {gr['skus']}")
    else:
        print(f"\n📦 NA Inbound GR: 0 rows (no data collected yet)")

    # Run log
    cursor.execute("SELECT COUNT(*) as cnt FROM run_log WHERE status='success'")
    success = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM run_log WHERE status='error'")
    errors = cursor.fetchone()['cnt']
    print(f"\n📋 Run History: {success} successful, {errors} errors")

    # DB size
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    print(f"\n💾 Database size: {db_size / 1024:.1f} KB")
    print("=" * 50)

    conn.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        get_stats()
    else:
        setup_database()
        get_stats()
