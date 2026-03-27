"""Telegram intake handlers — routes incoming photos, links, and text to the right agent.

Flow:
  Phone → Telegram → Bot → intake.py → agent pipeline → dashboard

Handlers:
  1. FINANCE:   Photo of statement  → OCR → CSV → finance agent
  2. EDUCATION: YouTube/IG link     → transcript extract → education agent
  3. HEALTH:    /log command         → daily metrics → health agent
  4. CONTENT:   /idea command        → content backlog → content agent
  5. Generic:   Forward any link     → auto-classify → right agent
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


# ── URL pattern detection ──────────────────────────────────────────────

YT_PATTERN = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w\-]+"
)
IG_PATTERN = re.compile(
    r"(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[\w\-]+"
)
URL_PATTERN = re.compile(r"https?://\S+")


CONTENT_CATEGORIES = {
    # category → (vault_folder, obsidian_section, emoji, agent_label)
    "recipe":    ("Personal/Recipes",      "Recipes",        "🍳", "Personal"),
    "finance":   ("Finance/Research",      "Finance",        "💰", "Finance"),
    "tech":      ("Research/Technology",   "Technology",     "💻", "Research"),
    "ai":        ("Research/AI",           "AI & ML",        "🤖", "Research"),
    "health":    ("Health",                "Health",         "🏃", "Health"),
    "career":    ("Professional/Career",   "Career",         "🎯", "Professional"),
    "personal":  ("Personal",             "Personal",       "📝", "Personal"),
    "education": ("Education",             "Education",      "📚", "Education"),
    "research":  ("Research",              "Research",       "🔬", "Research"),
}

# Keywords that override the default → maps to CONTENT_CATEGORIES key
_CATEGORY_SIGNALS: list[tuple[str, list[str]]] = [
    ("recipe",  ["recipe", "ingredient", "cook", "bake", "meal", "dish", "food",
                 "allrecipes", "bbcgoodfood", "delish", "tasty", "seriouseats",
                 "nytimes.com/recipes", "epicurious", "bonappetit"]),
    ("finance", ["bloomberg", "ft.com", "reuters.com/finance", "wsj.com",
                 "investopedia", "morningstar", "marketwatch", "seeking-alpha",
                 "stock", "etf", "fund", "portfolio", "invest", "market", "trading",
                 "hedge fund", "asset management", "private equity", "fintech"]),
    ("ai",      ["openai", "anthropic", "huggingface", "arxiv", "deepmind",
                 "llm", "gpt", "claude", "gemini", "machine learning", "neural",
                 "transformer", "diffusion", "ai agent", "langchain", "rag"]),
    ("tech",    ["github.com", "stackoverflow", "hackernews", "ycombinator",
                 "techcrunch", "wired.com", "python", "javascript", "kubernetes",
                 "docker", "api", "tutorial", "developer", "programming", "software"]),
    ("health",  ["health", "fitness", "workout", "nutrition", "sleep", "mental health",
                 "meditation", "running", "yoga", "diet", "wellbeing", "nhs.uk",
                 "mayoclinic", "pubmed", "exercise"]),
    ("career",  ["linkedin.com/pulse", "career", "interview", "promotion", "salary",
                 "leadership", "management", "team", "workplace", "productivity",
                 "harvard business", "mckinsey", "deloitte insights"]),
]


def classify_link(text: str) -> str:
    """Classify a URL into a content category for routing.

    Returns one of: recipe, finance, ai, tech, health, career, education, personal, research
    """
    lower = text.lower()

    # Check domain/keyword signals in priority order
    for category, signals in _CATEGORY_SIGNALS:
        if any(s in lower for s in signals):
            return category

    # YouTube/IG always education
    if YT_PATTERN.search(text) or IG_PATTERN.search(text):
        return "education"

    # Default to research (most links dropped are for learning/reference)
    return "research"


# ── Finance: Bank name detection ──────────────────────────────────────

# Ordered so the most specific / distinctive strings come first
_BANK_SIGNATURES: list[tuple[str, str]] = [
    ("first direct",       "First Direct"),
    ("firstdirect",        "First Direct"),
    ("american express",   "Amex"),
    ("amex",               "Amex"),
    ("santander",          "Santander"),
    ("barclays",           "Barclays"),
    ("barclaycard",        "Barclays"),
    ("natwest",            "NatWest"),
    ("national westminster","NatWest"),
    ("hsbc",               "HSBC"),
    ("halifax",            "Halifax"),
    ("lloyds",             "Lloyds"),
    ("monzo",              "Monzo"),
    ("starling",           "Starling"),
    ("virgin money",       "Virgin Money"),
    ("metro bank",         "Metro Bank"),
]


def detect_bank_from_ocr(text: str) -> str:
    """Identify the issuing bank from raw OCR text.

    Checks for distinctive bank names / headers in the statement text.
    Returns a human-readable bank name, or 'Unknown Bank' if not found.
    """
    lower = text.lower()
    for signature, name in _BANK_SIGNATURES:
        if signature in lower:
            return name
    return "Unknown Bank"


# ── Finance: OCR from photo ────────────────────────────────────────────

async def process_statement_photo(photo_path: Path, account_id: str = "statement") -> dict[str, Any]:
    """Extract transactions from a photographed bank statement.

    Pipeline:
      1. OCR via macOS Vision (built-in, best quality) or tesseract fallback
      2. Parse transactions via Gemini AI (handles any bank format) → regex fallback
      3. Save as CSV → return for ledger import
    """
    log.info("Processing statement photo: %s", photo_path)

    # ── Step 1: OCR ────────────────────────────────────────────────────────
    ocr_text = await _ocr_macos_vision(photo_path)
    if not ocr_text:
        ocr_text = await _ocr_tesseract(photo_path)

    if not ocr_text:
        return {"status": "error", "message": "Could not extract text from image. Try a clearer photo."}

    bank = detect_bank_from_ocr(ocr_text)

    # ── Step 2: Parse transactions — Gemini first, regex fallback ──────────
    transactions = await _parse_transactions_with_gemini(ocr_text, account_id or bank)
    if not transactions:
        transactions = _parse_ocr_to_transactions(ocr_text, account_id or bank)

    if not transactions:
        return {
            "status": "partial",
            "message": "Text extracted but no transactions detected.",
            "bank": bank,
            "raw_text": ocr_text[:500],
        }

    # ── Step 3: Save CSV ───────────────────────────────────────────────────
    csv_path = _save_transactions_csv(transactions, photo_path.stem, bank)

    return {
        "status": "success",
        "bank": bank,
        "transactions": len(transactions),
        "csv_path": str(csv_path),
        "sample": transactions[:5],
    }


async def _parse_transactions_with_gemini(ocr_text: str, account_id: str) -> list[dict[str, Any]]:
    """Use Gemini to parse raw OCR text into structured transaction rows.

    Works with any bank statement format — Gemini is far more robust than regex.
    Returns list of {tx_date, description, amount, type, account_id} dicts.
    Falls back gracefully (returns []) if Gemini is unavailable.
    """
    try:
        from vaishali.core.gemini_client import gemini
        if not gemini.has_key():
            return []

        prompt = f"""You are a financial data extraction expert.
