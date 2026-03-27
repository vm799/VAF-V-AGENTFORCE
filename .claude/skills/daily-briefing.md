---
name: daily-briefing
description: Run the morning briefing ritual to load goals, review yesterday's Goggins score, scan calendar, and set today's top 3 priorities with agent assignments
---

# Daily Briefing Protocol

Execute this every morning before any other work begins. Total time: 5 minutes.

## Step 1: Load Current State (1 min)

1. Read `context/current-goals.md` and identify which quarterly goals are on track, behind, or ahead.
2. Read `context/goggins-nonneg.md` and pull yesterday's score. Flag if below 35/50.
3. Read `context/agent-status.md` and note which agents are Ready vs Blocked.

## Step 2: Calendar Scan (1 min)

1. Check today's calendar for meetings, deadlines, and commitments.
2. Identify available deep work blocks (minimum 90 minutes uninterrupted).
3. Flag any conflicts or double-bookings.

## Step 3: Priority Selection (2 min)

Select exactly 3 priorities for today using this ranking framework:

| Rank | Criteria |
|------|----------|
| 1 | Deadline-driven: anything due today or tomorrow |
| 2 | Revenue-generating: moves the £250K target forward |
| 3 | Compounding: builds system or asset that pays dividends |

For each priority, define:
- **What**: One-sentence deliverable
- **Done means**: Specific completion criteria (not "work on" but "ship/complete/publish")
- **Agent**: Which of the 10 agents owns this task
- **Time block**: When in the day this gets done

## Step 4: Agent Activation (30 sec)

Update `context/agent-status.md` with today's assignments:
- Set primary agent to Active with task description
- Set secondary agents to Standby if needed
- Clear yesterday's completed tasks

## Step 5: Goggins Check-in (30 sec)

Log the morning check-in in `context/goggins-nonneg.md`:
- Record intended workout for BODY
- Record intended ship target for BUILD
- Record intended learning for LEARN
- Record intended content piece for AMPLIFY
- Mark BRIEF morning check-in as done (+5 points baseline)

## Morning Briefing Output Template

```
## Daily Briefing — [DATE]

### Yesterday's Goggins Score: [XX]/50 [streak: X days]

### Today's Top 3
1. [PRIORITY] → Agent: [NAME] → Done: [CRITERIA] → Block: [TIME]
2. [PRIORITY] → Agent: [NAME] → Done: [CRITERIA] → Block: [TIME]
3. [PRIORITY] → Agent: [NAME] → Done: [CRITERIA] → Block: [TIME]

### Calendar
- [TIME] [EVENT]
- Deep work blocks: [TIMES]

### Goggins Intentions
- BODY: [WORKOUT PLAN]
- BUILD: [SHIP TARGET]
- LEARN: [LEARNING TARGET]
- AMPLIFY: [CONTENT TARGET]
- BRIEF: Morning check-in ✓

### Blockers / Flags
- [Any issues requiring attention]
```

## Checklist Before Closing Briefing

- [ ] 3 priorities are specific and have completion criteria
- [ ] Each priority has an assigned agent
- [ ] Time blocks are realistic given calendar
- [ ] Goggins intentions are logged
- [ ] Agent status board is updated
- [ ] No carry-over items from yesterday left unaddressed
