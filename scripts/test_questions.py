#!/usr/bin/env python3
"""
LGX-OPS-BOT Question Test Harness

Runs a batch of questions through the same LLM SQL generation + Snowflake execution
pipeline as the Slack listener, but outputs results to terminal instead of Slack.

Usage:
    python3 test_questions.py              # Run all test questions
    python3 test_questions.py --quick      # Run quick subset (10 questions)
    python3 test_questions.py "custom question here"  # Test a single question
"""
import json, sys, os, glob, time, re
from pathlib import Path
from typing import Optional, List, Tuple

# ── Snowflake connection ──
_sf_conn = None

def get_sf():
    global _sf_conn
    if _sf_conn:
        try:
            _sf_conn.cursor().execute("SELECT 1")
            return _sf_conn
        except:
            _sf_conn = None
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import snowflake.connector
    kf = glob.glob(str(Path.home() / 'Desktop/Automation/lgx-ops-bot/credentials/LGX_OPS_BOT_private_keys_*.json'))
    with open(kf[0]) as f:
        d = json.load(f)
    pk = serialization.load_pem_private_key(d['square']['private_key'].encode(), password=None, backend=default_backend())
    _sf_conn = snowflake.connector.connect(account='square', user='LGX_OPS_BOT@squareup.com', private_key=pk, warehouse='ETL__MEDIUM', role='LGX_OPS_BOT__SNOWFLAKE__ADMIN')
    return _sf_conn

def query(sql):
    cur = get_sf().cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return cols, rows

# ── LLM SQL generation (same as listener) ──
sys.path.insert(0, str(Path.home() / 'Desktop/Automation/lgx-ops-bot/scripts'))
from slack_listener import SCHEMA_CONTEXT, _get_databricks_token

def generate_sql(question: str) -> Optional[str]:
    import requests
    host = os.environ.get('DATABRICKS_HOST', 'https://block-lakehouse-production.cloud.databricks.com')
    token = _get_databricks_token()
    if not token:
        return None
    resp = requests.post(
        f'{host}/serving-endpoints/goose-claude-4-5-haiku/invocations',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'messages': [
                {'role': 'system', 'content': 'You are a SQL expert. Return ONLY a Snowflake SQL query. No explanation, no markdown fences, no comments, no semicolons.'},
                {'role': 'user', 'content': f'{SCHEMA_CONTEXT}\n\nQuestion: {question}'}
            ],
            'max_tokens': 500
        },
        timeout=30
    )
    if resp.ok:
        sql = resp.json()['choices'][0]['message']['content'].strip()
        if sql.startswith('```sql'): sql = sql[6:]
        elif sql.startswith('```'): sql = sql[3:]
        if sql.endswith('```'): sql = sql[:-3]
        sql = sql.strip().rstrip(';')
        if sql.upper().startswith('SELECT'):
            return sql
    return None

# ── Test questions ──
TEST_QUESTIONS = [
    # ── Order lookups ──
    ("What's the status of order US-373216476?", "order_lookup"),
    ("Look up US-009227617", "order_lookup"),

    # ── Delivery / shipping counts ──
    ("How many orders shipped from CVU yesterday?", "delivery"),
    ("How many orders shipped from IMC this week?", "delivery"),
    ("How many orders shipped late from CVU yesterday?", "delivery"),
    ("How many orders are stuck at warehouse for more than 3 days?", "delivery"),
    ("What's the average transit time for orders shipped last week?", "delivery"),
    ("Which facility shipped the most orders yesterday?", "delivery"),
    ("How many orders were cancelled last week?", "delivery"),
    ("How many undelivered orders are there from the last 7 days?", "delivery"),

    # ── Inventory ──
    ("What's the current inventory at CVU?", "inventory"),
    ("What's the current inventory at GBR?", "inventory"),
    ("How many units of A-SKU-0665 are in inventory?", "inventory"),
    ("Which facility has the most inventory right now?", "inventory"),
    ("What are the top 10 SKUs by inventory quantity at CVU?", "inventory"),

    # ── Inbound ──
    ("What came in to CVU yesterday?", "inbound"),
    ("How many inbound receipts at IMC this week?", "inbound"),
    ("Any inbound discrepancies in the last 7 days?", "inbound"),

    # ── Retail ops ──
    ("How many units of A-SKU-0665 shipped to Amazon US in Dec 2025?", "retail"),
    ("How many units of A-SKU-0665 shipped to Best Buy in Dec 2025?", "retail"),
    ("What's the price for A-SKU-0665 at Amazon?", "retail"),
    ("Show me open Walmart orders", "retail"),
    ("What retail order exceptions came in this week?", "retail"),
    ("How many Best Buy orders shipped last month?", "retail"),
    ("What's the total retail revenue for Amazon in Q1 2026?", "retail"),
    ("Which SKU has the most retail order exceptions?", "retail"),

    # ── SKU / product ──
    ("What product family is A-SKU-0665?", "product"),
    ("How many active SKUs do we have?", "product"),
    ("List all SKUs in the Square Terminal product family", "product"),

    # ── Shipments (856) ──
    ("How many units of A-SKU-0665 shipped last week?", "shipments"),
    ("How many warranty replacement orders shipped this month?", "shipments"),
    ("What's the total shipment cost for CVU last month?", "shipments"),
]

