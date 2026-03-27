# 🚀 COWORK EXECUTION BRIEF — V AgentForce MVP Build
> FORGE sending orders. Execute this in sequence. Ship clean code.

---

## MISSION

Build V AgentForce (VAF) MVP — a personal AI operating system that orchestrates 5 specialist agents through a unified Command Center dashboard. This is Vaishali's primary portfolio piece and the foundation of her teaching business.

**Repository:** https://github.com/vm799 (confirm exact repo name with V)
**Stack:** Python/FastAPI + LangGraph + Vanilla HTML/JS + SQLite + Claude API
**Target:** Working MVP in 2 weeks (Sprint 1)

---

## PHASE 1 — PROJECT SCAFFOLD (Do This First)

### 1.1 Create Directory Structure

```bash
mkdir -p vaf/{src/{agents,orchestrator,ingest,dashboard,core},skills/agents,data/{finance/raw,health,content,education,summaries/{finance,health,content,education},briefings},reports/{finance/daily,finance/weekly,daily},docs,tests}
```

### 1.2 Create Core Files

**`pyproject.toml`** (use uv for package management):
```toml
[project]
name = "vaf"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "anthropic>=0.40.0",
    "httpx>=0.28.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "aiosqlite>=0.20.0",
    "python-dotenv>=1.0.0",
    "feedparser>=6.0.11",
    "pandas>=2.2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.3.0", "pytest-asyncio>=0.24.0", "httpx>=0.28.0"]
```

**`.env.example`:**
```
ANTHROPIC_API_KEY=your_key_here
VAF_DATA_DIR=./data
VAF_REPORTS_DIR=./reports
VAF_ICLOUD_STATEMENTS_DIR=~/Library/Mobile Documents/com~apple~CloudDocs/VAF/statements
VAF_OBSIDIAN_VAULT_DIR=~/Documents/Obsidian/V AgentForce
```

**`.gitignore`:**
```
.env
data/finance/
data/health/
*.db
__pycache__/
.venv/
*.pyc
.DS_Store
```

**`src/core/config.py`:**
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    anthropic_api_key: str
    vaf_data_dir: Path = Path("./data")
    vaf_reports_dir: Path = Path("./reports")
    vaf_icloud_statements_dir: Path = Path("~/Library/Mobile Documents/com~apple~CloudDocs/VAF/statements")
    vaf_obsidian_vault_dir: Path = Path("~/Documents/Obsidian/V AgentForce")
    claude_model: str = "claude-sonnet-4-5"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

**`src/core/logging.py`:**
```python
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

---

## PHASE 2 — SKILLS SYSTEM (DeerFlow Pattern)

Create `skills/agents/` directory. Each agent gets a `SKILL.md`.

For each agent, create `skills/agents/[AGENT_NAME]/SKILL.md` by reading the corresponding agent file from the project documents and condensing to a structured prompt with:
- Persona (2-3 sentences)
- Core protocol (numbered steps)  
- Output format (explicit JSON or Markdown schema)
- Example output

**Priority order:** PHOENIX → VITALITY → SENTINEL → CIPHER → AMPLIFY

**`src/core/skills.py`** — skill loader:
```python
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=None)
def load_skill(agent_name: str) -> str:
    """Load agent skill file. Cached after first load."""
    skill_path = Path("skills/agents") / agent_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"No skill found for agent: {agent_name}")
    return skill_path.read_text(encoding="utf-8")
```

---

## PHASE 3 — PHOENIX AGENT (Finance)

**`src/agents/phoenix.py`:**

```python
"""PHOENIX — Finance Agent. Parses UK bank statements → SQLite ledger → daily finance summary."""
import asyncio
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import aiosqlite
import anthropic
import pandas as pd
from pydantic import BaseModel

from src.core.config import settings
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    category: str
    account: str
    raw: str


class FinanceSummary(BaseModel):
    date: str
    total_income: float
    total_spend: float
    net: float
    top_categories: list[dict]
    anomalies: list[str]
    recurring_payments: list[dict]
    narrative: str  # PHOENIX plain-English summary


async def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                account TEXT,
                raw TEXT,
                ingested_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()


async def parse_statement_csv(file_path: Path) -> list[dict]:
    """Parse UK bank statement CSV. Handles First Direct, Barclays, Santander formats."""
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    # Normalise column names (banks use different headers)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    transactions = df.to_dict(orient="records")
    return transactions


