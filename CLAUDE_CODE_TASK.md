# Task: Add DM Listener + Learning Commands to LGX-OPS-BOT

## Context
`scripts/slack_listener.py` is a Python Slack bot that polls channels every 10 seconds, queries Snowflake for logistics data, and posts answers. It currently only watches channels the bot is a member of (via `users.conversations` API).

We want to add:
1. **DM listener** — the bot responds to direct messages the same way it responds in channels
2. **Learning commands** — admin (dsteffy, user ID U04RK34LMFG) can teach the bot new facts, corrections, and rules via DM

## Phase 1: DM Listener

### How it works
- The `discover_channels()` function already calls `users.conversations` with `types='public_channel,private_channel'`
- Add `'im'` to the types parameter: `types='public_channel,private_channel,im'`
- DMs will appear as channels with `is_im: true` — process them the same way
- DM messages won't have `subtype: bot_message` so they'll be processed normally
- No oscar_cc or disclaimer in DM responses (use DEFAULT_CHANNEL_CONFIG)

### Key detail
- The bot token is in `LGX_BOT_TOKEN` (env var `SLACK_BOT_TOKEN`)
- Bot user ID is `BOT_USER_ID = "U0ASVFR7NMB"`
- Messages from the bot itself should be ignored (check user == BOT_USER_ID)
- DMs don't have threads the same way — respond in the conversation directly

## Phase 2: Learning Commands

### Admin user
- Only `U04RK34LMFG` (dsteffy) can use learning commands
- If anyone else tries, respond: "Learning commands are admin-only. Ask @dsteffy to add this."

### Commands (detected by prefix in DM messages)

1. **`remember: <fact>`**
   - Stores the fact to `shared/learned_facts.json`
   - Each fact has: `id` (auto-increment), `fact` (text), `added_at` (ISO timestamp), `added_by` (user ID)
   - Respond: "✅ Got it — I'll remember that. (fact #N)"

2. **`correct: <topic> → <correction>`**
   - Stores as a fact with `type: "correction"` 
   - Respond: "✅ Correction noted for '<topic>'. I'll use this going forward."

3. **`forget: <N>` or `forget: <search text>`**
   - By number: removes fact #N
   - By text: removes first fact containing that text
   - Respond: "✅ Forgot: '<fact text>'"

4. **`show memory`**
   - Lists all stored facts with their IDs
   - Format: `#1 [2026-04-17] <fact text>`

5. **`clear memory`**
   - Removes ALL learned facts (with confirmation — respond "Are you sure? Reply 'yes' to confirm")

### Storage
- File: `shared/learned_facts.json`
- Format: `{"facts": [{"id": 1, "fact": "...", "type": "fact|correction", "added_at": "...", "added_by": "..."}]}`
- Load at startup into a global `LEARNED_FACTS` variable
- Reload from disk after any write

### Injection into LLM calls
- In `generate_sql_llm()` — append learned facts to the system prompt after SCHEMA_CONTEXT
- In `answer_process_question()` — append learned facts after the KB context
- In the triage handler — append learned facts after the playbook
- Format: `\n\nLEARNED FACTS (from team feedback):\n- fact 1\n- fact 2\n...`
- Only inject if there are facts to inject

## Files to modify
- `scripts/slack_listener.py` — all changes go here
- `shared/learned_facts.json` — new file, created on first `remember:` command

## Testing
After making changes, verify:
```bash
python3 -c "import ast; ast.parse(open('scripts/slack_listener.py').read()); print('OK')"
```

## Don't change
- The Snowflake connection logic
- The Databricks LLM endpoint
- The channel polling logic (just extend it to include IMs)
- The existing process/data question routing
