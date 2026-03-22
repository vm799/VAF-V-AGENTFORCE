"""Bank statement parsers — each returns a list of normalised transaction dicts."""

from __future__ import annotations

from vaishali.finance.parsers.first_direct import FirstDirectParser
from vaishali.finance.parsers.generic_csv import GenericCsvParser

__all__ = ["GenericCsvParser", "FirstDirectParser"]