async def categorise_transactions(transactions: list[dict]) -> list[Transaction]:
    """Use Claude to categorise transactions intelligently."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    skill = load_skill("PHOENIX")
    
    batch_text = json.dumps(transactions[:50], default=str)  # batch for efficiency
    
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2000,
        system=skill,
        messages=[{
            "role": "user",
            "content": f"Categorise these transactions. Return a JSON array of objects with fields: date, description, amount, category, account. Categories: Housing, Groceries, Eating Out, Transport, Childcare, Subscriptions, Clothing, Health, Entertainment, Savings, Business, Income, Other.\n\nTransactions:\n{batch_text}"
        }]
    )
    
    # Parse JSON response safely
    text = response.content[0].text
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1:
        logger.error("PHOENIX: Claude did not return valid JSON array")
        return []
    
    items = json.loads(text[start:end])
    return [Transaction(**{**item, "raw": json.dumps(item)}) for item in items]


async def generate_finance_summary(transactions: list[Transaction]) -> FinanceSummary:
    """Generate PHOENIX narrative summary from categorised transactions."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    skill = load_skill("PHOENIX")
    
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_spend = abs(sum(t.amount for t in transactions if t.amount < 0))
    
    by_category: dict[str, float] = {}
    for t in transactions:
        if t.amount < 0:
            by_category[t.category] = by_category.get(t.category, 0) + abs(t.amount)
    
    top_categories = sorted(
        [{"category": k, "amount": round(v, 2)} for k, v in by_category.items()],
        key=lambda x: x["amount"], reverse=True
    )[:5]
    
    # Get narrative from PHOENIX
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=500,
        system=skill,
        messages=[{
            "role": "user",
            "content": f"Generate the PHOENIX VERDICT for this financial data. Plain English. Max 3 sentences. Include: what this month tells us, one CUT recommendation, one GROW recommendation.\n\nIncome: £{total_income:.2f}\nSpend: £{total_spend:.2f}\nTop categories: {json.dumps(top_categories)}"
        }]
    )
    
    return FinanceSummary(
        date=date.today().isoformat(),
        total_income=round(total_income, 2),
        total_spend=round(total_spend, 2),
        net=round(total_income - total_spend, 2),
        top_categories=top_categories,
        anomalies=[],  # TODO: implement anomaly detection in Sprint 2
        recurring_payments=[],  # TODO: implement in Sprint 2
        narrative=response.content[0].text.strip()
    )


async def run_phoenix() -> FinanceSummary:
    """Main PHOENIX entrypoint. Called by LangGraph orchestrator."""
    logger.info("PHOENIX: Starting finance ingestion run")
    
    db_path = settings.vaf_data_dir / "finance" / "ledger.db"
    await init_db(db_path)
    
    # Find new statement files
    statements_dir = settings.vaf_icloud_statements_dir.expanduser()
    if not statements_dir.exists():
        logger.warning(f"PHOENIX: Statements directory not found: {statements_dir}")
        return FinanceSummary(
            date=date.today().isoformat(),
            total_income=0, total_spend=0, net=0,
            top_categories=[], anomalies=["No statements directory found"],
            recurring_payments=[], narrative="No statements found. Check iCloud folder path in .env"
        )
    
    csv_files = list(statements_dir.glob("*.csv"))
    logger.info(f"PHOENIX: Found {len(csv_files)} statement files")
    
    all_transactions: list[Transaction] = []
    for csv_file in csv_files:
        raw = await parse_statement_csv(csv_file)
        categorised = await categorise_transactions(raw)
        all_transactions.extend(categorised)
        logger.info(f"PHOENIX: Processed {len(categorised)} transactions from {csv_file.name}")
    
    if not all_transactions:
        logger.warning("PHOENIX: No transactions parsed")
        return FinanceSummary(
            date=date.today().isoformat(),
            total_income=0, total_spend=0, net=0,
            top_categories=[], anomalies=[], recurring_payments=[],
            narrative="No transactions found in statement files."
        )
    
    # Persist to SQLite
    async with aiosqlite.connect(db_path) as db:
        await db.executemany(
            "INSERT INTO transactions (date, description, amount, category, account, raw) VALUES (?, ?, ?, ?, ?, ?)",
            [(t.date, t.description, t.amount, t.category, t.account, t.raw) for t in all_transactions]
        )
        await db.commit()
    
    summary = await generate_finance_summary(all_transactions)
    
    # Write JSON summary for SENTINEL
    summary_path = settings.vaf_data_dir / "summaries" / "finance" / f"{summary.date}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary.model_dump_json(indent=2))
    
    # Write Markdown report
    report_path = settings.vaf_reports_dir / "finance" / "daily" / f"{summary.date}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(f"""# PHOENIX Finance Report — {summary.date}

