#!/usr/bin/env bash
# install_autostart.sh — Install VAF as a macOS LaunchAgent.
# Runs once: bash scripts/install_autostart.sh
# After that, VAF starts automatically on every login.

set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST="$PLIST_DIR/com.vaishaliagentforce.plist"
LAUNCH_SCRIPT="$DIR/scripts/launch_vaf.sh"

chmod +x "$LAUNCH_SCRIPT"
mkdir -p "$PLIST_DIR"
mkdir -p "$DIR/logs"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vaishaliagentforce</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${LAUNCH_SCRIPT}</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>StandardOutPath</key>
    <string>${DIR}/logs/launchagent.log</string>

    <key>StandardErrorPath</key>
    <string>${DIR}/logs/launchagent.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>
</dict>
</plist>
PLIST

# Load it immediately (no need to log out)
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo ""
echo "✅ VAF LaunchAgent installed!"
echo ""
echo "   • Starts automatically on every login"
echo "   • Starting right now..."
echo ""

# Start immediately
bash "$LAUNCH_SCRIPT"

echo ""
echo "   • Dashboard: http://localhost:${VAF_API_PORT:-8077}"
echo "   • Logs: $DIR/logs/"
echo "   • To uninstall: launchctl unload $PLIST && rm $PLIST"
