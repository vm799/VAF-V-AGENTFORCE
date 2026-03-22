"""Dashboard backend API — FastAPI app serving agent summaries and commands.

Routes are mounted under /api so the React SPA can be served from root.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import read_all_summaries, read_summary
from vaishali.dashboard.graph import build_graph_data

log = get_logger(__name__)

# ── FastAPI app + API router ───────────────────────────────────────────

app = FastAPI(
    title="Vaishali Agent Force",
    description="Command Center dashboard API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


# ── Models ─────────────────────────────────────────────────────────────

class CommandRequest(BaseModel):
    command: str  # "morning", "evening", "ingest", "where_are_we"


# ── API Routes ─────────────────────────────────────────────────────────

@api.get("/status")
def get_status() -> dict[str, Any]:
    """Per-agent last run status and system health."""
    today = date.today()
    summaries = read_all_summaries(today)
    return {
        "date": today.isoformat(),
        "agents": {
            agent: {
                "has_data": s is not None,
                "headline": s.get("headline", "") if s else "No data",
                "status": s.get("status", "idle") if s else "idle",
                "mood": s.get("mood", "") if s else "",
            }
            for agent, s in summaries.items()
        },
        "system": "ok",
    }


@api.get("/finance/summary/today")
def finance_summary_today() -> dict[str, Any]:
    return _get_today_summary("finance")


@api.get("/content/summary/today")
def content_summary_today() -> dict[str, Any]:
    return _get_today_summary("content")


@api.get("/education/summary/today")
def education_summary_today() -> dict[str, Any]:
    return _get_today_summary("education")


@api.get("/research/summary/today")
def research_summary_today() -> dict[str, Any]:
    return _get_today_summary("research")


@api.get("/health/summary/today")
def health_summary_today() -> dict[str, Any]:
    return _get_today_summary("health")


@api.get("/braindump/summary/today")
def braindump_summary_today() -> dict[str, Any]:
    return _get_today_summary("braindump")


@api.get("/braindump/thoughts")
def braindump_thoughts() -> dict[str, Any]:
    """Return all braindump thoughts (recent first)."""
    from vaishali.braindump.storage import get_active_actions, get_stats, load_thoughts
    thoughts = load_thoughts()
    thoughts.reverse()  # newest first
    return {
        "thoughts": [t.to_dict() for t in thoughts[:50]],
        "stats": get_stats(),
        "active_actions": [t.to_dict() for t in get_active_actions()],
    }


@api.get("/briefings/today")
def briefing_today() -> dict[str, Any]:
    """Today's unified briefing — returns empty skeleton if no briefing run yet."""
    import json

    today = date.today()
    path = settings.briefings_dir / f"{today.isoformat()}.json"
    if not path.exists():
        # Try yesterday's briefing as fallback so the dashboard always has data
        yesterday = settings.briefings_dir / f"{(today.replace(day=today.day - 1)).isoformat()}.json"
        if yesterday.exists():
            data = json.loads(yesterday.read_text(encoding="utf-8"))
            data["_stale"] = True
            data["_stale_message"] = "Showing yesterday's briefing — run /run_morning to refresh."
            return data
        return {
            "date": today.isoformat(),
            "headline": "No briefing yet today",
            "summary": "Send /run_morning in Telegram to generate your first briefing, or run: ./vaf.sh briefing",
            "agents": {},
            "_empty": True,
        }
    return json.loads(path.read_text(encoding="utf-8"))


@api.get("/insights")
def get_insights(limit: int = 20) -> dict[str, Any]:
    """Recent Claude-extracted insights from dropped links.

    Each insight has: title, url, summary, key_insights, key_topics,
    action_items, quality_score, created_at.
    """
    from vaishali.education.insight_writer import load_recent_insights
    items = load_recent_insights(limit=limit)
    return {"insights": items, "total": len(items)}


@api.get("/graph")
def get_graph() -> dict[str, Any]:
    """Knowledge graph data for the dashboard visualisation."""
    return build_graph_data()


