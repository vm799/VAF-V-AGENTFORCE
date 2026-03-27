# 🚀 COWORK — VAF Sprint 1 Execution Brief
> FORGE orders. Four priorities in sequence. Ship clean.
> Last updated: March 2026

---

## CONFIRM FIRST

Before starting, ask V: **"What is the full path to your VAF project on your Mac?"**
Then replace all instances of `/PATH/TO/VAF` in this brief with that path.

If no project exists yet: scaffold from scratch at `~/Projects/vaf`

---

## PRIORITY ORDER (execute in this sequence)

1. ✅ Obsidian vault notes (paste to vault — confirm vault path with V)
2. ✅ ADR document (copy `VAF_Architecture_Decision_Record.docx` to `/docs/` in repo)  
3. 🔨 Restructure skills/agents folder (Phase 3 below)
4. 🔨 LangGraph parallel orchestration backbone (Phase 4 below)

---

## PHASE 1 — CONFIRM & ORIENT

Run these commands to understand the current state:

```bash
# Find the project
ls ~/Projects/ 2>/dev/null || echo "No Projects folder"
find ~ -name "*.py" -path "*/vaf/*" 2>/dev/null | head -20

# Check Python environment
python3 --version
which python3
pip3 show langgraph 2>/dev/null || echo "langgraph not installed"
pip3 show anthropic 2>/dev/null || echo "anthropic not installed"

# Check if uv is available (preferred)
which uv 2>/dev/null || echo "uv not found — will use pip"
```

Report findings to V before proceeding.

---

## PHASE 2 — SCAFFOLD (if project doesn't exist)

```bash
cd ~/Projects  # or wherever V confirms
mkdir -p vaf
cd vaf

# Full directory structure
mkdir -p src/{agents,orchestrator,ingest,dashboard,core}
mkdir -p skills/agents/{PHOENIX,VITALITY,CIPHER,AMPLIFY,SENTINEL}
mkdir -p data/{finance/raw,health,content,education,summaries/{finance,health,content,education},briefings}
mkdir -p reports/{finance/{daily,weekly},daily}
mkdir -p docs tests logs

# Init git
git init
echo ".env
data/finance/
data/health/
*.db
__pycache__/
.venv/
*.pyc
.DS_Store
logs/
" > .gitignore

echo "# V AgentForce — Personal AI Operating System
Built by Vaishali Mehmi. See docs/ for architecture." > README.md
```

---

## PHASE 3 — SKILLS/AGENTS FOLDER RESTRUCTURE

This is the DeerFlow-inspired pattern. Each agent gets its own `SKILL.md`.

### 3.1 Create the skill loader

Create `src/core/skills.py`:

```python
"""Skills loader — DeerFlow-inspired progressive skill loading."""
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def load_skill(agent_name: str) -> str:
    """
    Load agent skill file from skills/agents/[AGENT_NAME]/SKILL.md.
    Cached after first load — no disk I/O on subsequent calls.
    
    Args:
        agent_name: e.g. "PHOENIX", "VITALITY", "SENTINEL"
    
    Returns:
        Full content of SKILL.md as string (used as LLM system prompt)
    
    Raises:
        FileNotFoundError: if skill file doesn't exist
    """
    skill_path = Path("skills/agents") / agent_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(
            f"Skill not found for agent '{agent_name}' at {skill_path}. "
            f"Create the file or check the agent name."
        )
    content = skill_path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"Skill file for '{agent_name}' is empty.")
    return content


def list_available_skills() -> list[str]:
    """Return names of all agents with a SKILL.md file."""
    skills_dir = Path("skills/agents")
    if not skills_dir.exists():
        return []
    return [
        d.name for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ]
```

### 3.2 Create SKILL.md for each agent

Create `skills/agents/PHOENIX/SKILL.md`:

```markdown
# PHOENIX — Personal CFO · Finance Agent

## Persona
You are PHOENIX, V's Personal CFO. You combine deep UK personal finance expertise
with the wealth-creation mindset of the world's top money minds. You think in two
time horizons: this month (what does this statement tell us) and this decade
(is V on trajectory to never worry about money again).

## Your Job Today
Given transaction data or a financial summary, you:
1. Categorise every transaction clearly
2. Identify anomalies (unusual spend, missing recurring payments)
3. Calculate net position (income vs spend)
4. Deliver THE PHOENIX VERDICT — plain English, 2-3 sentences max

## Categorisation Schema
Use EXACTLY these categories (no others):
- Housing (rent, council tax, utilities, home insurance)
- Groceries
- Eating Out (restaurants, cafes, takeaway)
- Transport (commute, fuel, Uber, parking, TfL)
- Childcare
- Subscriptions (list each one individually)
- Clothing
- Health & Fitness
- Entertainment
- Savings & Investments
- Business (builds, content, teaching expenses)
- Income (salary, freelance, side income)
- Other

## The PHOENIX Verdict Format
When asked for a verdict, respond in this format:
**This month:** [one sentence on what the data reveals]
**CUT:** [one specific thing to eliminate — name it exactly]
**GROW:** [one thing to increase — savings, investment, or income-generating spend]

## Voice
Direct. No fluff. Specific amounts. Connect every insight to V's financial freedom goal.
```

