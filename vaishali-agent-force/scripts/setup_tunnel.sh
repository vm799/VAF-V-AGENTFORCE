#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# setup_tunnel.sh — Interactive tunnel setup for Vaishali Agent Force
#
# Configures remote dashboard access via:
#   1. Cloudflare Tunnel (primary, free, permanent)
#   2. ngrok (fallback, quick temporary)
#
# Usage:
#   ./scripts/setup_tunnel.sh
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${BLUE}🌐 Vaishali Agent Force — Tunnel Setup${NC}\n"

# ── Step 1: Check for cloudflared ──────────────────────────────────

if command -v cloudflared &>/dev/null; then
    echo -e "${GREEN}✓${NC} cloudflared found at: $(command -v cloudflared)"
    echo ""

    # Check if already authenticated
    if [ -f "$HOME/.cloudflared/cert.pem" ]; then
        echo -e "${GREEN}✓${NC} Cloudflare credentials found"
    else
        echo -e "${YELLOW}⚠${NC}  Not authenticated with Cloudflare yet."
        echo "   Run: cloudflared tunnel login"
        read -p "   Press Enter once you've authenticated, or Ctrl+C to cancel."
        echo ""
    fi

    # Check if tunnel exists
    if cloudflared tunnel list | grep -q "vaishali-agentforce"; then
        echo -e "${GREEN}✓${NC} Tunnel 'vaishali-agentforce' already exists"
    else
        echo -e "${YELLOW}⚠${NC}  Creating new tunnel 'vaishali-agentforce'..."
        cloudflared tunnel create vaishali-agentforce
        echo ""
    fi

    # Ensure config.yml exists
    mkdir -p "$HOME/.cloudflared"
    CONFIG_FILE="$HOME/.cloudflared/config.yml"

    if [ -f "$CONFIG_FILE" ]; then
        if grep -q "vaishali-agentforce" "$CONFIG_FILE"; then
            echo -e "${GREEN}✓${NC} config.yml already configured"
        else
            echo -e "${YELLOW}⚠${NC}  Updating config.yml with tunnel config..."
            # Append to existing config
            cat >> "$CONFIG_FILE" <<'EOF'

tunnel: vaishali-agentforce
credentials-file: /Users/$USER/.cloudflared/vaishali-agentforce.json

ingress:
  - hostname: vaishali.example.com
    service: http://localhost:3000
  - service: http_status:404
EOF
        fi
    else
        echo -e "📝 Creating $CONFIG_FILE..."
        mkdir -p "$(dirname "$CONFIG_FILE")"
        cat > "$CONFIG_FILE" <<EOF
tunnel: vaishali-agentforce
credentials-file: $HOME/.cloudflared/vaishali-agentforce.json

ingress:
  - hostname: vaishali.example.com
    service: http://localhost:3000
  - service: http_status:404
EOF
    fi

    # Create LaunchAgent plist for auto-start
    LAUNCHD_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$LAUNCHD_DIR/com.vaishali.agentforce.tunnel.plist"

    mkdir -p "$LAUNCHD_DIR"

    if [ -f "$PLIST_FILE" ]; then
        echo -e "${GREEN}✓${NC} LaunchAgent already configured"
    else
        echo -e "📝 Creating LaunchAgent for auto-start on login..."
        cat > "$PLIST_FILE" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vaishali.agentforce.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/cloudflared</string>
        <string>tunnel</string>
        <string>run</string>
        <string>vaishali-agentforce</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/cloudflared-tunnel.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/cloudflared-tunnel.out</string>
</dict>
</plist>
EOF
        chmod 644 "$PLIST_FILE"
    fi

    echo ""
    echo -e "${GREEN}✅ Cloudflare Tunnel configured!${NC}"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Test the tunnel: cloudflared tunnel run vaishali-agentforce"
    echo "   2. Or auto-start on login: launchctl load $PLIST_FILE"
    echo "   3. Get the URL: cloudflared tunnel info vaishali-agentforce"
    echo "   4. Add to .env: VAF_TUNNEL_URL=<your-url>"
    echo "   5. Then use /webdash in Telegram to see the URL"
    echo ""

else
    # Cloudflared not installed — try ngrok
    echo -e "${YELLOW}⚠${NC}  cloudflared not found."
    echo ""
    echo "To install Cloudflare Tunnel (recommended):"
    echo "  ${BLUE}brew install cloudflared${NC}"
    echo ""

    if command -v ngrok &>/dev/null; then
        echo -e "${GREEN}✓${NC} ngrok found at: $(command -v ngrok)"
        echo ""
        echo "📝 To use ngrok:"
        echo "   1. Run: ngrok http 3000"
        echo "   2. Copy the public URL from the ngrok window"
        echo "   3. Add to .env: VAF_TUNNEL_URL=<ngrok-url>"
        echo "   4. Or let ngrok auto-detect it via: ./vaf.sh tunnel"
        echo ""
    else
        echo "To install ngrok as a fallback:"
        echo "  ${BLUE}brew install ngrok${NC}"
        echo ""
    fi

    read -p "Install cloudflared now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        brew install cloudflared
        # Recursively call ourselves
        exec "$0"
    else
        echo "Setup cancelled."
        exit 1
    fi
fi

echo -e "${GREEN}Done!${NC}\n"
