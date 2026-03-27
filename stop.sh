#!/bin/bash
# VAF Stop
pkill -f "http.server 3000" 2>/dev/null && echo "Dashboard stopped" || echo "Dashboard was not running"
pkill -f "bot.py" 2>/dev/null && echo "Telegram bot stopped" || echo "Telegram bot was not running"
