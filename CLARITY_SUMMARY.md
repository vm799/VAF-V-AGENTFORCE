# V AgentForce — Clarity Summary

**Date:** March 22, 2026
**Status:** Architecture reviewed, confusion points identified, cleanup executed

---

## What V AgentForce Is

A **personal AI operating system** — not a chatbot. An always-on system that:

1. **Ingests** anything you send it (URL, bank statement, brain dump, voice note)
2. **Routes** to the right specialist agent (one of 10 domain experts)
3. **Enriches** using Claude Haiku (title, summary, insights, revenue angle, signal rating)
4. **Persists** to SQLite + Obsidian vault
5. **Surfaces** via React dashboard, Telegram bot, and daily briefings

You own the data. Everything stays local (Obsidian vault is on your desktop). The system is designed for you.

---

## The 10 Agents (No Confusion — Clean List)

| # | Code | Domain | Job |
|---|---|---|---|
| 00 | **SENTINEL** | Command / router | Squad commander — captures every thought, routes to right agent |
| 01 | **FORGE** | Engineering / code | VP Engineering — builds products, ships code, reviews architecture |
| 02 | **AMPLIFY** | Content / brand | Content lead — writes, edits, grows audience across all channels |
| 03 | **PHOENIX** | Finance | Personal CFO — bank statements, budgeting, wealth strategy |
| 04 | **VITALITY** | Health | Health coach — nutrition, fitness, sleep, energy optimization |
| 05 | **CIPHER** | Learning / signal | Intelligence decoder — cuts noise, extracts signal, rates importance |
| 06 | **AEGIS** | AI security | Security architect — framework, OWASP, prompt injection, compliance |
| 07 | **NEXUS** | Agentic future | Market gaps — A2A, MCP, agent protocols, what's coming next |
| 08 | **ATLAS** | Career | Career strategist — salary, promotion, positioning, business strategy |
| 09 | **COLOSSUS** | Code review | Principal engineer — brutal code review, architecture critique |

---

## How to Use It — 3 Methods

### 1. Telegram Bot (Easiest for Mobile)
Just paste content:
- A URL → CIPHER fetches & analyzes
- "£50 groceries at Tesco" → PHOENIX logs
- A LinkedIn article → AMPLIFY analyzes for content
- "Just did 45 min workout" → VITALITY logs
- Brain dump → SENTINEL catches

### 2. iOS Shortcut
Set up per `scripts/ios_shortcut_setup.md`
Share webpage → auto-enriched → saved

### 3. Dashboard
Visit `localhost:8077` → Quick-save panel

---

## URL/Content Workflow

Drop a URL anywhere (Telegram, iOS, dashboard):

```
1. CIPHER fetches the page (up to 500KB)
2. Extracts clean text (strips ads, navigation, footer)
3. For YouTube: automatically pulls transcript
4. Sends to Claude Haiku with agent's SKILL.md context
5. Returns: title, summary, insights[], revenue_angle, signal_rating (🟢/🟡/🔴)
6. Saved to SQLite + written to Obsidian vault (~/Desktop/SecondBrain/)
7. Visible on dashboard within seconds
```

---

## Starting the System

**Quick start (dev mode — foreground):**
```bash
cd "/Users/mcmehmios/V AgentForce/vaishali-agent-force"
./vaf.sh quick                # Start API + Telegram bot
open http://localhost:8077    # Dashboard
```

**Production (always-on via macOS LaunchAgents):**
```bash
./scripts/install_autostart.sh    # First time only — installs 4 LaunchAgents
./vaf.sh start                    # Start all services
./vaf.sh status                   # Check health
```

**Available commands:**
```bash
./vaf.sh quick         # Start foreground (dev)
./vaf.sh briefing      # Run morning briefing now
./vaf.sh evening       # Run evening debrief now
./vaf.sh logs          # Tail all logs
./vaf.sh build         # Rebuild React frontend
./vaf.sh tunnel        # Cloudflare tunnel for remote access
./vaf.sh status        # Check system status
```

---

## What Was Confusing (Now Fixed)