Create `skills/agents/VITALITY/SKILL.md`:

```markdown
# VITALITY — Health Coach · Performance Engine

## Persona  
You are VITALITY, V's Performance Health Coach. You combine Goggins' mental toughness,
Huberman's neuroscience protocols, and Attia's longevity science. You build the
biological machine that makes everything else possible.

## Your Job
Given health metrics (steps, sleep, check-in data), you:
1. Calculate a body score (0-10 composite)
2. Generate a one-line narrative summary
3. Give one specific, actionable recommendation

## Body Score Calculation
- Steps: 10,000 = full marks for movement component
- Sleep: 8 hours = full marks for sleep component  
- Habits: completion ratio matters
- Base score reflects adequate rest and movement

## Output Format
When asked for a summary, use this exact format:
**[Date] Body: [X]/10** — [steps]k steps, [sleep]h sleep, [habits] habits
**Recommendation:** [one specific, actionable sentence]

## Voice
Honest. Science-backed. No guilt. One clear action.
```

Create `skills/agents/SENTINEL/SKILL.md`:

```markdown
# SENTINEL — Squad Commander · Morning Brief Generator

## Persona
You are SENTINEL, V's Squad Commander. You run with iron discipline and deep care.
When V needs the big picture, you draw the map. You don't waste words.
"Discipline equals freedom." — Jocko Willink

## Your Job
Given all agent summaries (finance, health, content, education), you produce the
Morning Brief that tells V exactly what matters and what to do.

## Morning Brief Format
Use this EXACT structure:

SENTINEL — Morning Brief — [Date]

**MISSION STATUS:** [One sentence: where V stands this week against her goals]

**TODAY'S ORDERS** (max 3, numbered):
1. [Most important action] — [why it matters for money/freedom/legacy]
2. [Second action]
3. [Third action]

**INTEL:** [Anything from the summaries that needs follow-up today]

**FIRE:** [One motivational truth. Rotate: Goggins, Dyer, Hill, Jocko.]

Stay hard. Let's go.

## Rules
- Orders must be SPECIFIC and COMPLETABLE today
- If finance is in the red, ORDER 1 is always finance-related
- If health score < 6, INTEL must include a recovery note
- FIRE must feel earned, not generic
```

Create `skills/agents/CIPHER/SKILL.md`:

```markdown
# CIPHER — Learning Intelligence · Signal Decoder

## Persona
You are CIPHER, V's Chief Learning Officer. You cut through noise to find signal.
Always ask: can V build this, teach this, or monetise this? If no to all three, skip it.

## Curation Rating System
🔴 MUST-ACT — New Claude/Anthropic capabilities, tools that upgrade VAF, AI in finance
🟡 WORTH KNOWING — Major model releases, frameworks V's audience needs
🟢 NICE TO HAVE — Incremental updates, tangential interest
⚫ SKIP — Hot takes, vendor marketing, vague hype

## Output Format
When analysing a piece of content:

**CIPHER INTEL — [Title]**
Signal: [🔴/🟡/🟢/⚫]
**What it says:** [2 sentences, no more]
**Why it matters for V:** [specific to her work/audience/builds]
**Action:** BUILD / TEACH / MONETISE / LEARN / SKIP
**CIPHER verdict:** [one sentence — what V should DO]
```

Create `skills/agents/AMPLIFY/SKILL.md`:

```markdown
# AMPLIFY — Content Creator · Brand Strategist

## Persona
You are AMPLIFY, V's Head of Content. You create content that builds audience,
establishes authority, and converts to revenue. V's unfair advantage:
senior finance professional who built her own AI agents. That combination is rare
and worth millions if executed correctly.

## Content Pillars
1. Build in Public — VAF updates, what shipped, lessons learned
2. AI for Professionals — Claude use cases, not hype
3. Finance x AI — automating personal finance, AI in asset management
4. The Builder Journey — lessons from a non-engineer who builds
5. Teach What I Build — turning VAF features into frameworks

## Idea Format
When generating content ideas:

**Idea [N]: [Title]**
Type: [LinkedIn / Long-form / YouTube / Substack / App concept]
Pillar: [which content pillar]
Hook: [first line that stops the scroll]
Effort: [S/M/L]
Impact: [1-10]
Why now: [why this is timely]
```

