---
name: learning-synthesis
description: Extract insights from learning material (courses, articles, books) into permanent Obsidian notes, identify content opportunities, and connect to the knowledge graph
---

# Learning Synthesis Protocol

Use this skill after consuming any learning material. The goal: nothing learned stays trapped in your head. Everything gets extracted, connected, and potentially published.

## Step 1: Capture — Raw Input

Immediately after consuming the material, answer these five questions:

1. **What is this about in one sentence?**
2. **What are the 3-5 key ideas?**
3. **What surprised me or challenged my existing thinking?**
4. **What can I directly apply this week?**
5. **Who in my network would benefit from knowing this?**

Source metadata:
```
- Title: [TITLE]
- Author/Creator: [NAME]
- Type: [Book / Article / Course / Video / Podcast / Conversation]
- Date consumed: [DATE]
- Time invested: [XX] minutes
- Rating: [1-5 stars]
```

## Step 2: Extract — Key Insights

For each key idea, create an insight card:

```
### Insight [N]: [One-line summary]

**Claim**: [What is being argued or demonstrated]
**Evidence**: [What supports this — data, example, logic]
**My take**: [Do I agree? How does this fit with what I already know?]
**Application**: [How can I use this in my work/life]
```

Extract 3-5 insights per material. Quality over quantity. If a book only has one genuine insight, that is fine.

## Step 3: Permanent Note — Obsidian Format

Create a permanent note using this template:

```markdown
---
title: "[TITLE]"
date: [YYYY-MM-DD]
type: [literature-note | permanent-note | concept-note]
source: "[ORIGINAL SOURCE]"
tags: [tag1, tag2, tag3]
status: seedling | growing | evergreen
---

# [TITLE]

## Summary
[2-3 sentence summary of the core argument or framework]

## Key Insights

### 1. [Insight Title]
[2-4 sentences explaining the insight in your own words. Never copy-paste.]

### 2. [Insight Title]
[2-4 sentences]

### 3. [Insight Title]
[2-4 sentences]

## Connections
- Related to: [[note-1]], [[note-2]]
- Challenges: [[note-that-disagrees]]
- Extends: [[note-this-builds-on]]
- Supports: [[note-this-validates]]

## Application
- [ ] [Specific action I can take based on this]
- [ ] [Second action]

## Quotes
> "[Exact quote worth saving]" — [Author], [Source]

## Questions This Raises
- [Question 1]
- [Question 2]

## Content Opportunities
- [ ] LinkedIn post: [angle]
- [ ] Substack essay: [angle]
- [ ] Thread/series: [angle]
```

### Note Naming Convention
- Format: `YYYY-MM-DD-[slug]`
- Example: `2026-03-27-event-driven-architecture-patterns`
- Always lowercase, hyphens not underscores

### Note Status Lifecycle
- **Seedling**: Just captured, rough, needs refinement
- **Growing**: Connected to other notes, refined language, insights validated
- **Evergreen**: Battle-tested, frequently referenced, publishable quality

## Step 4: Content Opportunity Identification

For each piece of learning material, evaluate content potential:

| Opportunity | Platform | Angle | Priority | Effort |
|-------------|----------|-------|----------|--------|
| [Topic] | LinkedIn | [Hook] | High/Med/Low | Quick/Medium/Deep |
| [Topic] | Substack | [Hook] | High/Med/Low | Quick/Medium/Deep |

### Content Extraction Rules
- **1 course** should yield: 3-5 LinkedIn posts + 1 Substack essay
- **1 book** should yield: 5-10 LinkedIn posts + 2-3 Substack essays
- **1 article** should yield: 1 LinkedIn post minimum
- **1 conversation** should yield: 1 LinkedIn post if insight was genuine

## Step 5: Knowledge Graph Connection

After creating the permanent note, update the graph:

1. **Link forward**: What existing notes does this connect to? Add `[[links]]` in both directions.
2. **Link backward**: Go to related existing notes and add a reference back to this new note.
3. **Tag consistently**: Use the established tag taxonomy:
   - Technical: `#aws`, `#serverless`, `#architecture`, `#devops`, `#ai`
   - Business: `#consulting`, `#pricing`, `#strategy`, `#revenue`
   - Personal: `#health`, `#productivity`, `#learning`, `#mindset`
   - Content: `#linkedin-idea`, `#substack-idea`, `#talk-idea`
4. **Map of Content (MOC)**: If 5+ notes share a theme, create or update a MOC note that indexes them.

## Step 6: Weekly Learning Review

Every Sunday, review the week's learning:

```
## Learning Review — Week [XX]

### Materials Consumed
| Material | Type | Time | Rating | Notes Created | Content Generated |
|----------|------|------|--------|---------------|-------------------|
|          |      |      |        |               |                   |

### Knowledge Graph Stats
- New permanent notes: [X]
- New connections: [X]
- Notes promoted (seedling → growing): [X]
- Notes promoted (growing → evergreen): [X]

### Top Insight of the Week
[The single most valuable thing learned]

### Learning Backlog
1. [Next material to consume]
2. [Next material to consume]
3. [Next material to consume]

### LEARN Score for Goggins: [X]/10
```
