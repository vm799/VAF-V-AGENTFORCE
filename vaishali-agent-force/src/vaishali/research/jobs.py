"""Research job management — define, run, and track research tasks."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class ResearchJob:
    """Schema for a research task."""

    id: str = ""
    title: str = ""
    question: str = ""  # The core research question
    status: str = "pending"  # pending, in_progress, completed, archived
    priority: str = "medium"  # low, medium, high
    sources: list[str] = field(default_factory=list)  # URLs or file paths
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    dossier_path: str = ""  # Path to generated dossier markdown

    def __post_init__(self) -> None:
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()


def _jobs_file() -> Path:
    return settings.data_dir / "research" / "jobs.json"


def load_jobs() -> list[ResearchJob]:
    """Load all research jobs from disk."""
    path = _jobs_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ResearchJob(**j) for j in data]
    except (json.JSONDecodeError, TypeError) as e:
        log.warning("Failed to load research jobs: %s", e)
        return []


def save_jobs(jobs: list[ResearchJob]) -> None:
    """Persist all research jobs to disk."""
    path = _jobs_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(j) for j in jobs], indent=2, default=str),
        encoding="utf-8",
    )
    log.info("Saved %d research jobs", len(jobs))


def create_job(title: str, question: str, priority: str = "medium", tags: list[str] | None = None, sources: list[str] | None = None) -> ResearchJob:
    """Create a new research job and persist it."""
    job = ResearchJob(
        title=title,
        question=question,
        priority=priority,
        tags=tags or [],
        sources=sources or [],
    )
    jobs = load_jobs()
    jobs.append(job)
    save_jobs(jobs)
    log.info("Created research job: %s (%s)", job.title, job.id)
    return job


def update_job(job_id: str, **kwargs: Any) -> ResearchJob | None:
    """Update fields on an existing job."""
    jobs = load_jobs()
    for job in jobs:
        if job.id == job_id:
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            job.updated_at = datetime.utcnow().isoformat()
            save_jobs(jobs)
            return job
    log.warning("Research job %s not found", job_id)
    return None


def get_active_jobs() -> list[ResearchJob]:
    """Return jobs that are pending or in progress."""
    return [j for j in load_jobs() if j.status in ("pending", "in_progress")]