@api.get("/urls")
def get_urls() -> dict[str, Any]:
    """All queued / processed URLs with NLM status.

    Returns items newest-first. Each entry includes:
      id, url, title, category, status, queued_at, nlm_summary, error
    """
    from vaishali.education.url_queue import get_all
    items = get_all()  # already sorted newest-first
    total = len(items)
    pending = sum(1 for i in items if i.get("status") == "pending")
    done = sum(1 for i in items if i.get("status") == "done")
    failed = sum(1 for i in items if i.get("status") == "failed")
    return {
        "urls": items,
        "total": total,
        "pending": pending,
        "done": done,
        "failed": failed,
    }


@api.get("/captures")
def get_captures(limit: int = 50) -> dict[str, Any]:
    """Recent Claude Project captures — drops saved via /save or POST /api/capture."""
    from vaishali.captures.store import get_captures as _get
    items = _get(limit=limit)
    return {
        "captures": items,
        "total": len(items),
        "by_agent": _count_by_agent(items),
    }


class CaptureRequest(BaseModel):
    content: str
    title: str | None = None
    agent: str | None = None     # override auto-detection
    source_url: str | None = None
    tags: list[str] | None = None


@api.post("/capture")
def create_capture(req: CaptureRequest) -> dict[str, Any]:
    """Accept a Claude Project output drop — detect agent, save to SQLite + Obsidian.

    Called by:
      - Telegram /save handler
      - iOS Shortcut (future)
    """
    from vaishali.captures.store import save_capture
    capture = save_capture(
        content=req.content,
        title=req.title,
        agent=req.agent,
        source_url=req.source_url,
        tags=req.tags,
    )
    return {
        "status": "saved",
        "agent": capture["agent"],
        "title": capture["title"],
        "vault_path": capture["vault_path"],
        "obsidian_written": bool(capture["obsidian_written"]),
        "revenue_angle": capture["revenue_angle"],
    }


def _count_by_agent(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        a = item.get("agent", "UNKNOWN")
        counts[a] = counts.get(a, 0) + 1
    return counts


# ── Goggins Non-Negotiables / Accountability endpoints ────────────────────────

@api.get("/checkins")
def get_checkins_endpoint(limit: int = 30) -> dict[str, Any]:
    """Return recent daily check-ins with streak + stats."""
    from vaishali.checkins.store import get_checkins, get_streak, get_stats
    stats = get_stats(days=limit)
    return {
        "streak": stats["streak"],
        "avg_total": stats["avg_total"],
        "best_total": stats["best_total"],
        "completion_rate": stats["completion_rate"],
        "by_negotiable": stats["by_negotiable"],
        "checkins": stats["checkins"],
    }


@api.get("/checkins/today")
def get_today_checkin_endpoint() -> dict[str, Any]:
    """Return today's check-in or empty state."""
    from vaishali.checkins.store import get_today_checkin, get_streak
    today = get_today_checkin()
    return {
        "checkin": today,
        "streak": get_streak(),
        "has_checkin": today is not None,
    }


@api.post("/commands/run")
def run_command(req: CommandRequest) -> dict[str, Any]:
    """Trigger a script (morning briefing, evening briefing, etc.)."""
    command_map: dict[str, str] = {
        "morning": "run_morning_briefing.py",
        "evening": "run_evening_briefing.py",
        "where_are_we": "where_are_we_today.py",
        "ingest": "ingest_finance_statements.py",
    }

    script_name = command_map.get(req.command)
    if not script_name:
        raise HTTPException(status_code=400, detail=f"Unknown command: {req.command}")

    script_path = settings.scripts_dir / script_name
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script not found: {script_name}")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(settings.base_dir),
            env={**__import__("os").environ, "PYTHONPATH": str(settings.base_dir / "src")},
        )
        return {
            "command": req.command,
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"command": req.command, "status": "timeout", "stdout": "", "stderr": "Script timed out after 120s"}


