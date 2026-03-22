"""Minimal CLI entry point for Vaishali Agent Force."""

from __future__ import annotations

import argparse
import sys

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="vaf",
        description="Vaishali Agent Force — local-first personal agent system",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show system status")
    sub.add_parser("init-db", help="Initialise / migrate the database")

    args = parser.parse_args(argv or sys.argv[1:])

    if args.command == "status":
        _status()
    elif args.command == "init-db":
        _init_db()
    else:
        parser.print_help()


def _status() -> None:
    log.info("Vaishali Agent Force v0.1.0")
    log.info("Base directory : %s", settings.base_dir)
    log.info("Data directory : %s", settings.data_dir)
    log.info("Database       : %s", settings.db_path)
    log.info("Status: OK")


def _init_db() -> None:
    from vaishali.core.storage import init_db

    init_db()
    log.info("Database initialised at %s", settings.db_path)