## Summary
{summary.narrative}

## Numbers
- **Income:** £{summary.total_income:,.2f}
- **Spend:** £{summary.total_spend:,.2f}
- **Net:** £{summary.net:,.2f}

## Top Spending Categories
{chr(10).join(f"- **{c['category']}:** £{c['amount']:,.2f}" for c in summary.top_categories)}

## Anomalies
{chr(10).join(f"- {a}" for a in summary.anomalies) if summary.anomalies else "- None detected"}

---
*Generated by PHOENIX at {datetime.now().strftime('%H:%M')}*
""")
    
    logger.info(f"PHOENIX: Complete. Net: £{summary.net:,.2f}")
    return summary
```

---

## PHASE 4 — VITALITY AGENT (Health)

**`src/agents/vitality.py`:**

```python
"""VITALITY — Health Agent. Reads Apple Health CSV → daily health summary."""
import csv
import json
from datetime import date, timedelta
from pathlib import Path

import anthropic
from pydantic import BaseModel

from src.core.config import settings
from src.core.logging import get_logger
from src.core.skills import load_skill

logger = get_logger(__name__)


class HealthSummary(BaseModel):
    date: str
    steps: int
    sleep_hours: float
    energy: int  # 1-5 manual check-in
    mood: int    # 1-5 manual check-in
    habits_completed: int
    habits_total: int
    body_score: float  # 0-10 composite
    narrative: str
    recommendation: str


async def run_vitality() -> HealthSummary:
    """Main VITALITY entrypoint."""
    logger.info("VITALITY: Starting health summary run")
    
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    # Read Apple Health CSV (V exports via iPhone Shortcut)
    health_file = settings.vaf_data_dir / "health" / "daily_metrics.csv"
    
    steps = 0
    sleep_hours = 0.0
    
    if health_file.exists():
        with open(health_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("date", "").startswith(yesterday[:10]):
                    steps = int(float(row.get("steps", 0)))
                    sleep_hours = float(row.get("sleep_hours", 0))
                    break
    
    # Calculate body score (0-10 composite)
    step_score = min(steps / 10000, 1.0) * 3   # max 3 pts for 10k steps
    sleep_score = min(sleep_hours / 8.0, 1.0) * 4  # max 4 pts for 8hrs sleep
    body_score = round(step_score + sleep_score + 3, 1)  # base 3 + up to 7
    body_score = min(body_score, 10.0)
    
    # Generate narrative
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    skill = load_skill("VITALITY")
    
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=200,
        system=skill,
        messages=[{
            "role": "user",
            "content": f"Generate a one-line body summary and one-line recommendation for: steps={steps}, sleep={sleep_hours}hrs, body_score={body_score}/10. Format: SUMMARY | RECOMMENDATION"
        }]
    )
    
    parts = response.content[0].text.strip().split("|")
    narrative = parts[0].strip() if parts else f"Body {body_score}/10 — {steps:,} steps, {sleep_hours}h sleep"
    recommendation = parts[1].strip() if len(parts) > 1 else "Stay consistent."
    
    summary = HealthSummary(
        date=yesterday,
        steps=steps,
        sleep_hours=sleep_hours,
        energy=3, mood=3,  # Default until manual check-in
        habits_completed=0, habits_total=4,
        body_score=body_score,
        narrative=narrative,
        recommendation=recommendation
    )
    
    # Write JSON summary
    summary_path = settings.vaf_data_dir / "summaries" / "health" / f"{yesterday}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary.model_dump_json(indent=2))
    
    logger.info(f"VITALITY: Complete. Body score: {body_score}/10")
    return summary
```

---

## PHASE 5 — LANGGRAPH ORCHESTRATOR

**`src/orchestrator/pipeline.py`:**

```python
"""Morning pipeline orchestrator using LangGraph parallel fan-out."""
import asyncio
import json
from datetime import date
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

from src.agents.phoenix import run_phoenix, FinanceSummary
from src.agents.vitality import run_vitality, HealthSummary
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class PipelineState(TypedDict):
    finance_summary: dict | None
    health_summary: dict | None
    content_summary: dict | None
    education_summary: dict | None
    briefing: dict | None
    errors: list[str]


async def phoenix_node(state: PipelineState) -> PipelineState:
    try:
        summary = await run_phoenix()
        return {**state, "finance_summary": summary.model_dump()}
    except Exception as e:
        logger.error(f"PHOENIX node error: {e}")
        return {**state, "errors": state["errors"] + [f"PHOENIX: {e}"]}


async def vitality_node(state: PipelineState) -> PipelineState:
    try:
        summary = await run_vitality()
        return {**state, "health_summary": summary.model_dump()}
    except Exception as e:
        logger.error(f"VITALITY node error: {e}")
        return {**state, "errors": state["errors"] + [f"VITALITY: {e}"]}


async def cipher_node(state: PipelineState) -> PipelineState:
    """Stub for Sprint 2 CIPHER implementation."""
    logger.info("CIPHER: Stub — Sprint 2 implementation pending")
    return {**state, "education_summary": {"date": date.today().isoformat(), "insights": [], "narrative": "CIPHER coming in Sprint 2"}}


async def amplify_node(state: PipelineState) -> PipelineState:
    """Stub for Sprint 2 AMPLIFY implementation."""
    logger.info("AMPLIFY: Stub — Sprint 2 implementation pending")
    return {**state, "content_summary": {"date": date.today().isoformat(), "ideas": [], "narrative": "AMPLIFY coming in Sprint 2"}}


async def sentinel_node(state: PipelineState) -> PipelineState:
    """SENTINEL convergence — synthesise all agent summaries into unified briefing."""
    import anthropic
    from src.core.skills import load_skill
    
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    skill = load_skill("SENTINEL")
    
    all_summaries = json.dumps({
        "finance": state.get("finance_summary"),
        "health": state.get("health_summary"),
        "content": state.get("content_summary"),
        "education": state.get("education_summary"),
    }, indent=2, default=str)
    
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1000,
        system=skill,
        messages=[{
            "role": "user",
            "content": f"Generate today's Morning Brief from these agent summaries. Include: MISSION STATUS (1 sentence), TODAY'S ORDERS (max 3, numbered), INTEL (key follow-ups), FIRE (one motivational truth). Today's date: {date.today().isoformat()}\n\n{all_summaries}"
        }]
    )
    
    today = date.today().isoformat()
    briefing = {
        "date": today,
        "narrative": response.content[0].text.strip(),
        "finance": state.get("finance_summary"),
        "health": state.get("health_summary"),
        "errors": state.get("errors", [])
    }
    
    # Write briefing JSON
    briefing_path = settings.vaf_data_dir / "briefings" / f"{today}.json"
    briefing_path.parent.mkdir(parents=True, exist_ok=True)
    briefing_path.write_text(json.dumps(briefing, indent=2, default=str))
    
    # Write daily report MD
    report_path = settings.vaf_reports_dir / "daily" / f"{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(f"""# Vaishali Daily Briefing — {today}