Extract ALL transactions from this bank statement OCR text.

Return ONLY a JSON array of objects with these exact keys:
  tx_date     (YYYY-MM-DD string)
  description (merchant/payee name, cleaned up)
  amount      (decimal number — NEGATIVE for debits/spending, POSITIVE for credits/income)
  type        ("debit" or "credit")

Rules:
- Include every transaction row you can find
- If the year is missing from a date, assume {date.today().year}
- Remove currency symbols from amounts (£, $, €)
- Remove commas from amounts (e.g. 1,234.56 → 1234.56)
- DR/OUT/debit = negative amount, CR/IN/credit = positive amount
- If you see a balance column, ignore it — only extract transaction amounts
- Skip header rows, totals rows, and account summary rows
- Return [] if no transactions found

OCR TEXT:
{ocr_text[:3000]}

JSON array only, no markdown:"""

        raw = await gemini.complete_async(prompt=prompt, system="Return valid JSON only.", max_tokens=2000, temperature=0.1)

        # Strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        import json as _json
        rows = _json.loads(raw)

        if not isinstance(rows, list):
            return []

        # Normalise and validate each row
        from decimal import Decimal as _Dec
        result = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            try:
                tx_date_raw = str(r.get("tx_date", "")).strip()
                desc = str(r.get("description", "")).strip()
                amt_raw = str(r.get("amount", "0")).replace(",", "").replace("£", "").replace("$", "").replace("€", "").strip()
                amount = _Dec(amt_raw)
                tx_type = "credit" if amount >= 0 else "debit"
                # Validate date
                from dateutil import parser as _dp
                tx_date = _dp.parse(tx_date_raw, dayfirst=True).date().isoformat()
                result.append({
                    "tx_date": tx_date,
                    "description": desc[:120],
                    "amount": str(amount),
                    "type": tx_type,
                    "account_id": account_id,
                })
            except Exception:
                continue

        log.info("Gemini parsed %d transactions from OCR", len(result))
        return result

    except Exception as e:
        log.warning("Gemini transaction parsing failed: %s", e)
        return []


async def _ocr_macos_vision(photo_path: Path) -> str | None:
    """Use macOS Vision framework via a compiled Swift script.

    This is far more reliable than the AppleScript bridge approach.
    The script is compiled once and cached as a binary for speed.
    Falls back to running the .swift source if compilation fails.
    """
    swift_src = settings.scripts_dir / "ocr_vision.swift"
    swift_bin = settings.base_dir / ".cache" / "ocr_vision"

    if not swift_src.exists():
        log.warning("ocr_vision.swift not found at %s", swift_src)
        return None

    # Compile once — cache the binary for instant subsequent runs
    if not swift_bin.exists() or swift_bin.stat().st_mtime < swift_src.stat().st_mtime:
        swift_bin.parent.mkdir(parents=True, exist_ok=True)
        try:
            compile_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["swiftc", "-O", str(swift_src), "-o", str(swift_bin),
                     "-framework", "Vision", "-framework", "AppKit"],
                    capture_output=True, text=True, timeout=60,
                ),
            )
            if compile_result.returncode != 0:
                log.warning("Swift compile failed: %s", compile_result.stderr[:300])
                # Fall back to interpreted mode
                swift_bin = None
        except Exception as e:
            log.warning("Swift compilation error: %s", e)
            swift_bin = None

    # Run OCR — either compiled binary or interpreted
    cmd = [str(swift_bin), str(photo_path)] if swift_bin else ["swift", str(swift_src), str(photo_path)]

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            ),
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            log.info("Vision OCR extracted %d chars", len(text))
            return text
        elif result.stderr.strip():
            log.warning("Vision OCR stderr: %s", result.stderr[:300])
    except Exception as e:
        log.warning("macOS Vision OCR failed: %s", e)

    return None


async def _ocr_tesseract(photo_path: Path) -> str | None:
    """Fallback OCR using tesseract if installed."""
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["tesseract", str(photo_path), "stdout"],
                capture_output=True, text=True, timeout=30,
            ),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        log.info("tesseract not installed — skipping fallback OCR")
    return None


def _parse_ocr_to_transactions(text: str, account_id: str) -> list[dict[str, Any]]:
    """Parse raw OCR text into structured transactions.

    Handles UK bank statement formats (no LLM needed):
      Standard:    01/03/2026  TESCO STORES        -£45.67
      Month-name:  01 Mar 2026 Direct Debit - Sky   £32.00
      DR/CR:       01 MAR  TESCO STORES  45.67 DR
      ISO date:    2026-03-01  Payroll    +£3,450.00
      4-col:       01/03  BARCLAYS DEBIT  45.67        1,234.00   (debit, balance)
      4-col:       01/03  SALARY                   3,450.00  4,684.00  (credit, balance)
    """
    from dateutil import parser as _dp

    THIS_YEAR = date.today().year

    # ── Normalise common OCR artefacts ────────────────────────────────────
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Non-breaking spaces → regular space
    text = text.replace("\u00a0", " ").replace("\u2009", " ")
    # Curly quotes / dashes
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # ── Date patterns (compiled once) ────────────────────────────────────
    DATE_PAT = re.compile(
        r"""
        (?:
          \d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}  # 01/03/2026  or  01-03-26
          | \d{4}[\/\-]\d{2}[\/\-]\d{2}            # 2026-03-01
          | \d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{0,4}  # 01 Mar 2026
          | \d{1,2}[\/\-]\d{1,2}                   # 01/03  (no year)
        )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # ── Amount pattern (with optional currency symbol, commas, sign) ──────
    AMT_PAT = re.compile(
        r"[£$€]?\s*([+\-]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+\.\d{2})"
    )
    SKIP_HEADERS = {
        "date", "description", "details", "balance", "debit", "credit",
        "money in", "money out", "statement", "account", "sort code",
        "page", "opening", "closing", "brought forward", "carried forward",
        "transaction", "payments", "receipts",
    }

    def _clean_amount(s: str) -> Decimal | None:
        s = re.sub(r"[£$€\s,]", "", s).replace(" ", "")
        try:
            return Decimal(s)
        except Exception:
            return None

    def _parse_date(s: str) -> date | None:
        s = s.strip()
        # Append current year if no year present (e.g. "01/03" or "01 Mar")
        if re.fullmatch(r"\d{1,2}[\/\-]\d{1,2}", s):
            s = f"{s}/{THIS_YEAR}"
        elif re.fullmatch(r"\d{1,2}\s+[A-Za-z]+", s):
            s = f"{s} {THIS_YEAR}"
        try:
            return _dp.parse(s, dayfirst=True).date()
        except Exception:
            return None

    transactions: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line or len(line) < 5:
            continue
        # Skip header rows
        ll = line.lower()
        if any(h in ll for h in SKIP_HEADERS) and not re.search(r"\d{2,}", line):
            continue

        # Find date anywhere in line
        dm = DATE_PAT.search(line)
        if not dm:
            continue
        raw_date = dm.group(0)
        tx_date = _parse_date(raw_date)
        if not tx_date:
            continue

        # Everything after the date is description + amounts
        rest = line[dm.end():].strip()
        if not rest:
            continue

        # Find all amounts in rest
        amounts = AMT_PAT.findall(rest)
        if not amounts:
            continue

        # Description = rest with amount tokens removed
        desc = AMT_PAT.sub("", rest)
        # Remove DR/CR suffixes captured after amounts
        desc = re.sub(r"\b(DR|CR|D|C)\b", "", desc, flags=re.IGNORECASE)
        # Remove currency symbols and punctuation leftovers
        desc = re.sub(r"[£$€]", "", desc)
        desc = re.sub(r"\s{2,}", " ", desc).strip(" |-/,.")
        if not desc or len(desc) < 2:
            continue

        # Determine debit/credit from suffix or column position
        dr_cr_match = re.search(r"\b(DR|CR)\b", rest, re.IGNORECASE)

        # ── 4-column format: debit | credit | balance  ─────────────────
        # If 2+ amounts: first non-zero amount is debit or credit; last is balance
        amount: Decimal | None = None
        if len(amounts) >= 2:
            # Last amount is usually balance — ignore it
            # Use the first non-zero amount; sign determined by column
            # If we have exactly 2: first=debit or credit, second=balance
            # If we have 3: debit, credit, balance
            if len(amounts) == 3:
                debit_raw = _clean_amount(amounts[0])
                credit_raw = _clean_amount(amounts[1])
                if credit_raw and credit_raw != Decimal("0"):
                    amount = abs(credit_raw)   # credit = positive
                elif debit_raw and debit_raw != Decimal("0"):
                    amount = -abs(debit_raw)   # debit = negative
            else:
                # 2 amounts: heuristic — check which column the first amount occupies
                first = _clean_amount(amounts[0])
                if first is not None:
                    # Use DR/CR hint if present
                    if dr_cr_match:
                        suffix = dr_cr_match.group(1).upper()
                        amount = -abs(first) if suffix == "DR" else abs(first)
                    else:
                        amount = first  # keep sign as-is
        elif len(amounts) == 1:
            first = _clean_amount(amounts[0])
            if first is None:
                continue
            if dr_cr_match:
                suffix = dr_cr_match.group(1).upper()
                amount = -abs(first) if suffix == "DR" else abs(first)
            else:
                amount = first

        if amount is None:
            continue

        tx_type = "credit" if amount >= 0 else "debit"
        dedup_key = f"{tx_date}|{desc[:30]}|{amount}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        transactions.append({
            "tx_date": tx_date.isoformat(),
            "description": desc[:120],
            "amount": str(amount),
            "type": tx_type,
            "account_id": account_id,
        })

    return transactions


