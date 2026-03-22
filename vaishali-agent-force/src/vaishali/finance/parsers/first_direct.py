"""Parser tuned for First Direct CSV exports.

First Direct typically exports with columns:
  Date, Description, Amount
Date format: DD/MM/YYYY
Amounts: negative for debits, positive for credits.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vaishali.finance.parsers.generic_csv import ColumnMapping, GenericCsvParser


@dataclass
class FirstDirectParser(GenericCsvParser):
    """Pre-configured parser for First Direct current account CSVs."""

    account_id: str = "first-direct-current"
    currency: str = "GBP"
    date_format: str = "%d/%m/%Y"
    mapping: ColumnMapping = field(
        default_factory=lambda: ColumnMapping(
            date="Date",
            description="Description",
            amount="Amount",
        )
    )
