# VAF Build Roadmap 2026
> FORGE + SENTINEL — March 2026

---

## The Mission

Ship V AgentForce v1.0 MVP as a **working, deployed, portfolio-quality** AI operating system. This is both V's personal intelligence layer AND the proof of capability that drives corporate workshops and teaching income.

**North Star:** Every component built becomes a teaching asset. Build it → document it → teach it → charge for it.

---

## Sprint 1 — Foundation (Weeks 1–2)
*Goal: Working pipeline from statements → dashboard*

- [ ] Scaffold project structure (`src/`, `data/`, `skills/`, `reports/`, `docs/`)
- [ ] PHOENIX agent: parse First Direct CSV → SQLite ledger → `reports/finance/daily/YYYY-MM-DD.md`
- [ ] VITALITY agent: Apple Health CSV → `data/summaries/health/YYYY-MM-DD.json`
- [ ] SENTINEL basic: combine summaries → daily briefing Markdown
- [ ] Minimal dashboard: 4 agent panels + hero briefing line
- [ ] macOS LaunchAgent: 07:00 morning trigger
- [ ] `.env` + `.gitignore` + README in place before first commit

**Definition of Done:** Drop a CSV statement → run pipeline → see result in dashboard

---

## Sprint 2 — Orchestration Upgrade (Weeks 3–4)
*Goal: Parallel pipeline + remaining agents*

- [ ] Replace sequential pipeline with **LangGraph parallel fan-out** (ADR-001)
- [ ] CIPHER: RSS + YouTube ingest → Obsidian note output
- [ ] AMPLIFY: content backlog management + 3–5 daily ideas
- [ ] Voice briefing: `POST /api/speak` → macOS `say` command
- [ ] Knowledge graph: D3.js force layout in dashboard
- [ ] Multi-bank support: Barclays + Amex + HSBC + Santander parsers

---

## Sprint 3 — Polish & Publish (Weeks 5–8)
*Goal: Production-quality + public portfolio*

- [ ] Telegram bot: `/brief`, `/checkin`, `/save` commands
- [ ] Obsidian auto-sync: agent outputs written to vault paths
- [ ] Open-source MCP server: UK banking data (FCA Register + Companies House)
- [ ] Write LinkedIn article: "I Built My Own AI Operating System"
- [ ] GitHub README with architecture diagram + demo
- [ ] Corporate workshop deck using VAF as the case study

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Parallel agents, checkpointing, DeerFlow-validated |
| Backend API | FastAPI (Python async) | V's primary language, production-ready |
| Frontend | Vanilla HTML/CSS/JS | No build tooling, easy to iterate, localhost |
| Database | SQLite | Local-first, finance data stays on Mac |
| AI | Claude API (Sonnet) | Best reasoning + tool use |
| Skills | Markdown SKILL.md | DeerFlow pattern, human-readable |
| Voice | macOS say | Zero dependency |
| Storage | Obsidian-compatible MD | Knowledge graph, no vendor lock-in |

---

## ADRs (Architecture Decision Records)
See full document: [[VAF-Architecture-Decision-Record]]

Key decisions:
1. LangGraph for orchestration (parallel, stateful, resilient)
2. Local-first data storage (SQLite + CSV, no cloud DB in v1)
3. Skills-as-Markdown (DeerFlow pattern)
4. Vanilla HTML/JS dashboard (not React)
5. Claude API primary (not OpenAI)

---

## Revenue Milestones

| Milestone | When | Revenue Signal |
|---|---|---|
| VAF MVP shipped | Sprint 1 complete | Portfolio piece live |
| MCP server open-sourced | Sprint 3 | GitHub audience + DeerFlow community |
| LinkedIn article published | Sprint 3 | Inbound corporate enquiries |
| First workshop booked | Q3 2026 | £5,000–10,000 |
| VAF becomes the course | Q3/Q4 2026 | £997–1,997/student |

---

## Links
- DeerFlow Analysis: [[DeerFlow-Analysis-VAF-Upgrade]]
- Project Requirements: [[VAF-Project-Requirements]]
- ADR Document: (see `/docs/VAF_Architecture_Decision_Record.docx` in repo)

---

## Tags
#vaf #builds #forge #sentinel #architecture #roadmap #sprint
#status/active #actionable #high-priority

## Vault Path
`V AgentForce/Builds/Vaishali Agent Force/VAF-Build-Roadmap-2026.md`