def _save_transactions_csv(transactions: list[dict[str, Any]], stem: str, bank: str = "") -> Path:
    """Save parsed transactions as a CSV in the finance raw directory.

    Columns: Date, Description, Amount, Type, Bank
    Type is 'debit' or 'credit'. Bank is the auto-detected issuer.
    """
    import csv

    settings.ensure_dirs()
    safe_bank = bank.lower().replace(" ", "_") if bank else "ocr"
    csv_path = settings.finance_raw_dir / f"{safe_bank}_{stem}_{date.today().isoformat()}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Description", "Amount", "Type", "Bank"])
        writer.writeheader()
        for tx in transactions:
            writer.writerow({
                "Date": tx["tx_date"],
                "Description": tx["description"],
                "Amount": tx["amount"],
                "Type": tx.get("type", "debit" if float(tx["amount"]) < 0 else "credit"),
                "Bank": bank,
            })

    log.info("Saved %d transactions (%s) to %s", len(transactions), bank, csv_path)
    return csv_path


# ── Finance: Quick manual spend/income ─────────────────────────────────

def parse_spend(text: str) -> dict[str, Any] | None:
    """Parse a quick spend/income entry from natural text.

    Expected formats:
        /spend 45.50 Tesco groceries
        /spend -15.99 Netflix
        /spend +3450 Salary
        /spend 8.50 Costa coffee
        /spend 875 rent
    """
    text = text.strip()
    if not text:
        return None

    # Try to extract amount and description
    m = re.match(r"([+-]?\d[\d,]*\.?\d*)\s+(.+)", text)
    if not m:
        # Try reversed: description then amount
        m = re.match(r"(.+?)\s+([+-]?\d[\d,]*\.?\d*)$", text)
        if m:
            desc, raw_amount = m.group(1).strip(), m.group(2)
        else:
            return None
    else:
        raw_amount, desc = m.group(1), m.group(2).strip()

    try:
        amount = float(raw_amount.replace(",", ""))
    except ValueError:
        return None

    # Negative by default (spending) unless explicitly positive
    if not raw_amount.startswith("+") and amount > 0:
        amount = -amount

    return {
        "date": date.today().isoformat(),
        "description": desc,
        "amount": amount,
    }


