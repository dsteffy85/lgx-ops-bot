#!/usr/bin/env python3
"""
LGX Ops Bot - Query Bot
Answers natural language questions about collected data.

This module maps common operations questions to SQL queries against the local
SQLite database. Designed to be called by Goose or used standalone.

Usage:
    python3 query_bot.py "How many units received at CVU this week?"
    python3 query_bot.py "Top SKUs at IMC last 7 days"
    python3 query_bot.py "Daily breakdown for CVU"
    python3 query_bot.py --list-queries
"""

import sqlite3
import os
import sys
import json
import argparse
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'lgx_ops.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Pre-built Queries ───
# These are the common questions the bot can answer.
# Each query has: name, description, sql, params_builder

QUERIES = {
    "facility_summary": {
        "name": "Facility Summary",
        "description": "Total AVL/UNAVL quantities by facility for a date range",
        "sql": """
            SELECT facility_id,
                   COUNT(DISTINCT adjustment_date) as days,
                   COUNT(DISTINCT item_code) as unique_skus,
                   SUM(avl_quantity) as total_avl,
                   SUM(unavl_quantity) as total_unavl,
                   SUM(return_quantity) as total_returns,
                   ROUND(SUM(extended_cost), 2) as total_cost
            FROM na_inbound_gr
            WHERE adjustment_date >= :start_date
              AND (:facility IS NULL OR facility_id = :facility)
            GROUP BY facility_id
            ORDER BY total_avl DESC
        """,
    },
    "daily_breakdown": {
        "name": "Daily Breakdown",
        "description": "Day-by-day AVL/UNAVL totals, optionally filtered by facility",
        "sql": """
            SELECT adjustment_date,
                   facility_id,
                   COUNT(DISTINCT item_code) as unique_skus,
                   SUM(avl_quantity) as total_avl,
                   SUM(unavl_quantity) as total_unavl,
                   SUM(return_quantity) as total_returns
            FROM na_inbound_gr
            WHERE adjustment_date >= :start_date
              AND (:facility IS NULL OR facility_id = :facility)
            GROUP BY adjustment_date, facility_id
            ORDER BY adjustment_date DESC, facility_id
        """,
    },
    "top_skus": {
        "name": "Top SKUs",
        "description": "Top N SKUs by AVL quantity received",
        "sql": """
            SELECT item_code, product_name,
                   SUM(avl_quantity) as total_avl,
                   SUM(unavl_quantity) as total_unavl,
                   COUNT(DISTINCT adjustment_date) as days_active,
                   COUNT(DISTINCT facility_id) as facilities
            FROM na_inbound_gr
            WHERE adjustment_date >= :start_date
              AND (:facility IS NULL OR facility_id = :facility)
            GROUP BY item_code, product_name
            ORDER BY total_avl DESC
            LIMIT :limit
        """,
    },
    "sku_detail": {
        "name": "SKU Detail",
        "description": "Detailed history for a specific SKU",
        "sql": """
            SELECT adjustment_date, facility_id,
                   avl_quantity, unavl_quantity, return_quantity,
                   std_cost, extended_cost
            FROM na_inbound_gr
            WHERE item_code = :item_code
              AND adjustment_date >= :start_date
              AND (:facility IS NULL OR facility_id = :facility)
            ORDER BY adjustment_date DESC
        """,
    },
    "product_summary": {
        "name": "Product Summary",
        "description": "Aggregated by product name (groups related SKUs)",
        "sql": """
            SELECT product_name,
                   COUNT(DISTINCT item_code) as sku_count,
                   SUM(avl_quantity) as total_avl,
                   SUM(unavl_quantity) as total_unavl,
                   ROUND(SUM(extended_cost), 2) as total_cost
            FROM na_inbound_gr
            WHERE adjustment_date >= :start_date
              AND product_name IS NOT NULL AND product_name != ''
              AND (:facility IS NULL OR facility_id = :facility)
            GROUP BY product_name
            ORDER BY total_avl DESC
            LIMIT :limit
        """,
    },
    "data_freshness": {
        "name": "Data Freshness",
        "description": "When was data last collected and what's the coverage",
        "sql": """
            SELECT
                (SELECT MAX(adjustment_date) FROM na_inbound_gr) as latest_data_date,
                (SELECT MIN(adjustment_date) FROM na_inbound_gr) as earliest_data_date,
                (SELECT COUNT(*) FROM na_inbound_gr) as total_rows,
                (SELECT COUNT(DISTINCT item_code) FROM na_inbound_gr) as total_skus,
                (SELECT COUNT(DISTINCT facility_id) FROM na_inbound_gr) as total_facilities,
                (SELECT MAX(fetched_at) FROM na_inbound_gr) as last_fetched,
                (SELECT COUNT(*) FROM run_log WHERE source_id='na_inbound_gr' AND status='success') as successful_runs
        """,
    },
    "week_over_week": {
        "name": "Week over Week",
        "description": "Compare this week vs last week by facility",
        "sql": """
            WITH this_week AS (
                SELECT facility_id,
                       SUM(avl_quantity) as avl,
                       SUM(unavl_quantity) as unavl
                FROM na_inbound_gr
                WHERE adjustment_date >= date('now', '-7 days')
                GROUP BY facility_id
            ),
            last_week AS (
                SELECT facility_id,
                       SUM(avl_quantity) as avl,
                       SUM(unavl_quantity) as unavl
                FROM na_inbound_gr
                WHERE adjustment_date >= date('now', '-14 days')
                  AND adjustment_date < date('now', '-7 days')
                GROUP BY facility_id
            )
            SELECT
                COALESCE(t.facility_id, l.facility_id) as facility_id,
                COALESCE(t.avl, 0) as this_week_avl,
                COALESCE(l.avl, 0) as last_week_avl,
                COALESCE(t.avl, 0) - COALESCE(l.avl, 0) as avl_change,
                CASE WHEN COALESCE(l.avl, 0) > 0
                     THEN ROUND((COALESCE(t.avl, 0) - l.avl) * 100.0 / l.avl, 1)
                     ELSE NULL END as avl_pct_change
            FROM this_week t
            FULL OUTER JOIN last_week l ON t.facility_id = l.facility_id
            ORDER BY facility_id
        """,
    },
}


