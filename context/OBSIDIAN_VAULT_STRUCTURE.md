# Obsidian Vault Structure — V AgentForce Semantic Filesystem
> The canonical folder map for V's tiered context database.
> Architecture: OpenViking-inspired L0/L1/L2 tiered loading.

---

## Philosophy

The vault is V's **semantic context database** — not just storage, but an intelligent filesystem where every directory knows what it contains (L0 abstract), how it's structured (L1 overview), and the full detail is loaded only when needed (L2).

**Loading protocol:** L0 first → L1 if relevant → L2 only when confirmed. **87% token savings.**

Every directory has:
- `.abstract.md` (~100 tokens) — one-sentence summary for instant relevance check
- `.overview.md` (~2K tokens) — structural overview with navigation to children

---

## Folder Structure

```
SecondBrain/AgentForce/
│
├── resources/                              # EXTERNAL KNOWLEDGE
│   ├── enterprise-pipeline/                # VAF 10-build data intelligence pipeline
│   ├── market-intelligence/                # Sector reports, competitor analysis
│   ├── learning/                           # AI research, CIPHER syntheses
│   ├── consulting/                         # Client frameworks, processes
│   └── standards/                          # Compliance, governance, ADRs
│
├── user/                                   # V'S PERSISTENT MEMORY
│   └── memories/
│       ├── preferences/                    # Communication, business, coding style
│       ├── entities/                       # Projects, people, concepts
│       └── events/                         # Decisions, milestones (immutable)
│
├── agent/                                  # AGENT LEARNED INTELLIGENCE
│   ├── memories/
│   │   ├── cases/                          # Problem → solution pairs (immutable)
│   │   └── patterns/                       # Reusable strategies (mergeable)
│   ├── skills/                             # Tool definitions
│   └── instructions/                       # Agent 00-09 directives
│
├── sessions/                               # CONVERSATION ARCHIVES
│   ├── {session-id}/
│   │   ├── .abstract.md                    # What was discussed
│   │   ├── .overview.md                    # Key decisions, outcomes
│   │   └── messages.jsonl                  # Full conversation
│   └── history/
│
└── inbox/                                  # Quick capture (clears daily)
```

---

## Memory Categories

| Category | Scope | Mutability | Example |
|----------|-------|-----------|---------|
| **preferences** | user | appendable | "Prefers direct answers, ROI focus" |
| **entities** | user | appendable | "Project: KidsVid pipeline" |
| **events** | user | immutable | "Decided to expand ATLAS (2026-03-28)" |
| **cases** | agent | immutable | "ROI question → ATLAS venture eval" |
| **patterns** | agent | mergeable | "Multi-agent: route to PRIMARY INTENT" |

**Immutable** = historical record, never changed
**Appendable** = grows over time (new info added)
**Mergeable** = refined as agent learns more

---

## MCP Access Protocol

```
# 1. Navigate (cheap, ~500 tokens)
tree("resources", depth=2)

# 2. Check relevance (very cheap, ~100 tokens)
abstract("resources/enterprise-pipeline")

# 3. Understand structure (medium, ~2K tokens)
overview("resources/enterprise-pipeline")

# 4. Load full content (expensive, only when needed)
fetch_knowledge("build-06-council")

# 5. Search with directory context
search_knowledge("council agent debate")

# 6. Persist memories
save_memory("agent", "cases", "name", "content")
save_memory("user", "preferences", "name", "content")

# 7. Archive sessions
commit_session("session-id", messages, abstract, overview)
```

---

## Tag Taxonomy

- Domain: `#finance`, `#builds`, `#content`, `#teaching`, `#health`, `#learning`, `#career`
- Agent: `#agent/sentinel`, `#agent/forge`, `#agent/amplify`, `#agent/phoenix`, `#agent/vitality`, `#agent/cipher`, `#agent/aegis`, `#agent/nexus`, `#agent/atlas`, `#agent/colossus`
- Status: `#status/inbox`, `#status/active`, `#status/done`, `#status/paused`
- Memory: `#memory/preference`, `#memory/entity`, `#memory/event`, `#memory/case`, `#memory/pattern`
- Context tier: `#L0`, `#L1`, `#L2`

---

## Legacy Compatibility

Original folders preserved but content mirrored to semantic structure:
- `ADRs/` → `resources/standards/adrs/`
- `Standards/` → `resources/standards/`
- `Processes/` → `resources/consulting/processes/`
- `Learnings/` → `agent/memories/patterns/`