def save_spend(entry: dict[str, Any], account_id: str = "manual") -> Path:
    """Append a manual transaction to the daily spending log CSV."""
    import csv

    settings.ensure_dirs()
    today = date.today()
    csv_path = settings.finance_raw_dir / f"manual_{today.isoformat()}.csv"

    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Description", "Amount"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Date": entry["date"],
            "Description": entry["description"],
            "Amount": f"{entry['amount']:.2f}",
        })

    log.info("Saved spend: £%.2f %s", entry["amount"], entry["description"])
    return csv_path


def process_csv_file(file_path: Path, bank: str = "generic", account_id: str | None = None) -> dict[str, Any]:
    """Process a CSV file uploaded via Telegram through the standard finance ingestion pipeline.

    Returns a dict with status, rows_parsed, rows_inserted.
    """
    from vaishali.core.storage import init_db, get_session
    from vaishali.finance.models import Transaction
    from vaishali.finance.parsers.first_direct import FirstDirectParser
    from vaishali.finance.parsers.generic_csv import GenericCsvParser

    init_db()

    # Auto-detect bank from file content
    if bank == "auto":
        bank = _detect_bank_format(file_path)

    parsers = {
        "first-direct": FirstDirectParser,
        "generic": GenericCsvParser,
    }

    parser_cls = parsers.get(bank, GenericCsvParser)
    kwargs = {}
    if account_id:
        kwargs["account_id"] = account_id
    else:
        kwargs["account_id"] = bank if bank != "generic" else "uploaded"

    parser = parser_cls(**kwargs)

    try:
        rows = parser.parse(file_path)
    except Exception as e:
        log.warning("CSV parse failed: %s", e)
        return {"status": "error", "message": f"Could not parse CSV: {e}", "rows_parsed": 0, "rows_inserted": 0}

    if not rows:
        return {"status": "error", "message": "No transactions found in CSV", "rows_parsed": 0, "rows_inserted": 0}

    # Insert into DB
    from sqlalchemy.exc import IntegrityError

    session = get_session()
    inserted = 0
    skipped = 0

    try:
        for row_data in rows:
            tx = Transaction(**row_data)
            try:
                session.add(tx)
                session.flush()
                inserted += 1
            except IntegrityError:
                session.rollback()
                skipped += 1
        session.commit()
    finally:
        session.close()

    return {
        "status": "success",
        "rows_parsed": len(rows),
        "rows_inserted": inserted,
        "rows_skipped": skipped,
        "bank": bank,
    }