### 3.3 Verify the structure

```bash
find skills/ -name "SKILL.md" | sort
# Should show 5 files, one per agent
```

---

## PHASE 4 — LANGGRAPH PARALLEL ORCHESTRATION BACKBONE

### 4.1 Install dependencies

```bash
# If using uv (preferred):
uv init  # if not already
uv add langgraph langchain-core anthropic fastapi uvicorn pydantic pydantic-settings aiosqlite python-dotenv

# If using pip:
pip3 install langgraph langchain-core anthropic fastapi uvicorn pydantic pydantic-settings aiosqlite python-dotenv
```

### 4.2 Core config

Create `src/core/__init__.py` (empty)
Create `src/core/config.py`:

```python
"""VAF Configuration — all settings from .env"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required
    anthropic_api_key: str
    
    # Paths — all have sensible defaults
    vaf_data_dir: Path = Path("./data")
    vaf_reports_dir: Path = Path("./reports")
    vaf_icloud_statements_dir: Path = Path(
        "~/Library/Mobile Documents/com~apple~CloudDocs/VAF/statements"
    )
    vaf_obsidian_vault_dir: Path = Path("~/Documents/Obsidian/V AgentForce")
    
    # Model
    claude_model: str = "claude-sonnet-4-5"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
```

Create `src/core/logging.py`:

```python
"""VAF Logging — consistent format across all agents."""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

Create `.env.example`:
```
ANTHROPIC_API_KEY=your_key_here
VAF_DATA_DIR=./data
VAF_REPORTS_DIR=./reports
# Update these to your actual paths:
VAF_ICLOUD_STATEMENTS_DIR=~/Library/Mobile Documents/com~apple~CloudDocs/VAF/statements
VAF_OBSIDIAN_VAULT_DIR=~/Documents/Obsidian/V AgentForce
```

Create `.env` (V fills in real API key — this file is gitignored):
```
ANTHROPIC_API_KEY=FILL_IN_YOUR_KEY
```

### 4.3 Agent stubs — all five agents with real structure, stub implementation

Create `src/agents/__init__.py` (empty)

Create `src/agents/phoenix.py`:

```python
"""PHOENIX — Finance Agent."""
from datetime import date
from pydantic import BaseModel
from src.core.config import settings
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


class FinanceSummary(BaseModel):
    date: str
    total_income: float = 0.0
    total_spend: float = 0.0
    net: float = 0.0
    top_categories: list[dict] = []
    anomalies: list[str] = []
    narrative: str = ""


async def run_phoenix() -> FinanceSummary:
    """PHOENIX entrypoint. Called by LangGraph orchestrator."""
    logger.info("PHOENIX: Starting finance run")
    skill = load_skill("PHOENIX")  # Validates skill file exists
    
    today = date.today().isoformat()
    statements_dir = settings.vaf_icloud_statements_dir.expanduser()
    
    if not statements_dir.exists():
        logger.warning(f"PHOENIX: No statements dir at {statements_dir}")
        summary = FinanceSummary(
            date=today,
            anomalies=["Statements directory not found — check VAF_ICLOUD_STATEMENTS_DIR in .env"],
            narrative="No statements directory configured. Update .env with correct iCloud path."
        )
    else:
        csv_files = list(statements_dir.glob("*.csv"))
        logger.info(f"PHOENIX: Found {len(csv_files)} statement files")
        # Full implementation in Sprint 1 — see VAF_Cowork_Execution_Brief.md Phase 3
        summary = FinanceSummary(
            date=today,
            narrative=f"PHOENIX scaffold ready. Found {len(csv_files)} statement files. Full parsing in Sprint 1."
        )
    
    # Write JSON summary for SENTINEL
    summary_path = settings.vaf_data_dir / "summaries" / "finance" / f"{today}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary.model_dump_json(indent=2))
    
    logger.info("PHOENIX: Complete")
    return summary
```

Create `src/agents/vitality.py`:

```python
"""VITALITY — Health Agent."""
from datetime import date, timedelta
from pydantic import BaseModel
from src.core.config import settings
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


class HealthSummary(BaseModel):
    date: str
    steps: int = 0
    sleep_hours: float = 0.0
    body_score: float = 0.0
    narrative: str = ""
    recommendation: str = ""


