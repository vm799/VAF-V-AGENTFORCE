# VAF Enterprise — 5-Minute Demo Script

**Audience:** CTO, COO, or Head of Operations at a 50-500 person company
**Goal:** Show the pipeline running live, explain the business value at each step, close on a discovery call

---

## Before You Start (2 min prep)

1. Open terminal, navigate to `enterprise/`
2. Have `outputs/dashboard.html` ready to open in Chrome (not Safari)
3. Have this document on a second screen as your script
4. Take a screenshot of the dashboard after the run for your LinkedIn post

---

## The 90-Second Setup

> "Most organisations drown in data they can't act on. The problem isn't data access — it's the gap between raw information and a decision. This pipeline closes that gap in 9 automated steps. Let me show you."

---

## Live Demo (run this first, talk while it runs)

```bash
cd enterprise
python3 orchestrator.py run --mode with-dashboard
```

While it's running, talk through each build:

---

## Build-by-Build Narrative

### Build 01 — Ingestion
> "Step 1: we pull data from any source. In demo mode, this is our knowledge base. For your organisation, this is Confluence, SharePoint, Salesforce, your ticketing system — whatever has the data."

**Business value:** Eliminates manual data gathering. Analysts stop spending 40% of their time pulling data.

---

### Build 02 — Sanitisation
> "Step 2: deterministic cleaning. Deduplication, format standardisation, noise removal. Every time, same rules. No human judgment needed here."

**Business value:** Data quality by default, not by heroics. Compliance-ready outputs.

---

### Build 03 — Identity & Persona
> "Step 3: we enrich each record with context. Who is involved, what's the relationship, what's the history. This is where generic data becomes business intelligence."

**Business value:** Context that would take an analyst an hour per record, done automatically.

---

### Build 04 — RAG (Retrieval-Augmented Generation)
> "Step 4: the knowledge layer. We index all documents and make them queryable. Ask any question, get an answer with citations. No more 'I know we have that somewhere.'"

**Business value:** Institutional knowledge becomes searchable and actionable. Junior staff work like seniors.

---

### Build 05 — Self-Evolving Loop
> "Step 5: the system learns. Each run improves on the last. Patterns get captured, anomalies get flagged earlier. It gets smarter without you touching it."

**Business value:** Compounding returns. Month 3 is better than month 1 automatically.

---

### Build 06 — Council (Multi-Agent Synthesis)
> "Step 6: four AI agents deliberate in parallel. A Bull, a Bear, a Risk analyst, and a Synthesiser. They argue, check each other's work, and reach a consensus. Same as having 4 senior analysts — in seconds."

**Business value:** Multiple perspectives, no groupthink. Board-quality analysis at analyst speed.

---

### Build 07 — Compliance
> "Step 7: every output is checked against your compliance rules before it goes anywhere. FCA, GDPR, internal policy — you define the rules, the system enforces them automatically."

**Business value:** Compliance is built in, not bolted on. Zero human sign-off for routine checks.

---

### Build 08 — Synthesis
> "Step 8: the narrative. Not raw data — a written brief. The kind your C-suite can read in 2 minutes and make a decision from."

**Business value:** Decisions made faster, with more confidence, by people at the right level.

---

### Build 09 — Output
> "Step 9: delivery. To Slack, Teams, email, dashboard — wherever your team works. The right information, to the right person, in the right format."

**Business value:** Information pull becomes information push. No chasing, no latency.

---

## Open the Dashboard

```bash
open outputs/dashboard.html
```

> "This is what your operations team sees. Real-time KPIs, pipeline timeline, data quality metrics. One screen, everything you need to know."

---

## Closing the Conversation

> "What you've just seen is 9 workflows that your team currently does manually, taking hours or days, for each data cycle. We can deploy this for your specific data sources in 6 weeks. The question isn't whether AI will do this in your industry — it's whether your organisation builds this capability now or in 18 months when your competitors already have."

**Discovery call ask:** "Can we book 30 minutes to map your current data flows to these 9 steps? I'll show you exactly which builds apply to your use case."

---

## Pricing Context (for your reference, not to share in demo)

| Package | What's included | Price range |
|---------|----------------|-------------|
| Assessment | Map current flows → pipeline blueprint | £5K–£10K |
| Pilot | 3 builds deployed, 1 data source | £15K–£25K |
| Full deployment | All 9 builds, training, 90-day support | £40K–£80K |
| Retained | Ongoing, monthly optimisation | £3K–£5K/month |

---

## After the Demo

1. Screenshot `outputs/dashboard.html` for LinkedIn
2. Post: "Just ran a live demo of a 9-step AI pipeline. [screenshot] Built this for [use case]. If you're a [CTO/COO/Head of Ops] curious about what this looks like for your organisation — DM me."
3. Log the conversation in Obsidian: `/dump Demo with [name] — they were interested in builds [X, Y]`