def _detect_bank_format(file_path: Path) -> str:
    """Try to auto-detect which bank a CSV came from by reading the header row."""
    try:
        with open(file_path, encoding="utf-8-sig") as f:
            header = f.readline().lower()

        # First Direct: "Date,Description,Amount"
        if "date" in header and "description" in header and "amount" in header:
            return "first-direct"
        # Monzo: "Date,Time,Description,Amount,Currency"
        if "time" in header and "currency" in header:
            return "generic"
        # HSBC: different format
        return "generic"
    except Exception:
        return "generic"


# ── Education: Extract info from video/article links ───────────────────

async def process_education_link(url: str, note: str = "") -> dict[str, Any]:
    """Extract educational content from a YouTube/IG/article link.

    For YouTube: extracts transcript via yt-dlp subtitle download.
    For articles: extracts text via httpx.
    Saves as raw education item for the summariser.
    """
    log.info("Processing education link: %s", url)

    content = ""
    title = url  # fallback

    if YT_PATTERN.search(url):
        result = await _extract_youtube(url)
        title = result.get("title", url)
        content = result.get("transcript", "")
    elif IG_PATTERN.search(url):
        title = "Instagram content"
        content = note or "Instagram video — manual notes needed"
    else:
        result = await _extract_article(url)
        title = result.get("title", url)
        content = result.get("text", "")

    if not content and note:
        content = note

    # Save as raw education item
    item = {
        "id": f"tg_{date.today().isoformat()}_{hash(url) % 10000:04d}",
        "title": title,
        "url": url,
        "content": content[:5000],  # cap at 5k chars
        "source": "telegram",
        "user_note": note,
        "date": datetime.now().isoformat(),
    }

    _save_education_item(item)

    return {
        "status": "success" if content else "partial",
        "title": title,
        "url": url,
        "content": content,            # full content for insight extraction
        "content_length": len(content),
        "message": f"Saved: {title[:60]}" if content else "Link saved — add notes for richer processing",
    }


