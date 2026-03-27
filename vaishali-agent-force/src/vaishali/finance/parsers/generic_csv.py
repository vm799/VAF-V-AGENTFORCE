"""Configurable CSV parser that maps arbitrary column names to the Transaction schema."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from dateutil import parser as dateparser

from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class ColumnMapping:
    """Maps CSV column headers → internal field names."""

    date: str = "Date"
    description: str = "Description"
    amount: str = "Amount"
    credit: str | None = None  # If debit/credit are separate columns
    debit: str | None = None
    currency: str | None = None
    balance: str | None = None  # Informational — not stored but useful for reconciliation


@dataclass
class GenericCsvParser:
    """Parse any bank CSV using a configurable column mapping."""

    account_id: str
    mapping: ColumnMapping = field(default_factory=ColumnMapping)
    currency: str = "GBP"
    date_format: str | None = None  # e.g. "%d/%m/%Y" — None = auto-detect
    encoding: str = "utf-8-sig"  # BOM-safe default
    skip_rows: int = 0  # Header rows to skip before the CSV header

    def parse(self, path: Path) -> list[dict[str, Any]]:
        """Read a CSV file and return normalised transaction dicts."""
        log.info("Parsing %s (account=%s)", path.name, self.account_id)
        rows: list[dict[str, Any]] = []

        with open(path, newline="", encoding=self.encoding) as fh:
            # Skip leading non-CSV rows
            for _ in range(self.skip_rows):
                next(fh)

            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                try:
                    tx = self._normalise_row(row, path)
                    if tx is not None:
                        rows.append(tx)
                except Exception:
                    log.warning("Skipping row %d in %s — parse error", i + 1, path.name, exc_info=True)

        log.info("Parsed %d transactions from %s", len(rows), path.name)
        return rows

    def _normalise_row(self, row: dict[str, str], source: Path) -> dict[str, Any] | None:
        """Convert one CSV row into a normalised transaction dict."""
        raw_date = row.get(self.mapping.date, "").strip()
        raw_desc = row.get(self.mapping.description, "").strip()

        if not raw_date or not raw_desc:
            return None

        # Parse date
        tx_date = self._parse_date(raw_date)

        # Parse amount — handle single-column or split debit/credit
        amount = self._parse_amount(row)
        if amount is None:
            return None

        currency = (
            row.get(self.mapping.currency, "").strip().upper()
            if self.mapping.currency
            else self.currency
        ) or self.currency

        dedup = self._dedup_hash(tx_date, raw_desc, amount, self.account_id)

        return {
            "tx_date": tx_date,
            "description": raw_desc,
            "amount": amount,
            "currency": currency,
            "account_id": self.account_id,
            "source_file": str(source.name),
            "dedup_hash": dedup,
        }

    def _parse_date(self, raw: str) -> date:
        if self.date_format:
            from datetime import datetime

            return datetime.strptime(raw, self.date_format).date()
        return dateparser.parse(raw, dayfirst=True).date()  # UK convention

    def _parse_amount(self, row: dict[str, str]) -> Decimal | None:
        """Extract amount — supports single Amount column or split Debit/Credit."""
        if self.mapping.debit and self.mapping.credit:
            debit_raw = row.get(self.mapping.debit, "").strip()
            credit_raw = row.get(self.mapping.credit, "").strip()
            debit = self._clean_decimal(debit_raw)
            credit = self._clean_decimal(credit_raw)
            if debit is not None:
                return -abs(debit)
            if credit is not None:
                return abs(credit)
            return None

        raw = row.get(self.mapping.amount, "").strip()
        return self._clean_decimal(raw)

    @staticmethod
    def _clean_decimal(raw: str) -> Decimal | None:
        if not raw:
            return None
        cleaned = raw.replace(",", "").replace("£", "").replace("$", "").replace("€", "").strip()
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    @staticmethod
    def _dedup_hash(tx_date: date, description: str, amount: Decimal, account_id: str) -> str:
        payload = f"{tx_date.isoformat()}|{description}|{amount}|{account_id}"
        return hashlib.sha256(payload.encode()).hexdigest()