QUICK_QUESTIONS = TEST_QUESTIONS[:10]

def fmt_val(v):
    if v is None: return 'NULL'
    if isinstance(v, (int, float)): return f"{int(v):,}" if v == int(v) else f"{v:,.2f}"
    s = str(v)
    return s[:60] + '...' if len(s) > 60 else s

def run_test(question: str, category: str, idx: int, total: int):
    print(f"\n{'='*70}")
    print(f"  [{idx}/{total}] {category.upper()}")
    print(f"  Q: {question}")
    print(f"{'='*70}")

    # Check for order lookup
    order_match = re.search(r'US-\d{6,}', question)

    start = time.time()
    sql = generate_sql(question)
    llm_time = time.time() - start

    if not sql:
        print(f"  ❌ LLM FAILED — no SQL generated ({llm_time:.1f}s)")
        return {"question": question, "category": category, "status": "LLM_FAIL", "sql": None, "rows": 0, "answer": None}

    print(f"  SQL ({llm_time:.1f}s): {' '.join(sql.split())[:120]}")

    try:
        start = time.time()
        cols, rows = query(sql)
        sf_time = time.time() - start

        if not rows:
            print(f"  ⚠️  0 ROWS returned ({sf_time:.1f}s)")
            return {"question": question, "category": category, "status": "ZERO_ROWS", "sql": sql, "rows": 0, "answer": None}

        # Show results
        print(f"  ✅ {len(rows)} rows, {len(cols)} cols ({sf_time:.1f}s)")
        for i, row in enumerate(rows[:5]):
            vals = " | ".join(f"{c}={fmt_val(v)}" for c, v in zip(cols, row))
            print(f"     [{i}] {vals}")
        if len(rows) > 5:
            print(f"     ... and {len(rows)-5} more rows")

        # Quick sanity check
        if len(rows) == 1 and len(cols) == 1:
            val = rows[0][0]
            if val is None or val == 0:
                print(f"  ⚠️  SUSPICIOUS — single value is {val}")
                return {"question": question, "category": category, "status": "SUSPICIOUS_ZERO", "sql": sql, "rows": len(rows), "answer": val}

        answer = rows[0][0] if len(cols) == 1 and len(rows) == 1 else f"{len(rows)} rows"
        return {"question": question, "category": category, "status": "OK", "sql": sql, "rows": len(rows), "answer": answer}

    except Exception as e:
        print(f"  ❌ SQL ERROR: {e}")
        return {"question": question, "category": category, "status": "SQL_ERROR", "sql": sql, "rows": 0, "answer": str(e)}


def main():
    if len(sys.argv) > 1 and sys.argv[1] != '--quick':
        # Single custom question
        q = ' '.join(sys.argv[1:])
        run_test(q, "custom", 1, 1)
        return

    questions = QUICK_QUESTIONS if '--quick' in sys.argv else TEST_QUESTIONS
    print(f"\n🤖 LGX-OPS-BOT Test Harness — {len(questions)} questions\n")

    results = []
    for i, (q, cat) in enumerate(questions, 1):
        try:
            r = run_test(q, cat, i, len(questions))
        except Exception as e:
            print(f"  ❌ CRASH: {e}")
            r = {"question": q, "category": cat, "status": "CRASH", "sql": None, "rows": 0, "answer": str(e)}
        results.append(r)
        time.sleep(2)  # Rate limit protection

    # Summary
    ok = sum(1 for r in results if r['status'] == 'OK')
    zero = sum(1 for r in results if r['status'] in ('ZERO_ROWS', 'SUSPICIOUS_ZERO'))
    fail = sum(1 for r in results if r['status'] in ('LLM_FAIL', 'SQL_ERROR'))

    print(f"\n{'='*70}")
    print(f"  SUMMARY: {ok} ✅ OK | {zero} ⚠️ Zero/Suspicious | {fail} ❌ Failed")
    print(f"  Total: {len(results)} questions")
    print(f"{'='*70}")

    if zero + fail > 0:
        print(f"\n  ISSUES:")
        for r in results:
            if r['status'] != 'OK':
                print(f"    {r['status']:20s} | {r['question'][:60]}")
                if r['sql']:
                    print(f"    {'':20s} | SQL: {' '.join(r['sql'].split())[:80]}")
    print()


if __name__ == "__main__":
    main()
