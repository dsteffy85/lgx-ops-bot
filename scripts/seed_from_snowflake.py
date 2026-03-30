#!/usr/bin/env python3
"""
Seed the lgx-ops-bot database directly from Snowflake JSON results.
Usage: python3 seed_from_snowflake.py <json_file>
  or pipe JSON: echo '{"data":[...]}' | python3 seed_from_snowflake.py --stdin
"""
import sys, json, csv, os

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_OUT = os.path.join(PROJ, "data", "snowflake_30day.csv")

def main():
    # Read JSON from file or stdin
    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        raw = sys.stdin.read()
    elif len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            raw = f.read()
    else:
        print("Usage: python3 seed_from_snowflake.py <json_file>")
        print("   or: cat result.json | python3 seed_from_snowflake.py --stdin")
        sys.exit(1)

    payload = json.loads(raw)
    
    # Handle both {"data": [...]} and plain [...]
    if isinstance(payload, dict):
        rows = payload.get("data", payload.get("rows", []))
        columns = payload.get("columns", [])
    elif isinstance(payload, list):
        rows = payload
        columns = list(rows[0].keys()) if rows else []
    else:
        print("ERROR: Unexpected JSON format")
        sys.exit(1)

    if not rows:
        print("ERROR: No data rows found")
        sys.exit(1)

    # If columns is a list of strings, use as-is
    # If columns is missing, derive from first row
    if not columns:
        columns = list(rows[0].keys())

    # Write CSV
    with open(CSV_OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"✅ Wrote {len(rows)} rows to {CSV_OUT}")
    print(f"   Columns: {', '.join(columns)}")
    
    # Now import into SQLite
    print(f"\n📦 Importing into SQLite...")
    sys.path.insert(0, os.path.join(PROJ, "scripts"))
    from collect_na_inbound_gr import import_from_csv
    result = import_from_csv(CSV_OUT)
    
    # Print summary
    print(f"\n📊 Running summary...")
    from collect_na_inbound_gr import query_summary
    query_summary(30)

if __name__ == "__main__":
    main()
