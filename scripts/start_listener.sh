#!/bin/bash
# Auto-restarting LGX-OPS-BOT listener
# Restarts automatically if it crashes or Mac wakes from sleep
# Run: ~/Desktop/Automation/lgx-ops-bot/scripts/start_listener.sh

cd ~/Desktop/Automation/lgx-ops-bot

while true; do
    echo "[$(date)] Starting LGX-OPS-BOT listener..."
    caffeinate -si python3 -u scripts/slack_listener.py 2>&1 | tee -a /tmp/lgx-ops-bot-listener.log
    echo "[$(date)] Listener stopped. Restarting in 10 seconds..."
    sleep 10
done