{response.content[0].text.strip()}

---
*Generated by SENTINEL | V AgentForce*
""")
    
    logger.info("SENTINEL: Briefing complete")
    return {**state, "briefing": briefing}


def build_morning_pipeline() -> StateGraph:
    """Build LangGraph morning pipeline with parallel agent fan-out."""
    graph = StateGraph(PipelineState)
    
    # Add agent nodes
    graph.add_node("phoenix", phoenix_node)
    graph.add_node("vitality", vitality_node)
    graph.add_node("cipher", cipher_node)
    graph.add_node("amplify", amplify_node)
    graph.add_node("sentinel", sentinel_node)
    
    # Parallel fan-out from START
    graph.set_entry_point("phoenix")  # LangGraph runs from entry
    # Note: For true parallelism, we'll use asyncio.gather in run_morning_pipeline
    
    # Sentinel after all agents complete
    for agent in ["phoenix", "vitality", "cipher", "amplify"]:
        graph.add_edge(agent, "sentinel")
    
    graph.add_edge("sentinel", END)
    return graph.compile()


async def run_morning_pipeline() -> dict:
    """Run all agents in parallel, then SENTINEL. Returns final briefing."""
    logger.info("=== VAF Morning Pipeline Starting ===")
    
    initial_state: PipelineState = {
        "finance_summary": None,
        "health_summary": None,
        "content_summary": None,
        "education_summary": None,
        "briefing": None,
        "errors": []
    }
    
    # Run 4 agents in true parallel with asyncio.gather
    logger.info("Running PHOENIX, VITALITY, CIPHER, AMPLIFY in parallel...")
    results = await asyncio.gather(
        run_phoenix(),
        run_vitality(),
        cipher_node(initial_state),
        amplify_node(initial_state),
        return_exceptions=True
    )
    
    # Build merged state
    state = {**initial_state}
    labels = ["finance_summary", "health_summary", "content_summary", "education_summary"]
    for i, (label, result) in enumerate(zip(labels, results)):
        if isinstance(result, Exception):
            state["errors"].append(f"{label}: {result}")
        elif hasattr(result, "model_dump"):
            state[label] = result.model_dump()
        elif isinstance(result, dict):
            state[label] = result.get(label)
    
    # SENTINEL convergence
    final_state = await sentinel_node(state)
    
    logger.info("=== VAF Morning Pipeline Complete ===")
    return final_state.get("briefing", {})
```

---

## PHASE 6 — DASHBOARD

**`src/dashboard/main.py`:**

```python
"""VAF Command Center Dashboard — FastAPI backend."""
import json
import subprocess
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.core.logging import get_logger
from src.orchestrator.pipeline import run_morning_pipeline

logger = get_logger(__name__)
app = FastAPI(title="V AgentForce Dashboard", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_file = Path("src/dashboard/index.html")
    if html_file.exists():
        return html_file.read_text()
    return HTMLResponse("<h1>VAF Dashboard — index.html not found</h1>")


@app.get("/api/briefing/today")
async def get_today_briefing():
    today = date.today().isoformat()
    briefing_path = settings.vaf_data_dir / "briefings" / f"{today}.json"
    if not briefing_path.exists():
        return JSONResponse({"date": today, "narrative": "No briefing generated yet. Run the morning pipeline.", "errors": []})
    return JSONResponse(json.loads(briefing_path.read_text()))


@app.get("/api/finance/summary/today")
async def get_finance_summary():
    today = date.today().isoformat()
    summary_path = settings.vaf_data_dir / "summaries" / "finance" / f"{today}.json"
    if not summary_path.exists():
        raise HTTPException(404, "No finance summary for today")
    return JSONResponse(json.loads(summary_path.read_text()))


@app.get("/api/health/summary/today")
async def get_health_summary():
    from datetime import timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    summary_path = settings.vaf_data_dir / "summaries" / "health" / f"{yesterday}.json"
    if not summary_path.exists():
        raise HTTPException(404, "No health summary for yesterday")
    return JSONResponse(json.loads(summary_path.read_text()))


@app.post("/api/pipeline/morning")
async def trigger_morning_pipeline():
    """Manually trigger the morning pipeline."""
    import asyncio
    briefing = await run_morning_pipeline()
    return JSONResponse({"status": "complete", "briefing": briefing})


@app.post("/api/speak")
async def speak_briefing():
    """Speak today's briefing via macOS say."""
    today = date.today().isoformat()
    briefing_path = settings.vaf_data_dir / "briefings" / f"{today}.json"
    if not briefing_path.exists():
        raise HTTPException(404, "No briefing to speak")
    
    data = json.loads(briefing_path.read_text())
    narrative = data.get("narrative", "No briefing available.")
    
    # macOS say command — runs in background
    subprocess.Popen(["say", "-r", "175", narrative])
    return JSONResponse({"status": "speaking", "length_chars": len(narrative)})


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
```

---

## PHASE 7 — DASHBOARD HTML

Create `src/dashboard/index.html` — a dark, calm, beautiful single-page dashboard:

Key requirements:
- **Dark theme:** background `#0D1B2A`, primary accent `#00B4D8` (teal)
- **Hero section:** Date, "What matters most today?", 4 action buttons
- **4 Agent panels:** Finance (green), Content (purple), Education (blue), Health (orange)
- **Agent Activity Feed:** Timeline of recent agent runs
- **Speak Briefing button:** calls `POST /api/speak`
- **Run Pipeline button:** calls `POST /api/pipeline/morning`
- All data fetched from the FastAPI endpoints above
- Auto-refreshes every 5 minutes
- No external dependencies — pure HTML/CSS/JS
- Fonts: system-ui or Inter loaded from Google Fonts CDN only

