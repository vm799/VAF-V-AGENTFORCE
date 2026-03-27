# Loom Video 1 — "What is VAF and Why I Built It"
**Duration:** 8–10 minutes
**Audience:** LinkedIn followers, potential consulting clients, aspiring AI builders
**Goal:** Explain what VAF is, show it working, invite DMs

---

## Setup Before Recording

- [ ] Open Claude Code in v-agentforce-architecture/ (show the repo structure)
- [ ] Have `enterprise/outputs/dashboard.html` ready (or run `./enterprise/demo.sh` beforehand)
- [ ] Have DAILY_START.html open at localhost:3000
- [ ] Have your Obsidian vault open in one tab
- [ ] Clean desktop — only these windows visible
- [ ] Record in 1080p minimum

---

## Script

### HOOK (0:00–0:45)
*Show screen: Claude Code open with the repo*

> "I want to show you the AI system I've been quietly building for the past 6 days. Not a tutorial — the actual thing I use every day to run my life and consulting business. It's called VAF — Vaishali Agent Force — and it's two things at once: a personal AI operating system, and an enterprise data intelligence platform. Same architecture, two different scales. Let me show you both."

---

### THE PROBLEM (0:45–2:00)
*Screen: blank — just talk to camera*

> "Here's the problem I was solving for myself. I'm a builder, a content creator, and I'm trying to manage my health, finances, career, and learning all at the same time. I kept using AI tools, but every time I started a new session, I had to re-explain everything. The AI had no memory of who I was, what I was working on, or what mattered to me.

> The second problem was for the world of Enterprise. They have huge amounts of data, brilliant analysts, and still can't get a clear answer to 'what should I do next' without a week of work. The data exists, the intelligence doesn't flow.

> VAF solves both problems. Different scales, same principle: structured intelligence layers."

---

### THE TWO LAYERS (2:00–3:30)
*Screen: CLAUDE.md file open*

> "There are two layers to understand.

> Layer 1 is what I call Claude Code Contexts. These are 10 specialist agents — think of them as hats that Claude wears depending on what I need. When I'm working on code, FORGE activates. When I'm managing money, PHOENIX takes over. When I'm overwhelmed and don't know where to start, SENTINEL orchestrates everything.

> *[Scroll through CLAUDE.md trigger table]*

> They're not separate apps. They're markdown files that define how Claude behaves in each domain. When I trigger a keyword, Claude reads that agent file and operates with a specific workflow, specific tools, and specific quality standards.

> Layer 2 is the pipeline. This one IS real running code."

---

### THE PIPELINE (3:30–5:30)
*Screen: run `./enterprise/demo.sh` — show it running*

> "9 Python modules, each doing one step of data intelligence. Ingestion, sanitisation, identity enrichment, RAG search, self-evolution, multi-agent council, compliance checking, synthesis, and output delivery.

> *[Show pipeline running in terminal]*

> Watch. I'm going to run the whole thing with one command.

> *[Wait for it to complete, then open dashboard]*

> This dashboard. Every build, its status, how long it took, data quality metrics. This is what your analysts see when they want to know 'did the pipeline run cleanly?'

> The Council — Build 6 — is my favourite. Four AI agents: a Bull, a Bear, a Risk analyst, and a Synthesiser. They analyse in parallel, they disagree, they check each other's work. Then Synthesis turns it into a written brief your C-suite can read in 2 minutes."

---

### THE PERSONAL SYSTEM (5:30–7:00)
*Screen: DAILY_START.html in browser, then Obsidian vault*

> "Now the personal side. This dashboard — I open this every morning. Six agents running my domains: Owlbert for finance, Foxy for content, Whiskers for learning, Bamboo for health.

> But the magic is what happens between sessions. When Claude and I finish a session — like this morning when I was designing architecture — I run /extract-learnings. That triggers my MCP server, which writes the key insights permanently into my Obsidian vault.

> *[Show Obsidian, show the Learnings folder]*

> Next session, Claude has memory. Not because I re-explained it. Because it was crystallised into my knowledge base and retrieved automatically."

---

### THE BIGGER PICTURE (7:00–8:30)
*Screen: repo structure overview*

> "Everything lives in one repository. The personal OS and the enterprise pipeline share the same architecture. When I improve one, the other benefits.

> I'm going to record 12 more videos. One for each agent, explaining what it does, how to trigger it, and what business problem it solves. And one showing the full enterprise demo from cold start to dashboard.

> But more importantly — I'm building this in public. Not just showing the wins. The architecture decisions, the wrong turns, the 'this didn't work the way I thought it would.'

> If you're  thinking about what AI looks like inside your organisation — this is what it looks like when it's actually built. Not slides, not demos of other people's products. Code you can run.

> And if you're a developer or consultant trying to build something like this . Try it out



---

### OUTRO (8:30–9:00)
*Show repo one more time*

> "VAF. Two layers. One system. Building in public. See you in video 2."

---

## Post-Recording

1. Trim silence at start/end
2. Add captions (Loom auto-captions or manual)
3. Thumbnail: Screenshot of dashboard + "AI OS I built for myself"
4. LinkedIn post (see template below)
5. Pin to profile

---

## LinkedIn Post Template

```
I've been quietly building this for 6 months.

It's called VAF — Vaishali Agent Force.

Two things at once:
→ A personal AI OS (10 specialist agents, Obsidian memory)
→ An enterprise data pipeline (9 automated builds, live dashboard)

Built on Claude Code. All runs locally. Zero vendor lock-in.

I just recorded an 8-minute walkthrough: [Loom link]

What you'll see:
• The 10 agents and how they activate
• The 9-build enterprise pipeline running live
• The dashboard auto-generated after the run
• How learnings crystallise to Obsidian between sessions


#AI #BuildInPublic #ClaudeAI #AIStrategy
```
