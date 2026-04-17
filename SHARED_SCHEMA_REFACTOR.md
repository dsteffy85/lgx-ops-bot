# Task: Shared Schema Context + G2 App "Ask" Feature Upgrade

## Goal
Extract the schema context from `scripts/slack_listener.py` into a shared source file, then update both the Slack listener and the G2 app to consume it. Also upgrade the G2 app's "Ask LGX-OPS-BOT" feature to match the Slack listener's quality (natural language answers, not just raw tables).

## Current State

### Slack Listener (`scripts/slack_listener.py`)
- Has a massive `SCHEMA_CONTEXT` string (~8,720 chars, 117 lines) with:
  - All table definitions (LGX_OPS_BOT + ORACLE_ERP.SCM retail tables)
  - Product abbreviations (T2, X2, R4X, B4, Kiosk, etc.)
  - Customer LIKE patterns (Amazon, Walmart, Best Buy)
  - Facility codes and mappings
  - Order number format routing
  - Definitions (late shipment, stuck at warehouse, etc.)
  - SQL rules (no TOP N, no semicolons, fully qualified names)
- Uses Databricks Claude Haiku for SQL generation
- Uses a SECOND LLM call (`_format_answer_llm`) to turn raw query results into a natural language Slack message with bold key numbers and bullet points
- This is the gold standard — works great

### G2 App (`src/components/pages/Query.tsx`)
- Has a minimal `SCHEMA_CONTEXT` (~40 lines) — missing most of the above
- Uses G2's LLM (Claude Opus) via `useLlm` hook for SQL generation
- Shows raw data tables only — NO natural language summary
- This is what needs upgrading

## What to Build

### 1. Shared Schema File
Create `shared/schema_context.json` (or `.yaml` or `.py` — your choice of format that's easy to consume from both Python and TypeScript).

Contents should include:
- The full schema context text (the big prompt string)
- Structured metadata if helpful (table list, abbreviations, etc.)

### 2. Update `scripts/slack_listener.py`
- Import/load `SCHEMA_CONTEXT` from the shared file instead of having it inline
- Everything else stays the same

### 3. Update G2 App `src/components/pages/Query.tsx`
- Import the schema context from the shared file (or a generated TypeScript file)
- **Add a natural language answer step**: After the SQL query returns results, make a second LLM call to format the results into a concise human-readable summary (same pattern as `_format_answer_llm` in the Slack listener)
- Show the natural language summary ABOVE the data table (keep the table too — best of both worlds)
- Update the example questions to match the fuller capability set

### 4. Sync Script
Create a script (e.g., `scripts/sync_schema.py` or `scripts/build_shared.sh`) that:
- Reads the shared schema source
- Generates/updates the TypeScript constant for the G2 app
- Can be run manually or as a pre-deploy step
- Prints a diff or confirmation of what changed

## File Locations
- Slack listener: `/Users/dsteffy/Desktop/Automation/lgx-ops-bot/scripts/slack_listener.py`
- G2 app source: `/Users/dsteffy/Desktop/Automation/conduit-app/lgx-ops-bot/src/`
- G2 app Query page: `/Users/dsteffy/Desktop/Automation/conduit-app/lgx-ops-bot/src/components/pages/Query.tsx`
- G2 LLM hook: `/Users/dsteffy/Desktop/Automation/conduit-app/lgx-ops-bot/src/hooks/useLlm.ts`
- G2 Snowflake lib: `/Users/dsteffy/Desktop/Automation/conduit-app/lgx-ops-bot/src/lib/snowflake.ts`
- G2 MCP lib: `/Users/dsteffy/Desktop/Automation/conduit-app/lgx-ops-bot/src/lib/mcp.ts`

## Key Constraints
- The G2 app uses `useLlm` hook (postMessage to G2 parent) for LLM calls — NOT direct Databricks API
- The G2 app uses `querySnowflake` (via query-expert MCP tool) — NOT direct Snowflake connection
- The shared schema must be the SINGLE source of truth — both consumers derive from it
- Don't break the existing Slack listener functionality
- The G2 app's LLM service profile is `claude-4-6-opus` — keep using that

## Answer Formatting Prompt (from Slack listener)
The second LLM call should use this system prompt pattern:
```
Format Snowflake query results as a concise Slack message. Rules:
- Start with the key number in bold (e.g., *4,049 units*)
- Add a one-sentence summary answering the question
- Add 3-5 bullet points with relevant breakdowns from the data
- Use Slack formatting: *bold*, bullet points with •
- Format numbers with commas
- Format dates as "Apr 6, 2025"
- Keep it under 10 lines total
- Do NOT include any header or bot name — just the answer content
```
For the G2 app, adapt this to use markdown (not Slack formatting) since it renders in a web UI.

## Testing
After changes:
1. Run `python3 scripts/slack_listener.py --test-only` and ask a question in #squirt-test — should work identically
2. Build the G2 app (`npm run build` in the conduit-app/lgx-ops-bot dir) — should compile clean
3. The Ask feature should now show a natural language summary above the data table
