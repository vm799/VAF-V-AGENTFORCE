---
name: finish
description: End session cleanly — summarize work, score Goggins, save context, recommend next steps.
---

# Finish: End Session Protocol

Close out the current session with a full debrief.

## Steps

1. **Summarize** what was accomplished
2. **Score** Goggins non-negotiables for today — ask user to rate each:
   - BODY (5x5 physical): /10
   - BUILD (shipped something): /10
   - LEARN (lesson + insight): /10
   - AMPLIFY (content created): /10
   - BRIEF (check-ins done): /10
3. **Update** `context/goggins-nonneg.md` with today's score
4. **Update** `context/agent-status.md` if any agent status changed
5. **Recommend** what to focus on next session
6. **Run** `/crystallize` to save learnings

## Output Format

```
🏁 SESSION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Shipped: [list]
📊 Goggins Score: XX/50
🔥 Streak: X days

💡 Next Session Recommendation:
   Primary Agent: [AGENT]
   Focus: [what to work on]

Stay hard. See you tomorrow.
```
