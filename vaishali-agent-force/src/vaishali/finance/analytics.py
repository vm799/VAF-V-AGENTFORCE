"""Finance analytics — balances, category summaries, recurring detection, anomalies."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from vaishali.core.logging_utils import get_logger
from vaishali.core.storage import get_session
from vaishali.finance.models import Transaction

log = get_logger(__name__)


# ── Data classes for typed results ──────────────────────────────────


@dataclass
class AccountBalance:
    account_id: str
    balance: Decimal
    tx_count: int


@dataclass
class CategorySummary:
    category: str
    total: Decimal
    count: int


@dataclass
class Anomaly:
    tx_id: int
    tx_date: date
    description: str
    amount: Decimal
    reason: str
    severity: str  # low | medium | high


# ── Analytics functions ─────────────────────────────────────────────


def balances_by_account() -> list[AccountBalance]:
    """Compute running balance per account (sum of all transactions)."""
    session = get_session()
    try:
        stmt = (
            select(
                Transaction.account_id,
                func.sum(Transaction.amount).label("balance"),
                func.count(Transaction.id).label("tx_count"),
            )
            .group_by(Transaction.account_id)
        )
        results = session.execute(stmt).all()
        return [
            AccountBalance(account_id=r.account_id, balance=Decimal(str(r.balance)), tx_count=r.tx_count)
            for r in results
        ]
    finally:
        session.close()


def net_change(days: int = 7) -> dict[str, Decimal]:
    """Net income/spend per account over the last N days."""
    cutoff = date.today() - timedelta(days=days)
    session = get_session()
    try:
        stmt = (
            select(
                Transaction.account_id,
                func.sum(Transaction.amount).label("net"),
            )
            .where(Transaction.tx_date >= cutoff)
            .group_by(Transaction.account_id)
        )
        results = session.execute(stmt).all()
        return {r.account_id: Decimal(str(r.net)) for r in results}
    finally:
        session.close()


def monthly_by_category(year: int, month: int) -> list[CategorySummary]:
    """Spending/income totals grouped by category for a given month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    session = get_session()
    try:
        stmt = (
            select(
                func.coalesce(Transaction.category, "Uncategorised").label("cat"),
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("cnt"),
            )
            .where(Transaction.tx_date >= start, Transaction.tx_date < end)
            .group_by("cat")
            .order_by(func.sum(Transaction.amount))
        )
        results = session.execute(stmt).all()
        return [
            CategorySummary(category=r.cat, total=Decimal(str(r.total)), count=r.cnt)
            for r in results
        ]
    finally:
        session.close()


def detect_recurring(min_occurrences: int = 3) -> list[dict]:
    """Find transactions with the same description appearing at least N times.

    Returns list of dicts: {description, count, avg_amount, last_date}.
    """
    session = get_session()
    try:
        stmt = (
            select(
                Transaction.description,
                func.count(Transaction.id).label("cnt"),
                func.avg(Transaction.amount).label("avg_amt"),
                func.max(Transaction.tx_date).label("last_date"),
            )
            .group_by(Transaction.description)
            .having(func.count(Transaction.id) >= min_occurrences)
            .order_by(func.count(Transaction.id).desc())
        )
        results = session.execute(stmt).all()
        return [
            {
                "description": r.description,
                "count": r.cnt,
                "avg_amount": round(float(r.avg_amt), 2),
                "last_date": str(r.last_date),
            }
            for r in results
        ]
    finally:
        session.close()


def detect_anomalies(
    amount_threshold: Decimal = Decimal("200"),
    lookback_days: int = 90,
) -> list[Anomaly]:
    """Flag unusual transactions using simple transparent rules.

    Rules:
    1. Any single transaction above the amount threshold.
    2. New merchants seen for the first time (if amount > £50).
    """
    cutoff = date.today() - timedelta(days=lookback_days)
    session = get_session()
    anomalies: list[Anomaly] = []

    try:
        # Rule 1: Large transactions in the lookback window
        stmt = (
            select(Transaction)
            .where(Transaction.tx_date >= cutoff)
            .where(func.abs(Transaction.amount) >= float(amount_threshold))
        )
        for tx in session.scalars(stmt):
            anomalies.append(
                Anomaly(
                    tx_id=tx.id,
                    tx_date=tx.tx_date,
                    description=tx.description,
                    amount=tx.amount,
                    reason=f"Large transaction (£{abs(tx.amount)})",
                    severity="medium" if abs(tx.amount) < amount_threshold * 2 else "high",
                )
            )

        # Rule 2: First-time merchants with amount > £50
        all_descriptions = session.execute(
            select(Transaction.description, func.min(Transaction.tx_date).label("first_seen"))
            .group_by(Transaction.description)
        ).all()

        new_merchants = {r.description for r in all_descriptions if r.first_seen >= cutoff}

        if new_merchants:
            stmt2 = (
                select(Transaction)
                .where(Transaction.description.in_(new_merchants))
                .where(func.abs(Transaction.amount) >= 50)
                .where(Transaction.tx_date >= cutoff)
            )
            for tx in session.scalars(stmt2):
                # Avoid duplicates with rule 1
                if not any(a.tx_id == tx.id for a in anomalies):
                    anomalies.append(
                        Anomaly(
                            tx_id=tx.id,
                            tx_date=tx.tx_date,
                            description=tx.description,
                            amount=tx.amount,
                            reason="New merchant (first time seen)",
                            severity="low",
                        )
                    )

    finally:
        session.close()

    return sorted(anomalies, key=lambda a: a.tx_date, reverse=True)


def daily_totals(days: int = 30) -> list[dict]:
    """Daily income/spend totals for the last N days."""
    cutoff = date.today() - timedelta(days=days)
    session = get_session()
    try:
        stmt = (
            select(
                Transaction.tx_date,
                func.sum(func.min(Transaction.amount, 0)).label("spend"),
                func.sum(func.max(Transaction.amount, 0)).label("income"),
            )
            .where(Transaction.tx_date >= cutoff)
            .group_by(Transaction.tx_date)
            .order_by(Transaction.tx_date)
        )
        # Fallback: just total per day since SQLite min/max in aggregate is awkward
        stmt_simple = (
            select(
                Transaction.tx_date,
                func.sum(Transaction.amount).label("net"),
                func.count(Transaction.id).label("count"),
            )
            .where(Transaction.tx_date >= cutoff)
            .group_by(Transaction.tx_date)
            .order_by(Transaction.tx_date)
        )
        results = session.execute(stmt_simple).all()
        return [
            {"date": str(r.tx_date), "net": float(r.net), "count": r.count}
            for r in results
        ]
    finally:
        session.close()
