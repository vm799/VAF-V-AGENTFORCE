#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# vaf.sh — Daily driver CLI for Vaishali Agent Force
#
# Usage:
#   ./vaf.sh start       Start dashboard + telegram bot
#   ./vaf.sh stop        Stop all services
#   ./vaf.sh restart     Restart all services
#   ./vaf.sh status      Show running services
#   ./vaf.sh briefing    Run morning briefing now
#   ./vaf.sh evening     Run evening briefing now
#   ./vaf.sh dashboard   Open dashboard in browser
#   ./vaf.sh logs        Tail all logs
#   ./vaf.sh seed        Re-seed example data
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
PORT=8077

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AGENTS=(
    "com.vaishali.agentforce.dashboard"
    "com.vaishali.agentforce.morning"
    "com.vaishali.agentforce.evening"
    "com.vaishali.agentforce.telegram"
)

case "${1:-help}" in

  start)
    echo -e "${BLUE}🚀 Starting Agent Force...${NC}"
    for agent in "${AGENTS[@]}"; do
        plist="${LAUNCH_AGENTS_DIR}/${agent}.plist"
        if [ -f "$plist" ]; then
            launchctl load "$plist" 2>/dev/null || true
            echo -e "  ${GREEN}✓${NC} ${agent}"
        fi
    done
    sleep 1
    echo -e "\n${GREEN}Dashboard: http://localhost:${PORT}${NC}"
    ;;

  stop)
    echo -e "${YELLOW}🛑 Stopping Agent Force...${NC}"
    for agent in "${AGENTS[@]}"; do
        plist="${LAUNCH_AGENTS_DIR}/${agent}.plist"
        if [ -f "$plist" ]; then
            launchctl unload "$plist" 2>/dev/null || true
            echo -e "  ${RED}■${NC} ${agent}"
        fi
    done
    ;;

  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;

  status)
    echo -e "${BLUE}📊 Service Status${NC}\n"
    for agent in "${AGENTS[@]}"; do
        if launchctl list | grep -q "$agent" 2>/dev/null; then
            echo -e "  ${GREEN}● running${NC}  ${agent}"
        else
            echo -e "  ${RED}○ stopped${NC}  ${agent}"
        fi
    done
    echo ""
    # Check if dashboard is responding
    if curl -s "http://localhost:${PORT}/status" > /dev/null 2>&1; then
        echo -e "  ${GREEN}🖥  Dashboard: http://localhost:${PORT}${NC}"
    else
        echo -e "  ${RED}🖥  Dashboard: not responding${NC}"
    fi
    ;;

  briefing)
    echo -e "${BLUE}🌅 Running morning briefing...${NC}"
    PYTHONPATH="${PROJECT_DIR}/src" "$PYTHON" "${PROJECT_DIR}/scripts/run_morning_briefing.py"
    echo -e "\n${GREEN}✓ Briefing complete${NC}"
    ;;

  evening)
    echo -e "${BLUE}🌙 Running evening briefing...${NC}"
    PYTHONPATH="${PROJECT_DIR}/src" "$PYTHON" "${PROJECT_DIR}/scripts/run_evening_briefing.py"
    echo -e "\n${GREEN}✓ Evening update complete${NC}"
    ;;

  dashboard)
    open "http://localhost:${PORT}"
    ;;

  logs)
    echo -e "${BLUE}📋 Tailing logs (Ctrl+C to stop)${NC}\n"
    tail -f "${PROJECT_DIR}/logs/"*.log "${PROJECT_DIR}/logs/"*.err 2>/dev/null || echo "No logs found — run setup.sh first"
    ;;

  seed)
    echo -e "${BLUE}🌱 Seeding example data...${NC}"
    PYTHONPATH="${PROJECT_DIR}/src" "$PYTHON" "${PROJECT_DIR}/scripts/dev_seed_example_data.py"
    echo -e "${GREEN}✓ Data seeded${NC}"
    ;;

  bot)
    echo -e "${BLUE}🤖 Starting Telegram bot...${NC}"
    echo -e "   Press Ctrl+C to stop\n"
    cd "${PROJECT_DIR}" && PYTHONPATH="${PROJECT_DIR}/src" "$PYTHON" -m vaishali.telegram_bot.run
    ;;

  build)
    echo -e "${BLUE}🔨 Rebuilding frontend...${NC}"
    cd "${PROJECT_DIR}/frontend" && npx vite build --outDir dist
    echo -e "${GREEN}✓ Frontend built${NC}"
    ;;

  quick)
    # Start dashboard API + Telegram bot together in foreground
    # Perfect for development or when LaunchAgents aren't set up yet
    echo -e "${BLUE}🚀 Quick-starting Agent Force (foreground)...${NC}"
    echo -e "   Dashboard: http://localhost:${PORT}"
    echo -e "   Press Ctrl+C to stop both\n"

    # Load .env vars
    if [ -f "${PROJECT_DIR}/.env" ]; then
        set -a
        # shellcheck disable=SC1091
        . "${PROJECT_DIR}/.env"
        set +a
    fi

    export PYTHONPATH="${PROJECT_DIR}/src"

    # Start dashboard in background, bot in foreground
    "$PYTHON" -m vaishali.dashboard.api &
    DASH_PID=$!
    trap "kill $DASH_PID 2>/dev/null; exit" INT TERM

    "$PYTHON" -m vaishali.telegram_bot.run
    kill $DASH_PID 2>/dev/null
    ;;

  tunnel)
    # Quick tunnel — no account/cert/domain needed. Points at the API port.
    TUNNEL_PORT="${VAF_API_PORT:-${PORT}}"
    TUNNEL_URL_FILE="${PROJECT_DIR}/.tunnel_url"
    echo -e "${BLUE}🌐 Starting Cloudflare Quick Tunnel → http://localhost:${TUNNEL_PORT}${NC}"
    echo -e "   No account needed — URL appears below in ~5 seconds."
    echo -e "   ${BLUE}Press Ctrl+C to stop${NC}\n"

    # Clean up saved URL on exit
    trap "rm -f '${TUNNEL_URL_FILE}'; echo ''; echo -e '  ${YELLOW}Tunnel stopped, URL cleared.${NC}'" INT TERM

    if command -v cloudflared &>/dev/null; then
        # Pipe output through awk to capture the trycloudflare.com URL and save it
        cloudflared tunnel --url "http://localhost:${TUNNEL_PORT}" 2>&1 | \
        awk -v url_file="${TUNNEL_URL_FILE}" -v green="${GREEN}" -v nc="${NC}" '
        {
            print $0
            if (/trycloudflare\.com/) {
                match($0, /https:\/\/[a-z0-9-]+\.trycloudflare\.com/)
                if (RSTART > 0) {
                    url = substr($0, RSTART, RLENGTH)
                    print url > url_file
                    close(url_file)
                    print "\n  " green "✓ URL saved — use /webdash in Telegram to open on your phone" nc "\n"
                }
            }
        }'
        rm -f "${TUNNEL_URL_FILE}"
    elif command -v ngrok &>/dev/null; then
        echo -e "   ${YELLOW}cloudflared not found, using ngrok (fallback)${NC}"
        ngrok http "${TUNNEL_PORT}"
    else
        echo -e "   ${RED}✗ cloudflared not found${NC}\n"
        echo "   Install it with:"
        echo "     ${YELLOW}brew install cloudflared${NC}"
        echo ""
        echo "   Then run:  ${YELLOW}./vaf.sh tunnel${NC}"
        exit 1
    fi
    ;;

  setup)
    echo -e "${BLUE}🔧 Installing / updating Python dependencies...${NC}"
    "${PROJECT_DIR}/.venv/bin/pip" install --quiet --upgrade pip
    "${PROJECT_DIR}/.venv/bin/pip" install --quiet -e "${PROJECT_DIR}[dev]" 2>/dev/null || \
      "${PROJECT_DIR}/.venv/bin/pip" install --quiet -e "${PROJECT_DIR}"
    echo -e "${GREEN}✓ Python deps installed${NC}"

    echo -e "\n${BLUE}🎭 Installing Playwright + Chromium (for NotebookLM automation)...${NC}"
    "${PROJECT_DIR}/.venv/bin/pip" install --quiet playwright
    "${PROJECT_DIR}/.venv/bin/playwright" install chromium
    echo -e "${GREEN}✓ Playwright ready${NC}"

    echo -e "\n${BLUE}📦 Installing frontend dependencies...${NC}"
    cd "${PROJECT_DIR}/frontend" && npm install --silent
    echo -e "${GREEN}✓ npm deps ready${NC}"

    echo -e "\n${GREEN}🎉 Setup complete — run ./vaf.sh quick to start${NC}"
    ;;

  help|*)
    echo ""
    echo "  🦉🦊🐱🐼🧠  Vaishali Agent Force"
    echo ""
    echo "  Usage: ./vaf.sh <command>"
    echo ""
    echo "  Commands:"
    echo "    setup      Install/update all dependencies (Python + Playwright + npm)"
    echo "    start      Start all services (dashboard, telegram, schedulers)"
    echo "    stop       Stop all services"
    echo "    restart    Restart all services"
    echo "    status     Show running services"
    echo "    bot        Run Telegram bot (reads token from .env)"
    echo "    briefing   Run morning briefing now"
    echo "    evening    Run evening briefing now"
    echo "    dashboard  Open dashboard in browser"
    echo "    logs       Tail all service logs"
    echo "    seed       Re-seed example data"
    echo "    build      Rebuild React frontend"
    echo "    quick      Start dashboard + bot in foreground (no LaunchAgents)"
    echo "    tunnel     Start Cloudflare quick tunnel (no account needed, auto-saves URL)"
    echo ""
    ;;

esac
