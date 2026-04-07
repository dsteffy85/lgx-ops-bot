#!/usr/bin/env python3
"""Convert Snowflake JSON result to CSV for import into SQLite."""
import csv
import json
import sys
import os


def convert(json_path: str, csv_path: str) -> int:
    """Read a Snowflake JSON result file and write it as CSV.

    Handles both ``{"data": [...]}`` wrapper format and plain list format.

    Returns:
        Number of rows written, or 0 if there was no data.
    """
    if not os.path.exists(json_path):
        print(f"ERROR: Input file not found: {json_path}")
        sys.exit(1)

    try:
        with open(json_path) as f:
            result = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON file: {e}")
        sys.exit(1)

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
