"""
checkins/store.py — Goggins 5 Non-Negotiables accountability engine.

The 5 Daily Non-Negotiables (scored 0–10 each day):
  BODY    — 5×5 Protocol (5 push-ups, 5 pull-ups, 5 abs, 5 squats, 5 flex)
  BUILD   — Ship 1 production thing (feature, fix, new tool, deployed)
  LEARN   — Complete 1 AWS Claude course lesson + drop key takeaway to CIPHER
  AMPLIFY — Create or schedule 1 piece of content (post, video, thread)
  BRIEF   — Morning SENTINEL brief + evening debrief completed

Total possible: 50 pts / day. Streak = consecutive days with total ≥ 25.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────────────────

NON_NEGOTIABLES: list[str] = ["BODY", "BUILD", "LEARN", "AMPLIFY", "BRIEF"]

NEGOTIABLE_DESCRIPTIONS: dict[str, str] = {
    "BODY":    "5×5 Protocol — push-ups, pull-ups, abs, squats, flex",
    "BUILD":   "Ship 1 production thing — code, feature, fix, or tool",
    "LEARN":   "1 AWS Claude course lesson + CIPHER note",
    "AMPLIFY": "1 piece of content created or scheduled",
    "BRIEF":   "Morning SENTINEL brief + evening debrief",
}

NEGOTIABLE_EMOJIS: dict[str, str] = {
    "BODY":    "🔥",
    "BUILD":   "🏗️",
    "LEARN":   "🧠",
    "AMPLIFY": "📱",
    "BRIEF":   "📋",
}

MIN_STREAK_SCORE = 25  # out of 50 — below this breaks the streak


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_path() -> Path:
    base = os.getenv("VAF_DATA_DIR", str(Path.home() / ".vaishali"))
    return Path(base) / "checkins.db"


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            checkin_date TEXT NOT NULL UNIQUE,
            body        INTEGER NOT NULL DEFAULT 0,
            build       INTEGER NOT NULL DEFAULT 0,
            learn       INTEGER NOT NULL DEFAULT 0,
            amplify     INTEGER NOT NULL DEFAULT 0,
            brief       INTEGER NOT NULL DEFAULT 0,
            total       INTEGER NOT NULL DEFAULT 0,
            note        TEXT DEFAULT '',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _conn() -> sqlite3.Connection:
    db = _db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


# ── Core functions ─────────────────────────────────────────────────────────────

def save_checkin(
    scores: dict[str, int],
    note: str = "",
    checkin_date: str | None = None,
) -> dict[str, Any]:
    """
    Save or update today's non-negotiable scores.

    scores: dict with keys BODY, BUILD, LEARN, AMPLIFY, BRIEF (each 0–10)
    Returns the full checkin record.
    """
    today = checkin_date or date.today().isoformat()

    # Clamp all scores to 0–10
    clean = {k: max(0, min(10, int(scores.get(k, 0)))) for k in NON_NEGOTIABLES}
    total = sum(clean.values())

    with _conn() as conn:
        conn.execute("""
            INSERT INTO checkins (checkin_date, body, build, learn, amplify, brief, total, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(checkin_date) DO UPDATE SET
                body    = excluded.body,
                build   = excluded.build,
                learn   = excluded.learn,
                amplify = excluded.amplify,
                brief   = excluded.brief,
                total   = excluded.total,
                note    = excluded.note,
                created_at = datetime('now')
        """, (
            today,
            clean["BODY"], clean["BUILD"], clean["LEARN"],
            clean["AMPLIFY"], clean["BRIEF"],
            total, note,
        ))
        conn.commit()

    record = get_today_checkin(today)
    _write_to_obsidian(record)
    return record


def get_today_checkin(checkin_date: str | None = None) -> dict[str, Any] | None:
    today = checkin_date or date.today().isoformat()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM checkins WHERE checkin_date = ?", (today,)
        ).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def get_checkins(limit: int = 30) -> list[dict[str, Any]]:
    """Return most recent `limit` checkins, newest first."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM checkins ORDER BY checkin_date DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_streak() -> int:
    """
    Current streak = consecutive days ending today (or yesterday) where
    total >= MIN_STREAK_SCORE.
    """
    checkins = get_checkins(limit=365)
    if not checkins:
        return 0

    by_date = {c["checkin_date"]: c["total"] for c in checkins}
    today = date.today()

    # Allow streak to be based on today or yesterday
    start = today if today.isoformat() in by_date else today - timedelta(days=1)

    streak = 0
    cursor = start
    while True:
        key = cursor.isoformat()
        if key in by_date and by_date[key] >= MIN_STREAK_SCORE:
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break

    return streak


def get_stats(days: int = 30) -> dict[str, Any]:
    """Aggregated stats for the last N days."""
    checkins = get_checkins(limit=days)
    if not checkins:
        return {
            "streak": 0,
            "avg_total": 0,
            "best_total": 0,
            "completion_rate": 0,
            "by_negotiable": {k: {"avg": 0, "best": 0} for k in NON_NEGOTIABLES},
            "checkins": [],
        }

    totals = [c["total"] for c in checkins]
    return {
        "streak": get_streak(),
        "avg_total": round(sum(totals) / len(totals), 1),
        "best_total": max(totals),
        "completion_rate": round(
            sum(1 for t in totals if t >= MIN_STREAK_SCORE) / len(totals) * 100, 1
        ),
        "by_negotiable": {
            k: {
                "avg": round(sum(c["scores"][k] for c in checkins) / len(checkins), 1),
                "best": max(c["scores"][k] for c in checkins),
            }
            for k in NON_NEGOTIABLES
        },
        "checkins": checkins,
    }


# ── Obsidian writer ────────────────────────────────────────────────────────────

def _write_to_obsidian(checkin: dict[str, Any] | None) -> bool:
    if checkin is None:
        return False

    vault_root = os.getenv("VAF_OBSIDIAN_VAULT_DIR")
    if not vault_root:
        return False

    folder = Path(vault_root) / "08 Accountability" / "Daily Check-ins"
    folder.mkdir(parents=True, exist_ok=True)

    score_bars = ""
    for k in NON_NEGOTIABLES:
        v = checkin["scores"][k]
        bar = "█" * v + "░" * (10 - v)
        score_bars += f"| {NEGOTIABLE_EMOJIS[k]} {k:<8} | {bar} | {v}/10 |\n"

    content = f"""---
date: {checkin["checkin_date"]}
type: daily-checkin
total: {checkin["total"]}
streak: {get_streak()}
tags: [accountability, goggins, daily]
---

# Daily Check-in — {checkin["checkin_date"]}

## 🔥 Non-Negotiables Score: {checkin["total"]}/50

| Non-Negotiable | Progress | Score |
|---|---|---|
{score_bars}
## 📝 Note
{checkin.get("note") or "_No note today._"}

---
*Logged via V AgentForce · Goggins Protocol*
"""

    note_path = folder / f"{checkin['checkin_date']}.md"
    try:
        note_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["scores"] = {
        "BODY":    d.pop("body"),
        "BUILD":   d.pop("build"),
        "LEARN":   d.pop("learn"),
        "AMPLIFY": d.pop("amplify"),
        "BRIEF":   d.pop("brief"),
    }
    return d


def motivational_feedback(total: int) -> str:
    """Goggins-style feedback based on total score."""
    if total == 50:
        return "🔥 PERFECT DAY. That's what carrying the boats looks like."
    if total >= 45:
        return "💪 Almost perfect. Identify what you missed — fix it tomorrow."
    if total >= 35:
        return "✅ Solid day. But you know you left something in the tank."
    if total >= 25:
        return "⚠️ You survived. That's not the same as winning. Tomorrow, go harder."
    if total >= 15:
        return "🛑 Soft day, V. These are non-negotiables. What happened?"
    return "🚨 You got outworked today. That feeling? Use it. Tomorrow is war."