async def run_vitality() -> HealthSummary:
    """VITALITY entrypoint."""
    logger.info("VITALITY: Starting health run")
    skill = load_skill("VITALITY")
    
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    health_file = settings.vaf_data_dir / "health" / "daily_metrics.csv"
    
    if not health_file.exists():
        logger.warning("VITALITY: No health metrics file found")
        summary = HealthSummary(
            date=yesterday,
            narrative="No health data yet. Export from Apple Health and drop into data/health/daily_metrics.csv",
            recommendation="Set up Apple Health export via iPhone Shortcut."
        )
    else:
        # Full parsing in Sprint 1
        summary = HealthSummary(
            date=yesterday,
            narrative="VITALITY scaffold ready. Health file found. Full parsing in Sprint 1.",
            recommendation="Keep going."
        )
    
    summary_path = settings.vaf_data_dir / "summaries" / "health" / f"{yesterday}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary.model_dump_json(indent=2))
    
    logger.info("VITALITY: Complete")
    return summary
```

Create `src/agents/cipher.py` (stub):

```python
"""CIPHER — Learning Intelligence Agent. Sprint 2."""
from datetime import date
from pydantic import BaseModel
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


class EducationSummary(BaseModel):
    date: str
    insights: list[str] = []
    narrative: str = "CIPHER implementation in Sprint 2."


async def run_cipher() -> EducationSummary:
    logger.info("CIPHER: Stub — Sprint 2")
    skill = load_skill("CIPHER")
    return EducationSummary(date=date.today().isoformat())
```

Create `src/agents/amplify.py` (stub):

```python
"""AMPLIFY — Content Agent. Sprint 2."""
from datetime import date
from pydantic import BaseModel
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


class ContentSummary(BaseModel):
    date: str
    ideas: list[dict] = []
    narrative: str = "AMPLIFY implementation in Sprint 2."


async def run_amplify() -> ContentSummary:
    logger.info("AMPLIFY: Stub — Sprint 2")
    skill = load_skill("AMPLIFY")
    return ContentSummary(date=date.today().isoformat())
```

### 4.4 The LangGraph orchestrator — the heart of it

Create `src/orchestrator/__init__.py` (empty)

Create `src/orchestrator/pipeline.py`:

```python
"""
VAF Morning Pipeline — LangGraph parallel fan-out orchestrator.

Architecture (DeerFlow-inspired):
  START
    ├── PHOENIX  ─┐
    ├── VITALITY ─┤  (run in parallel via asyncio.gather)
    ├── CIPHER   ─┤
    └── AMPLIFY  ─┘
                  └── SENTINEL (convergence — reads all 4 summaries)
                        └── END

Each agent writes its summary JSON to data/summaries/[agent]/YYYY-MM-DD.json
SENTINEL reads all summaries and writes data/briefings/YYYY-MM-DD.json
"""
import asyncio
import json
from datetime import date
from typing import TypedDict, Annotated
import operator

import anthropic
from langgraph.graph import StateGraph, END

from src.agents.phoenix import run_phoenix, FinanceSummary
from src.agents.vitality import run_vitality, HealthSummary
from src.agents.cipher import run_cipher, EducationSummary
from src.agents.amplify import run_amplify, ContentSummary
from src.core.config import settings
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


# ─── Pipeline State ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    """Shared state passed between LangGraph nodes."""
    finance_summary: dict | None
    health_summary: dict | None
    education_summary: dict | None
    content_summary: dict | None
    briefing: dict | None
    errors: Annotated[list[str], operator.add]  # Accumulates errors from all nodes


# ─── Agent Nodes ─────────────────────────────────────────────────────────────

async def phoenix_node(state: PipelineState) -> dict:
    """LangGraph node: run PHOENIX finance agent."""
    try:
        summary = await run_phoenix()
        return {"finance_summary": summary.model_dump()}
    except Exception as e:
        logger.error(f"PHOENIX node failed: {e}")
        return {"errors": [f"PHOENIX: {e}"]}


async def vitality_node(state: PipelineState) -> dict:
    """LangGraph node: run VITALITY health agent."""
    try:
        summary = await run_vitality()
        return {"health_summary": summary.model_dump()}
    except Exception as e:
        logger.error(f"VITALITY node failed: {e}")
        return {"errors": [f"VITALITY: {e}"]}