---

## PHASE 8 — MACOS LAUNCHAGENT

Create `~/Library/LaunchAgents/com.vaishali.vaf.morning.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vaishali.vaf.morning</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/vaf/.venv/bin/python</string>
        <string>-m</string>
        <string>src.orchestrator.pipeline</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/path/to/vaf</string>
    <key>StandardOutPath</key>
    <string>/path/to/vaf/logs/morning.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/vaf/logs/morning.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Register: `launchctl load ~/Library/LaunchAgents/com.vaishali.vaf.morning.plist`

---

## PHASE 9 — README FOR GITHUB

Create `README.md` — public-facing portfolio README:

```markdown
# V AgentForce (VAF)

> Personal AI operating system built by Vaishali Mehmi — a finance professional who self-taught AI engineering.

VAF orchestrates five specialist AI agents through a unified Command Center dashboard, running autonomously every morning to produce a 5-minute spoken briefing on finance, health, learning, and content.

## Architecture

Built on LangGraph + FastAPI + Claude API. Inspired by DeerFlow (ByteDance, 22.7k ⭐). Local-first — financial data never leaves your machine.

## Agent Squad

| Agent | Role | Technology |
|---|---|---|
| PHOENIX | Personal CFO | Claude + SQLite + bank statement parsing |
| VITALITY | Health Coach | Apple Health CSV + Claude |
| CIPHER | Learning Intelligence | RSS + YouTube + Claude |
| AMPLIFY | Content Studio | Claude + content backlog |
| SENTINEL | Squad Commander | LangGraph orchestration |

