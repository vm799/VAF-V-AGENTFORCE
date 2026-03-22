# 🚀 VAF ACTIVATION GUIDE — Your System is Ready

**Welcome to the Vaishali Agent Force Golden Thread.** This guide walks you through 5 workflows to start using your system immediately.

---

## ⚡ ONE-TIME SETUP (5 minutes)

```bash
cd vaishali-agent-force
bash vaf.sh restart
```

This starts:
- Dashboard on http://localhost:8000
- Telegram bot (listening for /save, /quick, /weekly)
- Obsidian sync (pushes captures to ~/Documents/VAF-Vault/)
- All 10 agents ready

Then:
```bash
# In another terminal:
python3 scripts/watch_folders.py
```

This monitors your data/uploads/, data/learning/, data/content/ folders and auto-processes them.

---

## 📊 WORKFLOW 1: Upload Bank Statements

**Where:** `vaishali-agent-force/data/uploads/statements/`
**What:** Drop your .csv or .pdf bank statements
**Who processes it:** SENTINEL (Finance Agent)
**Output:** Appears in Dashboard → Finance Panel, Obsidian vault

**Steps:**
1. Drop your statement file in: `data/uploads/statements/`
2. Wait 10 seconds (watch_folders.py detects it)
3. Dashboard shows: parsed transactions, trends, anomalies
4. Check: `~/Documents/VAF-Vault/SENTINEL/` for the processed note

**Example:**
```bash
# Copy your statement
cp ~/Downloads/Chase_Statement_Jan2026.csv vaishali-agent-force/data/uploads/statements/

# System auto-detects → SENTINEL parses → Dashboard updates
# Check Obsidian: ~/Documents/VAF-Vault/SENTINEL/Chase_Jan2026.md
```

---

## 🏗️ WORKFLOW 2: Start a Build from the Pipeline

**Where:** Telegram bot `/save` command
**What:** Say anything related to architecture, systems, or building
**Who processes it:** FORGE (Architecture Agent) + Orchestrator
**Output:** Enriched capture → Obsidian → Dashboard intelligence

**Steps:**
1. Open Telegram, find your VAF bot
2. Send: `/save I want to build a multi-tenant SaaS with microservices`
3. Wait 3 seconds (orchestrator enriches it)
4. Dashboard shows:
   - Which agent claimed it (FORGE)
   - Signal rating (🟢 must-act, 🟡 valuable, 🔴 noise)
   - Summary + key insights
   - Action items

**Example:**
```
Telegram → /save "Need to architect a real-time dashboard with WebSockets and Kafka"
↓
Orchestrator detects "architecture" + "real-time" → routes to FORGE
↓
FORGE enriches with: component patterns, trade-offs, code examples
↓
Dashboard shows signal = 🟢 (must-act), summary, insights
↓
Obsidian: ~/Documents/VAF-Vault/FORGE/architecture_dashboard_XXXXXX.md
```

---

## 📚 WORKFLOW 3: Add Learning Content

**Where:** `vaishali-agent-force/data/learning/sources/`
**What:** Drop .txt, .md, or .pdf files with content you want to learn from
**Who processes it:** NEXUS (Education Agent)
**Output:** Structured learning notes in Obsidian, searchable in Dashboard

**Steps:**
1. Save article/paper/tutorial to: `data/learning/sources/`
2. System extracts key concepts, summaries, connections
3. Check Dashboard → Education Panel for: topics, connections, progress
4. Obsidian: ~/Documents/VAF-Vault/NEXUS/ shows your learning graph

**Example:**
```bash
# Save a machine learning paper
curl https://arxiv.org/pdf/2401.12345.pdf -o vaishali-agent-force/data/learning/sources/transformers_2024.pdf

# System processes → NEXUS enriches → Dashboard shows learning progress
# Obsidian note: ~/Documents/VAF-Vault/NEXUS/transformers_2024_summary.md
```

---

## 🎓 WORKFLOW 4: Create Content to Teach

**Where:** `vaishali-agent-force/data/content/ideas/`
**What:** Drop your teaching ideas, outline, or raw thoughts
**Who processes it:** AMPLIFY (Content Agent)
**Output:** Polished teaching content → Obsidian → ready to publish

