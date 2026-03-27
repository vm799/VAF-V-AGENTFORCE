#!/usr/bin/env python3
"""
VAF Telegram Relay Bot
Simple capture relay: phone → Obsidian. No AI, no complexity.

Commands:
  /dump <text>          → writes to Obsidian _Inbox/ as timestamped note
  /spend <amount> <desc>→ appends to Finance/transactions.md (- prefix = expense, + prefix = income)
  /log <text>           → appends to Health/daily-log.md
  /idea <text>          → appends to Content/ideas.md with priority tag

Setup:
  pip install python-telegram-bot python-dotenv
  Set VAF_TELEGRAM_TOKEN and VAF_TELEGRAM_CHAT_ID in .env
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv(Path(__file__).parent.parent.parent / ".env")

TOKEN = os.getenv("VAF_TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("VAF_TELEGRAM_CHAT_ID", "0"))
OBSIDIAN = Path(os.getenv("VAF_OBSIDIAN_VAULT_DIR", str(Path.home() / "Desktop/SecondBrain")))

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def date_str():
    return datetime.now().strftime("%Y-%m-%d")

def append_to(filepath: Path, content: str):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a") as f:
        f.write(content + "\n")

async def cmd_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture a thought to Obsidian _Inbox/"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /dump <your thought>")
        return
    filename = OBSIDIAN / "_Inbox" / f"{date_str()}-dump.md"
    append_to(filename, f"\n## {ts()}\n{text}\n")
    await update.message.reply_text(f"Captured to _Inbox/ ✓")

async def cmd_spend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log a transaction. /spend 45.50 Tesco  or  /spend +3450 Salary"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /spend <amount> <description>\nIncome: /spend +3450 Salary\nExpense: /spend 45 Tesco")
        return
    amount_raw = context.args[0]
    description = " ".join(context.args[1:])
    is_income = amount_raw.startswith("+")
    amount = amount_raw.lstrip("+-")
    sign = "+" if is_income else "-"
    txn_type = "INCOME" if is_income else "EXPENSE"
    line = f"| {date_str()} | {txn_type} | {sign}£{amount} | {description} |"
    filepath = OBSIDIAN / "AgentForce" / "Finance" / "transactions.md"
    append_to(filepath, line)
    await update.message.reply_text(f"Logged: {sign}£{amount} — {description} ✓")

async def cmd_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log health data. /log 8000 steps, 7h sleep, mood 4"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /log <steps, sleep, mood, workout>")
        return
    filepath = OBSIDIAN / "AgentForce" / "Health" / "daily-log.md"
    append_to(filepath, f"\n## {ts()}\n{text}\n")
    await update.message.reply_text(f"Health logged ✓")

async def cmd_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture a content idea. /idea Video about building AI agents"""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /idea <your content idea>")
        return
    filepath = OBSIDIAN / "AgentForce" / "Content" / "ideas.md"
    append_to(filepath, f"\n- [ ] [{ts()}] {text}")
    await update.message.reply_text(f"Idea captured ✓")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "VAF Bot ready.\n\n"
        "/dump <thought>   → Obsidian _Inbox\n"
        "/spend <amt> <desc> → Finance log\n"
        "/log <health data> → Health log\n"
        "/idea <content idea> → Ideas list"
    )

def main():
    if not TOKEN:
        print("ERROR: VAF_TELEGRAM_TOKEN not set in .env")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("dump", cmd_dump))
    app.add_handler(CommandHandler("spend", cmd_spend))
    app.add_handler(CommandHandler("log", cmd_log))
    app.add_handler(CommandHandler("idea", cmd_idea))
    print("VAF Telegram bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
