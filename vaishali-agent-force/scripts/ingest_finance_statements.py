#!/usr/bin/env python3
"""Ingest bank statements from a source directory into the finance ledger.

Usage:
    python scripts/ingest_finance_statements.py --input-dir ~/icloud/statements
    python scripts/ingest_finance_statements.py --bank first-direct --input-dir ./samples
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy.exc import IntegrityError

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.storage import get_session, init_db
from vaishali.finance.models import Transaction
from vaishali.finance.parsers.first_direct import FirstDirectParser
from vaishali.finance.parsers.generic_csv import GenericCsvParser

log = get_logger(__name__)

BANK_PARSERS = {
    "first-direct": FirstDirectParser,
    "generic": GenericCsvParser,
}


def ingest(
    input_dir: Path,
    archive_dir: Path | None = None,
    bank: str = "generic",
    account_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Ingest all CSV files from *input_dir* into the ledger.

    Returns a dict with keys: files_found, rows_parsed, rows_inserted, rows_skipped.
    """
    init_db()

    parser_cls = BANK_PARSERS.get(bank, GenericCsvParser)
    kwargs = {}
    if account_id:
        kwargs["account_id"] = account_id
    parser = parser_cls(**kwargs)

    csv_files = sorted(input_dir.glob("*.csv"))
    stats = {"files_found": len(csv_files), "rows_parsed": 0, "rows_inserted": 0, "rows_skipped": 0}

    if not csv_files:
        log.warning("No CSV files found in %s", input_dir)
        return stats

    session = get_session()
    try:
        for csv_path in csv_files:
            log.info("── Processing %s", csv_path.name)
            rows = parser.parse(csv_path)
            stats["rows_parsed"] += len(rows)

            for row_data in rows:
                if dry_run:
                    log.info("  [DRY RUN] Would insert: %s %s £%s", row_data["tx_date"], row_data["description"][:40], row_data["amount"])
                    stats["rows_inserted"] += 1
                    continue

                tx = Transaction(**row_data)
                try:
                    session.add(tx)
                    session.flush()
                    stats["rows_inserted"] += 1
                except IntegrityError:
                    session.rollback()
                    stats["rows_skipped"] += 1
                    log.debug("  Duplicate skipped: %s", row_data["description"][:40])

            # Archive the processed file
            if not dry_run and archive_dir:
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / csv_path.name
                if dest.exists():
                    dest = archive_dir / f"{csv_path.stem}_{csv_path.stat().st_mtime_ns}{csv_path.suffix}"
                shutil.move(str(csv_path), str(dest))
                log.info("  Archived → %s", dest.name)

        if not dry_run:
            session.commit()
    finally:
        session.close()

    log.info(
        "Ingestion complete: %d files, %d parsed, %d inserted, %d duplicates skipped",
        stats["files_found"],
        stats["rows_parsed"],
        stats["rows_inserted"],
        stats["rows_skipped"],
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest bank statements into the finance ledger")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=settings.icloud_statements_dir,
        help="Directory containing CSV statement files",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=settings.finance_archive_dir,
        help="Where to move processed files",
    )
    parser.add_argument(
        "--bank",
        choices=list(BANK_PARSERS.keys()),
        default="generic",
        help="Bank parser to use",
    )
    parser.add_argument("--account-id", help="Override account ID")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, don't write to DB")
    parser.add_argument("--no-archive", action="store_true", help="Don't move files after ingestion")

    args = parser.parse_args()
    archive = None if args.no_archive else args.archive_dir

    ingest(
        input_dir=args.input_dir,
        archive_dir=archive,
        bank=args.bank,
        account_id=args.account_id,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
