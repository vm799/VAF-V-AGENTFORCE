"""Dashboard backend API — FastAPI app serving agent summaries and commands.

Routes are mounted under /api so the React SPA can be served from root.

Golden thread endpoints:
  POST /api/capture          — enriched capture (orchestrator + Obsidian)
  POST /api/capture/quick    — fast capture (no LLM, just detect + save)
  GET  /api/captures         — list recent captures
  GET  /api/captures/stats   — aggregate capture intelligence
  GET  /api/captures/must-act — 🟢 must-act items requiring action
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
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
    description="Command Center dashboard API — the golden thread surfaces here",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


# ── Auth ──────────────────────────────────────────────────────────────

_CAPTURE_API_KEY = os.environ.get("VAF_CAPTURE_API_KEY", "")


def _verify_api_key(authorization: str | None = Header(None)) -> bool:
    """Verify Bearer token for external capture endpoints (iOS Shortcut).

    If no VAF_CAPTURE_API_KEY is set in env, auth is disabled (local-only mode).
    """
    if not _CAPTURE_API_KEY:
        return True  # No key configured = local development mode
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth format — use: Bearer <token>")
    token = authorization.removeprefix("Bearer ").strip()
    if token != _CAPTURE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


# ── Models ─────────────────────────────────────────────────────────────

class CommandRequest(BaseModel):
    command: str  # "morning", "evening", "ingest", "where_are_we"


class CaptureRequest(BaseModel):
    content: str
    title: str | None = None
    agent: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None


# ── Status + Summary Routes ───────────────────────────────────────────

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
    thoughts.reverse()
    return {
        "thoughts": [t.to_dict() for t in thoughts[:50]],
        "stats": get_stats(),
        "active_actions": [t.to_dict() for t in get_active_actions()],
    }


# ── Briefings ─────────────────────────────────────────────────────────

@api.get("/briefings/today")
def briefing_today() -> dict[str, Any]:
    """Today's unified briefing."""
    import json

    today = date.today()
    path = settings.briefings_dir / f"{today.isoformat()}.json"
    if not path.exists():
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
    """Recent Claude-extracted insights from dropped links."""
    from vaishali.education.insight_writer import load_recent_insights
    items = load_recent_insights(limit=limit)
    return {"insights": items, "total": len(items)}


@api.get("/graph")
def get_graph() -> dict[str, Any]:
    """Knowledge graph data for the dashboard visualisation."""
    return build_graph_data()


@api.get("/urls")
def get_urls() -> dict[str, Any]:
    """All queued / processed URLs."""
    from vaishali.education.url_queue import get_all
    items = get_all()
    total = len(items)
    pending = sum(1 for i in items if i.get("status") == "pending")
    done = sum(1 for i in items if i.get("status") == "done")
    failed = sum(1 for i in items if i.get("status") == "failed")
    return {"urls": items, "total": total, "pending": pending, "done": done, "failed": failed}


# ── Captures (Golden Thread) ─────────────────────────────────────────

@api.get("/captures")
def get_captures_endpoint(limit: int = 50) -> dict[str, Any]:
    """Recent captures — the intelligence feed."""
    from vaishali.captures.store import get_captures
    items = get_captures(limit=limit)
    return {
        "captures": items,
        "total": len(items),
        "by_agent": _count_by_agent(items),
    }


@api.get("/captures/stats")
def get_captures_stats() -> dict[str, Any]:
    """Aggregate capture intelligence for dashboard cards."""
    from vaishali.captures.store import get_capture_stats
    return get_capture_stats()


@api.get("/captures/must-act")
def get_must_act() -> dict[str, Any]:
    """Items rated 🟢 must-act — requires V's attention within 48hrs."""
    from vaishali.captures.store import get_must_act_captures
    items = get_must_act_captures(limit=10)
    return {"captures": items, "total": len(items)}


@api.get("/insights/weekly")
def get_weekly_insights_endpoint(days: int = 7) -> dict[str, Any]:
    """Weekly intelligence — themes, connections, revenue ops, Goggins trend."""
    from vaishali.insights.engine import get_weekly_insights
    return get_weekly_insights(days=days)


@api.get("/captures/agent/{agent}")
def get_captures_by_agent_endpoint(agent: str, limit: int = 20) -> dict[str, Any]:
    """Captures filtered by agent."""
    from vaishali.captures.store import get_captures_by_agent
    items = get_captures_by_agent(agent, limit=limit)
    return {"captures": items, "total": len(items), "agent": agent.upper()}


