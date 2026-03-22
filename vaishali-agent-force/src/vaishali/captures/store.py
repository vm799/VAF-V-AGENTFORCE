"""Captures store — persists intelligence drops from Claude Project to SQLite.

Receives structured payloads from:
  - Telegram /save command (V forwards Claude output)
  - POST /api/capture (iOS Shortcut)
  - POST /api/capture/enriched (with orchestrator enrichment)

Writes to:
  - SQLite captures table (for dashboard display)
  - Obsidian vault (via filesystem write)

The golden thread:
  Input → Orchestrator (LLM enrich) → THIS MODULE (persist) → Obsidian → Dashboard
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# ── Agent detection patterns ───────────────────────────────────────────

AGENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("PHOENIX", [
        r"bank\s+statement", r"transaction", r"debit|credit", r"sort\s+code",
        r"account\s+number", r"statement\s+analysis", r"spending", r"savings",
        r"isa\b", r"sipp\b", r"pension", r"interest\s+rate", r"mortgage",
        r"bloomberg\.com", r"ft\.com", r"financial\s+times",
        r"£\d+", r"salary", r"income", r"budget",
    ]),
    ("AEGIS", [
        r"maestro", r"owasp", r"prompt\s+injection", r"ai\s+security",
        r"llm\s+vulner", r"jailbreak", r"model\s+attack", r"red\s+team",
        r"nist\s+ai", r"eu\s+ai\s+act", r"security\s+framework",
        r"data\s+poisoning", r"insecure\s+output",
    ]),
    ("NEXUS", [
        r"\ba2a\b", r"\bmcp\b", r"agentic", r"agent\s+protocol",
        r"agent.to.agent", r"model\s+context\s+protocol",
        r"agent\s+payment", r"agent\s+infrastructure",
        r"open\s+banking.*agent", r"future\s+of\s+agent",
    ]),
    ("FORGE", [
        r"github\.com", r"python\s+code", r"fastapi", r"def\s+\w+\(",
        r"class\s+\w+", r"import\s+", r"async\s+def", r"architecture",
        r"pull\s+request", r"stack\s+overflow", r"dockerfile",
    ]),
    ("AMPLIFY", [
        r"instagram\.com", r"tiktok\.com", r"linkedin\.com/posts",
        r"youtube\.com/watch", r"youtu\.be/",
        r"tweet|twitter\.com", r"content\s+idea",
        r"substack\.com", r"newsletter",
        r"hook:", r"cta:", r"caption:",
    ]),
    ("VITALITY", [
        r"recipe", r"calories", r"protein", r"workout",
        r"sleep\s+quality", r"steps\s+today", r"gym",
        r"huberman", r"peter\s+attia", r"health\s+protocol",
    ]),
    ("CIPHER", [
        r"arxiv\.org", r"huggingface\.co", r"openai\.com",
        r"anthropic\.com", r"techcrunch\.com", r"wired\.com",
        r"ai\s+model", r"llm\b", r"gpt-", r"claude\s+\d",
        r"research\s+paper", r"new\s+study",
    ]),
    # ATLAS — career/strategy
    ("ATLAS", [
        r"promotion", r"career\s+path", r"salary\s+negotiat",
        r"should\s+i\s+take\s+this", r"positioning", r"consulting\s+rate",
        r"go.to.market", r"business\s+strategy",
    ]),
    # COLOSSUS — code review
    ("COLOSSUS", [
        r"review\s+my\s+code", r"tear\s+this\s+apart", r"ready\s+to\s+ship",
        r"code\s+review", r"architecture\s+critique", r"roast\s+this",
    ]),
]

VAULT_PATH_MAP: dict[str, str] = {
    "PHOENIX":  "02 Finance/Captures",
    "AEGIS":    "06 Learning/AI Security",
    "NEXUS":    "06 Learning/Agentic Future",
    "FORGE":    "03 Builds/Captures",
    "AMPLIFY":  "04 Content/Captures",
    "VITALITY": "07 Health/Captures",
    "CIPHER":   "06 Learning/Insights",
    "SENTINEL": "01 Brain Dumps/Captures",
    "ATLAS":    "05 Career/Captures",
    "COLOSSUS": "03 Builds/Code Reviews",
}


def detect_agent(text: str) -> str:
    """Detect which agent should handle this content based on text signals."""
    lower = text.lower()
    for agent, patterns in AGENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, lower):
                return agent
    return "SENTINEL"


def detect_revenue_angle(agent: str, text: str) -> str:
    """Generate a brief revenue angle hint based on agent and content."""
    angles: dict[str, str] = {
        "PHOENIX":  "💰 Finance insight → Teaching content or corporate workshop on personal finance + AI",
        "AEGIS":    "💰 Security knowledge → £3k-10k corporate AI security assessment + teaching content",
        "NEXUS":    "💰 Agentic future → Build the missing tool → open-source for audience + paid enterprise",
        "FORGE":    "💰 Build opportunity → ship it → teach how you built it → portfolio + product",
        "AMPLIFY":  "💰 Content signal → repurpose across platforms → grows audience → drives course sales",
        "VITALITY": "💰 Health content performs well → relatable hook for V's professional audience",
        "CIPHER":   "💰 Signal → CIPHER rating → if 🔴 must-read → content piece OR build idea within 48hrs",
        "SENTINEL": "💰 Brain dump → orders → forward motion → every order maps to income stream or skill",
        "ATLAS":    "💰 Career intelligence → positioning + negotiation → higher rate or promotion within 6mo",
        "COLOSSUS": "💰 Code quality → production-ready portfolio → proves enterprise capability to clients",
    }
    return angles.get(agent, "💰 How does this create revenue for V?")


# ── SQLite storage ─────────────────────────────────────────────────────

def _db_path() -> Path:
    data_dir = settings.data_dir if hasattr(settings, "data_dir") else Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "captures.db"


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at      TEXT NOT NULL,
            agent           TEXT NOT NULL,
            title           TEXT NOT NULL,
            content         TEXT NOT NULL,
            source_url      TEXT,
            vault_path      TEXT NOT NULL,
            tags            TEXT,
            revenue_angle   TEXT,
            obsidian_written INTEGER DEFAULT 0,
            enriched        INTEGER DEFAULT 0,
            signal_rating   TEXT DEFAULT '🟡',
            summary         TEXT,
            insights_json   TEXT
        )
    """)
    # Migrate: add new columns to existing tables gracefully
    for col, default in [
        ("enriched", "0"),
        ("signal_rating", "'🟡'"),
        ("summary", "NULL"),
        ("insights_json", "NULL"),
    ]:
        try:
            conn.execute(f"ALTER TABLE captures ADD COLUMN {col} TEXT DEFAULT {default}")
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()


