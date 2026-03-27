---
name: prime
description: Load session context — agent status, top priorities, recent learnings. Run at the start of every Claude session.
trigger: /prime, "start session", "what should I focus on", morning start
---

# PRIME: Session Context Loader

## What This Does
Loads your current state so Claude has full context before any work begins. Prevents repeating yourself every session.

## Step 1: Load Agent Status
Read: `context/agent-status.md`
Extract: which agents are Ready vs Building, any active blockers

## Step 2: Load Top Priorities
Read: `context/current-goals.md`
Extract: top 3 priorities for today based on quarterly milestones

## Step 3: Search Recent Learnings
MCP tool: `search_knowledge` with query "recent learnings"
Extract: last 3 crystallised insights from Obsidian

## Step 4: Check Goggins Non-Negotiables
Read: `context/goggins-nonneg.md`
Extract: today's 5 non-negotiables and current streak

## Step 5: Output Briefing
Present as:
```
TODAY'S FOCUS
━━━━━━━━━━━━━━━━━━━━━━
Priority 1: [most urgent/important goal task]
Priority 2: [next important task]
Priority 3: [quick win or admin]

AGENT STATUS: X/10 Ready | Blockers: [list]

GOGGINS STREAK: X days | Today: [non-negotiables]

LAST LEARNING: [most recent Obsidian entry]
━━━━━━━━━━━━━━━━━━━━━━
Recommended first action: [one specific thing]
```
