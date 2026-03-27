#!/usr/bin/env python3
"""
VAF Morning Briefing
Reads your context files and sends a daily brief to Telegram at 7am via LaunchAgent.

Setup:
  pip install python-dotenv requests
  Set VAF_TELEGRAM_TOKEN and VAF_TELEGRAM_CHAT_ID in root .env
"""

import os
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("VAF_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("VAF_TELEGRAM_CHAT_ID")
OBSIDIAN = Path(os.getenv("VAF_OBSIDIAN_VAULT_DIR", str(Path.home() / "Desktop/SecondBrain")))

def read_file(path: Path, max_lines=20) -> str:
    try:
        lines = path.read_text().splitlines()
        return "\n".join(lines[:max_lines])
    except:
        return ""

def extract_top_priorities(goals_text: str) -> list[str]:
    """Pull first 3 unchecked items from goals file."""
    priorities = []
    for line in goals_text.splitlines():
        if "- [ ]" in line and len(priorities) < 3:
            clean = line.replace("- [ ]", "").strip()
            priorities.append(clean)
    return priorities

def extract_goggins_streak(goggins_text: str) -> str:
    for line in goggins_text.splitlines():
        if "streak" in line.lower() or "day" in line.lower():
            return line.strip()
    return "Check goggins-nonneg.md"

def send_telegram(message: str):
    if not TOKEN or not CHAT_ID:
        print("Telegram not configured. Message:\n" + message)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    if resp.ok:
        print("Morning briefing sent.")
    else:
        print(f"Telegram error: {resp.text}")

def main():
    today = datetime.now().strftime("%A, %d %B %Y")

    goals_text = read_file(ROOT / "context" / "current-goals.md")
    goggins_text = read_file(ROOT / "context" / "goggins-nonneg.md")
    agent_text = read_file(ROOT / "context" / "agent-status.md")

    priorities = extract_top_priorities(goals_text)
    if not priorities:
        priorities = ["Review current-goals.md and set today's priorities"]

    # Count ready agents
    ready = agent_text.lower().count("ready")
    building = agent_text.lower().count("building")

    message = f"""🌅 *VAF Daily Briefing*
{today}
━━━━━━━━━━━━━━━━━

*TODAY'S FOCUS*
{"".join(f"{i+1}. {p}" + chr(10) for i, p in enumerate(priorities))}
*AGENT STATUS*
✅ {ready} Ready | 🔧 {building} Building

*GOGGINS NON-NEGOTIABLES*
Complete your 5 non-negotiables. No excuses.

━━━━━━━━━━━━━━━━━
Stay hard. Stay shipping. 💪
"""
    send_telegram(message)

if __name__ == "__main__":
    main()