def save_capture(
    *,
    content: str,
    title: str | None = None,
    agent: str | None = None,
    source_url: str | None = None,
    tags: list[str] | None = None,
    enrich: bool = True,
) -> dict[str, Any]:
    """Detect agent, optionally enrich via orchestrator, store in SQLite, write to Obsidian.

    Args:
        content: Raw text from V.
        title: Optional explicit title.
        agent: Optional agent override (skip detection).
        source_url: Optional explicit URL.
        tags: Optional additional tags.
        enrich: If True (default), run through orchestrator for LLM enrichment.

    Returns:
        The saved capture dict with all fields populated.
    """
    # Step 1: Run through orchestrator for intelligent enrichment
    enriched_data = None
    if enrich:
        try:
            from vaishali.orchestrator import orchestrate
            enriched_data = orchestrate(
                content,
                agent_override=agent,
                source_url=source_url,
            )
            log.info("Orchestrator enriched: agent=%s title=%s rating=%s",
                     enriched_data.agent, enriched_data.title, enriched_data.signal_rating)
        except Exception as e:
            log.warning("Orchestrator failed, falling back to static: %s", e)

    # Step 2: Determine final values (enriched or static fallback)
    if enriched_data:
        detected_agent = enriched_data.agent
        final_title = enriched_data.title
        revenue_angle = enriched_data.revenue_angle
        signal_rating = enriched_data.signal_rating
        summary = enriched_data.summary
        insights_json = json.dumps(enriched_data.insights)
        final_content = enriched_data.enriched_content
        final_tags = enriched_data.tags + ["#enriched"]
        source_url = enriched_data.source_url or source_url or ""
        is_enriched = True
    else:
        detected_agent = agent or detect_agent(content)
        final_content = content
        revenue_angle = detect_revenue_angle(detected_agent, content)
        signal_rating = "🟡"
        summary = content[:200]
        insights_json = "[]"
        is_enriched = False

        if not title:
            first_line = content.strip().split("\n")[0][:60].strip()
            final_title = first_line or f"Capture {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        else:
            final_title = title

        final_tags = []
        source_url = source_url or ""

    # Step 3: Build vault path + tag list
    vault_folder = VAULT_PATH_MAP.get(detected_agent, "00 INBOX")
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    all_tags = ["#vaf", f"#agent/{detected_agent.lower()}", "#capture"]
    if is_enriched:
        all_tags.append("#enriched")
    if signal_rating == "🟢":
        all_tags.append("#must-act")
    all_tags.extend(final_tags)
    if tags:
        all_tags.extend(tags)
    # Deduplicate
    all_tags = list(dict.fromkeys(all_tags))

    safe_title = re.sub(r"[^\w\s-]", "", final_title)[:40].strip().replace(" ", "-")
    vault_path = f"{vault_folder}/{date_str}-{safe_title}.md"

    # Step 4: Persist to SQLite
    capture: dict[str, Any] = {
        "created_at": now.isoformat(),
        "agent": detected_agent,
        "title": final_title,
        "content": final_content,
        "source_url": source_url,
        "vault_path": vault_path,
        "tags": json.dumps(all_tags),
        "revenue_angle": revenue_angle,
        "obsidian_written": 0,
        "enriched": int(is_enriched),
        "signal_rating": signal_rating,
        "summary": summary,
        "insights_json": insights_json,
    }

    db = _db_path()
    with sqlite3.connect(db) as conn:
        _init_db(conn)
        cur = conn.execute(
            """INSERT INTO captures
               (created_at, agent, title, content, source_url, vault_path,
                tags, revenue_angle, obsidian_written, enriched, signal_rating,
                summary, insights_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                capture["created_at"], capture["agent"], capture["title"],
                capture["content"], capture["source_url"], capture["vault_path"],
                capture["tags"], capture["revenue_angle"], 0,
                capture["enriched"], capture["signal_rating"],
                capture["summary"], capture["insights_json"],
            ),
        )
        capture["id"] = cur.lastrowid
        conn.commit()

    # Step 5: Write to Obsidian vault
    written = _write_to_obsidian(capture, all_tags, is_enriched)
    if written:
        with sqlite3.connect(db) as conn:
            conn.execute(
                "UPDATE captures SET obsidian_written=1 WHERE id=?",
                (capture["id"],),
            )
            conn.commit()
        capture["obsidian_written"] = 1

    log.info("Capture saved: agent=%s title=%s vault=%s enriched=%s",
             detected_agent, final_title, vault_path, is_enriched)
    return capture


def save_capture_quick(
    *,
    content: str,
    title: str | None = None,
    agent: str | None = None,
    source_url: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Fast capture without LLM enrichment — for when speed matters over depth."""
    return save_capture(
        content=content,
        title=title,
        agent=agent,
        source_url=source_url,
        tags=tags,
        enrich=False,
    )


def _write_to_obsidian(
    capture: dict[str, Any],
    tags: list[str],
    is_enriched: bool,
) -> bool:
    """Write capture as a markdown note to the Obsidian vault."""
    vault = getattr(settings, "obsidian_vault_dir", None)
    if not vault or not Path(vault).exists():
        log.warning("Obsidian vault not found at %s — capture stored in SQLite only", vault)
        return False

    vault_root = Path(vault)
    note_path = vault_root / "V AgentForce" / capture["vault_path"]
    note_path.parent.mkdir(parents=True, exist_ok=True)

    created_at = capture["created_at"][:10]
    source_line = f"source_url: {capture['source_url']}\n" if capture.get("source_url") else ""
    tag_str = " ".join(tags)
    signal = capture.get("signal_rating", "🟡")
    enriched_marker = "enriched: true\n" if is_enriched else ""

    # Build insights block if enriched
    insights_block = ""
    if is_enriched and capture.get("insights_json"):
        try:
            insights = json.loads(capture["insights_json"])
            if insights:
                items = "\n".join(f"- {i}" for i in insights)
                insights_block = f"\n## Key Insights\n\n{items}\n"
        except (json.JSONDecodeError, TypeError):
            pass

    # Build summary block
    summary_block = ""
    if capture.get("summary"):
        summary_block = f"\n> {capture['summary']}\n"

    note_content = f"""---
date: {created_at}
agent: {capture['agent']}
signal: {signal}
{enriched_marker}{source_line}tags: [{tag_str}]
vault_path: V AgentForce/{capture['vault_path']}
---

# {capture['title']}
{summary_block}
{capture['content']}
{insights_block}
---

{capture['revenue_angle']}
"""

    note_path.write_text(note_content, encoding="utf-8")
    log.info("Written to Obsidian: %s", note_path)
    return True


def get_captures(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent captures ordered newest first."""
    db = _db_path()
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        _init_db(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM captures ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_captures_by_agent(agent: str, limit: int = 20) -> list[dict[str, Any]]:
    """Return captures for a specific agent."""
    db = _db_path()
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        _init_db(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM captures WHERE agent=? ORDER BY id DESC LIMIT ?",
            (agent.upper(), limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_must_act_captures(limit: int = 10) -> list[dict[str, Any]]:
    """Return captures with 🟢 must-act signal rating."""
    db = _db_path()
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        _init_db(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM captures WHERE signal_rating='🟢' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_capture_stats() -> dict[str, Any]:
    """Return aggregate capture statistics for dashboard."""
    db = _db_path()
    if not db.exists():
        return {"total": 0, "enriched": 0, "must_act": 0, "by_agent": {}}
    with sqlite3.connect(db) as conn:
        _init_db(conn)
        total = conn.execute("SELECT COUNT(*) FROM captures").fetchone()[0]
        enriched = conn.execute("SELECT COUNT(*) FROM captures WHERE enriched=1").fetchone()[0]
        must_act = conn.execute("SELECT COUNT(*) FROM captures WHERE signal_rating='🟢'").fetchone()[0]
        obsidian = conn.execute("SELECT COUNT(*) FROM captures WHERE obsidian_written=1").fetchone()[0]

        agent_rows = conn.execute(
            "SELECT agent, COUNT(*) as cnt FROM captures GROUP BY agent ORDER BY cnt DESC"
        ).fetchall()
        by_agent = {row[0]: row[1] for row in agent_rows}

    return {
        "total": total,
        "enriched": enriched,
        "must_act": must_act,
        "obsidian_written": obsidian,
        "by_agent": by_agent,
    }
