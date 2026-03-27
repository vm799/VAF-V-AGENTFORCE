#!/usr/bin/env python3
"""Generate realistic sample CSV data for development and testing."""

from __future__ import annotations

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vaishali.core.config import settings

# Realistic UK transaction descriptions and amounts
RECURRING = [
    ("NETFLIX.COM", -15.99),
    ("SPOTIFY AB", -10.99),
    ("VIRGIN MEDIA", -45.00),
    ("COUNCIL TAX DD", -165.00),
    ("EE MOBILE", -35.00),
    ("SALARY CREDIT", 3450.00),
    ("TESCO BANK MORTGAGE", -875.00),
]

VARIABLE_SPEND = [
    ("TESCO STORES", -25, -85),
    ("SAINSBURYS", -15, -70),
    ("AMAZON.CO.UK", -8, -120),
    ("TFL.GOV.UK CONTACTLESS", -3, -12),
    ("COSTA COFFEE", -3, -7),
    ("UBER *TRIP", -8, -25),
    ("DELIVEROO", -12, -35),
    ("BOOTS", -5, -30),
    ("WATERSTONES", -8, -20),
    ("JOHN LEWIS", -20, -150),
    ("SHELL FUEL", -40, -75),
    ("NANDOS", -15, -35),
    ("THE GYM GROUP DD", -24.99, -24.99),
]


def generate_sample_csv(output_dir: Path, months: int = 3) -> Path:
    """Generate a First Direct-style CSV with realistic UK transactions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / "first_direct_sample.csv"

    today = date.today()
    start = today - timedelta(days=months * 30)
    transactions = []

    current = start
    while current <= today:
        # Recurring: add on roughly the same day each month
        if current.day == 1:
            for desc, amount in RECURRING:
                # Slight day variation
                tx_date = current + timedelta(days=random.randint(0, 5))
                if tx_date <= today:
                    transactions.append((tx_date, desc, amount))

        # Variable spend: 1-4 transactions per day
        n_daily = random.choices([0, 1, 2, 3, 4], weights=[10, 30, 30, 20, 10])[0]
        for _ in range(n_daily):
            desc, low, high = random.choice(VARIABLE_SPEND)
            amount = round(random.uniform(low, high), 2)
            transactions.append((current, desc, amount))

        current += timedelta(days=1)

    # Sort by date
    transactions.sort(key=lambda t: t[0])

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Amount"])
        for tx_date, desc, amount in transactions:
            writer.writerow([tx_date.strftime("%d/%m/%Y"), desc, f"{amount:.2f}"])

    print(f"Generated {len(transactions)} transactions → {filename}")
    return filename


def generate_health_data(days: int = 7) -> None:
    """Generate sample health CSVs for the last N days."""
    health_dir = settings.health_raw_dir
    health_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    for i in range(days):
        day = today - timedelta(days=i)
        path = health_dir / f"daily_{day.isoformat()}.csv"
        if path.exists():
            continue

        steps = random.randint(3000, 12000)
        workout = random.choice([0, 0, 15, 20, 30, 45, 60])
        sleep = round(random.uniform(5.5, 9.0), 1)
        resting_hr = random.randint(55, 75)
        mood = random.randint(2, 5)
        energy = random.randint(2, 5)
        habits_done = random.randint(1, 4)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "steps", "workout_minutes", "sleep_hours", "resting_hr", "mood", "energy", "habits_completed", "habits_total"])
            writer.writerow([day.isoformat(), steps, workout, sleep, resting_hr, mood, energy, habits_done, 4])

    print(f"Generated {days} days of health data → {health_dir}")


def generate_content_backlog() -> None:
    """Generate a sample content backlog."""
    import json

    backlog_path = settings.content_backlog_path
    backlog_path.parent.mkdir(parents=True, exist_ok=True)

    if backlog_path.exists():
        print(f"Content backlog already exists — skipping")
        return

    ideas = [
        {"id": "a1b2c3d4", "title": "How I built a personal AI agent system on my Mac", "type": "linkedin", "target_channel": "LinkedIn", "status": "idea", "effort_estimate": "M", "impact_estimate": 8, "source_ids": [], "tags": ["ai", "python", "productivity"], "notes": "", "created_at": "2026-03-20T10:00:00", "updated_at": "2026-03-20T10:00:00"},
        {"id": "e5f6g7h8", "title": "5 Python libraries every finance professional should know", "type": "long_form", "target_channel": "Blog / Medium", "status": "drafting", "effort_estimate": "L", "impact_estimate": 7, "source_ids": [], "tags": ["python", "finance", "career"], "notes": "", "created_at": "2026-03-19T10:00:00", "updated_at": "2026-03-20T14:00:00"},
        {"id": "i9j0k1l2", "title": "Quick tip: Automating bank statement parsing with Python", "type": "linkedin", "target_channel": "LinkedIn", "status": "needs_review", "effort_estimate": "S", "impact_estimate": 6, "source_ids": [], "tags": ["python", "automation", "finance"], "notes": "", "created_at": "2026-03-18T10:00:00", "updated_at": "2026-03-21T09:00:00"},
        {"id": "m3n4o5p6", "title": "Building a personal knowledge graph with Obsidian + Python", "type": "long_form", "target_channel": "Blog / Medium", "status": "idea", "effort_estimate": "L", "impact_estimate": 9, "source_ids": [], "tags": ["knowledge", "obsidian", "python"], "notes": "", "created_at": "2026-03-17T10:00:00", "updated_at": "2026-03-17T10:00:00"},
        {"id": "q7r8s9t0", "title": "The CFO Dashboard: How I track my personal finances like a business", "type": "video_script", "target_channel": "YouTube", "status": "idea", "effort_estimate": "L", "impact_estimate": 9, "source_ids": [], "tags": ["finance", "dashboard", "personal"], "notes": "", "created_at": "2026-03-16T10:00:00", "updated_at": "2026-03-16T10:00:00"},
    ]

    backlog_path.write_text(json.dumps(ideas, indent=2), encoding="utf-8")
    print(f"Generated {len(ideas)} content backlog items → {backlog_path}")


def test_persona_system() -> None:
    """Verify persona system is working."""
    from vaishali.core.persona_loader import load_persona, list_personas, get_persona_emoji

    print("\n" + "=" * 60)
    print("PERSONA SYSTEM TEST")
    print("=" * 60)

    # Test load_persona
    finance_persona = load_persona("finance")
    if finance_persona:
        print(f"\n✅ Loaded finance persona: {finance_persona.emoji} {finance_persona.name}")
        print(f"   Personality: {finance_persona.personality}")
        print(f"   Tone: {finance_persona.tone}")
        print(f"   Templates: {list(finance_persona.templates.keys())}")
    else:
        print("\n❌ Failed to load finance persona")

    # Test get_persona_emoji
    emoji = get_persona_emoji("health")
    print(f"\n✅ Health emoji: {emoji}")

    # Test list_personas
    all_personas = list_personas()
    print(f"\n✅ Loaded {len(all_personas)} total personas:")
    for p in all_personas:
        print(f"   {p.emoji} {p.name.ljust(15)} ({p.agent})")

    print("\n" + "=" * 60)


def main() -> None:
    seed_dir = settings.data_dir / "finance" / "raw"
    generate_sample_csv(seed_dir, months=3)
    generate_health_data(days=7)
    generate_content_backlog()
    test_persona_system()
    print(f"\nAll seed data ready.")
    print(f"Run: python scripts/ingest_finance_statements.py --input-dir {seed_dir} --bank first-direct --no-archive")
    print(f"Then: python scripts/run_morning_briefing.py --skip-education")


if __name__ == "__main__":
    main()
