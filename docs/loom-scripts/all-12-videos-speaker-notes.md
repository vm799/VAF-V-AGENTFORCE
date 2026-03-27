# VAF — 12 Video Speaker Notes
> Word-for-word scripts. Each video 3–5 minutes. Use NLM deck slides as visuals.
> Record in order. One take each. Don't overthink it.

---

## VIDEO 1 — Overview: "What is V AgentForce?"
**Duration:** 5 min | **Deck slides:** 1 (title), 2 (architecture), 13 (personal → enterprise)
**Show:** NLM deck page 1 → page 2 → run `./demo.sh` in terminal → page 13

### Speaker Notes

> "This is V AgentForce. I built it in evenings and weekends while working full-time in finance. It's two things at once — a personal AI operating system that runs my life, and an enterprise data intelligence pipeline I deploy for consulting clients.
>
> [SHOW SLIDE 2 — architecture diagram]
>
> The personal side has 10 specialist AI agents. SENTINEL orchestrates everything. FORGE builds code. PHOENIX manages my money. VITALITY tracks my health. CIPHER processes everything I read. They all run on Claude, and they all share memory through Obsidian via MCP.
>
> The enterprise side is a 10-build automated pipeline. Raw data goes in. Stakeholder-ready intelligence comes out. Let me show you it running.
>
> [SWITCH TO TERMINAL — run ./demo.sh]
>
> Watch. One command. 2,800 records. Ingested, cleaned, normalised, enriched, analysed, debated by four AI agents in a Council, ranked, formatted, and delivered. Under a second.
>
> [SHOW SLIDE 13 — personal to enterprise]
>
> Same architecture. Two scales. The personal OS is how I proved the concept. The enterprise pipeline is how I sell it. I'm recording one video per build module over the next few days. If you're a CTO or Head of Data and this looks like what you need — message me.
>
> Next video: Build 01 — how data gets into the system."

---

## VIDEO 2 — Build 01: Ingestion
**Duration:** 3 min | **Deck slides:** 2 (architecture — highlight access layer)
**Show:** NLM slide 2 → terminal running Build 01 → ingestion manifest output

### Speaker Notes

> "Build 01 is the pipeline's front door. It pulls data from every configured source — CSVs, REST APIs, databases, documents — and stages it with a timestamp and a manifest.
>
> [SHOW TERMINAL — point to Build 01 output]
>
> In the demo, it pulls from 6 sources: equities, FX, news wire, regulatory filings, research reports, and social sentiment. 2,800 records staged in 0.03 seconds.
>
> Every record gets a SHA-256 checksum and a source tag. The manifest records exactly what arrived, when, and from where. If a source fails, it logs the failure and continues — it never halts the pipeline for one bad source.
>
> This matters because in every organisation I've consulted with, the first problem is always the same: data exists in twelve places and nobody has a single ingest point. Build 01 solves that.
>
> Next: Build 02 — what happens when the data is dirty."

---

## VIDEO 3 — Build 02: Sanitisation
**Duration:** 3 min | **Deck slides:** none needed — terminal is enough
**Show:** Terminal output showing sanitisation stats

### Speaker Notes

> "Garbage in, garbage out. Build 02 is the filter.
>
> It takes everything Build 01 staged and runs four checks: deduplication by fingerprint hash, null field validation, range checking, and format validation. Anything that fails gets quarantined — not deleted, quarantined. You can always go back and inspect what was removed and why.
>
> [SHOW TERMINAL — sanitisation line: 2,800 in → 2,800 passed, 0 quarantined]
>
> In this demo run, all records passed. In production, you'll see quarantine rates. If the rate goes above 20%, that's not a pipeline problem — it's a source quality problem, and Build 10 will flag it automatically.
>
> The principle: never silently discard. Every removal is traceable.
>
> Next: Build 03 — making everything speak the same language."

---

## VIDEO 4 — Build 03: Normalisation
**Duration:** 3 min | **Deck slides:** none — terminal
**Show:** Terminal output, maybe a quick look at a normalised record

### Speaker Notes

> "Different sources use different formats. Dates as DD/MM or YYYY-MM-DD. Currencies as pounds or GBP or 826. Company names in different cases.
>
> Build 03 maps everything to a single canonical schema. ISO 8601 dates. ISO 4217 currency codes. Lowercase entity names. Consistent identifiers.
>
> Why this matters: you can't compare what you can't join. If one source calls it 'Barclays PLC' and another calls it 'barclays bank uk plc', your analysis sees two entities. Build 03 makes them one.
>
> [SHOW TERMINAL — normalisation: 2,800 in → 2,800 normalised, 0 rejected]
>
> Zero rejected means every record mapped successfully to the canonical schema. Clean data ready for enrichment.
>
> Next: Build 04 — adding the context that raw data doesn't have."

