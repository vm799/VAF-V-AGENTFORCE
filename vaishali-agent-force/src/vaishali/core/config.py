"""Centralised configuration — all paths derived from a single base directory."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


def _default_base() -> Path:
    """Resolve project root: walk up from this file to find pyproject.toml."""
    current = Path(__file__).resolve().parent
    for ancestor in [current] + list(current.parents):
        if (ancestor / "pyproject.toml").exists():
            return ancestor
    return Path.cwd()


class Settings(BaseSettings):
    """Application-wide settings with sensible defaults.

    Override any value via environment variable prefixed with ``VAF_``.
    Example: ``VAF_BASE_DIR=/custom/path python -m vaishali status``
    """

    model_config = {"env_prefix": "VAF_"}

    # ── Root paths ──────────────────────────────────────────────────
    base_dir: Path = _default_base()

    # iCloud folder where bank statements land (configurable per machine)
    icloud_statements_dir: Path = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Finance/Statements"

    # ── Derived paths (computed properties) ─────────────────────────
    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def reports_dir(self) -> Path:
        return self.base_dir / "reports"

    @property
    def scripts_dir(self) -> Path:
        return self.base_dir / "scripts"

    # Finance
    @property
    def db_path(self) -> Path:
        return self.data_dir / "finance" / "ledger.db"

    @property
    def finance_raw_dir(self) -> Path:
        return self.data_dir / "finance" / "raw"

    @property
    def finance_archive_dir(self) -> Path:
        return self.data_dir / "finance" / "raw" / "archive"

    # Summaries
    @property
    def summaries_dir(self) -> Path:
        return self.data_dir / "summaries"

    @property
    def briefings_dir(self) -> Path:
        return self.data_dir / "briefings"

    # Content
    @property
    def content_backlog_path(self) -> Path:
        return self.data_dir / "content" / "backlog.json"

    # Education
    @property
    def education_sources_path(self) -> Path:
        return self.data_dir / "education" / "sources.yml"

    @property
    def education_index_path(self) -> Path:
        return self.data_dir / "education" / "index.json"

    # Health
    @property
    def health_raw_dir(self) -> Path:
        return self.data_dir / "health" / "raw"

    # Braindump
    @property
    def braindump_dir(self) -> Path:
        return self.data_dir / "braindump"

    # Obsidian vault (set VAF_OBSIDIAN_VAULT_DIR to your vault path)
    obsidian_vault_dir: Path | None = None

    # LLM configuration — keys read from environment (VAF_ANTHROPIC_KEY_1..5, VAF_ANTHROPIC_KEY, ANTHROPIC_API_KEY)
    # No need to set here; the llm_client reads from environment directly
    # But you can set these for explicit control:
    anthropic_key_1: str = ""
    anthropic_key_2: str = ""
    anthropic_key_3: str = ""

    @property
    def llm_usage_path(self) -> Path:
        return self.data_dir / "llm_usage.json"

    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        dirs = [
            self.data_dir,
            self.finance_raw_dir,
            self.finance_archive_dir,
            self.summaries_dir / "finance",
            self.summaries_dir / "content",
            self.summaries_dir / "education",
            self.summaries_dir / "research",
            self.summaries_dir / "health",
            self.summaries_dir / "braindump",
            self.briefings_dir,
            self.reports_dir / "finance" / "daily",
            self.reports_dir / "finance" / "weekly",
            self.reports_dir / "daily",
            self.data_dir / "content" / "sources",
            self.data_dir / "education" / "notes",
            # Insight store — one sub-dir per category
            self.data_dir / "education" / "notes" / "insights",
            self.data_dir / "education" / "notes" / "insights" / "finance",
            self.data_dir / "education" / "notes" / "insights" / "ai",
            self.data_dir / "education" / "notes" / "insights" / "tech",
            self.data_dir / "education" / "notes" / "insights" / "health",
            self.data_dir / "education" / "notes" / "insights" / "research",
            self.data_dir / "education" / "notes" / "insights" / "education",
            self.data_dir / "education" / "notes" / "insights" / "recipe",
            self.data_dir / "education" / "notes" / "insights" / "career",
            self.data_dir / "research" / "dossiers",
            self.health_raw_dir,
            self.braindump_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# Singleton used everywhere
settings = Settings()
