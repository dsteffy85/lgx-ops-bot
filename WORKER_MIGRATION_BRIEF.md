# Slack Listener → Cloudflare Worker Migration

## Goal
Move the LGX-OPS-BOT Slack listener from a local Python process (requires Mac awake)
to a Cloudflare Worker cron trigger on the hw-panel G2 app (runs 24/7).

## Current Architecture (Python on Mac)
```
caffeinate → slack_listener.py → polls every 10s
  → sq agent-tools slack (read channel)
  → Databricks LLM API (generate SQL)
  → Snowflake direct connection (execute SQL)
  → Databricks LLM API (format response)
  → sq agent-tools slack (post reply)
```

## Target Architecture (Cloudflare Worker)
```
Cron trigger (every 1 min) → Worker scheduled handler
  → Slack API via G2 proxy (X-G2-Extension: 'slack') — read channel
  → query-expert MCP via postMessage (generate + execute SQL)
  → LLM via postMessage (format response)
  → Slack API via G2 proxy — post reply
```

## Key Differences
1. **Slack access:** G2 proxy with X-G2-Extension: 'slack' instead of sq agent-tools
2. **Snowflake access:** query-expert MCP tool calls instead of direct snowflake-connector
3. **LLM access:** cloudflare-llm-request postMessage instead of Databricks API
4. **State:** D1 database for processed_threads instead of in-memory set
5. **Cron:** Cloudflare Workers cron triggers instead of Python while loop

## Problem: Worker vs iframe
Workers run server-side — they can't use postMessage (that's client-side iframe → G2 parent).
The Worker's Hono server CAN use fetch() with X-G2-Extension headers for Slack.
But query-expert MCP is only available via postMessage from the client.

### Options:
A. **Worker does Slack + LLM, client does Snowflake**
   - Cron trigger hits /api/triage endpoint on Worker
   - Worker reads Slack via G2 proxy, calls LLM via G2 proxy
   - For Snowflake, Worker returns SQL to client, client calls query-expert, posts result back
   - Problem: no client is open 24/7

B. **Worker does everything via fetch**
   - Slack: fetch slack.com/api/* with X-G2-Extension: 'slack' ✅
   - Snowflake: Need to check if query-expert has a REST API, not just MCP
   - LLM: fetch with X-G2-Extension for LLM endpoint

C. **Hybrid: Worker for Slack, Snowflake Task for data prep**
   - Snowflake Tasks pre-compute common answers into summary tables
   - Worker reads pre-computed data from D1 (synced daily)
   - Only needs Slack proxy, no live Snowflake queries
   - Limitation: can't answer ad-hoc questions

D. **Worker calls Snowflake directly**
   - Use Snowflake SQL REST API (https://square.snowflakecomputing.com/api/v2/statements)
   - Auth via X-G2-Extension: 'block-data' (we proved this works on production)
   - This is what the old app did before we switched to query-expert
   - Might work from server-side Worker context

## Recommended: Option D
Worker calls Snowflake SQL REST API directly via G2 proxy (block-data extension).
We already proved this works. The switch to query-expert was for the client-side app,
but the Worker runs server-side and can use fetch() with X-G2-Extension.

## app.yaml Changes
```yaml
permissions:
  connections:
    - query-expert
    - slack
    - block-data
  extensions:
    query-expert:
      access: read
    slack:
      access: read_write
    block-data:
      access: read
```

## New Files Needed
- src/server/cron.ts — Cron handler (runs every 1 min)
- src/server/slack.ts — Slack read/write via G2 proxy
- src/server/snowflake.ts — Snowflake queries via block-data proxy
- src/server/llm.ts — LLM SQL generation via G2 proxy
- src/server/triage.ts — Main triage logic (port from Python)
- migrations/0001_processed_threads.sql — D1 table for dedup

## Migration Steps
1. Add slack + block-data to app.yaml connections
2. Create D1 migration for processed_threads table
3. Port slack_listener.py logic to TypeScript
4. Add cron trigger to wrangler config
5. Test locally with `npm run dev`
6. Deploy to production
7. Verify it answers questions
8. Kill the Python listener

## Schema Context
Port SCHEMA_CONTEXT string from slack_listener.py as-is.
The LLM prompt is the same — just the transport changes.