## Quick Start

\`\`\`bash
git clone https://github.com/vm799/vaf
cd vaf
cp .env.example .env  # Add your Anthropic API key
uv sync
uv run uvicorn src.dashboard.main:app --reload --port 8080
# Open http://localhost:8080
\`\`\`

## Architecture Decision Record

See `docs/VAF_Architecture_Decision_Record.docx` — full technical and non-technical documentation of every major decision.

## Built With

- Python 3.11 + FastAPI + LangGraph
- Anthropic Claude API (Sonnet)
- SQLite (local-first finance data)
- macOS LaunchAgent (scheduled runs)
- Obsidian (knowledge layer)

---

*"Build the machine. Work the machine. Become the machine."*
```

---

## EXECUTION ORDER

1. ✅ Phase 1 — Scaffold
2. ✅ Phase 2 — Skills system
3. ✅ Phase 3 — PHOENIX agent
4. ✅ Phase 4 — VITALITY agent
5. ✅ Phase 5 — LangGraph orchestrator
6. ✅ Phase 6 — FastAPI dashboard backend
7. ✅ Phase 7 — Dashboard HTML (dark, beautiful)
8. ✅ Phase 8 — LaunchAgent
9. ✅ Phase 9 — README

**After each phase: run the tests. Don't proceed if a phase is broken.**

```bash
# Test the pipeline manually
uv run python -c "import asyncio; from src.orchestrator.pipeline import run_morning_pipeline; asyncio.run(run_morning_pipeline())"

# Start dashboard
uv run uvicorn src.dashboard.main:app --reload --port 8080
```

---

## COLOSSUS PRE-SHIP CHECKLIST

Before declaring Sprint 1 done:
- [ ] `.env` not committed to Git (check with `git status`)
- [ ] All API keys in environment variables only
- [ ] Error handling: pipeline runs to completion even if one agent fails
- [ ] Health check endpoint returns 200: `GET /api/health`
- [ ] Dashboard loads with zero data (graceful empty states, not broken page)
- [ ] `README.md` is present and accurate
- [ ] At least one test per agent in `tests/`

---

*Cowork: Execute these phases in order. Report back after each phase is complete. Ship clean.*
