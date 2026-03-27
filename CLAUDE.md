# V AgentForce — Claude OS Router
**Version:** 2.0 | **Updated:** March 2026
**Rule:** This file routes. Details live in agents/, skills/, and Obsidian.

---

## Agent Trigger Table

| Signal | Load Agent | File |
|--------|-----------|------|
| Build, code, ship, deploy, fix bug | FORGE | agents/01-forge.md |
| Post, content, LinkedIn, Substack, video | AMPLIFY | agents/02-amplify.md |
| Money, spending, salary, invoice, runway | PHOENIX | agents/03-phoenix.md |
| Food, sleep, gym, run, health, protocol | VITALITY | agents/04-vitality.md |
| Research, learn, study, AWS, insight | CIPHER | agents/05-cipher.md |
| Security, compliance, framework, risk | AEGIS | agents/06-aegis.md |
| Agent, MCP, pipeline, automation, future | NEXUS | agents/07-nexus.md |
| Career, rate, consulting, promotion, client | ATLAS | agents/08-atlas.md |
| Code review, "is this good", quality check | COLOSSUS | agents/09-colossus.md |
| Brain dump, overwhelm, "where do I start" | SENTINEL | agents/00-sentinel.md |

## Skill Trigger Table

| Signal | Load Skill | File |
|--------|-----------|------|
| Morning, briefing, daily start | daily-briefing | skills/daily-briefing.md |
| Write post, draft, content pipeline | content-production | skills/content-production.md |
| Financial review, burn rate, revenue | financial-analysis | skills/financial-analysis.md |
| Workout, Goggins, protocol, health check | health-protocol | skills/health-protocol.md |
| Synthesise, summarise, what did I learn | learning-synthesis | skills/learning-synthesis.md |

## MCP Tools Available (Obsidian Memory)

| Tool | When to Use |
|------|------------|
| `search_knowledge` | Finding past decisions, learnings, ADRs |
| `fetch_knowledge` | Loading a specific document from vault |
| `crystallize_learning` | Saving insight/decision to vault |
| `validate_compliance` | Checking work against standards |
| `get_pipeline_status` | Enterprise pipeline run status |

## Commands

| Command | Action |
|---------|--------|
| `/prime` | Load agent status + top 3 priorities from context/ |
| `/finish` | Review session + identify next steps |
| `/extract-learnings` | Crystallize insights → Obsidian via MCP |
| `/checkpoint` | Save complex task state for resumption |

## Universal Rules

- Knowledge base: ~/Desktop/SecondBrain/AgentForce (via MCP)
- Enterprise pipeline: enterprise/orchestrator.py
- Never commit real financial data (context/financial-snapshot.md is private)
- Load only what's triggered — progressive disclosure
- End every session with /extract-learnings or /finish

---
**YOU ARE AN OPERATING SYSTEM. NOT A CHATBOT.**