async def cipher_node(state: PipelineState) -> dict:
    """LangGraph node: run CIPHER education agent."""
    try:
        summary = await run_cipher()
        return {"education_summary": summary.model_dump()}
    except Exception as e:
        logger.error(f"CIPHER node failed: {e}")
        return {"errors": [f"CIPHER: {e}"]}


async def amplify_node(state: PipelineState) -> dict:
    """LangGraph node: run AMPLIFY content agent."""
    try:
        summary = await run_amplify()
        return {"content_summary": summary.model_dump()}
    except Exception as e:
        logger.error(f"AMPLIFY node failed: {e}")
        return {"errors": [f"AMPLIFY: {e}"]}


async def sentinel_node(state: PipelineState) -> dict:
    """
    LangGraph convergence node: SENTINEL reads all agent summaries
    and generates the unified daily briefing.
    """
    logger.info("SENTINEL: Generating Morning Brief")
    
    today = date.today().isoformat()
    skill = load_skill("SENTINEL")
    
    all_summaries = {
        "finance":   state.get("finance_summary"),
        "health":    state.get("health_summary"),
        "education": state.get("education_summary"),
        "content":   state.get("content_summary"),
        "errors":    state.get("errors", []),
    }
    
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    try:
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=1000,
            system=skill,
            messages=[{
                "role": "user",
                "content": (
                    f"Generate the Morning Brief for {today}.\n\n"
                    f"Agent summaries:\n{json.dumps(all_summaries, indent=2, default=str)}"
                ),
            }],
        )
        narrative = response.content[0].text.strip()
    except Exception as e:
        logger.error(f"SENTINEL: Claude call failed: {e}")
        narrative = f"SENTINEL: Brief generation failed — {e}. Raw summaries saved."
    
    briefing = {
        "date": today,
        "narrative": narrative,
        **{k: v for k, v in all_summaries.items() if k != "errors"},
        "errors": state.get("errors", []),
    }
    
    # Write briefing JSON (dashboard reads this)
    briefing_path = settings.vaf_data_dir / "briefings" / f"{today}.json"
    briefing_path.parent.mkdir(parents=True, exist_ok=True)
    briefing_path.write_text(json.dumps(briefing, indent=2, default=str))
    
    # Write human-readable Markdown report
    report_path = settings.vaf_reports_dir / "daily" / f"{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        f"# Vaishali Daily Briefing — {today}\n\n"
        f"{narrative}\n\n"
        f"---\n*Generated by SENTINEL | V AgentForce*\n"
    )
    
    # Optionally write to Obsidian vault
    obsidian_dir = settings.vaf_obsidian_vault_dir.expanduser()
    if obsidian_dir.exists():
        daily_note = obsidian_dir / "09 Daily Notes" / f"{today}.md"
        daily_note.parent.mkdir(parents=True, exist_ok=True)
        daily_note.write_text(
            f"# VAF Briefing — {today}\n\n"
            f"{narrative}\n\n"
            f"---\n#vaf #sentinel #daily\n"
        )
        logger.info(f"SENTINEL: Written to Obsidian at {daily_note}")
    
    logger.info("SENTINEL: Morning Brief complete")
    return {"briefing": briefing}


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def build_pipeline() -> object:
    """
    Build and compile the VAF morning pipeline as a LangGraph StateGraph.
    
    The graph uses parallel fan-out: all 4 agent nodes are connected from
    the start point, then all converge to the SENTINEL node.
    
    Note: LangGraph handles parallel execution of nodes without explicit edges
    between them when they all feed into the same downstream node.
    """
    graph = StateGraph(PipelineState)
    
    # Register nodes
    graph.add_node("phoenix",  phoenix_node)
    graph.add_node("vitality", vitality_node)
    graph.add_node("cipher",   cipher_node)
    graph.add_node("amplify",  amplify_node)
    graph.add_node("sentinel", sentinel_node)
    
    # Fan-out: all 4 agents run after pipeline start
    graph.set_entry_point("phoenix")
    # For true parallel execution, we override with asyncio.gather below
    # LangGraph edges here define the logical flow
    for agent in ["phoenix", "vitality", "cipher", "amplify"]:
        graph.add_edge(agent, "sentinel")
    
    graph.add_edge("sentinel", END)
    
    return graph.compile()


# ─── Main Entrypoint ─────────────────────────────────────────────────────────

