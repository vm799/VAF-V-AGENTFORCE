---
name: extract-learnings
description: Crystallize insights from this Claude session into permanent Obsidian notes. Moves fluid knowledge from chat into cold memory.
trigger: /extract-learnings, "save what I learned", "crystallize", session end
---

# EXTRACT-LEARNINGS: Session Crystallization

## What This Does
Turns session insights into permanent Obsidian notes via MCP. Makes every session compound — next session starts smarter.

## Step 1: Scan Session for Insights
Look back at this conversation and identify:
- Decisions made (architectural, financial, personal)
- Problems solved and HOW they were solved
- New understanding about a domain
- Things that were harder/easier than expected
- Any "aha" moments

Skip: task outputs, code written, routine questions answered

## Step 2: Categorise Each Insight
Map to Obsidian folder:
- Architectural/technical decision → `ADRs/`
- Domain knowledge gained → `Learnings/`
- Process that worked → `Processes/`
- Standard/principle confirmed → `Standards/`

## Step 3: Draft Each Note
For each insight, draft:
```
Title: [concise, searchable]
Date: [today]
Context: [what we were working on]
Insight: [the actual learning — 2-4 sentences]
Why it matters: [how this changes future decisions]
Tags: [domain, agent-name, project]
```

## Step 4: Crystallize via MCP
For each drafted note:
- MCP tool: `crystallize_learning`
- Parameters: title, content, folder (ADRs/Learnings/Processes/Standards)
- Confirm write succeeded

## Step 5: Confirm
Report: "Crystallized X learnings to Obsidian: [list of titles]"
If zero learnings: "No new insights to crystallize this session."
