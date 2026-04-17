# LGX-OPS-BOT Slack Listener — Testing & Improvement Brief

## What this is
A Python Slack listener that answers data questions in real-time by:
1. Polling Slack channels every 10 seconds
2. Detecting questions (order lookups or general data questions)
3. Using an LLM (Databricks-hosted Claude Haiku) to generate Snowflake SQL
4. Executing the SQL against LGX_OPS_BOT database
5. Using a second LLM call to format results into a clean Slack response
6. Posting the answer as a threaded reply

## Key files
- `scripts/slack_listener.py` — Main listener (the file to improve)
- `scripts/test_questions.py` — Test harness (run questions without Slack)
- `scripts/order_lookup.py` — Direct order lookup helper
- `scripts/ask_lgx.py` — General question helper

## How to test
```bash
cd ~/Desktop/Automation/lgx-ops-bot

# Run full test suite (32 questions)
python3 scripts/test_questions.py

# Run quick subset (10 questions)
python3 scripts/test_questions.py --quick

# Test a single question
python3 scripts/test_questions.py "How many orders shipped from CVU yesterday?"
```

## Current pass rate: ~75% (24/32)

## Known issues to fix

### 1. LLM generates wrong SQL for retail queries
The LLM sometimes uses wrong column names or wrong tables for retail-specific questions.
- `SQ_RETAIL_ORDER_EXCEPTIONS_V` only has 5 columns: PO_NUMBER, ORDERED_DATE, BUSINESS_UNIT, ERROR_CATEGORY, ERROR_MESSAGE
- `SQ_RETAIL_SALES_ORDERS_V` has PARTY_NAME for customer filtering — ALWAYS use LIKE not exact match
- `DELIVERY_ORDERS.CUSTOMER_NAME` is always 'ECOMMERCE' — never use it for retail customer filtering

### 2. "Late" / "delayed" / "stuck" definitions inconsistent
The schema context defines these but the LLM sometimes ignores them:
- Late shipping = PROCESSING_DAYS > 2
- Late delivery = TRANSIT_DAYS > 5
- Stuck at warehouse = ORDER_STATUS = 'AT_WAREHOUSE' and days since SENT_TO_WH_DATE > threshold

### 3. Date column confusion
- `SQ_RETAIL_SALES_ORDERS_V` uses `SHIP_DATE` for shipment dates, `ORDERED_DATE` for order dates
- `DELIVERY_ORDERS` uses `FIRST_SHIP_DATE`, `ORDERED_DATE`, etc.
- `NA_INBOUND_GR` uses `ADJUSTMENT_DATE` (stored as string 'YYYY-MM-DD')
- `SQ_856_SC_INBOUND_V` uses `SHIPPING_DATE`

### 4. Inventory per-facility date issue
Latest SNAPSHOT_DATE varies by facility. When querying a specific facility, use:
```sql
WHERE SNAPSHOT_DATE = (SELECT MAX(SNAPSHOT_DATE) FROM ... WHERE FACILITY = 'X')
```
Not the global MAX.

### 5. Response formatting
When the query returns a single number, the response is too bare (just "4,049").
The second LLM call formats it nicely but sometimes the first LLM returns 0 due to bad SQL,
and the formatter makes a nice "0 units" response that looks correct but isn't.

## What to improve

### Priority 1: Get test pass rate to 95%+
- Fix the SCHEMA_CONTEXT in slack_listener.py to give the LLM better hints
- Add explicit column lists for each table
- Add more "IMPORTANT" routing rules
- Add example SQL for common question patterns

### Priority 2: Add more test questions
- Add edge cases (misspelled SKUs, ambiguous dates, multi-table joins)
- Add questions that SHOULD return 0 (so we know 0 is correct vs wrong)
- Add questions that should be unanswerable (no relevant table)

### Priority 3: Improve response quality
- Responses should always include context (SKU name, date range, facility)
- Single numbers should have bullet point breakdowns
- Multi-row results should be formatted as clean tables

## Snowflake connection
Uses RSA key pair auth. Credentials at:
`~/Desktop/Automation/lgx-ops-bot/credentials/LGX_OPS_BOT_private_keys_*.json`

Account: square
User: LGX_OPS_BOT@squareup.com
Warehouse: ETL__MEDIUM
Role: LGX_OPS_BOT__SNOWFLAKE__ADMIN

## Databricks LLM
Endpoint: goose-claude-4-5-haiku
Auth: OAuth token at ~/.config/goose/databricks/oauth/*.json
Token auto-refreshes but may expire — handle 403 gracefully

## DO NOT change
- The Slack posting mechanism (sq agent-tools slack)
- The channel IDs or configs
- The order lookup format (the :robot_face: LGX-OPS-BOT header)
- The Snowflake connection method
