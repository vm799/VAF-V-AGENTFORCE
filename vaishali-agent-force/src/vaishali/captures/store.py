"""Captures store — persists intelligence drops from Claude Project to SQLite.

Receives structured payloads from:
  - Telegram /save command (V forwards Claude output)
  - POST /api/capture (future iOS Shortcut)

Writes to:
  - SQLite captures table (for dashboard display)
  - Obsidian vault (via obsidian_sync logic)
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
    # PHOENIX — finance/money signals
    ("PHOENIX", [
        r"bank\s+statement", r"transaction", r"debit|credit", r"sort\s+code",
        r"account\s+number", r"statement\s+analysis", r"spending", r"savings",
        r"isa\b", r"sipp\b", r"pension", r"interest\s+rate", r"mortgage",
        r"bloomberg\.com", r"ft\.com", r"financial\s+times",
        r"£\d+", r"salary", r"income", r"budget",
    ]),
    # AEGIS — AI security signals
    ("AEGIS", [
        r"maestro", r"owasp", r"prompt\s+injection", r"ai\s+security",
        r"llm\s+vulner", r"jailbreak", r"model\s+attack", r"red\s+team",
        r"nist\s+ai", r"eu\s+ai\s+act", r"security\s+framework",
        r"data\s+poisoning", r"insecure\s+output",
    ]),
    # NEXUS — agentic future signals
    ("NEXUS", [
        r"\ba2a\b", r"\bmcp\b", r"agentic", r"agent\s+protocol",
        r"agent.to.agent", r"model\s+context\s+protocol",
        r"agent\s+payment", r"agent\s+infrastructure",
        r"open\s+banking.*agent", r"future\s+of\s+agent",
    ]),
    # FORGE — build/code signals
    ("FORGE", [
        r"github\.com", r"python\s+code", r"fastapi", r"def\s+\w+\(",
        r"class\s+\w+", r"import\s+", r"async\s+def", r"architecture",
        r"pull\s+request", r"stack\s+overflow", r"dockerfile",
    ]),
    # AMPLIFY — content/social signals
    ("AMPLIFY", [
        r"instagram\.com", r"tiktok\.com", r"linkedin\.com/posts",
        r"youtube\.com/watch", r"youtu\.be/",
        r"tweet|twitter\.com", r"content\s+idea",
        r"substack\.com", r"newsletter",
        r"hook:", r"cta:", r"caption:",
    ]),
    # VITALITY — health signals
    ("VITALITY", [
        r"recipe", r"calories", r"protein", r"workout",
        r"sleep\s+quality", r"steps\s+today", r"gym",
        r"huberman", r"peter\s+attia", r"health\s+protocol",
    ]),
    # CIPHER — learning/AI news (broad catch-all for URLs + articles)
    ("CIPHER", [
        r"arxiv\.org", r"huggingface\.co", r"openai\.com",
        r"anthropic\.com", r"techcrunch\.com", r"wired\.com",
        r"ai\s+model", r"llm\b", r"gpt-", r"claude\s+\d",
        r"research\s+paper", r"new\s+study",
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
}


def detect_agent(text: str) -> str:
    """Detect which agent should handle this content based on text signals."""
    lower = text.lower()
    for agent, patterns in AGENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, lower):
                return agent
    return "SENTINEL"  # default: route to squad commander


def detect_revenue_angle(agent: str, text: str) -> str:
    """Generate a brief revenue angle hint based on agent and content."""
    angles: dict[str, str] = {
        "PHOENIX": "💰 Finance insight → Teaching content or corporate workshop on personal finance + AI",
        "AEGIS":   "💰 Security knowledge → £3k-10k corporate AI security assessment + teaching content",
        "NEXUS":   "💰 Agentic future → Build the missing tool → open-source for audience + paid enterprise",
        "FORGE":   "💰 Build opportunity → ship it → teach how you built it → portfolio + product",
        "AMPLIFY": "💰 Content signal → repurpose across platforms → grows audience → drives course sales",
        "VITALITY":"💰 Health content performs well → relatable hook for V's professional audience",
        "CIPHER":  "💰 Signal → CIPHER rating → if 🔴 must-read → content piece OR build idea within 48hrs",
        "SENTINEL":"💰 Brain dump → orders → forward motion → every order maps to income stream or skill",
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
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT NOT NULL,
            agent       TEXT NOT NULL,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            source_url  TEXT,
            vault_path  TEXT NOT NULL,
            tags        TEXT,
            revenue_angle TEXT,
            obsidian_written INTEGER DEFAULT 0
        )
    """)
    conn.commit()


def save_capture(
    *,
    content: str,
    title: str | None = None,
    agent: str | None = None,
    source_url: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Detect agent, store in SQLite, write to Obsidian.

    Returns the saved capture dict.
    """
    detected_agent = agent or detect_agent(content)
    vault_folder = VAULT_PATH_MAP.get(detected_agent, "00 INBOX")
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Build title if not provided
    if not title:
        # Use first line or first 60 chars
        first_line = content.strip().split("\n")[0][:60].strip()
        title = first_line or f"Capture {date_str} {time_str}"

    revenue_angle = detect_revenue_angle(detected_agent, content)
    all_tags = ["#vaf", f"#agent/{detected_agent.lower()}", "#capture", "#mobile-drop"]
    if tags:
        all_tags.extend(tags)

    vault_path = f"{vault_folder}/{date_str}-{title[:40].replace(' ', '-').replace('/', '-')}.md"

    capture: dict[str, Any] = {
        "created_at": now.isoformat(),
        "agent": detected_agent,
        "title": title,
        "content": content,
        "source_url": source_url or "",
        "vault_path": vault_path,
        "tags": json.dumps(all_tags),
        "revenue_angle": revenue_angle,
        "obsidian_written": 0,
    }

    db = _db_path()
    with sqlite3.connect(db) as conn:
        _init_db(conn)
        cur = conn.execute(
            """INSERT INTO captures
               (created_at, agent, title, content, source_url, vault_path,
                tags, revenue_angle, obsidian_written)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                capture["created_at"], capture["agent"], capture["title"],
                capture["content"], capture["source_url"], capture["vault_path"],
                capture["tags"], capture["revenue_angle"], 0,
            ),
        )
        capture["id"] = cur.lastrowid
        conn.commit()

    # Write to Obsidian vault
    written = _write_to_obsidian(capture, all_tags)
    if written:
        with sqlite3.connect(db) as conn:
            conn.execute(
                "UPDATE captures SET obsidian_written=1 WHERE id=?",
                (capture["id"],),
            )
            conn.commit()
        capture["obsidian_written"] = 1

    log.info("Capture saved: agent=%s title=%s vault=%s", detected_agent, title, vault_path)
    return capture


def _write_to_obsidian(capture: dict[str, Any], tags: list[str]) -> bool:
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

    note_content = f"""---
date: {created_at}
agent: {capture['agent']}
tags: [{tag_str}]
{source_line}vault_path: V AgentForce/{capture['vault_path']}
---

# {capture['title']}

{capture['content']}

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
