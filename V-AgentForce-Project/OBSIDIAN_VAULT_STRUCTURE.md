# Obsidian Vault Structure — V AgentForce
> The canonical folder map and tag taxonomy for V's entire knowledge system.
> Tagged: #vaf #obsidian #structure

---

## Philosophy

The vault is V's **long-term memory and intelligence layer**. Everything Claude produces that has lasting value should end up here. The structure is designed so that:
- Any note can be found in under 10 seconds
- The Knowledge Graph reveals connections between domains
- Tags make cross-domain insights surfaceable
- Nothing valuable is ever lost

---

## Folder Structure

```
V AgentForce/                    ← Root (already exists)
│
├── 00 INBOX/                    ← Everything lands here first. Clear daily.
│   └── [Raw captures, quick notes, unprocessed]
│
├── 01 Brain Dumps/              ← Processed brain dump sessions
│   └── YYYY-MM/
│       └── YYYY-MM-DD Brain Dump.md
│
├── 02 Finance/                  ← All financial records and analysis
│   ├── Statements/
│   │   └── YYYY-MM/
│   │       └── YYYY-MM Statement Analysis.md
│   ├── Reviews/
│   │   └── YYYY-MM Monthly Review.md
│   ├── Goals/
│   │   └── Financial Goals 2026.md
│   └── Templates/
│       └── Statement Analysis Template.md
│
├── 03 Builds/                   ← All software projects
│   ├── Vaishali Agent Force/
│   │   ├── Architecture.md
│   │   ├── Decisions/           ← Architecture Decision Records
│   │   └── Sprints/
│   ├── [Project Name]/
│   │   ├── PRD.md
│   │   ├── Architecture.md
│   │   └── Sprints/
│   └── Ideas/                   ← Build ideas not yet started
│       └── [idea name].md
│
├── 04 Content/                  ← All content production
│   ├── YouTube/
│   │   └── YYYY-MM/
│   ├── Instagram/
│   │   └── YYYY-MM/
│   ├── LinkedIn/
│   │   └── YYYY-MM/
│   ├── Substack/
│   │   └── YYYY-MM/
│   └── Content Calendar.md
│
├── 05 Teaching/                 ← Courses, workshops, curriculum
│   ├── Course Ideas/
│   ├── AI for Professionals/    ← V's flagship course
│   │   ├── Curriculum.md
│   │   └── Modules/
│   └── Corporate Workshops/
│
├── 06 Learning/                 ← Everything V is consuming and learning
│   ├── AI News/
│   │   └── YYYY-MM/
│   │       └── YYYY-MM-DD [Topic].md
│   ├── Insights/                ← Link drop analysis (from VAF education pipeline)
│   │   ├── ai/
│   │   ├── finance/
│   │   ├── tech/
│   │   └── [other categories]/
│   ├── Weekly Syntheses/
│   │   └── YYYY-MM-DD Week Synthesis.md
│   └── Resources/
│       ├── AI Experts.md        ← Mirror of AI_EXPERTS_DATABASE.md
│       └── Reading List.md
│
├── 07 Health/                   ← Health tracking and protocols
│   ├── Weekly Check-ins/
│   │   └── YYYY-MM-DD Check-in.md
│   ├── Protocols/
│   │   └── My Health Protocol.md
│   └── Nutrition/
│       └── Meal Plans/
│
├── 08 Career/                   ← Work, promotion, professional
│   ├── Promotion Case.md        ← Running document for promotion evidence
│   ├── Wins/                    ← Log every work achievement
│   │   └── YYYY-MM-DD Win.md
│   └── Reviews/
│
├── 09 Daily Notes/              ← Optional: daily journal / log
│   └── YYYY-MM-DD.md
│
├── 10 Goals/                    ← Goals and reviews
│   ├── Goals 2026.md            ← Mirror of GOALS_2026.md
│   ├── Q1 Review.md
│   └── Monthly Reviews/
│
└── 99 Archive/                  ← Completed or inactive items
    └── [Year]/
```

---

## Tag Taxonomy

### Domain tags (every note gets one)
```
#finance       #builds        #content       #teaching
#health        #learning      #career        #braindump
#goals         #obsidian
```

### Agent tags (who produced this)
```
#agent/cfo          #agent/architect    #agent/content
#agent/health       #agent/education    #agent/librarian
```

### Status tags
```
#status/inbox       #status/active      #status/done
#status/paused      #status/archived
```

### Action tags
```
#actionable         #decision           #review-weekly
#review-monthly     #high-priority
```

### Content type tags
```
#note               #analysis           #template
#reference          #insight            #idea
#sprint             #adr
```

---

## Knowledge Graph Design

These connections should be made explicit with `[[wikilinks]]` in every note:

**Finance → Builds:** When a finance insight generates a build idea, link the statement analysis to the build idea note.

**Learning → Content:** When V learns something worth teaching, link the learning note to the content idea note.

**Builds → Teaching:** When V ships a feature, link the sprint note to a content/teaching note ("this becomes a tutorial").

**Goals → Everything:** All notes that contribute to a goal should link back to `Goals 2026.md`.

**Daily Notes → Everything:** Daily notes are the connective tissue — link out to whatever was worked on.

---

## How Claude Outputs to Obsidian

Every Claude response that produces a note will include:

```
---
Obsidian note ready:
Vault path: V AgentForce/[folder]/[filename].md
Tags: #[domain] #[agent] #[status]
---
[Note content in markdown]
```

V pastes this into Obsidian at the specified path. Over time, the vault becomes a comprehensive intelligence layer that the Knowledge Graph makes navigable visually.

---

## The Knowledge Graph Promise

Once the vault has 50+ linked notes, the graph view reveals:
- Which domains are most connected (builds + content = V's creative engine)
- Which ideas keep recurring (signal to act on them)
- Which agents are most active (where V is spending mental energy)
- Orphan notes (ideas that haven't been connected yet — find them, link them or archive them)

Run a monthly graph review: open Obsidian Graph View, look for clusters and orphans, and ask: *"What is the vault trying to tell me about where my attention is and where it should be?"*