async def _extract_youtube(url: str) -> dict[str, Any]:
    """Extract YouTube video title and transcript using yt-dlp."""
    result: dict[str, Any] = {"title": "", "transcript": ""}

    try:
        # Get title
        proc = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["yt-dlp", "--get-title", "--no-download", url],
                capture_output=True, text=True, timeout=30,
            ),
        )
        if proc.returncode == 0:
            result["title"] = proc.stdout.strip()

        # Get auto-generated subtitles
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            proc = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "yt-dlp",
                        "--write-auto-sub",
                        "--sub-lang", "en",
                        "--skip-download",
                        "--sub-format", "vtt",
                        "-o", f"{tmpdir}/%(id)s.%(ext)s",
                        url,
                    ],
                    capture_output=True, text=True, timeout=60,
                ),
            )

            # Find and read the subtitle file
            vtt_files = list(Path(tmpdir).glob("*.vtt"))
            if vtt_files:
                raw = vtt_files[0].read_text(encoding="utf-8", errors="replace")
                # Strip VTT headers and timestamps, keep just text
                lines = []
                for line in raw.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("WEBVTT") or "-->" in line or line.isdigit():
                        continue
                    if line.startswith("<"):  # strip HTML tags
                        line = re.sub(r"<[^>]+>", "", line)
                    if line and line not in lines[-1:]:  # dedup consecutive
                        lines.append(line)
                result["transcript"] = " ".join(lines)

    except FileNotFoundError:
        log.warning("yt-dlp not installed — cannot extract YouTube transcripts")
        log.warning("Install with: brew install yt-dlp")
    except Exception as e:
        log.warning("YouTube extraction failed: %s", e)

    return result


