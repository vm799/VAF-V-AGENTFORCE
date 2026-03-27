#!/bin/bash
# VAF Start — dev mode (no LaunchAgents required)
# Runs dashboard server + Telegram bot in background
# Usage: ./start.sh

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

echo "🚀 Starting VAF..."

# Dashboard server
if lsof -i :3000 > /dev/null 2>&1; then
    echo "  ✅ Dashboard already running at http://localhost:3000/DAILY_START.html"
else
    cd "$ROOT/dashboard" && python3 -m http.server 3000 > "$LOG_DIR/dashboard.log" 2>&1 &
    echo "  ✅ Dashboard started → http://localhost:3000/DAILY_START.html"
fi

# Telegram bot (only if token is set)
if [ -f "$ROOT/.env" ] && grep -q "VAF_TELEGRAM_TOKEN=" "$ROOT/.env"; then
    TELEGRAM_PID=$(pgrep -f "bot.py" 2>/dev/null)
    if [ -n "$TELEGRAM_PID" ]; then
        echo "  ✅ Telegram bot already running (PID $TELEGRAM_PID)"
    else
        cd "$ROOT" && python3 personal/telegram-relay/bot.py > "$LOG_DIR/telegram.log" 2>&1 &
        echo "  ✅ Telegram bot started"
    fi
else
    echo "  ⚠️  Telegram bot skipped (add VAF_TELEGRAM_TOKEN to .env to enable)"
fi

echo ""
echo "VAF running."
echo "  Dashboard: http://localhost:3000/DAILY_START.html"
echo "  Stop: ./stop.sh"