---

## VIDEO 5 — Build 04: Enrichment
**Duration:** 3 min | **Deck slides:** none — terminal
**Show:** Terminal output showing enrichment stats, entity resolution confidence

### Speaker Notes

> "A transaction is just a number. Enrichment turns it into a story.
>
> Build 04 adds what raw data doesn't contain: sector classifications, entity relationships, historical baselines, sentiment scores, and risk tags. It uses fuzzy entity resolution — matching company names even when they're slightly different — with an average confidence of 0.89 in this run.
>
> [SHOW TERMINAL — enrichment: 2,800 enriched, 2,800 entities resolved, avg confidence 0.89]
>
> This is the build where data becomes intelligence-ready. Without enrichment, you have facts. With enrichment, you have narrative.
>
> The enrichment layer is also where you plug in your organisation's specific taxonomy. Different sectors, different risk categories, different relationship graphs. The engine is the same — the configuration is yours.
>
> Next: Build 05 — finding the patterns humans miss."

---

## VIDEO 6 — Build 05: Analysis
**Duration:** 3 min | **Deck slides:** none — terminal
**Show:** Terminal showing 5 patterns detected

### Speaker Notes

> "Build 05 is the first build where intelligence is generated, not transformed.
>
> It runs pattern detection across all 2,800 enriched records. Sector clustering, z-score anomaly detection, sentiment consensus analysis, entity concentration. From 2,800 records, it distils 5 distinct patterns — each with a confidence score.
>
> [SHOW TERMINAL — analysis: 5 patterns detected, avg confidence 0.69]
>
> Average confidence of 0.69 — the system is honest about what it's sure of and what it's not. Every pattern comes with supporting evidence, not just a score.
>
> These 5 patterns are what feed the Council in the next build. Better patterns in means better insights out.
>
> Next: Build 06 — and this is the one I'm most proud of."

---

## VIDEO 7 — Build 06: The Council
**Duration:** 5 min | **Deck slides:** none, but this is your star build — show code if you can
**Show:** Terminal → maybe open council_engine.py briefly → show Council output

### Speaker Notes

> "Build 06 is the heart of the entire pipeline. This is the Council.
>
> Four AI agents. Each has a different mandate. The Strategist argues the opportunity — why this pattern matters and what action it supports. The Analyst provides quantitative backing. The Sceptic argues the risk — why this pattern might be overstated or dangerous. And the Synthesiser reads all three positions, resolves the tension, and writes the final insight brief.
>
> [SHOW TERMINAL — council: 5 patterns reviewed → 5 insights, avg confidence 0.70, agreement 87%]
>
> 87% agreement. That means on most insights, the agents converge. But when they don't — when the Sceptic disagrees with the Strategist — that disagreement IS the insight. It means there's genuine uncertainty, and the stakeholder needs to know that.
>
> Most AI systems give you one answer. The Council gives you four perspectives and then resolves them. The tension between agents produces insights that are more robust than any single model.
>
> This is what I demo to consulting clients. This is what makes them lean forward.
>
> Next: Build 07 — not all insights are equal."

---

## VIDEO 8 — Build 07: Ranking
**Duration:** 3 min | **Deck slides:** none — terminal
**Show:** Terminal showing ranking output with tiers

### Speaker Notes

> "The Council produces 5 insights. But a dashboard with 5 equally-weighted findings is useless. Build 07 decides which ones matter most.
>
> It scores each insight on two dimensions: impact — how significant is this? — and novelty — how different is this from what we've seen before? High impact plus high novelty equals top of the brief.
>
> [SHOW TERMINAL — ranking: 5 insights ranked, 0 critical, 1 high, 4 standard]
>
> In this run: 1 high-priority insight, 4 standard. Critical insights would trigger immediate delivery — within 5 minutes of pipeline completion. High-priority gets same-day. Standard gets batched.
>
> This tiering drives everything downstream. Build 08 uses the tier to decide how much detail to write. Build 09 uses it to decide which channels to deliver on.
>
> Next: Build 08 — writing for the right audience."

---

