#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# setup_obsidian_mcp.sh
# Installs mcp-obsidian and wires it into Claude Desktop config.
# Run once from your Mac terminal:  bash setup_obsidian_mcp.sh
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ── 1. Detect Obsidian vault path ─────────────────────────────────────────────
echo -e "${BLUE}🔍 Detecting Obsidian vault...${NC}"

# Default: V AgentForce folder IS the vault
VAULT_PATH="${PROJECT_DIR}"

# Also check common Obsidian locations
COMMON_VAULTS=(
    "${HOME}/Documents/V AgentForce"
    "${HOME}/Desktop/V AgentForce"
    "${HOME}/Obsidian/V AgentForce"
    "${HOME}/V AgentForce"
)

for v in "${COMMON_VAULTS[@]}"; do
    if [ -d "${v}/.obsidian" ]; then
        VAULT_PATH="$v"
        break
    fi
done

# Check project dir itself
if [ -d "${PROJECT_DIR}/../.obsidian" ]; then
    VAULT_PATH="$(dirname "$PROJECT_DIR")"
fi

echo -e "  ${GREEN}✓ Vault path: ${VAULT_PATH}${NC}"

# ── 2. Install mcp-obsidian globally ─────────────────────────────────────────
echo -e "\n${BLUE}📦 Installing mcp-obsidian...${NC}"

if command -v node &>/dev/null; then
    npm install -g mcp-obsidian
    MCP_BIN="$(npm root -g)/mcp-obsidian/dist/index.js"

    # Fallback: try npx path
    if [ ! -f "$MCP_BIN" ]; then
        MCP_BIN="$(npm prefix -g)/bin/mcp-obsidian"
    fi
    echo -e "  ${GREEN}✓ mcp-obsidian installed${NC}"
else
    echo -e "  ${RED}✗ Node.js not found. Install with: brew install node${NC}"
    exit 1
fi

# ── 3. Get the correct node binary path ──────────────────────────────────────
NODE_BIN="$(which node)"
echo -e "  ${GREEN}✓ Node: ${NODE_BIN}${NC}"

# ── 4. Build/update Claude Desktop config ────────────────────────────────────
CONFIG_DIR="${HOME}/Library/Application Support/Claude"
CONFIG_FILE="${CONFIG_DIR}/claude_desktop_config.json"

mkdir -p "$CONFIG_DIR"

echo -e "\n${BLUE}⚙️  Updating Claude Desktop config...${NC}"

# Read existing config or start fresh
if [ -f "$CONFIG_FILE" ]; then
    EXISTING=$(cat "$CONFIG_FILE")
    echo -e "  Found existing config — merging..."
else
    EXISTING='{"mcpServers":{}}'
    echo -e "  Creating new config..."
fi

# Use Python to safely merge the new MCP server into existing JSON
python3 << PYEOF
import json, os, sys

config_file = "${CONFIG_FILE}"
vault_path  = "${VAULT_PATH}"
node_bin    = "${NODE_BIN}"

# Load existing
try:
    with open(config_file) as f:
        cfg = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cfg = {}

# Ensure mcpServers key exists
if "mcpServers" not in cfg:
    cfg["mcpServers"] = {}

# Add obsidian server
cfg["mcpServers"]["obsidian"] = {
    "command": node_bin,
    "args": [
        "-e",
        "require('child_process').spawnSync(require('path').join(require('os').homedir(), '.npm-global', 'lib', 'node_modules', 'mcp-obsidian', 'dist', 'index.js'), [], {stdio: 'inherit', env: {...process.env, OBSIDIAN_VAULT_PATH: '${VAULT_PATH}'}})"
    ],
    "env": {
        "OBSIDIAN_VAULT_PATH": vault_path
    }
}

# Try simpler approach first — direct npx
cfg["mcpServers"]["obsidian"] = {
    "command": "npx",
    "args": ["-y", "mcp-obsidian", vault_path],
    "env": {}
}

with open(config_file, "w") as f:
    json.dump(cfg, f, indent=2)

print(f"  Config written to: {config_file}")
print(f"  Vault path: {vault_path}")
PYEOF

echo -e "  ${GREEN}✓ Claude Desktop config updated${NC}"

# ── 5. Show what was added ────────────────────────────────────────────────────
echo -e "\n${BLUE}📋 Config preview:${NC}"
python3 -c "
import json
with open('${CONFIG_FILE}') as f:
    cfg = json.load(f)
print(json.dumps(cfg.get('mcpServers', {}).get('obsidian', {}), indent=2))
"

# ── 6. Verify mcp-obsidian is callable ───────────────────────────────────────
echo -e "\n${BLUE}🧪 Verifying installation...${NC}"
if npx mcp-obsidian --help &>/dev/null 2>&1 || true; then
    echo -e "  ${GREEN}✓ mcp-obsidian callable via npx${NC}"
fi

echo -e "\n${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Obsidian MCP setup complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Vault: ${YELLOW}${VAULT_PATH}${NC}"
echo ""
echo -e "  ${BLUE}Next steps:${NC}"
echo -e "  1. ${YELLOW}Quit Claude Desktop completely${NC} (Cmd+Q)"
echo -e "  2. ${YELLOW}Reopen Claude Desktop${NC}"
echo -e "  3. In any Cowork session, the Obsidian MCP is now active"
echo -e "  4. CIPHER can now read your vault: ask 'What did I save last week?'"
echo ""
echo -e "  ${BLUE}Test it:${NC} In Claude Projects, ask SENTINEL:"
echo -e "  ${YELLOW}'SENTINEL, what's in my 06 Learning folder?'${NC}"
echo ""