@api.post("/capture")
def create_capture(
    req: CaptureRequest,
    _auth: bool = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Enriched capture — runs through orchestrator (LLM enrichment + URL fetch).

    Called by:
      - Telegram /save handler
      - iOS Shortcut (authenticated via Bearer token)
      - Claude Mobile share sheet

    The orchestrator:
      1. Detects agent from content signals
      2. Fetches URL if present (CIPHER URL processor)
      3. Calls Claude Haiku with agent SKILL.md for structured enrichment
      4. Writes enriched note to Obsidian vault
      5. Stores in SQLite with signal rating + insights
    """
    from vaishali.captures.store import save_capture
    capture = save_capture(
        content=req.content,
        title=req.title,
        agent=req.agent,
        source_url=req.source_url,
        tags=req.tags,
        enrich=True,
    )
    return {
        "status": "saved",
        "enriched": bool(capture.get("enriched")),
        "agent": capture["agent"],
        "title": capture["title"],
        "signal_rating": capture.get("signal_rating", "🟡"),
        "vault_path": capture["vault_path"],
        "obsidian_written": bool(capture["obsidian_written"]),
        "revenue_angle": capture["revenue_angle"],
        "summary": capture.get("summary", ""),
    }


@api.post("/capture/quick")
def create_capture_quick(
    req: CaptureRequest,
    _auth: bool = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Fast capture — no LLM enrichment, just detect agent + save.

    Use when speed matters more than depth (e.g., rapid-fire brain dumps).
    """
    from vaishali.captures.store import save_capture_quick
    capture = save_capture_quick(
        content=req.content,
        title=req.title,
        agent=req.agent,
        source_url=req.source_url,
        tags=req.tags,
    )
    return {
        "status": "saved",
        "enriched": False,
        "agent": capture["agent"],
        "title": capture["title"],
        "vault_path": capture["vault_path"],
        "obsidian_written": bool(capture["obsidian_written"]),
        "revenue_angle": capture["revenue_angle"],
    }


# ── Goggins Non-Negotiables / Accountability ─────────────────────────

@api.get("/checkins")
def get_checkins_endpoint(limit: int = 30) -> dict[str, Any]:
    """Return recent daily check-ins with streak + stats."""
    from vaishali.checkins.store import get_stats
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


# ── Commands ──────────────────────────────────────────────────────────

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
            env={**os.environ, "PYTHONPATH": str(settings.base_dir / "src")},
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


# ── Reports ───────────────────────────────────────────────────────────

@api.get("/reports")
def list_reports() -> dict[str, Any]:
    """List all report files."""
    result: dict[str, Any] = {"files": []}

    allowed_dirs = [
        settings.reports_dir,
        settings.briefings_dir,
        settings.data_dir / "summaries",
        settings.data_dir / "braindump",
    ]

    def get_file_type(path: Path) -> str:
        suffix = path.suffix.lower()
        type_map = {".md": "markdown", ".json": "json", ".csv": "csv", ".txt": "text", ".log": "text", ".pdf": "pdf"}
        return type_map.get(suffix, "text")

    def scan_dir(base_path: Path, rel_prefix: str = "") -> None:
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
                        "name": entry.name, "path": rel_path,
                        "type": get_file_type(entry), "size": stat.st_size, "modified": stat.st_mtime,
                    })
                elif entry.is_dir():
                    scan_dir(entry, rel_path)
        except (PermissionError, OSError):
            pass

    for base_dir in allowed_dirs:
        if base_dir.exists():
            scan_dir(base_dir)
    return result


@api.get("/reports/content")
def get_report_content(path: str) -> dict[str, Any]:
    """Return the content of a report file as text."""
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=403, detail="Invalid path")

    full_path = settings.base_dir / path
    allowed_dirs = [
        settings.reports_dir, settings.briefings_dir,
        settings.data_dir / "summaries", settings.data_dir / "braindump",
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

    suffix = full_path.suffix.lower()
    type_map = {".md": "markdown", ".json": "json", ".csv": "csv", ".txt": "text", ".log": "text"}
    return {"content": content, "type": type_map.get(suffix, "text"), "path": str(full_path.relative_to(settings.base_dir))}


# ── Helpers ────────────────────────────────────────────────────────────

def _get_today_summary(agent: str) -> dict[str, Any]:
    data = read_summary(agent, date.today())
    if data is None:
        return {
            "agent": agent, "date": date.today().isoformat(),
            "headline": f"No {agent} data yet", "status": "idle",
            "summary": f"No {agent} summary for today. Trigger a briefing run to populate.",
            "_empty": True,
        }
    return data


def _count_by_agent(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        a = item.get("agent", "UNKNOWN")
        counts[a] = counts.get(a, 0) + 1
    return counts


# ── Mount API router ───────────────────────────────────────────────────

app.include_router(api)


# ── Static file serving (built React frontend) ────────────────────────

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


# ── Server startup ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