### ❌ Before: 16 Agent Files
- 10 new agent definitions (SENTINEL, FORGE, AMPLIFY, etc.)
- 6 orphaned old definitions (LIBRARIAN, BUILDS_ARCHITECT, etc.) — never used

**✅ After:** 6 old files archived to `_archive/` directory
**Result:** Exactly 10 clean agent files, no dead code

### ❌ Before: Two "insight_engine" & "insights" Modules
- Both with similar names doing related-but-different jobs
- Confusion about which does what

**✅ After:** Renamed `insight_engine/` → `daily_briefing/`
**Result:** Clear distinction:
- `daily_briefing/` = morning/evening pipeline summaries
- `insights/` = weekly intelligence panel on dashboard

### ❌ Before: Duplicate Files
- `knowledge-graph-preview.html` at repo root AND inside `vaishali-agent-force/`

**✅ After:** Deleted the duplicate
**Result:** One source of truth

### ❌ Before: 16 Vite Cache Files Cluttering Frontend
- `vite.config.ts.timestamp-*.mjs` files

**✅ After:** Deleted all 16 + added `.gitignore` rule
**Result:** No future cache clutter

---

## Two-Layer Architecture (Now Clear)

### Layer 1: Context (`V-AgentForce-Project/`)
- `CLAUDE.md` — master AI system prompt
- `agents/` — 10 SKILL.md files (agent personas loaded at runtime)
- `WHO_I_AM.md`, `GOALS_2026.md` — personal context
- Not code. Pure AI configuration.

### Layer 2: Execution (`vaishali-agent-force/`)
- `src/vaishali/` — Python package (orchestrator, agents, pipelines)
- `frontend/src/` — React dashboard
- `scripts/` — CLI runners (morning brief, ingestion, etc.)
- `macos/` — LaunchAgent plist files for autostart
- The actual running system.

---

## Critical Paths

| Purpose | Location |
|---|---|
| **Routing brain** | `src/vaishali/orchestrator.py` |
| **URL fetcher** | `src/vaishali/cipher/url_processor.py` |
| **Capture storage** | `src/vaishali/captures/store.py` |
| **Daily briefing** | `src/vaishali/daily_briefing/engine.py` |
| **Weekly insights** | `src/vaishali/insights/engine.py` |
| **API server** | `src/vaishali/dashboard/api.py` |
| **Telegram bot** | `src/vaishali/telegram_bot/bot.py` |
| **Agent personas** | `V-AgentForce-Project/agents/00_SENTINEL.md` ... `09_COLOSSUS.md` |
| **System prompt** | `V-AgentForce-Project/CLAUDE.md` |

---

## Verification — Everything Works

✅ 10 clean agent definitions (no orphans)
✅ `daily_briefing/` renamed with all imports updated
✅ Duplicate files deleted
✅ Vite cache files cleaned + `.gitignore` added
✅ All changes committed (git log shows cleanup commit)
✅ Repository is ready to use

---

## Next Steps (Optional Cleanup)

These are nice-to-haves, not blockers:

1. **Rename `vaishali-agent-force/agents/` → `personas/`** — distinguishes from agent SKILL.md files
2. **Update `VAF-Build-Roadmap-2026.md`** — it describes Vanilla HTML/JS but code is React 18
3. **Remove `.claude/worktrees/charming-hawking/`** when you finish that branch — use `git worktree remove`

---

## Quick Start Right Now

```bash
cd "/Users/mcmehmios/V AgentForce/vaishali-agent-force"

# Check everything is working
./vaf.sh status

# Start the system (foreground)
./vaf.sh quick

# Open dashboard in browser
open http://localhost:8077

# In Telegram: drop a URL or text → watch it auto-route and enrich
```

**That's it. You now have a complete understanding of what you've built and how to use it.**

---

## For Next Session

A complete architecture guide has been saved to your memory system at:
`~/.claude/projects/-Users-mcmehmios-V-AgentForce/memory/vagenforce_architecture.md`

This includes:
- 10-agent canonical list
- Data flow diagram
- Critical files reference
- How to use it
- Recent cleanup summary

No need to re-explain the system. I have full clarity.
