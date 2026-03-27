#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# deploy_sprint0.sh — Activate Sprint 0 Golden Thread
# Run this from your Mac terminal inside vaishali-agent-force/
# ──────────────────────────────────────────────────────────────
set -euo pipefail

BOLD='\033[1m'
GOLD='\033[38;5;178m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GOLD}${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "${GOLD}${BOLD}  VAF Sprint 0 — Golden Thread Deployment${NC}"
echo -e "${GOLD}${BOLD}═══════════════════════════════════════════════${NC}"
echo ""

# ── Step 1: Clean old dist files ──────────────────────────────
echo -e "${BOLD}[1/5] Cleaning stale frontend build artifacts...${NC}"
cd frontend/dist/assets 2>/dev/null && {
    # Keep only the current build asset
    ls *.js | grep -v "index-M4-1mVkr.js" | xargs rm -f 2>/dev/null || true
    cd ../../..
    echo -e "${GREEN}  ✅ Old build artifacts cleaned${NC}"
} || echo -e "${GOLD}  ⚠ No dist/assets to clean (will be created on first build)${NC}"

# ── Step 2: Set API key ──────────────────────────────────────
echo -e "\n${BOLD}[2/5] Checking API key for iOS Shortcut...${NC}"
if [ -f .env ]; then
    if grep -q "VAF_CAPTURE_API_KEY" .env; then
        echo -e "${GREEN}  ✅ API key already set in .env${NC}"
    else
        API_KEY=$(openssl rand -hex 24)
        echo "VAF_CAPTURE_API_KEY=${API_KEY}" >> .env
        echo -e "${GREEN}  ✅ Generated API key: ${API_KEY}${NC}"
        echo -e "${GOLD}  → Use this key in your iOS Shortcut Bearer token${NC}"
    fi
else
    API_KEY=$(openssl rand -hex 24)
    echo "VAF_CAPTURE_API_KEY=${API_KEY}" > .env
    echo -e "${GREEN}  ✅ Created .env with API key: ${API_KEY}${NC}"
    echo -e "${GOLD}  → Use this key in your iOS Shortcut Bearer token${NC}"
fi

# ── Step 3: Git commit + push ────────────────────────────────
echo -e "\n${BOLD}[3/5] Git commit & push...${NC}"
git add -A
git status --short
echo ""
read -p "  Commit and push these changes? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "Sprint 0: Golden Thread — orchestrator, CIPHER, insights engine, dashboard v2

- Orchestrator: LLM enrichment with agent SKILL.md context
- CIPHER URL processor: HTML extraction + YouTube transcripts
- Captures store: enrichment columns, signal ratings, must-act queue
- InsightsEngine: weekly themes, cross-agent connections, content ideas
- Dashboard API v0.2: auth, /capture, /insights/weekly endpoints
- Telegram: /save (enriched), /quick (fast), /weekly (brief)
- CapturesPanel v2: intelligence feed with signal filters
- WeeklyInsightsPanel: themes, connections, Goggins protocol
- iOS Shortcut setup guide + deployment scripts"
    git push origin main
    echo -e "${GREEN}  ✅ Pushed to GitHub${NC}"
else
    echo -e "${GOLD}  ⚠ Skipped git push${NC}"
fi

# ── Step 4: Obsidian MCP check ───────────────────────────────
echo -e "\n${BOLD}[4/5] Obsidian vault check...${NC}"
VAULT_PATH="${HOME}/Documents/VAF-Vault"
if [ -d "$VAULT_PATH" ]; then
    echo -e "${GREEN}  ✅ Vault exists at ${VAULT_PATH}${NC}"
    # Ensure agent directories exist
    for agent in SENTINEL FORGE AMPLIFY PHOENIX VITALITY CIPHER AEGIS NEXUS ATLAS COLOSSUS; do
        mkdir -p "${VAULT_PATH}/${agent}"
    done
    echo -e "${GREEN}  ✅ All 10 agent directories ready${NC}"
else
    echo -e "${GOLD}  ⚠ Vault not found at ${VAULT_PATH}${NC}"
    echo -e "${GOLD}  → Run: bash scripts/setup_obsidian_mcp.sh${NC}"
fi

# ── Step 5: Restart services ─────────────────────────────────
echo -e "\n${BOLD}[5/5] Restarting VAF services...${NC}"
if [ -f "./vaf.sh" ]; then
    ./vaf.sh restart
    echo -e "${GREEN}  ✅ Services restarted${NC}"
else
    echo -e "${GOLD}  ⚠ vaf.sh not found — start services manually${NC}"
fi

echo -e "\n${GOLD}${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "${GOLD}${BOLD}  🏆 Sprint 0 Golden Thread — DEPLOYED${NC}"
echo -e "${GOLD}${BOLD}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Golden Thread Flow:${NC}"
echo -e "  Claude Mobile → /save → Orchestrator → Obsidian → Dashboard"
echo ""
echo -e "  ${BOLD}Test it:${NC}"
echo -e "  1. Telegram: ${GREEN}/save Check out this AI paper on transformers${NC}"
echo -e "  2. Dashboard: ${GREEN}http://localhost:8000${NC}"
echo -e "  3. Weekly:    ${GREEN}/weekly${NC}"
echo ""
