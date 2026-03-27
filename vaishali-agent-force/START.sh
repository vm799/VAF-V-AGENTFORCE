#!/bin/bash
# START.sh — Simple startup for VAF (bypasses broken vaf.sh)
# Run this: bash START.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python3"

echo "🚀 Starting Vaishali Agent Force..."
echo ""

# Check if venv exists
if [ ! -d "${PROJECT_DIR}/.venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv .venv"
    exit 1
fi

# Check if Python exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python not found in venv!"
    echo "   Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "✅ Using Python: $PYTHON"
echo ""

# Make sure we're in the project directory
cd "$PROJECT_DIR"

# Export environment
export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH:-}"

echo "📊 Starting Dashboard (port 8000)..."
$PYTHON -m vaishali.dashboard.api > /tmp/vaf_dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "   PID: $DASHBOARD_PID"
sleep 2

echo ""
echo "💬 Starting Telegram Bot..."
$PYTHON -m vaishali.telegram_bot.run > /tmp/vaf_telegram.log 2>&1 &
TELEGRAM_PID=$!
echo "   PID: $TELEGRAM_PID"
sleep 2

echo ""
echo "📁 Starting File Watcher..."
$PYTHON scripts/watch_folders.py > /tmp/vaf_watcher.log 2>&1 &
WATCHER_PID=$!
echo "   PID: $WATCHER_PID"
sleep 1

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ VAF IS RUNNING"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboard:        http://localhost:8000"
echo "💬 Telegram Bot:     Running (listening for /save commands)"
echo "📁 File Watcher:     Monitoring data/ folders"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Open: http://localhost:8000"
echo "   2. Send Telegram: /save \"Testing the golden thread\""
echo "   3. Check Obsidian vault: ~/Documents/VAF-Vault/"
echo ""
echo "📋 Logs:"
echo "   Dashboard:  tail -f /tmp/vaf_dashboard.log"
echo "   Telegram:   tail -f /tmp/vaf_telegram.log"
echo "   Watcher:    tail -f /tmp/vaf_watcher.log"
echo ""
echo "🛑 To stop: Press Ctrl+C (will stop all services)"
echo ""

# Keep services running and handle Ctrl+C
trap "kill $DASHBOARD_PID $TELEGRAM_PID $WATCHER_PID 2>/dev/null; echo ''; echo '🛑 Services stopped'; exit 0" INT

# Wait for any service to fail
wait