## VIDEO 9 — Build 08: Formatting
**Duration:** 3 min | **Deck slides:** show outputs/dashboard.html if generated
**Show:** Terminal → open executive-brief.html → open analyst-report.html

### Speaker Notes

> "A C-suite executive doesn't want methodology. They want a decision. An analyst wants the evidence. A Slack channel wants three bullets max.
>
> Build 08 takes the same ranked insights and writes them in four formats: executive brief, analyst report, API payload for downstream systems, and notification digest for Slack or Teams.
>
> [SHOW TERMINAL — formatting: 1 exec brief, 1 analyst, 1 API, 1 notification]
>
> [OPEN outputs/ — show executive brief HTML]
>
> Look at this. Auto-generated. Titled, dated, confidence-scored. The executive reads this in 90 seconds and knows what to do. The analyst clicks through to the full report with Bull, Bear, and Risk positions from the Council.
>
> Same data. Four audiences. One build.
>
> Next: Build 09 — getting it to the right people."

---

## VIDEO 10 — Build 09: Distribution
**Duration:** 3 min | **Deck slides:** none — terminal
**Show:** Terminal showing delivery receipts

### Speaker Notes

> "Intelligence that isn't delivered doesn't count. Build 09 is the last mile.
>
> It takes the formatted outputs and delivers them — email, Slack, dashboard, API endpoint, file drop. Each delivery gets a receipt: timestamp, channel, recipient, status. If a delivery fails, it retries with exponential backoff — up to 3 attempts.
>
> [SHOW TERMINAL — distribution: 2 deliveries, 2 success, 0 failed]
>
> After delivery, it archives the entire pipeline run — all 10 builds' outputs — for compliance retention. 90 days by default, configurable per client.
>
> The full pipeline: 2,800 records ingested, cleaned, normalised, enriched, analysed, debated, ranked, formatted, and delivered. Under one second. One command.
>
> Next: Build 10 — the build that makes the pipeline learn from itself."

---

## VIDEO 11 — Build 10: Self-Healing Loop
**Duration:** 4 min | **Deck slides:** 7 (persistent memory — static vs dynamic)
**Show:** Terminal → NLM slide 7 → maybe show security_layer.py briefly

### Speaker Notes

> "Builds 01 through 09 run the pipeline. Build 10 makes the pipeline smarter.
>
> Three components. First: the Health Monitor. It scans every build's logs, diagnoses failures against known patterns, and generates config patches. If a source keeps failing, it lowers its weight. If quarantine rates spike, it flags the source for review.
>
> Second: the Feedback Engine. It tracks which data sources consistently produce high-quality records — records that survive through all 10 builds. Over time, it promotes reliable sources and demotes noisy ones.
>
> Third: the Security Layer. This is MAESTRO-inspired — the AI threat modelling framework. It checks for prompt injection before any data reaches the Council's LLM agents. It scans for PII — emails, phone numbers, national insurance numbers, credit cards — before any external delivery. And it validates the audit trail at every build boundary.
>
> [SHOW TERMINAL — self-healing: 3 in / 3 out]
>
> [SHOW SLIDE 7 — static vs dynamic memory]
>
> This slide explains the concept perfectly. Static memory is your CLAUDE.md — it loads the same rules every session. Dynamic memory is what the system writes to itself — build commands, debugging insights, evolving preferences. Build 10 is the dynamic layer for the enterprise pipeline.
>
> The pipeline doesn't just run. It learns. It hardens. It self-heals.
>
> Next and final: the Personal OS that started it all."

---

## VIDEO 12 — Personal OS Overview
**Duration:** 5 min | **Deck slides:** 3 (10-agent C-suite), 4 (drop detection), 8 (agentic workflows), 10 (revenue lens), 11 (daily loop), 12 (Goggins protocol)
**Show:** Open dashboard/index.html → NLM slides → Claude Code running with CLAUDE.md visible

### Speaker Notes

