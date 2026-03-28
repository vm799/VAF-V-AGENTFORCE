# AgentForce + OpenViking: Architecture Augmentation Strategy

## What You Have vs What OpenViking Adds

| Capability | V AgentForce Today | With OpenViking Patterns | Gap |
|---|---|---|---|
| **Context storage** | Obsidian vault (flat folders) + MCP | Hierarchical `viking://` filesystem with URIs | Restructure vault into tiered hierarchy |
| **Context loading** | All-or-nothing (load full 8-12KB agent file) | L0/L1/L2 tiered loading (100 → 2K → full) | Add abstracts + overviews to every context node |
| **Retrieval** | `search_knowledge` (flat text search via MCP) | Directory recursive retrieval with score propagation | Replace flat search with hierarchical drill-down |
| **Memory extraction** | Manual `/extract-learnings` command | Automatic 6-category extraction after every session | Automate the extraction + add deduplication |
| **Memory persistence** | `crystallize_learning` (manual MCP call) | Auto-persisted, vectorized, searchable | Automate persistence + add vector search |
| **Observability** | None — can't trace why context was picked | Full retrieval trajectory with scores | Add trajectory logging |
| **Session management** | No session memory between conversations | Automatic session archiving + compression | Add session commit + archival |
| **Self-evolution** | None — agent starts fresh each session | Agent improves with every interaction | Close the feedback loop |

---

## Augmentation Plan: 5 Layers

### Layer 1: Restructure Obsidian Vault as Semantic Filesystem

**Current vault structure:**
```
SecondBrain/AgentForce/
├── 00 INBOX/
├── 01 Brain Dumps/
├── 02 Finance/
├── 03 Builds/
├── 04 Content/
├── 05 Teaching/
├── 06 Learning/
├── 07 Health/
├── 08 Career/
├── 09 Daily Notes/
├── 10 Goals/
└── 99 Archive/
```

**Target structure (OpenViking-aligned):**
```
SecondBrain/AgentForce/
├── resources/                          # Knowledge base (L0/L1/L2)
│   ├── enterprise-pipeline/
│   │   ├── .abstract.md               # L0: "10-build data intelligence pipeline"
│   │   ├── .overview.md               # L1: Architecture + navigation
│   │   ├── specs/                     # L2: Full build specs
│   │   └── docs/                      # L2: Full documentation
│   ├── market-intelligence/
│   │   ├── .abstract.md
│   │   ├── .overview.md
│   │   ├── sector-reports/
│   │   └── competitor-profiles/
│   ├── finance/
│   │   ├── .abstract.md
│   │   ├── .overview.md
│   │   ├── statements/
│   │   └── goals/
│   └── learning/
│       ├── .abstract.md
│       ├── .overview.md
│       ├── ai-news/
│       └── syntheses/
│
├── user/                               # V's persistent memory
│   └── memories/
│       ├── preferences/                # "Prefers direct answers"
│       │   ├── communication.md
│       │   ├── coding.md
│       │   └── business.md
│       ├── entities/                   # People, projects, concepts
│       │   ├── projects/
│       │   │   ├── kidsvid-pipeline.md
│       │   │   └── enterprise-pipeline.md
│       │   └── people/
│       └── events/                     # Decisions, milestones (immutable)
│           ├── 2026-03-28-atlas-venture-eval.md
│           └── 2026-03-28-kidsvid-decision.md
│
├── agent/                              # Agent learned intelligence
│   ├── memories/
│   │   ├── cases/                      # Problem → solution pairs
│   │   │   ├── roi-question-atlas-framework.md
│   │   │   └── multi-agent-routing.md
│   │   └── patterns/                   # Reusable strategies
│   │       ├── venture-evaluation-pattern.md
│   │       └── context-loading-pattern.md
│   ├── skills/                         # Tool definitions
│   └── instructions/                   # Agent 00-09 directives
│
├── sessions/                           # Conversation archives
│   ├── 2026-03-28-kidsvid-planning/
│   │   ├── .abstract.md
│   │   ├── .overview.md
│   │   └── messages.jsonl
│   └── history/
│
└── inbox/                              # Capture (clears daily)
```