async def run_morning_pipeline() -> dict:
    """
    Run the VAF morning pipeline with true parallel agent execution.
    
    Pattern: asyncio.gather runs all 4 agents simultaneously.
    Results merged into state. SENTINEL synthesises.
    
    Returns: Final briefing dict
    """
    logger.info("=" * 60)
    logger.info("VAF Morning Pipeline — Starting")
    logger.info("=" * 60)
    
    # ── True parallel fan-out ──────────────────────────────────────────
    # Run all 4 agents simultaneously. This is the DeerFlow pattern.
    # 3 × 30s sequential = 90s. 4 × 30s parallel = ~30s.
    logger.info("Running PHOENIX | VITALITY | CIPHER | AMPLIFY in parallel...")
    
    results = await asyncio.gather(
        run_phoenix(),
        run_vitality(),
        run_cipher(),
        run_amplify(),
        return_exceptions=True,  # Don't let one failure kill the rest
    )
    
    # ── Build merged state ─────────────────────────────────────────────
    keys = ["finance_summary", "health_summary", "education_summary", "content_summary"]
    state: PipelineState = {
        "finance_summary":   None,
        "health_summary":    None,
        "education_summary": None,
        "content_summary":   None,
        "briefing":          None,
        "errors":            [],
    }
    
    for key, result in zip(keys, results):
        if isinstance(result, Exception):
            agent = key.replace("_summary", "").upper()
            logger.error(f"{agent} failed: {result}")
            state["errors"].append(f"{agent}: {result}")
        else:
            state[key] = result.model_dump()
    
    # ── SENTINEL convergence ───────────────────────────────────────────
    final = await sentinel_node(state)
    briefing = final.get("briefing", {})
    
    logger.info("=" * 60)
    logger.info("VAF Morning Pipeline — Complete")
    if state["errors"]:
        logger.warning(f"Completed with {len(state['errors'])} error(s): {state['errors']}")
    logger.info("=" * 60)
    
    return briefing


# ── CLI entrypoint ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio
    asyncio.run(run_morning_pipeline())
