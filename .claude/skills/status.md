---
name: status
description: Show current state of all 10 agents, active goals, and Goggins streak. Quick overview of the entire system.
---

# Status: System Overview

Read these files and present a dashboard:

1. `context/agent-status.md` — full agent roster with status
2. `context/current-goals.md` — progress on Q2 goals
3. `context/goggins-nonneg.md` — current streak and today's score

## Output Format

```
📊 V AGENTFORCE STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENTS
  SENTINEL  ✅ Ready     | Last: [date]
  FORGE     ✅ Ready     | Last: [date]
  AMPLIFY   ✅ Ready     | Last: [date]
  PHOENIX   ✅ Ready     | Last: [date]
  VITALITY  ✅ Ready     | Last: [date]
  CIPHER    ✅ Ready     | Last: [date]
  AEGIS     ✅ Ready     | Last: [date]
  NEXUS     🔨 Building  | Task: [current]
  ATLAS     ✅ Ready     | Last: [date]
  COLOSSUS  ✅ Ready     | Last: [date]

GOALS (Q2 2026)
  Financial: [X/Y complete]
  Creative:  [X/Y complete]
  Technical: [X/Y complete]
  Health:    [X/Y complete]

GOGGINS
  Today: --/50 | Streak: X days | Best: XX/50
```
