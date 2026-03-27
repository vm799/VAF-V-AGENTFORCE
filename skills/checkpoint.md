---
name: checkpoint
description: Save complex task state for resumption in a future session. Use when stopping mid-task or before a context reset.
trigger: /checkpoint, "save my place", "I need to stop", "resume later"
---

# CHECKPOINT: Task State Preservation

## What This Does
Creates a handoff note that lets you (or Claude) resume exactly where you stopped, with full context, without re-explaining everything.

## Step 1: Capture Current State
Identify and document:
- Task: what were we building/solving?
- Progress: what has been completed so far?
- Next step: the exact next action needed
- Blockers: anything waiting on external input
- Files in play: list all modified/created files
- Decisions made: choices locked in during this session

## Step 2: Write Checkpoint File
Create: `context/checkpoint-[YYYY-MM-DD].md`

```markdown
# Checkpoint: [Task Name]
**Date:** [date]
**Status:** In Progress
**Resume With:** [one-line instruction for resuming]

## What We're Building
[2-3 sentences on the task]

## Completed
- [x] item 1
- [x] item 2

## Next Step (Start Here)
[single specific action to take immediately on resume]

## Files Modified
- path/to/file1
- path/to/file2

## Decisions Made
- [decision]: [why]

## Context for Resume
[any additional context Claude needs that isn't obvious from the files]
```

## Step 3: Crystallize if Warranted
If insights were gained during this session, run /extract-learnings before saving checkpoint.

## Step 4: Confirm
"Checkpoint saved to context/checkpoint-[date].md. Resume command: /checkpoint resume [date]"

## Resuming from Checkpoint
When user says `/checkpoint resume [date]`:
1. Read `context/checkpoint-[date].md`
2. Read all files listed under "Files Modified"
3. Present the "Next Step" immediately
4. Ask: "Ready to continue with [next step]?"
