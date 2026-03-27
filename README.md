# V AgentForce (VAF)

**A personal AI operating system + enterprise data intelligence platform.**
Built with Claude Code. Obsidian as long-term memory. Building in public.

---

## Two Systems, One Architecture

### Personal OS — How I run my life
10 specialist agents activate inside Claude Code based on keywords. Finance, content, health, code, security, learning, strategy — each domain has a dedicated workflow. Claude reads my Obsidian vault via MCP. Every session ends by crystallising insights back to the vault.

### Enterprise Pipeline — How organisations make decisions faster
9 Python modules transforming raw data into actionable intelligence. One command runs all 9. A dashboard auto-generates. Insights route to Slack/Teams/Telegram.

```
Ingestion → Sanitisation → Identity → RAG → Self-Evolving
     → Council (4 agents) → Compliance → Synthesis → Output
```

---

## Quick Start

```bash
# Personal system
cp .env.example .env   # add Telegram token + Obsidian path
./start.sh             # dashboard at localhost:3000

# Enterprise demo
cd enterprise && ./demo.sh   # runs all 9 builds + opens dashboard

# Claude session
claude .
/prime                 # loads context + top 3 priorities
/extract-learnings     # crystallise session to Obsidian
```

---

## Structure

```
v-agentforce-architecture/
├── CLAUDE.md           ← Router: triggers agents and skills (60 lines)
├── agents/             ← 10 specialist agent definitions
├── skills/             ← 8 procedural skill files
├── context/            ← Goals, financial snapshot, Goggins protocol
├── enterprise/         ← 9-build pipeline + orchestrator + demo docs
├── personal/           ← Telegram bot, morning briefing, LaunchAgents
├── mcp/                ← MCP server: Claude ↔ Obsidian
├── dashboard/          ← DAILY_START.html personal dashboard
└── docs/               ← Loom scripts, consulting materials
```

---

## The 10 Agents

| Agent | Trigger words | Domain |
|-------|--------------|--------|
| SENTINEL | Brain dump, overwhelm, "where do I start" | Orchestration |
| FORGE | Build, ship, code, deploy | Engineering |
| AMPLIFY | Post, content, LinkedIn, Substack | Content |
| PHOENIX | Money, spending, salary, runway | Finance |
| VITALITY | Food, sleep, gym, run | Health |
| CIPHER | Research, learn, study, insight | Learning |
| AEGIS | Security, compliance, framework, risk | Security |
| NEXUS | Agent, MCP, pipeline, automation | Future-building |
| ATLAS | Career, rate, consulting, clients | Career |
| COLOSSUS | Code review, "is this good" | Quality |

---

## The 9 Enterprise Builds

| Build | Purpose |
|-------|---------|
| 01 Ingestion | Pull data from Obsidian/Confluence/SharePoint |
| 02 Sanitisation | Clean, deduplicate, standardise |
| 03 Identity | Enrich with context and relationships |
| 04 RAG | Index + queryable answers with citations |
| 05 Self-Evolving | Improves from each run |
| 06 Council | 4 AI agents deliberate in parallel |
| 07 Compliance | FCA, GDPR, custom rule checking |
| 08 Synthesis | Write the brief your C-suite can act on |
| 09 Output | Slack, Teams, Telegram, dashboard |

---

## The Goggins Protocol

5 non-negotiables scored daily (50 pts max):

| # | Category | What |
|---|----------|------|
| 1 | BODY | 5x5 physical activity |
| 2 | BUILD | Ship 1 thing |
| 3 | LEARN | 1 lesson + extract insight |
| 4 | AMPLIFY | 1 content piece created |
| 5 | BRIEF | Morning + evening check-in |

---

## Building in Public

📺 [Loom series](docs/loom-scripts/) — 12 videos: overview, 10 agent deep dives, enterprise demo
✍️ Substack essays — architecture decisions every Tuesday
💼 LinkedIn — weekly updates on what shipped

---

## Consulting

Building this for organisations that want data intelligence infrastructure.

- Assessment (map your flows → blueprint): £5K–£10K
- Pilot (3 builds, 1 data source): £15K–£25K
- Full deployment (all 9 + training): £40K–£80K

DM on LinkedIn.

---

Built with Claude Code | All data stays local | Open source
