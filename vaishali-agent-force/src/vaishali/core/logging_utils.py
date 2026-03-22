"""Structured logging setup using the standard library + Rich."""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def _configure_once() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    try:
        from rich.logging import RichHandler

        handler: logging.Handler = RichHandler(
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
    except ImportError:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
        )

    root = logging.getLogger("vaishali")
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``vaishali`` namespace."""
    _configure_once()
    return logging.getLogger(name)
