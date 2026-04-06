#!/usr/bin/env python3
"""
LGX Ops Bot - Direct Snowflake Query Runner
Connects to Snowflake using RSA key pair auth (robot user) and runs queries.
Designed to run in GitHub Actions or any CI/CD environment.

Environment variables required:
    SNOWFLAKE_ACCOUNT   - Snowflake account (e.g., square)
    SNOWFLAKE_USER      - Robot user name (e.g., LGX_OPS_BOT)
    SNOWFLAKE_WAREHOUSE - Warehouse to use (e.g., ETL__MEDIUM)
    SNOWFLAKE_PRIVATE_KEY - RSA private key (PEM format, base64-encoded)

Usage:
    python3 snowflake_query.py --query queries/na_inbound_gr.sql --output data/results.csv
    python3 snowflake_query.py --sql "SELECT 1" --output data/test.csv
"""

import os
import sys
import csv
import argparse
import base64
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import snowflake.connector


def get_connection():
    """Create Snowflake connection using RSA key pair auth."""
    account = os.environ.get('SNOWFLAKE_ACCOUNT', 'square')
    user = os.environ.get('SNOWFLAKE_USER', 'LGX_OPS_BOT')
    warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE', 'ETL__MEDIUM')
    private_key_b64 = os.environ.get('SNOWFLAKE_PRIVATE_KEY', '')

    if not private_key_b64:
        print("ERROR: SNOWFLAKE_PRIVATE_KEY environment variable not set")
        sys.exit(1)

    # Decode the base64-encoded private key
    private_key_pem = base64.b64decode(private_key_b64)
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )

    # Get the raw bytes for Snowflake connector
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        private_key=private_key_bytes,
        warehouse=warehouse,
    )

    print(f"Connected to Snowflake as {user} on {account} (warehouse: {warehouse})")
    return conn


def run_query(conn, sql, output_path=None):
    """Execute a query and optionally save results to CSV."""
    print(f"Executing query ({len(sql)} chars)...")
    start = datetime.now()

    cursor = conn.cursor()
    cursor.execute(sql)

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    elapsed = (datetime.now() - start).total_seconds()
    print(f"Query returned {len(rows):,} rows in {elapsed:.1f}s")

    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        print(f"Results saved to {output_path}")

    cursor.close()
    return columns, rows


def main():
    parser = argparse.ArgumentParser(description='LGX Ops Bot - Snowflake Query Runner')
    parser.add_argument('--query', type=str, help='Path to SQL file')
    parser.add_argument('--sql', type=str, help='Inline SQL query')
    parser.add_argument('--output', type=str, help='Output CSV path')
    parser.add_argument('--lookback-days', type=int, default=30, help='Lookback days (replaces {lookback_days} in SQL)')
    parser.add_argument('--test', action='store_true', help='Test connection only')

    args = parser.parse_args()

    conn = get_connection()

    if args.test:
        print("Testing connection...")
        run_query(conn, "SELECT CURRENT_TIMESTAMP() AS ts, CURRENT_USER() AS user, CURRENT_WAREHOUSE() AS warehouse")
        print("Connection test passed!")
        conn.close()
        return

    if args.query:
        with open(args.query, 'r') as f:
            sql = f.read()
        # Replace template variables
        sql = sql.replace('{lookback_days}', str(args.lookback_days))
    elif args.sql:
        sql = args.sql
    else:
        print("ERROR: Provide --query (SQL file) or --sql (inline query)")
        sys.exit(1)

    columns, rows = run_query(conn, sql, args.output)

    # Print summary
    print(f"\nSummary: {len(columns)} columns, {len(rows):,} rows")
    if rows:
        print(f"Columns: {', '.join(columns)}")

    conn.close()


if __name__ == '__main__':
    main()