**Steps:**
1. Write or drop your idea in: `data/content/ideas/`
2. AMPLIFY processes: structures it, finds teaching angles, suggests examples
3. Dashboard shows: content pipeline, publication status
4. Obsidian: ~/Documents/VAF-Vault/AMPLIFY/ has your teaching materials

**Example:**
```bash
# Create a teaching outline
echo "# How to Build Microservices
- Event-driven architecture
- Message queues (Kafka, RabbitMQ)
- Distributed transactions
- Example: eCommerce order service" > vaishali-agent-force/data/content/ideas/microservices_course.md

# AMPLIFY enriches it → expands examples → suggests narrative structure
# Obsidian: ~/Documents/VAF-Vault/AMPLIFY/microservices_course_FULL.md
# Dashboard: marks as "ready to teach"
```

---

## 🧠 WORKFLOW 5: Keep Adding Knowledge

**Where:** `~/Documents/VAF-Vault/` (your Obsidian vault)
**What:** Add notes, insights, connections in Obsidian
**Who reads it:** All 10 agents sync back via MCP
**Output:** Your knowledge becomes part of the system's context

**Steps:**
1. Open Obsidian
2. Create notes in your vault: `~/Documents/VAF-Vault/`
3. Use agent folders: SENTINEL/, FORGE/, AMPLIFY/, etc.
4. Tag your notes (e.g., `#revenue`, `#architecture`, `#learning`)
5. System automatically reads them → agents use as context → Dashboard surfaces insights

**Example:**
```
Obsidian note: ~/Documents/VAF-Vault/INSIGHTS/revenue_expansion.md

Content:
---
agent: COLOSSUS
tags: #revenue #expansion #SaaS
---
# Revenue Expansion Ideas
- Implement tiered pricing tiers
- Add API rate-limit monetization
- Cross-sell to existing customers

---

System reads this → COLOSSUS incorporates in future decisions → Dashboard shows patterns
```

---

## 📱 MORNING & EVENING TELEGRAM UPDATES

You'll receive automated Telegram updates every day:

**Morning (8:00 AM):**
```
🌅 Good morning! Here's your VAF status:

📊 Captures this week: 23 (18 enriched)
🎯 Must-act items: 3 (all from FORGE)
💰 Revenue insights: 2 new opportunities in your Obsidian
📚 Learning progress: 5 new concepts added
```

**Evening (6:00 PM):**
```
🌆 Evening brief:

🔥 Top themes this week: "microservices", "real-time", "monetization"
🔗 Cross-agent connections: FORGE ↔ COLOSSUS on pricing architecture
💡 Content ideas ready to teach: 2 (eCommerce & APIs)
👤 Goggins check: 8.2/10 today, 7-day streak active
```

---

## 🎯 YOUR DAILY RHYTHM

**Morning:**
1. Open Telegram → read morning brief
2. Open Dashboard (localhost:8000) → scan intelligence feed
3. Open Obsidian → review any new insights from yesterday

**Throughout the day:**
- Send statements to `/uploads/statements/` → auto-processed
- Slack a thought to Telegram `/save` → enriched in real-time
- Drop learning materials to `data/learning/sources/` → indexed
- Write teaching content in Obsidian → system enhances it

**Evening:**
1. Check Telegram → read evening brief
2. Review Dashboard → see what the agents discovered
3. Add any knowledge to Obsidian → sync back to system

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Dashboard won't load | `bash vaf.sh restart` and check http://localhost:8000 |
| Telegram bot not responding | `bash vaf.sh logs` and check bot service |
| Files not auto-processing | Check `python3 scripts/watch_folders.py` is running |
| Obsidian not syncing | Verify `~/Documents/VAF-Vault/` exists, then `bash vaf.sh restart` |
| Telegram updates not arriving | Set timezone in `.env`: `TZ=America/New_York` |

---

## 🚀 YOU'RE READY

The system is now production-ready. Use these 5 workflows to:
- ✅ Upload statements → SENTINEL enriches
- ✅ Build from pipeline → FORGE + Orchestrator enriches
- ✅ Add learning → NEXUS indexes
- ✅ Create teaching → AMPLIFY polishes
- ✅ Keep adding knowledge → System evolves

**Golden Thread:** Input (Claude Mobile / Telegram) → Orchestrator → Obsidian → Dashboard → Insights

Start with Workflow 1 or 2. The system learns and gets better with every input.

Questions? Check the logs: `bash vaf.sh logs`