def run_query(query_name, params=None):
    """Run a named query and return results as list of dicts."""
    if query_name not in QUERIES:
        return {"error": f"Unknown query: {query_name}. Available: {list(QUERIES.keys())}"}

    query_def = QUERIES[query_name]
    conn = get_db()

    # Default params
    defaults = {
        'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'facility': None,
        'limit': 20,
        'item_code': None,
    }
    if params:
        defaults.update(params)

    try:
        cursor = conn.cursor()
        cursor.execute(query_def['sql'], defaults)
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        result = {
            "query": query_name,
            "description": query_def['description'],
            "params": {k: v for k, v in defaults.items() if v is not None},
            "row_count": len(rows),
            "columns": columns,
            "data": rows,
        }
        conn.close()
        return result

    except Exception as e:
        conn.close()
        return {"error": str(e), "query": query_name}


def format_result(result):
    """Format query result for human-readable output."""
    if 'error' in result:
        return f"❌ Error: {result['error']}"

    lines = []
    lines.append(f"\n📊 {QUERIES[result['query']]['name']}")
    lines.append(f"   {result['description']}")
    lines.append(f"   Rows: {result['row_count']}")
    lines.append("")

    if not result['data']:
        lines.append("   (no data)")
        return '\n'.join(lines)

    # Auto-format as table
    columns = result['columns']
    col_widths = {col: max(len(col), max(len(str(row.get(col, ''))) for row in result['data'])) for col in columns}

    # Header
    header = ' | '.join(col.ljust(col_widths[col]) for col in columns)
    lines.append(f"   {header}")
    lines.append(f"   {'-' * len(header)}")

    # Rows
    for row in result['data']:
        line = ' | '.join(str(row.get(col, '')).ljust(col_widths[col]) for col in columns)
        lines.append(f"   {line}")

    return '\n'.join(lines)


def list_queries():
    """List all available queries."""
    print("\n📋 Available Queries")
    print("=" * 60)
    for key, q in QUERIES.items():
        print(f"\n  {key}")
        print(f"    {q['name']}: {q['description']}")
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LGX Ops Bot - Query Interface')
    parser.add_argument('query', nargs='?', help='Query name or natural language question')
    parser.add_argument('--facility', '-f', type=str, help='Filter by facility (CVU, IMC, IMU)')
    parser.add_argument('--days', '-d', type=int, default=7, help='Lookback days (default: 7)')
    parser.add_argument('--limit', '-l', type=int, default=20, help='Result limit (default: 20)')
    parser.add_argument('--sku', '-s', type=str, help='SKU/Item code for detail query')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--list-queries', action='store_true', help='List available queries')

    args = parser.parse_args()

    if args.list_queries:
        list_queries()
        sys.exit(0)

    if not args.query:
        list_queries()
        print("Usage: python3 query_bot.py <query_name> [--facility CVU] [--days 7]")
        sys.exit(0)

    params = {
        'start_date': (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d'),
        'facility': args.facility,
        'limit': args.limit,
        'item_code': args.sku,
    }

    result = run_query(args.query, params)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(format_result(result))