async def _extract_article(url: str) -> dict[str, Any]:
    """Extract article text using httpx."""
    try:
        import httpx

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            html_text = resp.text

        # Simple title extraction
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html_text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else url

        # Strip HTML tags for basic text extraction
        text = re.sub(r"<script[^>]*>.*?</script>", "", html_text, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return {"title": title, "text": text[:5000]}

    except Exception as e:
        log.warning("Article extraction failed for %s: %s", url, e)
        return {"title": url, "text": ""}


def _save_education_item(item: dict[str, Any]) -> None:
    """Append an education item to today's raw items file."""
    settings.ensure_dirs()
    today = date.today()
    raw_path = settings.data_dir / "education" / "notes" / f"{today.isoformat()}_raw.json"

    existing: list[dict[str, Any]] = []
    if raw_path.exists():
        try:
            existing = json.loads(raw_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    existing.append(item)
    raw_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Saved education item: %s (total: %d today)", item["title"][:40], len(existing))


# ── Health: Parse daily log from text ──────────────────────────────────

def parse_health_log(text: str) -> dict[str, Any]:
    """Parse a quick health log message into daily metrics.

    Expected format (flexible):
      steps:8000 sleep:7.5 workout:30 mood:4 energy:4 water:yes meditate:yes

    Or natural:
      8000 steps, slept 7.5h, 30 min workout, mood 4, energy 4
    """
    metrics: dict[str, Any] = {
        "date": date.today().isoformat(),
        "steps": 0,
        "sleep_hours": 0.0,
        "workout_minutes": 0,
        "mood": 3,
        "energy": 3,
        "resting_hr": None,
        "habits_completed": 0,
        "habits_total": 4,
    }

    text_lower = text.lower()

    # Steps
    m = re.search(r"(\d[\d,]*)\s*steps?", text_lower)
    if m:
        metrics["steps"] = int(m.group(1).replace(",", ""))

    # Sleep
    m = re.search(r"(?:sleep|slept)[:\s]*(\d+\.?\d*)\s*h?", text_lower)
    if not m:
        m = re.search(r"(\d+\.?\d*)\s*h(?:ours?)?\s*sleep", text_lower)
    if m:
        metrics["sleep_hours"] = float(m.group(1))

    # Workout
    m = re.search(r"(?:workout|gym|exercise)[:\s]*(\d+)\s*(?:min)?", text_lower)
    if not m:
        m = re.search(r"(\d+)\s*min\w*\s*(?:workout|gym|exercise)", text_lower)
    if m:
        metrics["workout_minutes"] = int(m.group(1))

    # Mood (1-5)
    m = re.search(r"mood[:\s]*(\d)", text_lower)
    if m:
        metrics["mood"] = min(5, max(1, int(m.group(1))))

    # Energy (1-5)
    m = re.search(r"energy[:\s]*(\d)", text_lower)
    if m:
        metrics["energy"] = min(5, max(1, int(m.group(1))))

    # Habits count
    habits = 0
    for habit in ["water", "meditat", "read", "journal", "vitamin", "stretch"]:
        if habit in text_lower:
            habits += 1
    if habits > 0:
        metrics["habits_completed"] = habits

    return metrics


def save_health_log(metrics: dict[str, Any]) -> Path:
    """Save health metrics to daily CSV for the health agent."""
    import csv

    settings.ensure_dirs()
    today = date.today()
    csv_path = settings.health_raw_dir / f"daily_{today.isoformat()}.csv"

    fieldnames = [
        "date", "steps", "sleep_hours", "workout_minutes",
        "mood", "energy", "resting_hr", "habits_completed", "habits_total",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(metrics)

    log.info("Saved health log to %s", csv_path)
    return csv_path


# ── Content: Add idea from text ────────────────────────────────────────

def add_content_idea(text: str) -> dict[str, Any]:
    """Parse a content idea and add it to the backlog.

    Expected: just describe the idea naturally.
    E.g.: "Video about building personal AI agents with Python — YouTube tutorial"
    """
    from vaishali.content.backlog import add_item

    # Try to detect content type
    text_lower = text.lower()
    content_type = "article"  # default
    if any(w in text_lower for w in ["video", "youtube", "yt", "reel", "short"]):
        content_type = "video"
    elif any(w in text_lower for w in ["thread", "tweet", "post"]):
        content_type = "thread"
    elif any(w in text_lower for w in ["newsletter", "email"]):
        content_type = "newsletter"

    # Detect target channel
    channel = "blog"
    if any(w in text_lower for w in ["youtube", "yt"]):
        channel = "youtube"
    elif any(w in text_lower for w in ["linkedin", "li"]):
        channel = "linkedin"
    elif any(w in text_lower for w in ["instagram", "ig", "reel"]):
        channel = "instagram"
    elif any(w in text_lower for w in ["twitter", "x.com", "tweet"]):
        channel = "twitter"

    from vaishali.content.backlog import ContentItem

    item = add_item(ContentItem(
        title=text[:100],
        type=content_type if content_type in ("linkedin", "long_form", "app_idea", "video_script", "childrens_book", "other") else "other",
        target_channel=channel,
        effort_estimate="M",
        impact_estimate=7,
        notes=text,
    ))

    return {
        "status": "success",
        "id": item.id,
        "title": item.title[:60],
        "type": content_type,
        "channel": channel,
    }
