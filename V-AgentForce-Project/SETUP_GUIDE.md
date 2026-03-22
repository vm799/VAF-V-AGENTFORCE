# V AgentForce — Claude Project Setup Guide
> Get this entire system live in 30 minutes.

---

## What You're Setting Up

A Claude Project called **"V AgentForce"** that gives you a fully staffed AI team — CFO, architect, content strategist, health coach, learning curator, and librarian — all with deep knowledge of who you are, what you're building, and what you're working toward. Every conversation in this project has your full context. No re-explaining. No generic advice.

---

## Step 1 — Create the Project in Claude.ai (5 minutes)

1. Open **claude.ai** on desktop or mobile
2. In the left sidebar, click **"New Project"**
3. Name it: **V AgentForce**
4. Click into **"Set project instructions"** (or "Custom instructions")
5. Paste the entire contents of **`CLAUDE.md`** into this field
6. Save

This is the master brain — it's always in context for every conversation.

---

## Step 2 — Upload Knowledge Files (10 minutes)

In your project, find **"Project Knowledge"** or **"Add content"**. Upload these files in this order (most important first):

**Priority 1 — Upload first:**
- `WHO_I_AM.md`
- `GOALS_2026.md`

**Priority 2 — Agent files:**
- `agents/00_LIBRARIAN.md`
- `agents/01_BUILDS_ARCHITECT.md`
- `agents/02_CONTENT_CREATOR.md`
- `agents/03_FINANCE_CFO.md`
- `agents/04_HEALTH_COACH.md`
- `agents/05_EDUCATION_CURATOR.md`

**Priority 3 — Reference files:**
- `builds/TEAM_MANIFEST.md`
- `teaching/AI_EXPERTS_DATABASE.md`
- `teaching/CONTENT_FORMATS.md`
- `OBSIDIAN_VAULT_STRUCTURE.md`

Claude.ai Projects support up to ~200,000 tokens of knowledge. All these files together are well within that limit.

---

## Step 3 — Personalise WHO_I_AM.md (10 minutes)

Before you start using the system, fill in the blanks in `WHO_I_AM.md`:
- Your job title and company
- Financial context (income range, accounts, savings goal)
- Health context (goals, current routine)
- Your content channel URLs
- Your GitHub URL
- Communities you're active in beyond Multiverses and Skool

Re-upload the updated file. The more specific your context, the better every response will be.

---

## Step 4 — Set Up Obsidian (5 minutes)

Create the folder structure from `OBSIDIAN_VAULT_STRUCTURE.md` in your vault. The key folders to create now:

```
00 INBOX/
01 Brain Dumps/
02 Finance/Statements/
03 Builds/Vaishali Agent Force/
04 Content/
06 Learning/Insights/
08 Career/
10 Goals/
```

Install the **Obsidian Knowledge Graph** plugin if not already active. It will start revealing connections as you add notes.

---

## Step 5 — First Conversations (5 minutes to test, forever to use)

**Test 1 — Finance CFO:**
Take a photo of any bank statement. Open the V AgentForce project. Upload the photo and say: *"Analyse this statement."*

Expected result: Categorised spending, specific flags, CFO verdict, Obsidian note ready to paste.

**Test 2 — Builds Architect:**
Describe an app idea in one sentence. Say: *"I want to build [X]. Help me think through this."*

Expected result: Clarifying questions from the BA, then a proposed architecture and Sprint 1 plan.

**Test 3 — Content Creator:**
Share a link to any AI article or news. Say: *"What's the content angle here?"*

Expected result: 2-sentence summary, why it matters for your audience, suggested post/video format.

**Test 4 — Brain Dump:**
Just type whatever's in your head — messy, stream of consciousness. Say: *"Brain dump — help me make sense of this."*

Expected result: Librarian captures it all, extracts actions and ideas, routes to the right agent, offers to create the Obsidian note.

---

## Daily Use Patterns

**Morning (2 minutes):** Open V AgentForce project. Say "Morning brief me" — Claude synthesises your goals, what's pending, and your top 3 priorities for today.

**Finance (when needed):** Photo of statement → immediate CFO analysis → paste Obsidian note.

**Building (during build sessions):** Describe what you're working on or paste code. Name which agent you want: "Architect hat: is this the right way to structure this?"

**Content (any time you see something interesting):** Paste the link. Get the content angle immediately.

**End of week (10 minutes):** "Weekly synthesis" — Librarian reviews everything from the week and produces your Sunday reflection note.

---

## Keeping It Current

Update these files as your situation evolves:
- `WHO_I_AM.md` — when your job, finances, or goals change materially
- `GOALS_2026.md` — monthly review, mark progress
- `agents/03_FINANCE_CFO.md` → `MY_FINANCIAL_CONTEXT.md` — update the baseline after each monthly review
- `teaching/AI_EXPERTS_DATABASE.md` — add new voices as you discover them

The system gets smarter as the knowledge files get more specific to your reality.

---

## The Relationship Between Claude Projects and VAF Dashboard

These two systems complement each other:

| Claude Projects | VAF Dashboard |
|---|---|
| Input layer (where you talk to AI) | Output layer (where you see the intelligence) |
| Real-time analysis and advice | Historical data and trends |
| Qualitative insight | Quantitative summaries |
| Finance CFO conversation | Finance panel showing totals |
| Content ideation | Learning insights panel |
| Brain dump + routing | Brain dump storage and retrieval |

**The flow:** Claude Projects → produce structured markdown → paste to Obsidian → VAF syncs from Obsidian → Dashboard shows the intelligence layer.

You're not replacing what you built. You're giving it a brain.
