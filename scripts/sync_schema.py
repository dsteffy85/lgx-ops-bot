#!/usr/bin/env python3
"""
sync_schema.py — Generate TypeScript schema_context.ts from shared/schema_context.json.

Usage:
  python3 scripts/sync_schema.py

Reads:  ../shared/schema_context.json
Writes: ../conduit/lgx-ops-bot/src/lib/schema_context.ts
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_JSON = ROOT / 'shared' / 'schema_context.json'
# The G2 app lives alongside this project under conduit-app/ (not conduit/)
DEST_TS = ROOT.parent / 'conduit-app' / 'lgx-ops-bot' / 'src' / 'lib' / 'schema_context.ts'


def main():
    if not SRC_JSON.exists():
        print(f'ERROR: Source not found: {SRC_JSON}', file=sys.stderr)
        sys.exit(1)

    with open(SRC_JSON) as f:
        data = json.load(f)

    schema = data.get('schema_context', '')
    if not schema:
        print('ERROR: "schema_context" key missing or empty in JSON', file=sys.stderr)
        sys.exit(1)

    # Check if destination already exists and show diff summary
    old_schema = None
    if DEST_TS.exists():
        old_content = DEST_TS.read_text()
        # Extract the old schema string between the backtick delimiters
        marker = 'export const SCHEMA_CONTEXT = `'
        if marker in old_content:
            start = old_content.index(marker) + len(marker)
            end = old_content.rindex('`')
            old_schema = old_content[start:end]

    # Escape backticks in the schema text (shouldn't exist, but be safe)
    escaped = schema.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

    ts_content = f'''// AUTO-GENERATED — do not edit directly.
// Source: shared/schema_context.json
// Regenerate: python3 scripts/sync_schema.py

export const SCHEMA_CONTEXT = `{escaped}`
'''

    DEST_TS.parent.mkdir(parents=True, exist_ok=True)
    DEST_TS.write_text(ts_content)

    # Print summary
    if old_schema is None:
        print(f'Created: {DEST_TS}')
    elif old_schema == schema:
        print(f'No change: {DEST_TS}')
    else:
        old_lines = old_schema.splitlines()
        new_lines = schema.splitlines()
        added = sum(1 for l in new_lines if l not in old_lines)
        removed = sum(1 for l in old_lines if l not in new_lines)
        print(f'Updated: {DEST_TS}  (+{added} lines, -{removed} lines)')

    print(f'Schema length: {len(schema):,} chars')


if __name__ == '__main__':
    main()
