---
name: content-production
description: Execute the content creation workflow for LinkedIn posts and Substack essays including topic selection, drafting, optimization, and scheduling
---

# Content Production Protocol

Use this skill when creating content for LinkedIn or Substack. Every piece starts from real work, real learnings, real outcomes.

## Step 1: Topic Selection

Source topics from the past 7 days:
1. **What did I build?** (technical insights, architecture decisions, tools shipped)
2. **What did I learn?** (courses, books, conversations, failures)
3. **What did I change my mind about?** (contrarian takes, updated mental models)
4. **What question keeps coming up?** (from clients, community, self)

Score each candidate topic:

| Topic | Relevance to Audience | Unique Angle | Content Depth | Timeliness | Total /20 |
|-------|----------------------|--------------|---------------|------------|-----------|
|       | /5                   | /5           | /5            | /5         |           |

Pick the highest-scoring topic. If tie, choose the one you have the strongest opinion on.

## Step 2: Platform Decision

| Factor | LinkedIn | Substack |
|--------|----------|----------|
| Length | <300 words | 1500+ words |
| Depth | One insight, one takeaway | Deep exploration, frameworks |
| Frequency | 4-5x per week | 1x per week |
| Goal | Visibility, engagement, network growth | Authority, depth, subscriber growth |
| Tone | Punchy, direct, conversational | Thorough, structured, analytical |

**Rule**: If you can say it in 300 words, it is LinkedIn. If it needs diagrams, code, or multi-section analysis, it is Substack. Substack essays can be repurposed into 3-5 LinkedIn posts.

## Step 3: LinkedIn Post Template

```
[HOOK — 1-2 lines that stop the scroll. Pattern interrupt or bold claim.]

[CONTEXT — 2-3 lines. What happened, what you were doing, what the situation was.]

[INSIGHT — 3-5 lines. The actual lesson, framework, or observation. This is the meat.]

[PROOF — 1-2 lines. Specific result, metric, or outcome that validates the insight.]

[CTA — 1 line. Question to the audience, or clear next step.]

---
#hashtag1 #hashtag2 #hashtag3
```

### LinkedIn Writing Rules
- First line must be < 10 words and create curiosity
- No fluff words: "just", "really", "actually", "basically"
- One idea per post. Kill your darlings.
- Use line breaks aggressively. Walls of text die in the feed.
- End with a genuine question, not "Agree?"
- Total: 200-300 words maximum
- Post between 08:00-09:00 or 17:00-18:00 UK time

### LinkedIn Example Structure
```
I mass deleted 47 AWS Lambda functions last week.

Not because they were broken.
Because they were "fine."

Here's what "fine" was costing us:
→ £380/month in idle compute
→ 3 hours/week in maintenance overhead
→ Zero business value

The cleanup took 2 hours.
The annual savings: £4,560.

Your "fine" infrastructure is probably bleeding money too.

What's one thing in your stack that's "fine" but should be deleted?

---
#AWS #Serverless #CloudArchitecture
```

## Step 4: Substack Essay Template

```markdown
# [TITLE — Specific, promises value, not clickbait]

## The Problem / The Question
[Set the stage. Why should the reader care? What tension exists? 150-200 words.]

## What I Discovered / What Changed
[The core narrative. Walk through the journey, the analysis, or the framework.
Include code snippets, diagrams, or real examples. 600-800 words.]

## The Framework / The Model
[Distill into a reusable framework the reader can apply.
Tables, numbered lists, decision trees work well here. 200-300 words.]

## What This Means For You
[Direct application. How does the reader use this Monday morning? 150-200 words.]

## Key Takeaways
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

---
*[Brief sign-off with CTA to subscribe or reply with questions]*
```

### Substack Writing Rules
- 1500-2500 words. Enough depth to be worth subscribing for.
- Include at least one original diagram, table, or code block
- Every section must earn its place. If it does not advance the argument, cut it.
- Write the intro last — you will know what the essay is about only after writing it
- Publish on Tuesday or Wednesday morning for best engagement
- Always include 3 concrete takeaways at the end

## Step 5: Editing Checklist

Before publishing any piece:

- [ ] Does the first line create genuine curiosity?
- [ ] Is there exactly ONE core idea?
- [ ] Have I removed every word that does not earn its place?
- [ ] Is there a specific example, metric, or story (not just abstract advice)?
- [ ] Would I share this if someone else wrote it?
- [ ] Does the CTA invite genuine conversation?
- [ ] Platform-appropriate length? (LinkedIn <300, Substack 1500+)

## Step 6: Scheduling and Tracking

### Publishing Schedule
| Day       | Platform  | Content Type |
|-----------|-----------|--------------|
| Monday    | LinkedIn  | Weekly insight from work |
| Tuesday   | Substack  | Deep-dive essay |
| Wednesday | LinkedIn  | Framework or mental model |
| Thursday  | LinkedIn  | Contrarian take or hot take |
| Friday    | LinkedIn  | Week review or personal reflection |

### Engagement Tracking (Weekly)
```
| Post Date | Platform | Topic | Impressions | Engagement Rate | Comments | New Followers/Subs |
|-----------|----------|-------|-------------|-----------------|----------|--------------------|
|           |          |       |             |                 |          |                    |
```

Target metrics:
- LinkedIn: >5% engagement rate, >10 meaningful comments per post
- Substack: >40% open rate, >5% click-through rate, net positive subscriber growth weekly
