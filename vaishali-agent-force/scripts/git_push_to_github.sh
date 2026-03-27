#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# git_push_to_github.sh
# Initial commit + push of V AgentForce to GitHub.
# Run from your Mac terminal — do NOT run from Claude VM.
#
# Usage:
#   cd "/path/to/V AgentForce"
#   bash vaishali-agent-force/scripts/git_push_to_github.sh
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
echo -e "${BLUE}📁 Repository root: ${REPO_DIR}${NC}"
cd "$REPO_DIR"

# ── 1. Clear stale lock if it exists ─────────────────────────────────────────
if [ -f ".git/index.lock" ]; then
    echo -e "${YELLOW}🔓 Removing stale git lock...${NC}"
    rm -f .git/index.lock
    echo -e "  ${GREEN}✓ Lock removed${NC}"
fi

# ── 2. Git config ─────────────────────────────────────────────────────────────
echo -e "\n${BLUE}⚙️  Configuring git...${NC}"
git config user.email "vaishalimehmi@yahoo.co.uk"
git config user.name "V Mehmi"
echo -e "  ${GREEN}✓ Identity set${NC}"

# ── 3. Set remote ─────────────────────────────────────────────────────────────
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/vm799/VAF-V-AGENTFORCE.git
echo -e "  ${GREEN}✓ Remote: https://github.com/vm799/VAF-V-AGENTFORCE.git${NC}"

# ── 4. Stage everything (respecting .gitignore) ───────────────────────────────
echo -e "\n${BLUE}📦 Staging files...${NC}"
git add -A

# Safety: remove any .env files that may have slipped through
git rm --cached vaishali-agent-force/.env 2>/dev/null || true
git rm --cached .env 2>/dev/null || true
git rm --cached "**/.env" 2>/dev/null || true

# Show what's being committed
echo -e "\n${BLUE}📋 Files to be committed:${NC}"
git status --short | head -60
TOTAL=$(git status --short | wc -l | tr -d ' ')
echo -e "\n  Total: ${YELLOW}${TOTAL} files${NC}"

# ── 5. Confirm .env is NOT staged ────────────────────────────────────────────
if git diff --cached --name-only | grep -q "\.env$"; then
    echo -e "\n${RED}🚨 ABORT: .env file is staged. This contains API keys.${NC}"
    echo -e "${RED}   Run: git rm --cached vaishali-agent-force/.env${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓ .env confirmed NOT staged${NC}"

# ── 6. Initial commit ─────────────────────────────────────────────────────────
echo -e "\n${BLUE}💾 Creating initial commit...${NC}"

git commit -m "$(cat <<'EOF'
feat: V AgentForce v1.0 — 10-agent AI operating system

Complete production build of V AgentForce — a personal AI command centre
for finance, health, content, learning, security, and agentic intelligence.

## Squad (10 agents)
SENTINEL · FORGE · AMPLIFY · PHOENIX · VITALITY · CIPHER
AEGIS · NEXUS · ATLAS (career) · COLOSSUS (technical review)

## Core Systems
- FastAPI backend with 20+ endpoints
- React/TypeScript dashboard with live panels
- SQLite persistence (finance, health, education, braindumps, captures, checkins)
- Telegram bot (/brief /checkin /nonneg /save /captures)
- Obsidian vault auto-sync via filesystem writes
- Captures system: auto-routes drops to correct agent
- Goggins Protocol: 5 non-negotiables daily accountability tracker

## Intelligence Pipeline
- Morning briefing: PHOENIX + VITALITY + CIPHER + AMPLIFY → SENTINEL
- Evening synthesis with Obsidian sync
- Knowledge graph (D3.js force layout)
- Insight engine with cross-agent pattern detection

## Architecture
- DeerFlow-validated patterns (ByteDance, 22.7k ⭐)
- Skills-as-Markdown agent definitions
- Local-first data (SQLite, no cloud DB)
- macOS LaunchAgents for 07:00 auto-run
- LangGraph orchestration planned: Sprint 2

## Roadmap
See V-AgentForce-Project/VAF-Build-Roadmap-2026.md
See V-AgentForce-Project/DeerFlow-Analysis-VAF-Upgrade.md

Built by Vaishali Mehmi — March 2026
EOF
)"

echo -e "  ${GREEN}✓ Commit created${NC}"

# ── 7. Push to GitHub ─────────────────────────────────────────────────────────
echo -e "\n${BLUE}🚀 Pushing to GitHub...${NC}"
echo -e "  ${YELLOW}You may be prompted for GitHub credentials.${NC}"
echo -e "  ${YELLOW}Use a Personal Access Token (PAT) as your password.${NC}"
echo -e "  ${YELLOW}Create one at: https://github.com/settings/tokens${NC}\n"

git push -u origin main

echo -e "\n${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ V AgentForce pushed to GitHub!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "\n  ${BLUE}Repo: https://github.com/vm799/VAF-V-AGENTFORCE${NC}"
echo -e "\n  Next steps:"
echo -e "  1. Add a README.md to the repo root"
echo -e "  2. Add repo description + topics on GitHub"
echo -e "  3. Star it and share the link on LinkedIn"
echo -e "  4. This is now your portfolio piece — it's real, it's deployed\n"
