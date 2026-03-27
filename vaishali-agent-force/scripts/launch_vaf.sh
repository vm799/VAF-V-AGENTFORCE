#!/usr/bin/env bash
# launch_vaf.sh — Auto-start script called by LaunchAgent on login.
# Also called manually: bash scripts/launch_vaf.sh

set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

# Load .env
if [ -f "$DIR/.env" ]; then
    set -a; source "$DIR/.env"; set +a
fi

PYTHON="$DIR/.venv/bin/python"
PORT="${VAF_API_PORT:-8077}"
export PYTHONPATH="$DIR/src"

echo "[$(date)] VAF auto-starting..." >> "$LOG_DIR/launch.log"

# Kill any existing VAF processes cleanly
pkill -f "vaishali.dashboard.api" 2>/dev/null || true
pkill -f "vaishali.telegram_bot.run" 2>/dev/null || true
sleep 1

# Start dashboard API in background
"$PYTHON" -m vaishali.dashboard.api >> "$LOG_DIR/dashboard.log" 2>&1 &
echo $! > "$DIR/.vaf_dashboard.pid"
echo "[$(date)] Dashboard started (PID $!)" >> "$LOG_DIR/launch.log"

# Wait for API to be ready (up to 10s)
for i in $(seq 1 10); do
    if curl -s --max-time 1 "http://localhost:$PORT/api/status" > /dev/null 2>&1; then
        echo "[$(date)] Dashboard API ready on port $PORT" >> "$LOG_DIR/launch.log"
        break
    fi
    sleep 1
done

# Start Telegram bot in background
"$PYTHON" -m vaishali.telegram_bot.run >> "$LOG_DIR/bot.log" 2>&1 &
echo $! > "$DIR/.vaf_bot.pid"
echo "[$(date)] Bot started (PID $!)" >> "$LOG_DIR/launch.log"

# Open dashboard in browser (only if DISPLAY/GUI is available, i.e. on login)
if [ "${VAF_OPEN_BROWSER:-1}" = "1" ]; then
    sleep 2
    open "http://localhost:$PORT" 2>/dev/null || true
fi

echo "[$(date)] VAF fully started." >> "$LOG_DIR/launch.log"
