# Channel Pipeline — "Claude Like a Pro" YouTube Automation

> Loaded by AMPLIFY when V wants to generate, publish, or analyse YouTube content.
> Repo: `~/repos/v-claude-pro-channel/`

---

## When This Skill Activates

- V says: "run channel", "generate video", "what should I post", "channel analytics"
- V asks about YouTube content strategy or video performance
- V says: "Claude like a pro", "tutorial video", "upload video"

---

## Pipeline Commands

### Generate a full video
```bash
cd ~/repos/v-claude-pro-channel
python orchestrator.py run --mode full
```

### Generate with specific topic
```bash
python orchestrator.py run --topic "How to use Claude Projects"
```

### Script-only (for review before full production)
```bash
python orchestrator.py run --mode script-only
```

### Draft mode (ideation through visuals, no publish)
```bash
python orchestrator.py run --mode draft
```

### Check last run status
```bash
python orchestrator.py status
```

### Run analytics only
```bash
python orchestrator.py run --mode analytics-only
```

---

## Content Calendar

| Day | Series | Example |
|-----|--------|---------|
| Tuesday | Claude 101 | "How to use Claude Projects" |
| Thursday | Claude at Work | "How I write reports in 10 min" |
| Saturday | Rotating | "Replace X with Claude" / "Claude vs" / "Weekly Briefing" |
| Daily | Shorts | 60-sec clips from long-form |

---

## Workflow

1. **Ideation** — Pick topic from backlog or trending queries
2. **Script** — Claude writes script with [ANIMATION] and [SCREEN_DEMO] markers
3. **Voice** — ElevenLabs generates narration using V's voice clone
4. **Visuals** — Animated sections rendered (Remotion, Phase 2)
5. **Assembly** — FFmpeg stitches everything together
6. **Thumbnail** — DALL-E generates branded thumbnail with title overlay
7. **Publish** — YouTube Data API uploads, sets metadata, schedules
8. **Analytics** — Pull performance, feed back to ideation

---

## Revenue Angle

Every video is a funnel entry:
```
YouTube video (free value) → Lead magnet (Claude Prompt Toolkit) → Email list
→ Workshop (£97-197/person) → Corporate training (£5K-10K/day) → Consulting retainer
```
