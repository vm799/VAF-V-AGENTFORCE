#!/usr/bin/env python3
"""Standalone runner for the Telegram bot.

Usage:
    # Set env vars then run:
    export VAF_TELEGRAM_TOKEN="your-bot-token-from-BotFather"
    export VAF_TELEGRAM_CHAT_ID="your-chat-id"
    python -m vaishali.telegram_bot.run

    # Or pass via CLI:
    python -m vaishali.telegram_bot.run --token YOUR_TOKEN --chat-id 123456
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project src is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))


def _load_dotenv():
    """Load .env file from project root if it exists (no extra dependency)."""
    env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:  # don't override existing env vars
            os.environ[key] = value


def main():
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Run VAF Telegram bot")
    parser.add_argument("--token", default=os.environ.get("VAF_TELEGRAM_TOKEN"),
                        help="Telegram bot token (or set VAF_TELEGRAM_TOKEN)")
    parser.add_argument("--chat-id", type=int, default=int(os.environ.get("VAF_TELEGRAM_CHAT_ID", "0")) or None,
                        help="Chat ID for scheduled pushes (or set VAF_TELEGRAM_CHAT_ID)")
    args = parser.parse_args()

    if not args.token:
        print("Error: Telegram bot token required.")
        print("Set VAF_TELEGRAM_TOKEN env var or pass --token")
        print("\nTo create a bot:")
        print("  1. Message @BotFather on Telegram")
        print("  2. Send /newbot and follow the prompts")
        print("  3. Copy the token it gives you")
        sys.exit(1)

    from vaishali.telegram_bot.bot import create_bot

    print("🤖 Starting Vaishali Agent Force Telegram bot...")
    if args.chat_id:
        print(f"📬 Scheduled pushes enabled for chat_id={args.chat_id}")
        print("   Morning briefing: 07:00 | Evening briefing: 21:00")
    else:
        print("💡 No chat_id set — scheduled pushes disabled.")
        print("   Send /start to the bot to get your chat_id.")

    app = create_bot(token=args.token, chat_id=args.chat_id)
    app.run_polling()


if __name__ == "__main__":
    main()
