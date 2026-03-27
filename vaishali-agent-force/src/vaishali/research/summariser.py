"""Research summariser — produce dossiers and daily research summaries."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import write_summary
from vaishali.research.jobs import ResearchJob, get_active_jobs, load_jobs

log = get_logger(__name__)


def create_dossier(job: ResearchJob, content_blocks: list[str] | None = None) -> Path:
    """Generate a research dossier in Markdown + JSON from a completed job.

    Args:
        job: The research job with findings populated.
        content_blocks: Optional additional text blocks to include.
    """
    dossier_dir = settings.data_dir / "research" / "dossiers"
    dossier_dir.mkdir(parents=True, exist_ok=True)

    md_path = dossier_dir / f"{job.id}_{_slugify(job.title)}.md"
    json_path = dossier_dir / f"{job.id}_{_slugify(job.title)}.json"

    # Markdown dossier
    lines = [
        f"# Research Dossier: {job.title}",
        "",
        f"**Question:** {job.question}",
        f"**Priority:** {job.priority}",
        f"**Status:** {job.status}",
        f"**Tags:** {', '.join(job.tags)}",
        "",
        "## Key Findings",
        "",
    ]
    for i, finding in enumerate(job.findings, 1):
        lines.append(f"{i}. {finding}")

    if job.recommendations:
        lines.extend(["", "## Recommendations", ""])
        for rec in job.recommendations:
            lines.append(f"- {rec}")

    if job.sources:
        lines.extend(["", "## Sources", ""])
        for src in job.sources:
            lines.append(f"- {src}")

    if content_blocks:
        lines.extend(["", "## Additional Notes", ""])
        lines.extend(content_blocks)

    lines.extend(["", "---", f"_Generated {date.today().isoformat()}_"])

    md_path.write_text("\n".join(lines), encoding="utf-8")

    # JSON dossier
    json_path.write_text(
        json.dumps(asdict(job), indent=2, default=str),
        encoding="utf-8",
    )

    log.info("Created dossier → %s", md_path.name)
    return md_path


def generate_daily_summary(day: date | None = None) -> Path:
    """Write data/summaries/research/YYYY-MM-DD.json with active jobs and progress."""
    day = day or date.today()
    all_jobs = load_jobs()
    active = get_active_jobs()

    data: dict[str, Any] = {
        "date": day.isoformat(),
        "agent": "research",
        "active_jobs": len(active),
        "total_jobs": len(all_jobs),
        "jobs_summary": [
            {
                "id": j.id,
                "title": j.title,
                "status": j.status,
                "priority": j.priority,
                "findings_count": len(j.findings),
            }
            for j in active[:10]
        ],
        "headline": _build_headline(active, all_jobs),
    }

    return write_summary("research", data, day)


def _build_headline(active: list[ResearchJob], all_jobs: list[ResearchJob]) -> str:
    completed_today = sum(
        1 for j in all_jobs
        if j.status == "completed" and j.updated_at.startswith(date.today().isoformat())
    )
    parts = [f"{len(active)} active research jobs"]
    if completed_today:
        parts.append(f"{completed_today} completed today")
    if active:
        top = active[0]
        parts.append(f"top priority: {top.title}")
    return " — ".join(parts)


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]