**What changes:**
- Add `.abstract.md` (L0) and `.overview.md` (L1) to every directory
- Separate `user/memories/` from `agent/memories/` (user prefs vs agent learnings)
- Add `sessions/` for conversation archival
- Keep `inbox/` for quick capture

**What stays:**
- Obsidian remains the storage backend
- MCP server remains the access layer
- Telegram bot still captures to inbox/

---

### Layer 2: Add L0/L1/L2 to MCP Server

**Current MCP tools:**
```
fetch_knowledge    — Read a document
search_knowledge   — Full-text search
crystallize_learning — Save insight
validate_compliance  — Check against standards
```

**New MCP tools to add:**
```
abstract(uri)        — Read L0 (~100 tokens) for quick relevance check
overview(uri)        — Read L1 (~2K tokens) for structural understanding
read(uri)            — Read L2 (full content) only when needed
tree(uri, depth)     — Show hierarchy with L0 summaries
ls(uri)              — List directory contents with L0s
search(query)        — Hierarchical search (replaces flat search_knowledge)
commit_session(id)   — Archive + auto-extract memories
```

**Implementation in `mcp/src/index.js`:**

```javascript
// New tools to register
{
  name: "abstract",
  description: "Read L0 abstract (~100 tokens) for quick relevance check",
  inputSchema: { uri: "string" },
  handler: async ({ uri }) => {
    const abstractPath = path.join(uri, '.abstract.md');
    return fs.readFile(abstractPath, 'utf8');
  }
},
{
  name: "overview",
  description: "Read L1 overview (~2K tokens) for structural understanding",
  inputSchema: { uri: "string" },
  handler: async ({ uri }) => {
    const overviewPath = path.join(uri, '.overview.md');
    return fs.readFile(overviewPath, 'utf8');
  }
},
{
  name: "tree",
  description: "Show directory hierarchy with L0 summaries",
  inputSchema: { uri: "string", depth: "number" },
  handler: async ({ uri, depth = 3 }) => {
    // Walk directory, collect .abstract.md at each level
    // Return formatted tree with L0 annotations
  }
}
```

---

### Layer 3: Add Tiered Loading to Agent Files

**Current agent loading:**
```
Trigger "ROI" → Load agents/08_ATLAS.md (3.5KB, ALL content)
```

**With tiered loading:**
```
agents/
├── 08_ATLAS/
│   ├── .abstract.md        # L0: "Career & business strategist. Venture evaluation."
│   ├── .overview.md         # L1: Framework names, trigger words, key concepts
│   └── full.md              # L2: Complete agent context (only loaded when needed)
```

**CLAUDE.md routing with tiers:**
```
| Signal | Agent | L0 | Full |
|--------|-------|----|------|
| ROI, business idea | ATLAS | agents/08_ATLAS/.abstract.md | agents/08_ATLAS/full.md |
```

**Step 1:** Load L0 to confirm this is the right agent (~100 tokens)
**Step 2:** If confirmed, load full context (~3.5KB)

**Token savings:** For a question that triggers 3 agents, loading 3 L0s (300 tokens) to pick the right one vs loading 3 full agents (25KB) = 98% savings on routing.

---

### Layer 4: Automatic Session Memory (Self-Evolution)

**Current flow:**
```
V talks to Claude → Claude answers → V manually runs /extract-learnings → MCP saves to vault
```

**Target flow:**
```
V talks to Claude → Claude answers → Session auto-commits →
  Background: Extract 6 categories of memory →
  Background: Deduplicate against existing →
  Background: Persist to user/memories/ and agent/memories/
  Next session: Claude retrieves relevant memories automatically
```

**Implementation approach:**

Add a `/finish` hook or session-end trigger that:
1. Archives the conversation to `sessions/{date}-{topic}/messages.jsonl`
2. Generates `.abstract.md` and `.overview.md` for the session
3. Extracts memories into 6 categories (via Claude API call)
4. Deduplicates against existing memories in vault
5. Persists new/merged memories