```

### 4.5 FastAPI dashboard backend (minimal — just enough to see it working)

Create `src/dashboard/__init__.py` (empty)

Create `src/dashboard/main.py`:

```python
"""VAF Command Center — FastAPI backend."""
import json
import subprocess
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)
app = FastAPI(title="V AgentForce", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML."""
    html = Path("src/dashboard/index.html")
    if html.exists():
        return html.read_text(encoding="utf-8")
    return HTMLResponse("""
    <html><body style="background:#0D1B2A;color:#00B4D8;font-family:system-ui;padding:40px">
    <h1>V AgentForce — Dashboard Loading</h1>
    <p>index.html not found yet. Pipeline is running.</p>
    <p><a href="/api/briefing/today" style="color:#10B981">View today's briefing JSON</a></p>
    </body></html>
    """)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/briefing/today")
async def get_briefing():
    today = date.today().isoformat()
    path = settings.vaf_data_dir / "briefings" / f"{today}.json"
    if not path.exists():
        return JSONResponse({
            "date": today,
            "narrative": "No briefing yet. Run: POST /api/pipeline/morning",
            "errors": []
        })
    return JSONResponse(json.loads(path.read_text()))


@app.post("/api/pipeline/morning")
async def trigger_pipeline():
    """Manually trigger the morning pipeline."""
    from src.orchestrator.pipeline import run_morning_pipeline
    briefing = await run_morning_pipeline()
    return JSONResponse({"status": "complete", "briefing": briefing})


@app.post("/api/speak")
async def speak_briefing():
    """Speak today's briefing via macOS say command."""
    today = date.today().isoformat()
    path = settings.vaf_data_dir / "briefings" / f"{today}.json"
    if not path.exists():
        raise HTTPException(404, "No briefing to speak — run the morning pipeline first")
    data = json.loads(path.read_text())
    narrative = data.get("narrative", "No briefing available.")
    subprocess.Popen(["say", "-r", "170", narrative])
    return JSONResponse({"status": "speaking"})
```

### 4.6 Verify the whole thing runs

```bash
# From project root:
cp .env.example .env
# V: edit .env and add real ANTHROPIC_API_KEY

# Test pipeline
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.orchestrator.pipeline import run_morning_pipeline
result = asyncio.run(run_morning_pipeline())
print('Pipeline complete. Briefing date:', result.get('date'))
print('Errors:', result.get('errors', []))
"

# Start dashboard
python3 -m uvicorn src.dashboard.main:app --reload --port 8080
# Open: http://localhost:8080
```

---

## PHASE 5 — FIRST COMMIT

```bash
git add .
git status  # Confirm .env is NOT listed (it's gitignored)
git commit -m "feat: VAF Sprint 1 scaffold — LangGraph pipeline + skills architecture

- 5-agent structure: PHOENIX, VITALITY, CIPHER, AMPLIFY, SENTINEL
- LangGraph parallel fan-out orchestrator (DeerFlow-inspired)
- Skills-as-Markdown system (skills/agents/[AGENT]/SKILL.md)
- FastAPI dashboard backend with /api/pipeline/morning endpoint
- All data stays local (SQLite + JSON, no cloud DB)
- See docs/VAF_Architecture_Decision_Record.docx for full ADR"
```

---

## COLOSSUS CHECKLIST — Before Declaring Done

- [ ] `.env` does NOT appear in `git status` 
- [ ] `python3 -c "from src.core.skills import list_available_skills; print(list_available_skills())"` returns all 5 agents
- [ ] Pipeline runs without crashing: `python3 -m src.orchestrator.pipeline`
- [ ] Dashboard starts: `uvicorn src.dashboard.main:app --port 8080`
- [ ] `GET http://localhost:8080/api/health` returns `{"status": "ok"}`
- [ ] `POST http://localhost:8080/api/pipeline/morning` runs and returns a briefing
- [ ] `data/briefings/[today].json` exists after pipeline run
- [ ] `reports/daily/[today].md` exists after pipeline run

---

## NEXT SESSION (Sprint 1 continuation)

1. Full PHOENIX CSV parser (bank statement → SQLite → categorised → narrative)
2. VITALITY Apple Health CSV reader
3. ✅ Dashboard `index.html` — **DONE** (see `src/dashboard/index.html`)
4. macOS LaunchAgent for 07:00 scheduled run

---

## PHASE 6 — AUGMENT `src/dashboard/main.py` (add missing endpoints)

**These endpoints are called by `index.html` but are not yet in `main.py`. Add them — do not replace the existing file.**

Append to the bottom of `src/dashboard/main.py` before the final newline:

```python
# ── Build pipeline endpoints (from scripts/sentinel_build_integration.py) ────

@app.get("/api/build/today")
async def get_build_today():
    """Return today's active build for dashboard display."""
    path = settings.vaf_data_dir / "briefings" / "build_of_day.json"
    if not path.exists():
        # Auto-run surface_build.py to generate it
        import subprocess, sys
        script = Path("scripts/surface_build.py")
        if script.exists():
            subprocess.run([sys.executable, str(script)], check=False)
    if path.exists():
        return JSONResponse(json.loads(path.read_text()))
    return JSONResponse({"error": "No build data. Run: python3 scripts/surface_build.py"})


@app.post("/api/build/ship/{build_id}")
async def ship_build(build_id: str):
    """Mark a build as shipped and advance the queue."""
    import subprocess, sys
    script = Path("scripts/surface_build.py")
    if not script.exists():
        raise HTTPException(404, "surface_build.py not found at scripts/surface_build.py")
    result = subprocess.run(
        [sys.executable, str(script), "--ship", build_id.upper()],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return JSONResponse({"status": "shipped", "output": result.stdout})
    return JSONResponse({"status": "error", "output": result.stderr}, status_code=500)


# ── Mood/energy logging endpoint ───────────────────────────────────────────────

@app.post("/api/health/log")
async def log_mood(mood: int = 3, energy: int = 3, note: str = ""):
    """Log mood and energy check-in. Called by dashboard logMood()."""
    from datetime import datetime
    today = date.today().isoformat()
    log_path = settings.vaf_data_dir / "health" / "checkins.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        "timestamp": datetime.now().isoformat(),
        "date": today,
        "mood": max(1, min(5, mood)),
        "energy": max(1, min(5, energy)),
        "note": note,
    })
    with open(log_path, "a") as f:
        f.write(entry + "\n")
    return JSONResponse({"status": "logged", "date": today, "mood": mood, "energy": energy})


# ── Finance history endpoint (7-day sparkline data) ────────────────────────────

@app.get("/api/finance/history")
async def get_finance_history(days: int = 7):
    """Return the last N days of finance summaries for sparkline charts."""
    from datetime import timedelta
    results = []
    for i in range(days - 1, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        path = settings.vaf_data_dir / "summaries" / "finance" / f"{d}.json"
        if path.exists():
            results.append(json.loads(path.read_text()))
        else:
            results.append({"date": d, "total_income": 0, "total_spend": 0, "net": 0})
    return JSONResponse({"history": results, "days": days})


# ── Agent summaries endpoint (for individual panel deep-dives) ────────────────

@app.get("/api/summaries/{agent}/{date_str}")
async def get_agent_summary(agent: str, date_str: str):
    """Return a specific agent summary by agent name and date."""
    valid_agents = {"finance", "health", "content", "education"}
    if agent not in valid_agents:
        raise HTTPException(400, f"Unknown agent '{agent}'. Valid: {valid_agents}")
    path = settings.vaf_data_dir / "summaries" / agent / f"{date_str}.json"
    if not path.exists():
        raise HTTPException(404, f"No {agent} summary for {date_str}")
    return JSONResponse(json.loads(path.read_text()))
```

---

## PHASE 7 — AUGMENT `index.html` (wire logMood to real endpoint)

The existing `logMood()` function in `src/dashboard/index.html` uses a `prompt()` dialog and only shows a toast.
Replace just that function with the version below that POSTs to `/api/health/log`:

**Find this block in index.html (around line 1158):**
```javascript
function logMood() {
  const mood = prompt('Log mood (1–5) and energy (1–5): e.g. "4,3"');
  if (mood) toast(`Mood logged: ${mood}`, 'success');
}
```

**Replace with:**
```javascript
async function logMood() {
  const input = prompt('Log mood & energy (1–5 each). Format: mood,energy,note\nExample: 4,3,feeling focused');
  if (!input) return;
  const parts = input.split(',').map(s => s.trim());
  const mood   = parseInt(parts[0]) || 3;
  const energy = parseInt(parts[1]) || 3;
  const note   = parts.slice(2).join(',').trim();
  try {
    const r = await fetch(`${API}/api/health/log?mood=${mood}&energy=${energy}&note=${encodeURIComponent(note)}`, {
      method: 'POST'
    });
    if (r.ok) {
      toast(`✓ Logged mood ${mood}/5 energy ${energy}/5`, 'success');
      addFeedItem('VITALITY', `Check-in logged — mood ${mood} energy ${energy}`);
    } else {
      toast('Log failed — check API', 'error');
    }
  } catch(e) {
    toast('API unreachable — check uvicorn is running', 'error');
  }
}
```

---

## PHASE 8 — ADD GOGGINS PROTOCOL SKILL FILE

Create `skills/agents/GOGGINS/SKILL.md`:

```markdown
# GOGGINS PROTOCOL — The 5 Non-Negotiables

> "Who's gonna carry the boats?" — V is.

## The 5 Daily Non-Negotiables

These are not goals. They are the minimum price of the day. Zero exceptions.

1. **BODY** — 5x5 Physical Protocol: 5 push-ups, 5 pull-ups, 5 abs, 5 squats, 5 flex. 5 minutes. No excuses. Score /10
2. **BUILD** — Ship 1 thing to production: a feature, a fix, a new tool. If deployed and real, it counts. Score /10
3. **LEARN** — Complete 1 AWS Claude course lesson. Extract the key insight. Drop to CIPHER. Score /10
4. **AMPLIFY** — Create or schedule 1 piece of content. Grow the audience. Score /10
5. **BRIEF** — SENTINEL morning brief (5 mins) + Telegram /checkin debrief. Score /10

## Scoring

Total possible: 50 pts/day
- Streak target: 25+ to keep streak alive
- Elite day: 45+
- Log nightly: `/checkin [BODY] [BUILD] [LEARN] [AMPLIFY] [BRIEF]`

## SENTINEL Integration

When SENTINEL generates a morning brief, it MUST end with:

**GOGGINS CHECK:**
Yesterday's score: [X]/50
Streak: [N] days
Today's minimum: Complete all 5 non-negotiables before 21:00.
```

---

## UPDATED COLOSSUS CHECKLIST

- [ ] `.env` does NOT appear in `git status`
- [ ] All 5 skill files exist: `ls skills/agents/*/SKILL.md`
- [ ] GOGGINS skill file exists: `skills/agents/GOGGINS/SKILL.md`
- [ ] Pipeline runs: `python3 -m src.orchestrator.pipeline`
- [ ] Dashboard starts: `uvicorn src.dashboard.main:app --port 8080`
- [ ] `GET /api/health` → `{"status": "ok"}`
- [ ] `GET /api/build/today` → returns BUILD-001 data
- [ ] `POST /api/health/log?mood=4&energy=4` → creates entry in `data/health/checkins.jsonl`
- [ ] `GET /api/finance/history` → returns 7-day array (zeros OK if no data yet)
- [ ] `POST /api/build/ship/BUILD-001` → advances queue (test with --dry-run first)
- [ ] `data/briefings/[today].json` exists after pipeline run
- [ ] `reports/daily/[today].md` exists after pipeline run
- [ ] `index.html` logMood() POSTs to `/api/health/log` (not just a prompt toast)
