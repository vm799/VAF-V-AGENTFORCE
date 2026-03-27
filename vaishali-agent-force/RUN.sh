#!/bin/bash
# RUN.sh — Simple startup (handles spaces in paths)

set -e

cd "$(dirname "$0")" || exit 1

PYTHON="./.venv/bin/python3"

if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

echo "🚀 Starting Vaishali Agent Force..."
echo ""

export PYTHONPATH="./src:${PYTHONPATH:-}"

echo "📊 Dashboard..."
"$PYTHON" -m vaishali.dashboard.api > /tmp/vaf_dashboard.log 2>&1 &

echo "💬 Telegram Bot..."
"$PYTHON" -m vaishali.telegram_bot.run > /tmp/vaf_telegram.log 2>&1 &

echo "📁 File Watcher..."
"$PYTHON" scripts/watch_folders.py > /tmp/vaf_watcher.log 2>&1 &

sleep 2

echo ""
echo "✅ VAF RUNNING"
echo "   Dashboard: http://localhost:8000"
echo "   Telegram:  Ready"
echo "   Watcher:   Ready"
echo ""
echo "📋 Logs:"
echo "   tail -f /tmp/vaf_dashboard.log"
echo "   tail -f /tmp/vaf_telegram.log"
echo ""
echo "Press Ctrl+C to stop"
echo ""

wait