@api.post("/briefings/speak")
def speak_briefing() -> dict[str, Any]:
    """Load today's briefing and speak it aloud using macOS TTS."""
    from vaishali.dashboard.voice import speak_briefing_for_today

    try:
        result = speak_briefing_for_today()
        return {"status": "speaking", "duration_estimate": result.get("duration_estimate", "~5 minutes")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/reports")
def list_reports() -> dict[str, Any]:
    """List all files in reports/ and data/briefings/ and data/summaries/ recursively.

    Returns tree structure with metadata for each file.
    """
    import os

    result: dict[str, Any] = {"files": []}

    # Define allowed base directories
    allowed_dirs = [
        settings.reports_dir,
        settings.briefings_dir,
        settings.data_dir / "summaries",
        settings.data_dir / "braindump",
    ]

    def get_file_type(path: Path) -> str:
        """Determine preview type based on file extension."""
        suffix = path.suffix.lower()
        type_map = {
            ".md": "markdown",
            ".json": "json",
            ".csv": "csv",
            ".txt": "text",
            ".log": "text",
            ".pdf": "pdf",
        }
        return type_map.get(suffix, "text")

    def scan_dir(base_path: Path, rel_prefix: str = "") -> None:
        """Recursively scan directory and collect files."""
        if not base_path.exists():
            return

        try:
            for entry in sorted(base_path.iterdir()):
                if entry.name.startswith("."):
                    continue

                rel_path = f"{rel_prefix}/{entry.name}".lstrip("/")

                if entry.is_file():
                    stat = entry.stat()
                    result["files"].append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": get_file_type(entry),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
                elif entry.is_dir():
                    scan_dir(entry, rel_path)
        except (PermissionError, OSError):
            pass

    # Scan all allowed directories
    for base_dir in allowed_dirs:
        if base_dir.exists():
            scan_dir(base_dir)

    return result


@api.get("/reports/content")
def get_report_content(path: str) -> dict[str, Any]:
    """Return the content of a report file as text.

    path is relative to project base_dir.
    Security: only allow paths under reports/, data/briefings/, data/summaries/, data/braindump/
    """
    # Security: prevent path traversal
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=403, detail="Invalid path")

    # Resolve full path
    full_path = settings.base_dir / path

    # Verify path is within allowed directories
    allowed_dirs = [
        settings.reports_dir,
        settings.briefings_dir,
        settings.data_dir / "summaries",
        settings.data_dir / "braindump",
    ]

    is_allowed = False
    try:
        for allowed_dir in allowed_dirs:
            full_path.resolve().relative_to(allowed_dir.resolve())
            is_allowed = True
            break
    except ValueError:
        pass

    if not is_allowed:
        raise HTTPException(status_code=403, detail="Path not in allowed directories")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    # Determine file type
    suffix = full_path.suffix.lower()
    type_map = {
        ".md": "markdown",
        ".json": "json",
        ".csv": "csv",
        ".txt": "text",
        ".log": "text",
    }
    file_type = type_map.get(suffix, "text")

    return {
        "content": content,
        "type": file_type,
        "path": str(full_path.relative_to(settings.base_dir)),
    }


# ── Helpers ────────────────────────────────────────────────────────────

def _get_today_summary(agent: str) -> dict[str, Any]:
    data = read_summary(agent, date.today())
    if data is None:
        # Return empty skeleton — never 404 a live dashboard
        return {
            "agent": agent,
            "date": date.today().isoformat(),
            "headline": f"No {agent} data yet",
            "status": "idle",
            "summary": f"No {agent} summary for today. Trigger a briefing run to populate.",
            "_empty": True,
        }
    return data


# ── Mount API router ───────────────────────────────────────────────────

app.include_router(api)


# ── Static file serving (built React frontend) ────────────────────────
# Mounted AFTER API routes so /api/* is always handled by FastAPI.

_frontend_dist = settings.base_dir / "frontend" / "dist"
if _frontend_dist.exists() and (_frontend_dist / "index.html").exists():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="static-assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Serve React SPA — all non-API routes return index.html."""
        file_path = _frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))
