---
name: checkin
description: Log Goggins daily scores. Usage /checkin BODY BUILD LEARN AMPLIFY BRIEF (each 0-10). Quick daily accountability.
---

# Check-in: Daily Goggins Score

Log today's non-negotiable scores.

## Usage
User provides 5 scores (0-10 each):
`/checkin 8 7 6 9 8`

Order: BODY BUILD LEARN AMPLIFY BRIEF

## Steps

1. Parse the 5 scores from user input
2. Calculate total (max 50)
3. Read `context/goggins-nonneg.md` to get current streak
4. Append today's entry to the log section
5. Update streak count (25+ = streak maintained)

## Output

```
📊 GOGGINS CHECK-IN: [DATE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BODY:    ████████░░  8/10
BUILD:   ███████░░░  7/10
LEARN:   ██████░░░░  6/10
AMPLIFY: █████████░  9/10
BRIEF:   ████████░░  8/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:   38/50  🔥
STREAK:  X days [maintained/broken]
```

## Streak Rules
- 25+ daily = streak maintained
- <25 = streak broken (reset to 0)
- 45+ = elite day (🏆)
