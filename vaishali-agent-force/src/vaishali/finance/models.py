"""SQLAlchemy ORM models for the finance ledger."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    """Bank / credit card account metadata."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    bank: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="current"
    )  # current | savings | credit_card
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Transaction(Base):
    """Single financial transaction — the core ledger row."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core fields
    tx_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")

    # Classification
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)

    # Provenance
    source_file: Mapped[str | None] = mapped_column(String(512), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Deduplication hash: sha256(date + description + amount + account_id)
    dedup_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    __table_args__ = (
        Index("ix_tx_account_date", "account_id", "tx_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction {self.tx_date} {self.description[:30]} "
            f"{'£' if self.currency == 'GBP' else self.currency}{self.amount}>"
        )
