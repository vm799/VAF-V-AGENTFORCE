# 🚀 VAF IS READY TO USE

Your **Vaishali Agent Force** system is fully built and ready to activate. This is your **one-page quick start**.

---

## ⚡ ONE COMMAND TO START

```bash
cd vaishali-agent-force
bash vaf.sh restart
```

That's it. This starts:
- ✅ Dashboard (http://localhost:8000)
- ✅ Telegram bot (listening for commands)
- ✅ Obsidian sync (auto-syncs to ~/Documents/VAF-Vault/)
- ✅ All 10 agents ready to work
- ✅ Morning/evening Telegram briefings scheduled (07:00 & 21:00)

---

## 📱 THEN, IN ANOTHER TERMINAL

```bash
python3 scripts/watch_folders.py
```

This watches your workflow folders and auto-processes files.

---

## 🎯 THAT'S THE SYSTEM. Here's how to use it:

### **1️⃣ Upload Bank Statements**
```bash
# Drop your CSV or PDF into:
vaishali-agent-force/data/uploads/statements/

# System auto-detects → SENTINEL parses → Dashboard shows trends
# Check: ~/Documents/VAF-Vault/SENTINEL/ for the note
```

### **2️⃣ Start a Build from the Pipeline**
```
Telegram → /save "I want to build a multi-tenant SaaS"
↓
Orchestrator detects topic → routes to right agent
↓
Agent enriches it → Dashboard shows insights
↓
Note appears in Obsidian vault
```

### **3️⃣ Add Learning Content**
```bash
# Drop PDFs, articles, or notes into:
vaishali-agent-force/data/learning/sources/

# System auto-extracts → NEXUS indexes → Dashboard shows learning progress
```

### **4️⃣ Create Teaching Content**
```bash
# Drop your outlines or ideas into:
vaishali-agent-force/data/content/ideas/

# System auto-enhances → AMPLIFY structures → ready to teach
```

### **5️⃣ Keep Adding Knowledge**
```
Open Obsidian → ~/Documents/VAF-Vault/
Create notes → Use agent folders (SENTINEL/, FORGE/, etc.)
System reads them → agents use as context → Dashboard learns
```

---

## 📊 DAILY RHYTHM

**Morning (7:00 AM):**
```
Telegram automatically sends:
🌅 Morning briefing
📊 Captures this week
🎯 Must-act items
💰 Revenue insights
```

**Throughout the day:**
- Use `/save` to feed the pipeline
- Drop files into data/uploads/, data/learning/, data/content/
- System auto-processes them

**Evening (9:00 PM):**
```
Telegram automatically sends:
🌆 Evening brief
🔥 Top themes
🔗 Cross-agent connections
💡 Content ready to teach
```

---

## 🎓 WHAT HAPPENS WHEN YOU USE IT

**Golden Thread Architecture:**

```
YOU (Claude Mobile or Telegram)
  ↓
/save "interesting thought"
  ↓
ORCHESTRATOR (detects agent)
  ↓
AGENT ENRICHES (LLM enhances with context)
  ↓
SQLite STORES (with signal rating: 🟢 must-act, 🟡 valuable, 🔴 noise)
  ↓
OBSIDIAN VAULT (~/Documents/VAF-Vault/)
  ↓
DASHBOARD (http://localhost:8000 shows insights)
```

Every input flows through this pipeline automatically.

---

## 🤖 THE 10 AGENTS WORKING FOR YOU

| Agent | What it does | Input |
|-------|--------------|-------|
| **SENTINEL** | Finance tracking | Bank statements, spending |
| **FORGE** | Architecture & systems | Building ideas, tech decisions |
| **AMPLIFY** | Content creation | Teaching ideas, outlines |
| **PHOENIX** | Career & growth | Learning, development, goals |
| **VITALITY** | Health & fitness | Workouts, health logs |
| **CIPHER** | Research & knowledge | Papers, URLs, research |
| **AEGIS** | Security & risk | Security patterns, compliance |
| **NEXUS** | Education | Learning materials, courses |
| **ATLAS** | Career growth | Skills, opportunities, growth |
| **COLOSSUS** | Revenue & expansion | Business ideas, monetization |

---

## 📂 YOUR FOLDER STRUCTURE

```
vaishali-agent-force/
├── data/
│   ├── uploads/statements/    ← Drop bank statements here
│   ├── learning/sources/      ← Drop learning materials here
│   ├── content/ideas/         ← Drop teaching ideas here
│   └── knowledge_add/         ← Drop knowledge to sync
├── frontend/                   ← React dashboard
├── src/                        ← Python backend
├── scripts/
│   ├── watch_folders.py       ← File watcher (run this)
│   └── vaf.sh                 ← Service manager
├── ACTIVATION.md              ← Detailed workflows guide
└── agents/                     ← 10 agent SKILL.md files
```

---

## ❓ TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| Dashboard won't load | `bash vaf.sh restart` then visit http://localhost:8000 |
| Telegram bot not responding | Check VAF_TELEGRAM_TOKEN in .env is correct |
| Files not auto-processing | Make sure `python3 scripts/watch_folders.py` is running |
| Obsidian vault not syncing | Verify ~/Documents/VAF-Vault/ exists, then restart |
| Morning/evening updates not arriving | Check VAF_TELEGRAM_CHAT_ID in .env is set |

---

## 🎬 GETTING STARTED IN 3 MINUTES

```bash
# 1. Start services (1 terminal)
cd vaishali-agent-force
bash vaf.sh restart

# 2. Start file watcher (another terminal)
python3 scripts/watch_folders.py

# 3. Open dashboard (browser)
http://localhost:8000

# 4. Send your first input (Telegram)
/save "Testing the golden thread with my first input"

# 5. Watch it flow
Dashboard updates → Obsidian note appears → evening briefing arrives
```

---

## 📚 FOR MORE DETAILS

Read **ACTIVATION.md** in the vaishali-agent-force folder. It has:
- ✅ All 5 workflows explained with examples
- ✅ Telegram command reference
- ✅ File format specifications
- ✅ Troubleshooting guide

---

## 🏆 YOU'RE ALL SET

The system is built, tested, and ready. Everything flows through:

**Input → Orchestrator → Enrichment → Obsidian → Dashboard**

Start with any workflow. The system learns and improves with every input.

**Go build something amazing. 💪**
