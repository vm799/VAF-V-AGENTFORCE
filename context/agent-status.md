# Agent Status Board

Last updated: 2026-03-27

---

## Status Key
- **Ready**: Fully defined, skills loaded, can be activated immediately
- **Building**: Agent definition in progress, partially operational
- **Blocked**: Missing dependency, waiting on external input, or broken

---

## Agent Roster

| # | Agent | Status | Last Activated | Current Task | Notes |
|---|-------|--------|----------------|--------------|-------|
| 1 | **Architect** | Building | — | VAF system design, infrastructure planning | Core orchestration agent |
| 2 | **Builder** | Building | — | Code production, feature shipping, deployments | Needs MCP server access |
| 3 | **Analyst** | Building | — | Financial reviews, data analysis, projections | Depends on financial-snapshot data |
| 4 | **Writer** | Building | — | LinkedIn posts, Substack essays, copywriting | Content-production skill loaded |
| 5 | **Researcher** | Building | — | AWS study, learning synthesis, knowledge capture | Learning-synthesis skill loaded |
| 6 | **Coach** | Building | — | Goggins protocol, health tracking, accountability | Health-protocol skill loaded |
| 7 | **Strategist** | Building | — | Goal setting, quarterly planning, prioritization | Needs current-goals context |
| 8 | **Networker** | Building | — | Outreach, community engagement, lead generation | LinkedIn + community focus |
| 9 | **Operator** | Building | — | Daily briefing, routine automation, system maintenance | Daily-briefing skill loaded |
| 10 | **Reviewer** | Building | — | Code review, content editing, quality assurance | Cross-cuts all other agents |

---

## Activation Log

| Date | Agent | Task | Duration | Outcome | Score |
|------|-------|------|----------|---------|-------|
| — | — | — | — | — | — |

---

## Dependency Map

```
Operator (daily briefing)
  └── reads: current-goals, goggins-nonneg, agent-status
  └── activates: any agent based on priorities

Architect → Builder (designs flow to implementation)
Researcher → Writer (insights flow to content)
Analyst → Strategist (data flows to decisions)
Coach → Operator (health scores flow to daily briefing)
Reviewer → all agents (quality gate before shipping)
Networker → Writer (engagement data flows to content strategy)
```

---

## Agent Readiness Checklist

For an agent to move from **Building** to **Ready**:

- [ ] Agent definition file exists in `agents/` directory
- [ ] Primary skill(s) loaded and tested
- [ ] Required context files are populated with real data
- [ ] At least one successful activation logged
- [ ] Handoff protocol defined (how this agent passes work to others)

---

## Blocked Items

| Agent | Blocker | Needed | ETA |
|-------|---------|--------|-----|
| Builder | MCP server not yet deployed | Production MCP endpoint | Q2 W2 |
| Analyst | Financial data not yet populated | Real numbers in financial-snapshot.md | Q2 W1 |
| All | Agent definition files incomplete | Complete all 10 agent .md files | Q2 W1 |

---

## Weekly Status Review

Update this file every Sunday evening:
1. Move completed tasks to the Activation Log
2. Update status for each agent (Ready/Building/Blocked)
3. Clear resolved blockers
4. Assign next week's primary agent based on goal priorities