> "Everything I just showed you — the enterprise pipeline — started here. With a personal problem: my AI kept forgetting who I was.
>
> [SHOW SLIDE 3 — the 10-agent C-suite]
>
> I built 10 specialist agents. Not 10 separate apps — 10 behavioural contexts. Markdown files that define how Claude operates in each domain. When I talk about money, PHOENIX activates. When I'm overwhelmed, SENTINEL takes over. When I need code reviewed, COLOSSUS tears it apart.
>
> [SHOW SLIDE 4 — drop detection protocol]
>
> The routing engine is the CLAUDE.md file. I drop anything — a bank statement, a GitHub link, a brain dump — and it auto-routes to the right agent. No 'what would you like me to do with this?' Just execute.
>
> [SHOW SLIDE 8 — agentic workflows]
>
> Three patterns power the system. The Planning Pattern — SENTINEL breaks a massive brain dump into sub-tasks and sequences them. The ReAct Pattern — COLOSSUS reads code, runs a test, observes the error, reasons about it, and rewrites the fix in a loop. The Tool Use Pattern — PHOENIX queries my actual financial data through MCP, so the numbers are real, not hallucinated.
>
> [SHOW DASHBOARD — open dashboard/index.html in browser]
>
> This is my morning dashboard. Every day I open this. Goggins Protocol tracked. Agents visible. Commands ready.
>
> [SHOW SLIDE 10 — revenue lens / forced monetisation]
>
> Every response from every agent ends with a Revenue Angle block. Not motivational fluff — a specific monetisation path. CIPHER analyses a paper? AMPLIFY turns it into a workshop. FORGE ships a build? It becomes a portfolio piece. Nothing goes unmonetised.
>
> [SHOW SLIDE 11 — daily loop]
>
> The daily loop: 7 AM morning brief auto-triggers. During the day, my Telegram bot captures everything — ideas, spending, health logs. In deep work sessions, Claude loads context from Obsidian via MCP and the right agent activates. Evening: /checkin closes the loop.
>
> [SHOW SLIDE 12 — Goggins protocol]
>
> Five non-negotiables. Every day. BODY — 5 minutes of physical. BUILD — ship one thing. LEARN — extract one lesson. AMPLIFY — create one piece of content. BRIEF — morning brief plus evening debrief.
>
> AI scales your output. But your human discipline scales the AI.
>
> That's V AgentForce. Personal OS and enterprise pipeline. Same architecture. Two scales. Built in public. If you want to see how this applies to your organisation — message me."

---

## RECORDING CHECKLIST (before you start)

For ALL videos:
- [ ] Loom open, 1080p, screen + camera
- [ ] Clean desktop — only terminal + browser visible
- [ ] Enterprise repo terminal at: `cd ~/repos/v-enterprise-architecture`
- [ ] Dashboard open: `~/repos/v-agentforce-architecture/dashboard/index.html`
- [ ] NLM deck PDF open in Preview (ready to switch slides)
- [ ] Water nearby
- [ ] Phone on silent

For enterprise videos (1–11):
- [ ] Run `./demo.sh` once BEFORE recording so outputs/ is populated
- [ ] Have `outputs/dashboard.html` open in browser tab
- [ ] Have terminal scrolled to show pipeline output

For personal OS video (12):
- [ ] Dashboard at localhost:3000 or file:// path
- [ ] Claude Code open in v-agentforce-architecture/
- [ ] CLAUDE.md visible in editor
- [ ] Obsidian open to show vault structure

---

## RECORDING ORDER

Record in this exact sequence. Don't skip ahead.

1. Video 1 (overview) — sets the context
2. Videos 2–10 (builds 01–09) — the pipeline story, builds on itself
3. Video 11 (build 10) — the "wow, it learns" moment
4. Video 12 (personal OS) — the emotional closer

**Total recording time: ~45 minutes** (12 videos × 3–5 min each)
**Total post-production: ~30 minutes** (trim silence, add captions, upload)

---

## LINKEDIN POST TEMPLATES (one per video)

### For enterprise videos (2–11):
```
Build [XX] of my AI pipeline: [Build Name]

[One sentence about what this build does]

[One sentence about why it matters for your org]

Full walkthrough: [Loom link]

This is part of a 12-video series showing the full VAF Enterprise Pipeline — from raw data to stakeholder-ready intelligence.

#AI #DataIntelligence #BuildInPublic
```

### For overview (video 1):
```
I built a 10-build AI pipeline that turns raw data into stakeholder-ready intelligence.

4 AI agents debate every finding before it reaches your C-suite.

One command. Under a second. All 10 builds.

Full walkthrough: [Loom link]

#AI #BuildInPublic #DataPipeline
```

### For personal OS (video 12):
```
Before I built the enterprise pipeline, I built this for myself.

10 AI agents running my finances, health, learning, content, and career. With persistent memory. No cold starts.

The personal OS that became an enterprise architecture.

Full walkthrough: [Loom link]

#AI #PersonalOS #BuildInPublic
```

---

*Keep this file open while recording. One video. One script. Press record.*
