#!/usr/bin/env python3
"""Convert Snowflake JSON result to CSV for import into SQLite."""
import csv, json, sys, os

def convert(json_path, csv_path):
    with open(json_path) as f:
        result = json.load(f)
    
    data = result.get("data", result) if isinstance(result, dict) else result
    if not data:
        print("No data to convert")
        return 0
    
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Wrote {len(data)} rows to {csv_path}")
    return len(data)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 snowflake_to_csv.py input.json output.csv")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
