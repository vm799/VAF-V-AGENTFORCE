---
name: crystallize
description: Extract learnings from this session and save to Obsidian vault. Use at end of session or when a key insight/decision is made.
---

# Crystallize: Save Session Learnings

Extract key insights, decisions, and learnings from this session and persist them.

## Steps

1. **Summarize** what was accomplished this session (2-3 bullet points)
2. **Identify** key decisions made and their rationale
3. **Extract** any reusable insights or patterns discovered
4. **Ask** the user:
   - "Any decisions or insights worth recording permanently?"
   - "What should the next session focus on?"

3. **Save** to the Obsidian vault:
   - Copy the template from `SecondBrain/AgentForce/Learnings/session-template.md`
   - Fill in today's date, session number, agents used, insights
   - Write to `SecondBrain/AgentForce/Learnings/session-YYYY-MM-DD.md`

4. **If a major decision was made**, also create an ADR:
   - Write to `SecondBrain/AgentForce/ADRs/NNN-decision-name.md`
   - Use ADR format: Context, Decision, Consequences, Status

## Output Format

```
💎 CRYSTALLIZED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Saved: Learnings/session-YYYY-MM-DD.md
📋 Insights: X captured
🏗️ Decisions: Y recorded
📍 Next focus: [recommendation]
```

## Important
- If MCP server is connected, use `crystallize_learning` tool
- If not, write directly to filesystem
- Always ask before creating ADRs — they're permanent records
