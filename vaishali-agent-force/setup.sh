#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Vaishali Agent Force — One-command setup for macOS
#
# Usage:
#   chmod +x setup.sh && ./setup.sh
#
# What it does:
#   1. Creates Python virtual environment
#   2. Installs Python dependencies
#   3. Installs Telegram bot dependency
#   4. Builds the React frontend
#   5. Seeds example data
#   6. Runs initial morning briefing
#   7. Installs macOS LaunchAgents (dashboard + briefings)
#   8. Optionally configures Telegram bot
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
LOGS_DIR="${PROJECT_DIR}/logs"

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[VAF]${NC} $*"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🦉🦊🐱🐼  Vaishali Agent Force — Setup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── 0. Find Python 3.10+ ──────────────────────────────────────────

SYSTEM_PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
        if [ "$ver" -ge 10 ]; then
            SYSTEM_PYTHON="$(command -v "$candidate")"
            break
        fi
    fi
done

if [ -z "$SYSTEM_PYTHON" ]; then
    echo -e "${RED}[ERROR]${NC} Python 3.10+ is required but not found."
    echo ""
    echo "  Your system Python is too old ($(python3 --version 2>/dev/null || echo 'not found'))."
    echo ""
    echo "  Fix: Install Python 3.11 via Homebrew:"
    echo "    brew install python@3.11"
    echo ""
    echo "  Then re-run this script."
    exit 1
fi

ok "Found $($SYSTEM_PYTHON --version) at $SYSTEM_PYTHON"

# ── 1. Python venv ─────────────────────────────────────────────────

if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment..."
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
    ok "Virtual environment created"
else
    ok "Virtual environment exists"
fi

PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

# ── 2. Install Python deps ────────────────────────────────────────

info "Installing Python dependencies..."
"$PIP" install --quiet --upgrade pip
"$PIP" install --quiet -e "${PROJECT_DIR}[dev]"
ok "Python dependencies installed"

# ── 3. Install Telegram bot dependency ─────────────────────────────

info "Installing Telegram bot library..."
"$PIP" install --quiet 'python-telegram-bot[job-queue]>=20.0'
ok "Telegram bot library installed"

# ── 4. Build React frontend ───────────────────────────────────────

info "Building React frontend..."
cd "${PROJECT_DIR}/frontend"

if [ ! -d "node_modules" ]; then
    npm install --silent 2>/dev/null
fi

npx vite build --outDir dist 2>/dev/null
ok "Frontend built → frontend/dist/"
cd "$PROJECT_DIR"

# ── 5. Create log + data directories ──────────────────────────────

mkdir -p "$LOGS_DIR"
"$PYTHON" -c "
import sys; sys.path.insert(0, 'src')
from vaishali.core.config import settings
settings.ensure_dirs()
print('Directories created')
"
ok "Data directories initialised"

# ── 6. Seed example data ──────────────────────────────────────────

info "Seeding example data..."
PYTHONPATH="${PROJECT_DIR}/src" "$PYTHON" "${PROJECT_DIR}/scripts/dev_seed_example_data.py" 2>/dev/null || true
ok "Example data seeded"

# ── 7. Run initial morning briefing ───────────────────────────────

info "Running initial morning briefing..."
PYTHONPATH="${PROJECT_DIR}/src" "$PYTHON" "${PROJECT_DIR}/scripts/run_morning_briefing.py" --skip-education 2>/dev/null || true
ok "Initial briefing generated"

# ── 8. Install LaunchAgents ───────────────────────────────────────

info "Installing macOS LaunchAgents..."
mkdir -p "$LAUNCH_AGENTS_DIR"

install_plist() {
    local src="$1"
    local name=$(basename "$src")
    local dest="${LAUNCH_AGENTS_DIR}/${name}"

    # Replace placeholders
    sed \
        -e "s|__VAF_PYTHON__|${PYTHON}|g" \
        -e "s|__VAF_PROJECT__|${PROJECT_DIR}|g" \
        "$src" > "$dest"

    # Unload if already loaded, then load
    launchctl unload "$dest" 2>/dev/null || true
    launchctl load "$dest"
    ok "Installed: ${name}"
}

# Dashboard (always-on)
install_plist "${PROJECT_DIR}/macos/com.vaishali.agentforce.dashboard.plist"

# Morning + Evening briefings
install_plist "${PROJECT_DIR}/macos/com.vaishali.agentforce.morning.plist"
install_plist "${PROJECT_DIR}/macos/com.vaishali.agentforce.evening.plist"

echo ""
ok "Dashboard running at: http://localhost:8077"
ok "Morning briefing scheduled: 07:00 daily"
ok "Evening briefing scheduled: 21:00 daily"

# ── 9. Telegram bot setup (optional) ─────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  📱 Telegram Bot Setup (Optional)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "To get briefings on your phone:"
echo ""
echo "  1. Open Telegram → search @BotFather → /newbot"
echo "  2. Name it 'Vaishali Agent Force' (or anything you like)"
echo "  3. Copy the token BotFather gives you"
echo ""

read -p "Enter Telegram bot token (or press Enter to skip): " TELEGRAM_TOKEN

if [ -n "$TELEGRAM_TOKEN" ]; then
    # Save to .env file
    cat > "${PROJECT_DIR}/.env" << EOF
VAF_TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
VAF_TELEGRAM_CHAT_ID=
EOF

    echo ""
    info "Token saved to .env"
    info "Now starting the bot — send /start to your bot on Telegram"
    info "to get your chat_id, then update .env and re-run setup."
    echo ""

    # Install Telegram LaunchAgent (without chat_id for now)
    local_plist="${LAUNCH_AGENTS_DIR}/com.vaishali.agentforce.telegram.plist"
    sed \
        -e "s|__VAF_PYTHON__|${PYTHON}|g" \
        -e "s|__VAF_PROJECT__|${PROJECT_DIR}|g" \
        -e "s|__TELEGRAM_TOKEN__|${TELEGRAM_TOKEN}|g" \
        -e "s|__TELEGRAM_CHAT_ID__||g" \
        "${PROJECT_DIR}/macos/com.vaishali.agentforce.telegram.plist" > "$local_plist"

    launchctl unload "$local_plist" 2>/dev/null || true
    launchctl load "$local_plist"
    ok "Telegram bot running!"
    echo ""
    echo "  Next steps:"
    echo "  1. Open Telegram → find your bot → send /start"
    echo "  2. Copy the chat_id it shows"
    echo "  3. Edit .env → set VAF_TELEGRAM_CHAT_ID=<your-id>"
    echo "  4. Run: ./setup.sh  (to reload with scheduled pushes)"
else
    warn "Telegram setup skipped — you can run setup.sh again later"
fi

# ── Done ──────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Setup complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  🖥  Dashboard:  http://localhost:8077"
echo "  🌅 Morning:    07:00 daily (auto)"
echo "  🌙 Evening:    21:00 daily (auto)"
echo "  📱 Telegram:   /briefing /status /finance /health"
echo ""
echo "  Quick commands:"
echo "    ./vaf.sh start     # Start all services"
echo "    ./vaf.sh stop      # Stop all services"
echo "    ./vaf.sh status    # Check what's running"
echo "    ./vaf.sh briefing  # Run briefing now"
echo ""
