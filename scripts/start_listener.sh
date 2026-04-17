#!/bin/bash
# Start the LGX-OPS-BOT Slack listener locally
# Loads secrets from .env.local, runs with caffeinate to prevent sleep

cd "$(dirname "$0")/.." || exit 1

# Load local secrets
if [ -f .env.local ]; then
    export $(grep -v '^#' .env.local | xargs)
    echo "✅ Loaded secrets from .env.local"
else
    echo "❌ .env.local not found — create it with SLACK_BOT_TOKEN=xoxb-..."
    exit 1
fi

echo "Starting LGX-OPS-BOT listener..."
caffeinate -s python3 -u scripts/slack_listener.py > /tmp/lgx-ops-bot-listener.log 2>&1 &
sleep 3
echo "✅ Listener started (PID: $!)"
echo "📋 Log: tail -f /tmp/lgx-ops-bot-listener.log"
tail -10 /tmp/lgx-ops-bot-listener.log
