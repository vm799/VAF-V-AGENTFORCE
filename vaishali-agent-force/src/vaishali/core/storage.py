"""SQLite connection management and migration bootstrap."""

from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _sqlite_pragmas(dbapi_conn, _connection_record) -> None:  # type: ignore[no-untyped-def]
    """Set pragmas on every new SQLite connection.

    WAL mode is preferred for performance but may fail on network/mounted
    filesystems. We fall back gracefully to DELETE journal mode.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass  # WAL not supported on this filesystem — use default DELETE mode
    cursor.close()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings.ensure_dirs()
        url = f"sqlite:///{settings.db_path}"
        _engine = create_engine(url, echo=False, pool_pre_ping=True)
        event.listen(_engine, "connect", _sqlite_pragmas)
        log.info("SQLite engine created → %s", settings.db_path)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_session() -> Session:
    """Convenience: return a new session (caller must close/commit)."""
    return get_session_factory()()


def init_db() -> None:
    """Create all tables defined by the ORM Base metadata."""
    from vaishali.finance.models import Base  # noqa: F811

    engine = get_engine()
    Base.metadata.create_all(engine)
    log.info("Database tables created / verified")

    # Record schema version for future migration tracking
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS _schema_version "
                "(version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')))"
            )
        )
        result = conn.execute(text("SELECT MAX(version) FROM _schema_version"))
        current = result.scalar()
        if current is None:
            conn.execute(text("INSERT INTO _schema_version (version) VALUES (1)"))
            log.info("Schema version set to 1")
        else:
            log.info("Schema version: %d", current)
