# V AgentForce — Quick Start Guide

Everything you need to start using your system immediately.

---

## 30-Second Overview

You built a personal AI operating system with 10 specialist agents. Feed it URLs, bank statements, or brain dumps → it auto-routes, enriches with Claude, and saves to your Obsidian vault. You run it locally. You own the data.

---

## Start Right Now (2 minutes)

```bash
cd "/Users/mcmehmios/V AgentForce/vaishali-agent-force"

# Start the system
./vaf.sh quick

# Open dashboard
open http://localhost:8077
```

**Dashboard running:** http://localhost:8077
**Telegram bot:** Connected (if TELEGRAM_TOKEN is set in `.env`)

---

## Feed It Content (Pick Any Method)

### Method 1: Telegram (Easiest)
Open your Telegram bot chat and:
- Paste a URL → CIPHER analyzes it
- Type "£50 groceries" → PHOENIX logs it
- Share a brain dump → SENTINEL organizes it
- Drop a GitHub link → FORGE reviews it

### Method 2: iOS Shortcut
From any webpage:
1. Share button → "Add to VAF" → Done
(First-time setup: see `scripts/ios_shortcut_setup.md`)

### Method 3: Dashboard
Visit http://localhost:8077 → Click "Quick-save" → Paste anything

---

## What Happens When You Feed It Something

```
You paste a URL
    ↓
System detects which agent should handle it (CIPHER, FORGE, PHOENIX, etc.)
    ↓
CIPHER fetches the page + extracts clean text
    ↓
Claude enriches it: title, summary, insights, signal rating (🟢/🟡/🔴)
    ↓
Saved to: SQLite + Obsidian vault (~/Desktop/SecondBrain)
    ↓
Visible on dashboard within seconds
```

---

## The 10 Agents at a Glance

| When to Use | Agent | What It Does |
|---|---|---|
| Bank statement, spending, money | **PHOENIX** | Finance analysis + budgeting |
| Code, GitHub, build idea | **FORGE** | Engineering + architecture review |
| LinkedIn article, content, audience | **AMPLIFY** | Content strategy + writing |
| Workout, sleep, health data | **VITALITY** | Health + energy optimization |
| AI research, news, insight | **CIPHER** | Signal detection + learning |
| Security, vulnerability, framework | **AEGIS** | AI security + compliance |
| A2A, MCP, agentic, market gap | **NEXUS** | Future-focused architecture |
| Salary, promotion, career | **ATLAS** | Career strategy + negotiation |
| "Review my code" | **COLOSSUS** | Code review + critique |
| Brain dump, "help me think" | **SENTINEL** | Command center + organization |

---

## Essential Commands

```bash
# Status check
./vaf.sh status

# Run manually
./vaf.sh quick         # Start (foreground)
./vaf.sh briefing      # Morning briefing
./vaf.sh evening       # Evening debrief
./vaf.sh logs          # See logs

# Frontend
./vaf.sh build         # Rebuild React

# Production (always-on)
./scripts/install_autostart.sh    # First-time install
./vaf.sh start                    # Start all 4 services
./vaf.sh stop                     # Stop everything
./vaf.sh status                   # Check health

# Remote access
./vaf.sh tunnel        # Cloudflare tunnel (then /webdash in Telegram)
```

---

## How to Make URLs Work

For the system to fetch and analyze URLs:

1. **In `.env` file** (`vaishali-agent-force/.env`):
   - Add Claude API key: `ANTHROPIC_API_KEY=sk-ant-...`
   - (Or use one of 5 key slots: `VAF_ANTHROPIC_KEY_1=...`, etc.)

2. **Telegram bot needs:**
   - `VAF_TELEGRAM_TOKEN=...`
   - `VAF_TELEGRAM_CHAT_ID=...`

3. **Google AI (optional fallback):**
   - `VAF_GOOGLE_AI_KEY=...`

If you have a Telegram token already set, just add the Anthropic key and you're done.

---

## File Locations You'll Need

| What | Where |
|---|---|
| **Configuration** | `vaishali-agent-force/.env` |
| **Secrets** | Same `.env` file (not committed) |
| **Database** | `vaishali-agent-force/data/captures.db` |
| **Daily briefings** | `vaishali-agent-force/data/briefings/` |
| **Obsidian vault** | `~/Desktop/SecondBrain/` (or wherever you set `VAF_OBSIDIAN_VAULT_DIR`) |
| **Agent definitions** | `V-AgentForce-Project/agents/00_SENTINEL.md` ... `09_COLOSSUS.md` |
| **System prompt** | `V-AgentForce-Project/CLAUDE.md` |

---

## Dashboard Panels (What You'll See)

- **Hero Card** — Today's key number (usually money or streak)
- **Finance Panel** — Bank balance, spending, anomalies
- **Content Panel** — Content backlog + ideas
- **Health Panel** — Workout, sleep, energy scores
- **Education Panel** — Learning summary + new insights
- **Insights Panel** — Weekly intelligence brief
- **Activity Feed** — Recent captures + enrichments
- **Knowledge Graph** — Visual map of connected ideas
- **Goggins Non-Negotiables** — Daily check-in scores (BODY, BUILD, LEARN, AMPLIFY, BRIEF)

---

## Troubleshooting

**Dashboard won't load?**
```bash
./vaf.sh status        # Check if API is running
./vaf.sh quick         # Restart in foreground
```

**Telegram not responding?**
- Check `.env` has `VAF_TELEGRAM_TOKEN` and `VAF_TELEGRAM_CHAT_ID`
- Restart: `./vaf.sh stop && ./vaf.sh start`

**URLs not enriching?**
- Check `.env` has `ANTHROPIC_API_KEY` or `VAF_ANTHROPIC_KEY_1`
- Check logs: `./vaf.sh logs`

**Need help?**
- See full architecture guide: `CLARITY_SUMMARY.md`
- See complete memory: `~/.claude/projects/-Users-mcmehmios-V-AgentForce/memory/`

---

## That's It

You now have:
- ✅ Running system (or ready to start)
- ✅ 10 specialist agents ready to work
- ✅ 3 ways to feed it content
- ✅ Complete Obsidian integration
- ✅ Daily + weekly briefing pipelines
- ✅ React dashboard on localhost:8077
- ✅ Telegram bot for mobile access

**Everything is local. Everything is yours. No external dependency beyond Claude API.**

Next: Go start it with `./vaf.sh quick` and feed it something.