**Memory extraction prompt:**
```
Analyze this conversation and extract:

USER MEMORIES:
- profile: Identity facts about the user
- preferences: What they like/dislike, communication style
- entities: Projects, people, concepts they reference
- events: Decisions made, milestones reached (with dates)

AGENT MEMORIES:
- cases: Problem → solution pairs that worked
- patterns: Reusable strategies that proved effective

For each memory:
- Check if similar memory exists (I'll provide existing memories)
- If duplicate: SKIP
- If similar: MERGE (combine into one)
- If new: CREATE
- If contradicts existing: DELETE old + CREATE new
```

---

### Layer 5: Observable Context for Enterprise Clients

**For the enterprise pipeline (v-enterprise-architecture):**

Add retrieval trajectory logging to every Build that uses context:

```python
# In Build 06 (Council) — when agents retrieve context for evaluation

trajectory = {
    "query": "Evaluate pattern: AAPL volume anomaly",
    "steps": [
        {"action": "INTENT", "queries": ["equity anomaly pattern", "AAPL historical"]},
        {"action": "SEARCH", "dir": "resources/market-data/", "score": 0.89},
        {"action": "DRILL", "dir": "resources/market-data/equities/", "score": 0.93},
        {"action": "MATCH", "file": "aapl-vol-baseline.json", "score": 0.97},
        {"action": "CONVERGE", "rounds": 2}
    ],
    "result": "Used aapl-vol-baseline.json because: highest score (0.97) in correct hierarchy"
}
```

**For CEO delivery (Build 08 formatting):**

Include retrieval trajectory in executive briefs:

```
INSIGHT: AAPL volume anomaly detected (3.2σ)
CONFIDENCE: 0.94

EVIDENCE TRAIL:
├── Source: market-data/equities/aapl-vol-baseline.json (match: 0.97)
├── Context: market-data/equities/ directory (relevance: 0.93)
├── Cross-ref: user/memories/events/aapl-position-increase-2026-02
└── Search converged in 2 rounds (high confidence)

[Full trajectory available in audit log]
```

---

## Enterprise Product: "V Intelligence Memory"

### The Pitch

```
FOR: CEOs and enterprise leaders who need AI that:
  - Remembers every decision, every context, every preference
  - Gets smarter with every interaction (no retraining)
  - Explains WHY it retrieved certain information (audit trail)
  - Costs 87% less in tokens than traditional RAG
  - Works with their existing knowledge base

WHAT: A context database layer that sits between your AI agent
      and your knowledge base, adding:
  ✓ Tiered context loading (87% token reduction)
  ✓ Hierarchical search (46% better results)
  ✓ Automatic memory extraction (self-evolving agent)
  ✓ Full retrieval observability (compliance-ready)
  ✓ Multi-tenant isolation (per-user privacy)

HOW: Deploy as MCP server + Obsidian/Confluence/SharePoint backend
     Integrates with Claude, GPT, or any LLM
     Self-hosted or cloud


```

### Revenue Path

```
ATLAS VENTURE EVAL — V Intelligence Memory
============================================================

1. MARKET: Enterprise AI memory is a $2B+ market by 2027
2. AUTOMATION: 90% — deploy once, runs autonomously
3. TIME TO REVENUE: 3 months (first corporate training client)
4. COST: £500/month hosting → £10K/month enterprise license
5. COMPOUNDING: YES — every client interaction improves the product
6. MOAT FIT: Finance + AI + enterprise + teaching = PERFECT fit
7. OPPORTUNITY COST: Enhances (not replaces) existing pipeline work

VERDICT: BUILD
CONFIDENCE: High
FIRST 48-HOUR ACTION: Restructure Obsidian vault with L0/L1/L2 pattern
```

---

## Implementation Priority

| Priority | What | Impact | Effort |
|----------|------|--------|--------|
| 1 | Add `.abstract.md` + `.overview.md` to vault directories | 87% token savings on navigation | Low (script + Claude API) |
| 2 | Add `abstract`, `overview`, `tree` tools to MCP server | Tiered loading for all agents | Medium |
| 3 | Restructure vault into `resources/user/agent/session` hierarchy | Semantic filesystem paradigm | Medium |
| 4 | Auto-extract memories on session end | Self-evolution loop | High |
| 5 | Add retrieval trajectory logging | Observable context for enterprise | Medium |
| 6 | Package as enterprise product | Revenue generation | High |
