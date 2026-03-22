"""Telegram bot — mobile command centre for Vaishali Agent Force.

Provides:
  - /start       → Welcome + register chat
  - /briefing    → Today's full briefing
  - /finance     → Finance snapshot
  - /health      → Health snapshot
  - /content     → Content pipeline status
  - /education   → Education summary
  - /run_morning → Trigger morning briefing pipeline
  - /run_evening → Trigger evening briefing pipeline
  - /status      → Quick all-agents status strip

Scheduled push:
  - Morning briefing at 07:00
  - Evening briefing at 21:00

Uses HTML parse_mode (not MarkdownV2) to avoid escaping headaches.

Dependencies: python-telegram-bot>=20.0
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import subprocess
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import read_all_summaries, read_summary

log = get_logger(__name__)

# ── Agent emoji mapping ────────────────────────────────────────────────

AGENT_EMOJI = {
    "finance": "🦉",
    "content": "🦊",
    "education": "🐱",
    "research": "🐱",
    "health": "🐼",
    "braindump": "🧠",
}

# Try to enrich AGENT_EMOJI from persona definitions
try:
    from vaishali.core.persona_loader import get_persona_emoji as _gpe

    for _a in ["finance", "content", "education", "research", "health", "braindump"]:
        _emoji = _gpe(_a)
        if _emoji:
            AGENT_EMOJI[_a] = _emoji
except Exception:
    pass  # silently fall back to hardcoded emojis

STATUS_EMOJI = {
    "success": "🟢",
    "warning": "🟡",
    "idle": "⚪",
    "running": "🔵",
}


# ── Helpers ────────────────────────────────────────────────────────────

def _e(text: Any) -> str:
    """HTML-escape text for safe Telegram output."""
    return html.escape(str(text))


def _progress_bar(value: int | float, max_val: int, length: int = 10) -> str:
    filled = int(round(value / max_val * length))
    return "▓" * filled + "░" * (length - filled)


# ── Message formatters (HTML) ──────────────────────────────────────────

def format_briefing(briefing: dict[str, Any]) -> str:
    """Format full briefing for Telegram using HTML."""
    lines: list[str] = []
    day = briefing.get("date", date.today().isoformat())

    lines.append(f"🌅 <b>Briefing — {_e(day)}</b>")
    lines.append("")

    wm = briefing.get("what_matters_most_today", "")
    if wm:
        lines.append(f"📌 <b>What matters most:</b>\n{_e(wm)}")
        lines.append("")

    win = briefing.get("todays_win", "")
    if win:
        lines.append(f"🏆 <b>Today's win:</b>\n{_e(win)}")
        lines.append("")

    # Agent headlines
    headlines = briefing.get("agent_headlines", {})
    if headlines:
        lines.append("<b>Agent Status:</b>")
        for agent, headline in headlines.items():
            emoji = AGENT_EMOJI.get(agent, "🤖")
            lines.append(f"{emoji} <b>{_e(agent.title())}:</b> {_e(headline)}")
        lines.append("")

    # Cross-agent insights
    insights = briefing.get("cross_agent_insights", [])
    if insights:
        lines.append("🔗 <b>Cross-agent insights:</b>")
        for i in insights[:5]:
            lines.append(f"  • {_e(i)}")

    return "\n".join(lines)


def format_agent_summary(agent: str, data: dict[str, Any] | None) -> str:
    """Format a single agent's summary for Telegram using HTML."""
    emoji = AGENT_EMOJI.get(agent, "🤖")

    if not data:
        return f"{emoji} <b>{_e(agent.title())}:</b> No data for today."

    lines = [f"{emoji} <b>{_e(agent.title())} Summary</b>"]
    lines.append("")

    status = data.get("status", "idle")
    mood = data.get("mood", "")
    headline = data.get("headline", "")

    lines.append(f"{STATUS_EMOJI.get(status, '⚪')} Status: {_e(status)}")
    if mood:
        lines.append(f"💭 {_e(mood)}")
    if headline:
        lines.append(f"\n{_e(headline)}")

    # Agent-specific details
    if agent == "finance":
        total = data.get("total_balance_gbp")
        if total is not None:
            lines.append(f"\n💰 Balance: £{total:,.2f}")
        anomalies = data.get("anomalies", [])
        if anomalies:
            lines.append(f"⚠️ {len(anomalies)} anomalies flagged")
            for a in anomalies[:3]:
                lines.append(f"  · {_e(a.get('description', ''))} — £{abs(a.get('amount', 0)):.2f}")

    elif agent == "health":
        score = data.get("body_score")
        if score is not None:
            bar = _progress_bar(score, 10)
            lines.append(f"\n🏃 Body Score: {score}/10 {bar}")
        rec = data.get("recommendation")
        if rec:
            lines.append(f"💡 {_e(rec)}")

    elif agent == "content":
        total = data.get("total_backlog", 0)
        lines.append(f"\n📝 Backlog: {total} items")
        waiting = data.get("drafts_waiting_review", [])
        if waiting:
            lines.append(f"✍️ {len(waiting)} drafts need review")

    elif agent == "education":
        items = data.get("items_processed", 0)
        lines.append(f"\n📚 {items} items processed")
        topics = data.get("top_topics", [])
        if topics:
            lines.append(f"🏷 Topics: {_e(', '.join(topics[:5]))}")

    return "\n".join(lines)


def format_status_strip() -> str:
    """Quick one-line-per-agent status for /status command."""
    today = date.today()
    summaries = read_all_summaries(today)

    lines = [f"📊 <b>Agent Status — {today.isoformat()}</b>", ""]

    for agent in ["finance", "content", "education", "research", "health", "braindump"]:
        data = summaries.get(agent)
        emoji = AGENT_EMOJI.get(agent, "🤖")
        if data:
            status = data.get("status", "idle")
            mood = data.get("mood", "—")
            dot = STATUS_EMOJI.get(status, "⚪")
            lines.append(f"{emoji} {dot} <b>{_e(agent.title())}</b>  {_e(mood)}")
        else:
            lines.append(f"{emoji} ⚪ <b>{_e(agent.title())}</b>  No data")

    return "\n".join(lines)


# ── Load briefing from disk ────────────────────────────────────────────

def load_today_briefing() -> dict[str, Any] | None:
    today = date.today()
    path = settings.briefings_dir / f"{today.isoformat()}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ── Bot runner (requires python-telegram-bot) ──────────────────────────

def create_bot(token: str, chat_id: int | None = None):
    """Create and configure the Telegram bot.

    Args:
        token: Telegram bot token from @BotFather.
        chat_id: Optional default chat ID for scheduled pushes.
    """
    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            ContextTypes,
        )
    except ImportError:
        raise ImportError(
            "python-telegram-bot is required. Install with:\n"
            "  pip install 'python-telegram-bot>=20.0'"
        )

    PARSE = "HTML"

    # ── Command handlers ───────────────────────────────────────────

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        cid = update.effective_chat.id
        await update.message.reply_text(
            f"👋 Hello {_e(user.first_name)}! I'm your Agent Force bot.\n\n"
            f"Your chat ID is: <code>{cid}</code> — save this for scheduled pushes.\n\n"
            "<b>📊 View:</b>\n"
            "/briefing — Full daily briefing\n"
            "/status — Quick agent status\n"
            "/finance — Finance snapshot\n"
            "/health — Health snapshot\n"
            "/content — Content pipeline\n"
            "/education — Education summary\n\n"
            "<b>🧠 Braindump:</b>\n"
            "/dump — Capture a thought: <code>/dump Need to prep Q2 deck by Friday</code>\n"
            "/thoughts — View your braindump &amp; actions\n\n"
            "<b>💰 Finance:</b>\n"
            "/spend — Quick entry: <code>/spend 45.50 Tesco groceries</code>\n"
            "📄 Send a CSV file — bank statement auto-import\n"
            "/import — Process CSVs from the data folder\n\n"
            "<b>📥 Intake (feed your agents):</b>\n"
            "/log — Log health: <code>/log 8000 steps, 7h sleep, 30min gym, mood 4</code>\n"
            "/idea — Add content idea: <code>/idea Video about AI agents for YouTube</code>\n"
            "/learn — Add link: <code>/learn https://youtube.com/watch?v=...</code>\n"
            "💡 Or just send any YouTube/IG link!\n\n"
            "<b>📸 Statement Scanning:</b>\n"
            "Send a <b>photo</b> of a bank statement — Owlbert will OCR it!\n\n"
            "<b>🔍 Drill Down (tap into details):</b>\n"
            "/anomalies — View &amp; action finance anomalies\n"
            "/drafts — Review &amp; approve content drafts\n"
            "/ideas — Top content ideas by score\n"
            "/insights — Education insights from links\n"
            "/review &lt;id&gt; — Move content to review\n"
            "/publish &lt;id&gt; — Mark as published\n\n"
            "<b>🌐 Remote Access:</b>\n"
            "/webdash — Dashboard URL (phone access)\n\n"
            "<b>⚙️ Run:</b>\n"
            "/run_morning — Trigger morning pipeline\n"
            "/run_evening — Trigger evening pipeline\n\n"
            "<b>🛠 Admin (remote control):</b>\n"
            "/services — Check service status\n"
            "/restart — Restart all services\n"
            "/rebuild — Rebuild frontend + restart dashboard\n"
            "/logs — View recent log output",
            parse_mode=PARSE,
        )

    async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from vaishali.telegram_bot.callbacks import briefing_keyboard
        briefing = load_today_briefing()
        if not briefing:
            await update.message.reply_text("No briefing yet today. Run /run_morning first.")
            return
        await update.message.reply_text(
            format_briefing(briefing),
            parse_mode=PARSE,
            reply_markup=briefing_keyboard(),
        )

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = format_status_strip()
        await update.message.reply_text(text, parse_mode=PARSE)

    # ── Agent command handlers ─────────────────────────────────────

    async def _finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from vaishali.telegram_bot.callbacks import anomaly_list_keyboard
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        data = read_summary("finance", date.today())
        text = format_agent_summary("finance", data)

        # Add drill-down buttons
        anomalies = (data or {}).get("anomalies", [])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"⚠️ {len(anomalies)} Anomalies", callback_data="fin:anomalies"),
                InlineKeyboardButton("📊 Spending", callback_data="fin:spending"),
            ]
        ]) if data else None

        await update.message.reply_text(text, parse_mode=PARSE, reply_markup=kb)

    async def _health(update: Update, context: ContextTypes.DEFAULT_TYPE):
        data = read_summary("health", date.today())
        await update.message.reply_text(format_agent_summary("health", data), parse_mode=PARSE)

    async def _content(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        data = read_summary("content", date.today())
        text = format_agent_summary("content", data)

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✍️ Drafts", callback_data="cnt:drafts"),
                InlineKeyboardButton("💡 Ideas", callback_data="cnt:ideas"),
            ]
        ])
        await update.message.reply_text(text, parse_mode=PARSE, reply_markup=kb)

    async def _education(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        data = read_summary("education", date.today())
        text = format_agent_summary("education", data)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 View Insights", callback_data="edu:insights")]
        ]) if data else None
        await update.message.reply_text(text, parse_mode=PARSE, reply_markup=kb)

    # ── Drill-down shortcut commands ──────────────────────────────

    async def _cmd_anomalies(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct command to view finance anomalies."""
        summary = read_summary("finance", date.today())
        anomalies = (summary or {}).get("anomalies", [])

        if not anomalies:
            await update.message.reply_text("✅ No finance anomalies detected today!")
            return

        from vaishali.telegram_bot.callbacks import anomaly_list_keyboard
        lines = [f"🦉 <b>Finance Anomalies</b> — {len(anomalies)} flagged\n"]
        for i, a in enumerate(anomalies[:8]):
            severity = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(a.get("severity", ""), "⚪")
            lines.append(
                f"{i + 1}. {severity} <b>{_e(a.get('description', '')[:35])}</b>\n"
                f"   £{abs(a.get('amount', 0)):,.2f} — {_e(a.get('reason', ''))}"
            )

        await update.message.reply_text(
            "\n".join(lines), parse_mode=PARSE,
            reply_markup=anomaly_list_keyboard(anomalies),
        )

    async def _cmd_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct command to view content drafts needing review."""
        from vaishali.content.backlog import get_drafts_waiting_review
        from vaishali.telegram_bot.callbacks import draft_list_keyboard

        drafts = get_drafts_waiting_review()

        if not drafts:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            await update.message.reply_text(
                "✍️ No drafts awaiting review.\nUse /idea to add content, /ideas to see the pipeline.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💡 View Ideas", callback_data="cnt:ideas")]
                ]),
            )
            return

        lines = [f"✍️ <b>Drafts for Review</b> — {len(drafts)}\n"]
        for d in drafts[:8]:
            lines.append(f"  📝 <b>{_e(d.title[:40])}</b> ({_e(d.type)})")

        await update.message.reply_text(
            "\n".join(lines), parse_mode=PARSE,
            reply_markup=draft_list_keyboard(drafts),
        )

    async def _cmd_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct command to view top content ideas."""
        from vaishali.content.backlog import get_ideas
        from vaishali.telegram_bot.callbacks import idea_list_keyboard

        ideas = get_ideas()

        if not ideas:
            await update.message.reply_text("💡 No ideas yet! Use /idea to add some.")
            return

        lines = [f"💡 <b>Top Content Ideas</b> — {len(ideas)} total\n"]
        for i, idea in enumerate(ideas[:6], 1):
            stars = "⭐" * min(3, idea.impact_estimate // 3)
            lines.append(f"{i}. {stars} <b>{_e(idea.title[:40])}</b> ({idea.effort_estimate})")

        await update.message.reply_text(
            "\n".join(lines), parse_mode=PARSE,
            reply_markup=idea_list_keyboard(ideas),
        )

    async def _cmd_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct command to view education insights."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from vaishali.telegram_bot.callbacks import education_list_keyboard

        summary = read_summary("education", date.today())
        if not summary:
            await update.message.reply_text(
                "📚 No education insights today. Drop a link to get started!"
            )
            return

        insights = summary.get("insights", [])
        topics = summary.get("top_topics", [])
        items_processed = summary.get("items_processed", 0)

        lines = [f"📚 <b>Education Insights</b> — {items_processed} items\n"]
        if topics:
            lines.append(f"🏷 Topics: {_e(', '.join(topics[:8]))}\n")
        for i, ins in enumerate(insights[:6]):
            title = ins.get("title", "")[:40] if isinstance(ins, dict) else str(ins)[:40]
            lines.append(f"  {i + 1}. {_e(title)}")

        await update.message.reply_text(
            "\n".join(lines), parse_mode=PARSE,
            reply_markup=education_list_keyboard(insights),
        )

    async def _cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Move a content item to needs_review: /review <id>"""
        from vaishali.content.backlog import update_item

        text = update.message.text.replace("/review", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "Usage: <code>/review item_id</code>\n"
                "Use /ideas or /drafts to find item IDs.",
                parse_mode=PARSE,
            )
            return

        item = update_item(text, status="needs_review")
        if item:
            await update.message.reply_text(
                f"✅ '{_e(item.title[:50])}' moved to <b>needs_review</b>.\n"
                f"Use /drafts to review and approve it.",
                parse_mode=PARSE,
            )
        else:
            await update.message.reply_text(f"❌ Item '{_e(text)}' not found.")

    async def _cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mark a content item as published: /publish <id>"""
        from vaishali.content.backlog import update_item

        text = update.message.text.replace("/publish", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "Usage: <code>/publish item_id</code>", parse_mode=PARSE,
            )
            return

        item = update_item(text, status="published")
        if item:
            await update.message.reply_text(
                f"🎉 '{_e(item.title[:50])}' marked as <b>published</b>!",
                parse_mode=PARSE,
            )
        else:
            await update.message.reply_text(f"❌ Item '{_e(text)}' not found.")

    async def _cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """System health-check — diagnose every E2E flow in one command."""
        import os
        from pathlib import Path

        lines: list[str] = ["🔍 <b>Agent Force — System Check</b>\n"]

        # ── 1. Telegram Token ────────────────────────────────────────────
        tg_token = os.getenv("VAF_TELEGRAM_TOKEN", "")
        lines.append("<b>🔑 Credentials</b>")
        lines.append(f"  {'✅' if tg_token else '❌'} VAF_TELEGRAM_TOKEN — {'set' if tg_token else 'MISSING'}")

        # ── Gemini (fast AI — primary engine) ────────────────────────────
        import os as _os
        gemini_key = (
            _os.getenv("VAF_GOOGLE_AI_KEY")
            or _os.getenv("GOOGLE_AI_KEY")
            or _os.getenv("GEMINI_API_KEY")
        )
        lines.append("\n<b>🤖 Gemini AI (primary, free)</b>")
        if gemini_key:
            lines.append(f"  ✅ VAF_GOOGLE_AI_KEY set ({gemini_key[:8]}...) — AI analysis active!")
            lines.append("  💡 Every dropped link gets instant Gemini analysis (&lt;5s)")
        else:
            lines.append("  ❌ No Google AI key — links get sentence-extract preview only")
            lines.append("  → Get free key: <a href='https://aistudio.google.com/apikey'>aistudio.google.com/apikey</a>")
            lines.append("  → Add to .env: <code>VAF_GOOGLE_AI_KEY=AIza...</code>")

        # ── NotebookLM (deep AI — background enrichment) ─────────────────
        lines.append("\n<b>🔬 NotebookLM (deep analysis, background)</b>")
        try:
            import importlib.util
            has_playwright = importlib.util.find_spec("playwright") is not None
            lines.append(f"  {'✅' if has_playwright else '⚠️'} Playwright — {'installed' if has_playwright else 'not installed → run: pip install playwright &amp;&amp; playwright install chrome'}")
        except Exception:
            has_playwright = False
            lines.append("  ⚠️ Playwright — not installed → run: <code>pip install playwright &amp;&amp; playwright install chrome</code>")

        # Check dedicated VAF NLM profile exists (means first-run login was done)
        vaf_nlm_profile = Path.home() / ".vaf_nlm_profile"
        nlm_logged_in = (vaf_nlm_profile / "Default" / "Cookies").exists() or \
                        any(vaf_nlm_profile.rglob("Cookies")) if vaf_nlm_profile.exists() else False
        lines.append(f"  {'✅' if nlm_logged_in else '⚠️'} NLM profile — {'logged in' if nlm_logged_in else 'not yet signed in'}")
        if not nlm_logged_in and has_playwright:
            lines.append("  → Drop any link — a Chrome window will open to sign into Google (one-time)")
        elif has_playwright and nlm_logged_in:
            lines.append("  ✅ Ready — deep NLM analysis runs automatically in background after each link")

        # ── 2. Obsidian Vault ────────────────────────────────────────────
        lines.append("\n<b>📓 Obsidian Vault</b>")
        vault = settings.obsidian_vault_dir
        if vault and Path(vault).exists():
            lines.append(f"  ✅ Vault found: <code>{vault}</code>")
        elif vault:
            lines.append(f"  ❌ Vault path set but NOT found: <code>{vault}</code>")
            lines.append("  → Check VAF_OBSIDIAN_VAULT_DIR in .env")
        else:
            lines.append("  ⚠️ VAF_OBSIDIAN_VAULT_DIR not set — notes won't save to Obsidian")
            lines.append("  → Add: <code>VAF_OBSIDIAN_VAULT_DIR=/path/to/your/vault</code>")

        # ── 3. Data Directories ──────────────────────────────────────────
        lines.append("\n<b>📁 Data Directories</b>")
        settings.ensure_dirs()
        key_dirs = [
            (settings.data_dir / "education" / "notes" / "insights", "Insights store"),
            (settings.briefings_dir, "Briefings"),
            (settings.finance_raw_dir, "Finance raw"),
            (settings.summaries_dir, "Summaries"),
        ]
        for d, label in key_dirs:
            exists = d.exists()
            count = len(list(d.rglob("*"))) if exists else 0
            lines.append(f"  {'✅' if exists else '❌'} {label}: {count} files")

        # ── 4. Recent Activity ───────────────────────────────────────────
        lines.append("\n<b>📊 Recent Activity</b>")
        insight_base = settings.data_dir / "education" / "notes" / "insights"
        insight_files = sorted(insight_base.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if insight_base.exists() else []
        lines.append(f"  📚 Insights saved: {len(insight_files)} total")
        if insight_files:
            last = insight_files[0]
            import json as _json
            try:
                d = _json.loads(last.read_text())
                lines.append(f"  └ Last: <i>{_e(d.get('title','?')[:50])}</i>")
            except Exception:
                pass

        briefing_files = list(settings.briefings_dir.glob("*.json")) if settings.briefings_dir.exists() else []
        lines.append(f"  🌅 Briefings: {len(briefing_files)} total")
        if briefing_files:
            lines.append(f"  └ Last: {sorted(briefing_files)[-1].stem}")

        csv_files = list(settings.finance_raw_dir.glob("*.csv")) if settings.finance_raw_dir.exists() else []
        lines.append(f"  💳 Finance CSVs: {len(csv_files)} files")

        # ── 5. Dependencies ──────────────────────────────────────────────
        lines.append("\n<b>⚙️ Dependencies</b>")
        deps = [("httpx", "HTTP fetching"), ("yt_dlp", "YouTube transcripts"), ("playwright", "NotebookLM automation")]
        for mod, label in deps:
            try:
                __import__(mod)
                lines.append(f"  ✅ {label} ({mod})")
            except ImportError:
                lines.append(f"  ❌ {label} ({mod}) — run: <code>./vaf.sh setup</code>")

        # ── 6. Dashboard ─────────────────────────────────────────────────
        lines.append("\n<b>🖥️ Dashboard</b>")
        import subprocess as _sp
        try:
            r = _sp.run(["curl", "-s", "--max-time", "2", "http://localhost:8077/api/status"],
                        capture_output=True, text=True, timeout=3)
            if r.returncode == 0 and "date" in r.stdout:
                lines.append("  ✅ Dashboard API responding at http://localhost:8077")
            else:
                lines.append("  ❌ Dashboard not running — start with <code>./vaf.sh quick</code>")
        except Exception:
            lines.append("  ❌ Dashboard not running — start with <code>./vaf.sh quick</code>")

        # ── Summary ──────────────────────────────────────────────────────
        has_issues = any("❌" in l for l in lines)
        lines.append("\n" + ("🔴 <b>Action required</b> — see ❌ items above." if has_issues else "🟢 <b>All systems nominal!</b>"))

        await update.message.reply_text("\n".join(lines), parse_mode=PARSE)

    async def _cmd_webdash(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the remote dashboard URL for phone access."""
        url: str | None = None
        try:
            # Strategy 1: explicit env var
            import os
            url = os.getenv("VAF_TUNNEL_URL", "").strip() or None

            # Strategy 2: .tunnel_url file written by `./vaf.sh tunnel`
            if not url:
                tunnel_file = settings.base_dir / ".tunnel_url"
                if tunnel_file.exists():
                    candidate = tunnel_file.read_text().strip()
                    if candidate.startswith("https://"):
                        url = candidate

            # Strategy 3: ngrok local API
            if not url:
                import subprocess as _sp
                result = _sp.run(
                    ["curl", "-s", "--max-time", "2", "http://localhost:4040/api/tunnels"],
                    capture_output=True, text=True, timeout=3,
                )
                if result.returncode == 0:
                    import json as _json
                    data = _json.loads(result.stdout)
                    for t in data.get("tunnels", []):
                        if t.get("proto") == "https":
                            url = t.get("public_url")
                            break
        except Exception as exc:
            log.warning("Tunnel URL detection failed: %s", exc)

        if url:
            await update.message.reply_text(
                f"🌐 <b>Dashboard — Phone Access</b>\n\n"
                f"🔗 <a href='{_e(url)}'>{_e(url)}</a>\n\n"
                f"Tap the link to open your full dashboard — briefings, finance, content, all agents.\n\n"
                f"<i>URL refreshes each time you restart the tunnel.</i>",
                parse_mode=PARSE,
            )
        else:
            await update.message.reply_text(
                f"🌐 <b>Dashboard — Phone Access</b>\n\n"
                f"⚠️ No tunnel is running yet.\n\n"
                f"<b>Start order (two terminal tabs on Mac):</b>\n\n"
                f"<b>Tab 1 — start the app:</b>\n"
                f"<code>./vaf.sh quick</code>\n\n"
                f"<b>Tab 2 — start the tunnel:</b>\n"
                f"<code>./vaf.sh tunnel</code>\n\n"
                f"The tunnel prints a <code>trycloudflare.com</code> URL — "
                f"then type /webdash here and I'll send you the tappable link. "
                f"No Cloudflare account needed.",
                parse_mode=PARSE,
            )

    # ── Pipeline runners ───────────────────────────────────────────

    async def _run_pipeline(pipeline: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"⏳ Running {pipeline} briefing pipeline...")
        import subprocess, sys

        script = settings.scripts_dir / f"run_{pipeline}_briefing.py"
        if not script.exists():
            await update.message.reply_text(f"❌ Script not found: {script.name}")
            return

        env = {**__import__("os").environ, "PYTHONPATH": str(settings.base_dir / "src")}
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                [sys.executable, str(script)],
                capture_output=True, text=True, timeout=180,
                cwd=str(settings.base_dir),
                env=env,
            ),
        )

        if result.returncode == 0:
            await update.message.reply_text(f"✅ {pipeline.title()} briefing complete!")
            briefing = load_today_briefing()
            if briefing:
                await update.message.reply_text(format_briefing(briefing), parse_mode=PARSE)
        else:
            stderr = _e((result.stderr or "")[:500])
            await update.message.reply_text(f"❌ Pipeline failed:\n<pre>{stderr}</pre>", parse_mode=PARSE)

    async def _run_morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await _run_pipeline("morning", update, context)

    async def _run_evening(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await _run_pipeline("evening", update, context)

    # ── Scheduled push functions ───────────────────────────────────

    async def scheduled_briefing(context: ContextTypes.DEFAULT_TYPE):
        """Called by the job queue to push morning briefing."""
        target = chat_id
        if not target:
            log.warning("No chat_id configured for scheduled push")
            return

        import subprocess, sys
        script = settings.scripts_dir / "run_morning_briefing.py"
        if script.exists():
            env = {**__import__("os").environ, "PYTHONPATH": str(settings.base_dir / "src")}
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True, text=True, timeout=180,
                    cwd=str(settings.base_dir), env=env,
                ),
            )

        briefing = load_today_briefing()
        if briefing:
            from vaishali.telegram_bot.callbacks import briefing_keyboard
            text = format_briefing(briefing)
            await context.bot.send_message(
                chat_id=target, text=text, parse_mode=PARSE,
                reply_markup=briefing_keyboard(),
            )
        else:
            await context.bot.send_message(chat_id=target, text="⚠️ Briefing pipeline ran but no output generated.")

    async def scheduled_evening(context: ContextTypes.DEFAULT_TYPE):
        """Called by the job queue for evening briefing."""
        target = chat_id
        if not target:
            return

        import subprocess, sys
        script = settings.scripts_dir / "run_evening_briefing.py"
        if script.exists():
            env = {**__import__("os").environ, "PYTHONPATH": str(settings.base_dir / "src")}
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True, text=True, timeout=180,
                    cwd=str(settings.base_dir), env=env,
                ),
            )

        briefing = load_today_briefing()
        if briefing:
            text = "🌙 <b>Evening Update</b>\n\n" + format_briefing(briefing)
            await context.bot.send_message(chat_id=target, text=text, parse_mode=PARSE)

    # ── Intake handlers ──────────────────────────────────────────

    async def _handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming photos — route to finance OCR."""
        from vaishali.telegram_bot.intake import process_statement_photo

        msg = await update.message.reply_text("🦉 Owlbert is scanning your statement...")

        # Download the photo (pick highest resolution)
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        settings.ensure_dirs()
        dl_path = settings.data_dir / "finance" / "raw" / f"tg_photo_{date.today().isoformat()}_{photo.file_unique_id}.jpg"
        await file.download_to_drive(str(dl_path))

        result = await process_statement_photo(dl_path)

        if result["status"] == "success":
            bank = result.get("bank", "Unknown Bank")
            n = result["transactions"]

            # Build sample rows: date | description | amount | type
            sample_lines = []
            credits = debits = 0
            for tx in result.get("sample", [])[:5]:
                amt = tx.get("amount", "0")
                tx_type = tx.get("type", "debit")
                icon = "💚" if tx_type == "credit" else "🔴"
                try:
                    amt_f = float(amt)
                    amt_str = f"£{abs(amt_f):,.2f}"
                except Exception:
                    amt_str = f"£{amt}"
                if tx_type == "credit":
                    credits += 1
                else:
                    debits += 1
                desc = tx.get("description", "")[:28]
                sample_lines.append(f"  {icon} {tx.get('tx_date', '')}  {_e(desc)}  {amt_str}")

            sample_text = "\n".join(sample_lines) if sample_lines else ""

            await msg.edit_text(
                f"✅ <b>{bank}</b> — {n} transactions found\n\n"
                f"🔴 Debits: {debits}  💚 Credits: {credits}\n\n"
                f"<b>Sample:</b>\n{sample_text}\n\n"
                f"⏳ Auto-importing into ledger...",
                parse_mode=PARSE,
            )

            # Auto-ingest the CSV into the ledger immediately — no manual /import needed
            csv_path_str = result.get("csv_path", "")
            ingest_status = ""
            inserted = 0
            if csv_path_str:
                try:
                    from vaishali.telegram_bot.intake import process_csv_file
                    csv_result = process_csv_file(
                        Path(csv_path_str),
                        bank=bank.lower().replace(" ", "-") if bank else "generic",
                    )
                    inserted = csv_result.get("rows_inserted", 0)
                    skipped = csv_result.get("rows_skipped", 0)
                    ingest_status = f"\n✅ <b>Ledger updated</b> — {inserted} new · {skipped} duplicates skipped"
                except Exception as exc:
                    log.warning("Auto-ingest failed: %s", exc)
                    ingest_status = f"\n⚠️ Auto-import failed: <code>{_e(str(exc)[:80])}</code> — run /import manually"

            # ── Regenerate finance summary → feeds dashboard immediately ──
            obs_line = ""
            try:
                from vaishali.finance.summaries import generate_daily_summary
                summary_path = generate_daily_summary()
                log.info("Finance summary updated: %s", summary_path)
            except Exception as exc:
                log.warning("Finance summary generation failed: %s", exc)

            # ── Write Obsidian finance note ────────────────────────────────
            try:
                _write_finance_obsidian_note(bank, result.get("sample", []), inserted, n)
                vault_dir = settings.obsidian_vault_dir
                if vault_dir:
                    obs_line = f"\n📓 <b>Obsidian:</b> <code>Finance/Statements/</code>"
            except Exception as exc:
                log.warning("Obsidian finance write failed: %s", exc)

            await msg.edit_text(
                f"✅ <b>{bank}</b> — {n} transactions found\n\n"
                f"🔴 Debits: {debits}  💚 Credits: {credits}\n\n"
                f"<b>Sample:</b>\n{sample_text}"
                f"{ingest_status}"
                f"{obs_line}\n\n"
                f"📊 <i>Finance dashboard updated automatically.</i>",
                parse_mode=PARSE,
            )
        elif result["status"] == "partial":
            bank = result.get("bank", "")
            bank_line = f"🏦 Detected: <b>{_e(bank)}</b>\n\n" if bank and bank != "Unknown Bank" else ""
            raw = result.get("raw_text", "")[:400]
            await msg.edit_text(
                f"⚠️ {bank_line}OCR read text but couldn't match transaction rows.\n\n"
                f"<b>Raw text seen:</b>\n<pre>{_e(raw)}</pre>\n\n"
                f"Tips: crop tightly to just the transaction rows, good lighting, or upload the CSV file directly.",
                parse_mode=PARSE,
            )
        else:
            await msg.edit_text(
                f"❌ {_e(result.get('message', 'OCR failed'))}\n\n"
                f"Try better lighting, a closer crop, or upload the CSV export instead.",
                parse_mode=PARSE,
            )

    def _write_finance_obsidian_note(bank: str, sample_txs: list, inserted: int, total: int) -> None:
        """Write a daily bank statement note to the Obsidian Finance vault."""
        vault = settings.obsidian_vault_dir
        if not vault:
            return

        vault_path = Path(vault) / "Finance" / "Statements"
        vault_path.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat()
        note_path = vault_path / f"{today}_{bank.replace(' ', '-').lower()}_statement.md"

        lines = [
            f"# {bank} Statement — {today}",
            f"",
            f"**Imported:** {total} transactions ({inserted} new)",
            f"**Source:** Telegram photo → OCR → auto-import",
            f"",
            f"## Sample Transactions",
            f"",
            f"| Date | Description | Amount | Type |",
            f"|------|-------------|--------|------|",
        ]
        for tx in sample_txs[:10]:
            amt = tx.get("amount", "0")
            try:
                amt_f = float(amt)
                amt_str = f"£{abs(amt_f):,.2f}"
            except Exception:
                amt_str = str(amt)
            lines.append(
                f"| {tx.get('tx_date','?')} | {tx.get('description','?')[:40]} | {amt_str} | {tx.get('type','?')} |"
            )

        lines += [
            f"",
            f"## Tags",
            f"#finance #statement #{bank.lower().replace(' ','-')} #imported",
            f"",
            f"---",
            f"*Auto-generated by Vaishali Agent Force on {today}*",
        ]

        note_path.write_text("\n".join(lines), encoding="utf-8")
        log.info("Finance Obsidian note written: %s", note_path)

    async def _handle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /log command — quick health check-in."""
        from vaishali.telegram_bot.intake import parse_health_log, save_health_log

        text = update.message.text.replace("/log", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "🐼 <b>Quick health log:</b>\n\n"
                "<code>/log 8000 steps, 7.5h sleep, 30min gym, mood 4, energy 4, water, meditate</code>\n\n"
                "Just include what you have — Bamboo will fill in the rest!",
                parse_mode=PARSE,
            )
            return

        metrics = parse_health_log(text)
        save_health_log(metrics)

        await update.message.reply_text(
            f"🐼 <b>Health logged!</b>\n\n"
            f"🚶 Steps: {metrics['steps']:,}\n"
            f"😴 Sleep: {metrics['sleep_hours']}h\n"
            f"🏋️ Workout: {metrics['workout_minutes']}min\n"
            f"😊 Mood: {metrics['mood']}/5 | Energy: {metrics['energy']}/5\n"
            f"✅ Habits: {metrics['habits_completed']}/{metrics['habits_total']}\n\n"
            f"Run /run_morning to update your dashboard.",
            parse_mode=PARSE,
        )

    async def _handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /idea command — add to content backlog."""
        from vaishali.telegram_bot.intake import add_content_idea

        text = update.message.text.replace("/idea", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "🦊 <b>Add a content idea:</b>\n\n"
                "<code>/idea Video tutorial on building AI agents — YouTube</code>\n"
                "<code>/idea LinkedIn post about personal finance automation</code>\n"
                "<code>/idea Instagram reel showing my dashboard setup</code>",
                parse_mode=PARSE,
            )
            return

        result = add_content_idea(text)
        await update.message.reply_text(
            f"🦊 <b>Idea saved!</b>\n\n"
            f"📝 {_e(result['title'])}\n"
            f"📺 Type: {result['type']} | Channel: {result['channel']}\n\n"
            f"Check /content for your full pipeline.",
            parse_mode=PARSE,
        )

    async def _handle_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /learn command — add educational link."""
        from vaishali.telegram_bot.intake import process_education_link

        text = update.message.text.replace("/learn", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "🐱 <b>Add a learning link:</b>\n\n"
                "<code>/learn https://youtube.com/watch?v=xyz</code>\n"
                "<code>/learn https://interesting-article.com/ai-agents My notes here</code>",
                parse_mode=PARSE,
            )
            return

        # Split URL from optional notes
        parts = text.split(None, 1)
        url = parts[0]
        note = parts[1] if len(parts) > 1 else ""

        await update.message.reply_text("🐱 Whiskers is extracting content...")
        result = await process_education_link(url, note)

        await update.message.reply_text(
            f"🐱 <b>{_e(result['message'])}</b>\n"
            f"📏 Extracted {result['content_length']:,} chars\n\n"
            f"Run /run_morning to process into insights.",
            parse_mode=PARSE,
        )

    # ── Finance quick-entry handlers ────────────────────────────────

    async def _handle_spend(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /spend command — quick transaction entry."""
        from vaishali.telegram_bot.intake import parse_spend, save_spend

        text = update.message.text.replace("/spend", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "🦉 <b>Quick spend/income entry:</b>\n\n"
                "<code>/spend 45.50 Tesco groceries</code>\n"
                "<code>/spend 15.99 Netflix subscription</code>\n"
                "<code>/spend 8.50 Costa coffee</code>\n"
                "<code>/spend +3450 Salary</code> (use + for income)\n"
                "<code>/spend 875 Rent</code>\n\n"
                "💡 Amount first, then description. Treats everything as spending unless you add +",
                parse_mode=PARSE,
            )
            return

        entry = parse_spend(text)
        if not entry:
            await update.message.reply_text(
                "❌ Couldn't parse that. Try: <code>/spend 25.00 Tesco</code>",
                parse_mode=PARSE,
            )
            return

        save_spend(entry)

        # Refresh finance summary so dashboard reflects instantly
        try:
            from vaishali.finance.summaries import generate_daily_summary
            generate_daily_summary()
        except Exception as exc:
            log.warning("Finance summary after /spend failed: %s", exc)

        emoji = "💸" if entry["amount"] < 0 else "💰"
        await update.message.reply_text(
            f"🦉 <b>Transaction logged!</b>\n\n"
            f"{emoji} £{abs(entry['amount']):.2f} — {_e(entry['description'])}\n"
            f"📅 {entry['date']}\n\n"
            f"📊 <i>Finance dashboard updated.</i>",
            parse_mode=PARSE,
        )

    async def _handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads — route CSV to finance, others to education."""
        doc = update.message.document
        if not doc:
            return

        filename = doc.file_name or "unknown"
        mime = doc.mime_type or ""

        # CSV files → finance pipeline
        if filename.lower().endswith(".csv") or "csv" in mime:
            await update.message.reply_text("🦉 Owlbert is processing your CSV statement...")

            file = await context.bot.get_file(doc.file_id)
            settings.ensure_dirs()
            dl_path = settings.finance_raw_dir / f"tg_{date.today().isoformat()}_{filename}"
            await file.download_to_drive(str(dl_path))

            from vaishali.telegram_bot.intake import process_csv_file

            result = process_csv_file(dl_path)

            if result["status"] == "success":
                # Regenerate summary → dashboard reflects new data immediately
                obs_line = ""
                try:
                    from vaishali.finance.summaries import generate_daily_summary
                    generate_daily_summary()
                except Exception as exc:
                    log.warning("Finance summary after CSV failed: %s", exc)
                try:
                    _write_finance_obsidian_note(
                        result["bank"], [], result["rows_inserted"], result["rows_parsed"]
                    )
                    if settings.obsidian_vault_dir:
                        obs_line = "\n📓 <b>Obsidian:</b> <code>Finance/Statements/</code>"
                except Exception as exc:
                    log.warning("Obsidian write after CSV failed: %s", exc)

                await update.message.reply_text(
                    f"✅ <b>Statement processed!</b>\n\n"
                    f"📊 {result['rows_parsed']} transactions found\n"
                    f"📥 {result['rows_inserted']} new, {result['rows_skipped']} duplicates skipped\n"
                    f"🏦 Bank: {_e(result['bank'])}"
                    f"{obs_line}\n\n"
                    f"📊 <i>Finance dashboard updated automatically.</i>",
                    parse_mode=PARSE,
                )
            else:
                await update.message.reply_text(
                    f"❌ {_e(result.get('message', 'Failed to process CSV'))}",
                    parse_mode=PARSE,
                )
        else:
            await update.message.reply_text(
                "💡 I can process:\n"
                "📄 <b>CSV files</b> — bank statements (First Direct, generic)\n"
                "📸 <b>Photos</b> — photographed statements\n\n"
                "For other files, try /learn with a link instead.",
                parse_mode=PARSE,
            )

    async def _handle_import(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /import command — pull CSVs from the finance raw folder."""
        from vaishali.telegram_bot.intake import process_csv_file

        settings.ensure_dirs()
        csv_files = sorted(settings.finance_raw_dir.glob("*.csv"))

        if not csv_files:
            await update.message.reply_text(
                "🦉 No CSV files found in the finance folder.\n\n"
                "Ways to add statements:\n"
                "1. Send a CSV file here in Telegram\n"
                "2. Use <code>/spend 25.00 Tesco</code> for quick entries\n"
                f"3. Drop CSVs in <code>data/finance/raw/</code> then /import",
                parse_mode=PARSE,
            )
            return

        await update.message.reply_text(f"🦉 Found {len(csv_files)} CSV files — processing...")

        total_parsed = 0
        total_inserted = 0
        total_skipped = 0
        processed = 0

        for csv_file in csv_files:
            result = process_csv_file(csv_file)
            if result["status"] == "success":
                total_parsed += result["rows_parsed"]
                total_inserted += result["rows_inserted"]
                total_skipped += result["rows_skipped"]
                processed += 1

                # Archive after successful processing
                archive = settings.finance_archive_dir
                archive.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.move(str(csv_file), str(archive / csv_file.name))

        await update.message.reply_text(
            f"🦉 <b>Import complete!</b>\n\n"
            f"📁 {processed}/{len(csv_files)} files processed\n"
            f"📊 {total_parsed} transactions found\n"
            f"📥 {total_inserted} new, {total_skipped} duplicates skipped\n\n"
            f"Run /run_morning to update your dashboard.",
            parse_mode=PARSE,
        )

    # ── Braindump conversation state keys ──────────────────────────
    DUMP_WAITING_WHY = "dump_waiting_why"
    DUMP_WAITING_WHEN = "dump_waiting_when"
    DUMP_WAITING_PRIORITY = "dump_waiting_priority"
    DUMP_WAITING_CATEGORY = "dump_waiting_category"

    async def _handle_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /dump command — capture a braindump thought with guided prompts."""
        from vaishali.braindump.classifier import classify
        from vaishali.braindump.models import Thought

        text = update.message.text.replace("/dump", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "🧠 <b>Brain dump — capture any thought:</b>\n\n"
                "<code>/dump Need to prepare Q2 report for the team by Friday</code>\n"
                "<code>/dump Idea: build a personal finance tracker app</code>\n"
                "<code>/dump Feeling great about the agent system progress</code>\n"
                "<code>/dump Remember to book dentist appointment</code>\n\n"
                "I'll classify it and ask follow-up questions!",
                parse_mode=PARSE,
            )
            return

        # Auto-classify the raw text
        classified = classify(text)

        # Store in context for the conversation flow
        thought = Thought(
            raw_text=text,
            title=classified["title"],
            thought_type=classified["thought_type"],
            category=classified["category"],
            priority=classified["priority"],
            linked_agents=classified["linked_agents"],
            tags=classified["tags"],
        )

        context.user_data["pending_thought"] = thought

        # Show classification and ask: is this for work or home?
        type_emoji = {"action": "⚡", "todo": "✅", "idea": "💡", "reflection": "🪞", "question": "❓", "reference": "📌"}.get(
            thought.thought_type, "💭"
        )
        cat_emoji = {"work": "💼", "home": "🏠", "personal": "👤", "health": "🏃", "finance": "💰", "learning": "📚", "creative": "🎨"}.get(
            thought.category, "💭"
        )

        await update.message.reply_text(
            f"🧠 <b>Captured!</b>\n\n"
            f"{type_emoji} <b>Type:</b> {_e(thought.thought_type)}\n"
            f"{cat_emoji} <b>Category:</b> {_e(thought.category)}\n"
            f"🏷 <b>Tags:</b> {_e(', '.join(thought.tags[:5]))}\n\n"
            f"<b>Is this for work or home?</b>\n"
            f"Reply: <code>work</code> / <code>home</code> / <code>personal</code>\n"
            f"Or <code>skip</code> to keep '{_e(thought.category)}' and continue.",
            parse_mode=PARSE,
        )
        context.user_data["dump_state"] = DUMP_WAITING_CATEGORY

    async def _handle_dump_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handle braindump follow-up answers. Returns True if handled."""
        state = context.user_data.get("dump_state")
        thought: Any = context.user_data.get("pending_thought")

        if not state or not thought:
            return False

        text = (update.message.text or "").strip().lower()

        if state == DUMP_WAITING_CATEGORY:
            if text != "skip":
                from vaishali.braindump.models import VALID_CATEGORIES
                if text in VALID_CATEGORIES:
                    thought.category = text
                # Also accept shorthand
                elif text in ("w", "work"):
                    thought.category = "work"
                elif text in ("h", "home"):
                    thought.category = "home"
                elif text in ("p", "personal"):
                    thought.category = "personal"

            await update.message.reply_text(
                f"<b>Why does this matter?</b>\n"
                f"Reply with a reason, or <code>skip</code>",
                parse_mode=PARSE,
            )
            context.user_data["dump_state"] = DUMP_WAITING_WHY
            return True

        elif state == DUMP_WAITING_WHY:
            if text != "skip":
                thought.why = update.message.text.strip()

            await update.message.reply_text(
                f"<b>When should this happen?</b>\n"
                f"Reply: <code>today</code> / <code>this week</code> / <code>someday</code> / a date\n"
                f"Or <code>skip</code>",
                parse_mode=PARSE,
            )
            context.user_data["dump_state"] = DUMP_WAITING_WHEN
            return True

        elif state == DUMP_WAITING_WHEN:
            if text != "skip":
                thought.when = update.message.text.strip()

            await update.message.reply_text(
                f"<b>Priority?</b>\n"
                f"🔴 <code>urgent</code>  🟠 <code>high</code>  🟡 <code>medium</code>  🟢 <code>low</code>  ⚪ <code>someday</code>\n"
                f"Or <code>skip</code> to keep '{_e(thought.priority)}'",
                parse_mode=PARSE,
            )
            context.user_data["dump_state"] = DUMP_WAITING_PRIORITY
            return True

        elif state == DUMP_WAITING_PRIORITY:
            if text != "skip":
                from vaishali.braindump.models import VALID_PRIORITIES
                if text in VALID_PRIORITIES:
                    thought.priority = text

            # All questions answered — save the thought
            from vaishali.braindump.storage import add_thought
            from vaishali.braindump.obsidian import write_thought_note

            saved = add_thought(thought)

            # Write to Obsidian
            obsidian_path = write_thought_note(saved)
            if obsidian_path:
                saved.obsidian_path = str(obsidian_path)

            priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "someday": "⚪"}.get(
                saved.priority, "🟡"
            )

            obsidian_line = ""
            if obsidian_path:
                obsidian_line = f"\n📓 Saved to Obsidian vault"

            agents_line = ""
            if saved.linked_agents:
                agents_line = f"\n🔗 Linked: {', '.join(a.title() for a in saved.linked_agents)}"

            await update.message.reply_text(
                f"🧠 <b>Thought saved!</b>\n\n"
                f"📝 {_e(saved.title)}\n"
                f"📂 {_e(saved.category)} | {priority_emoji} {_e(saved.priority)}\n"
                f"📅 {_e(saved.when or 'No deadline')}"
                f"{agents_line}"
                f"{obsidian_line}\n\n"
                f"Use /thoughts to see your braindump, or /dump for another!",
                parse_mode=PARSE,
            )

            # Clean up conversation state
            context.user_data.pop("dump_state", None)
            context.user_data.pop("pending_thought", None)
            return True

        return False

    async def _handle_thoughts(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /thoughts command — show recent braindump thoughts."""
        from vaishali.braindump.storage import get_active_actions, get_stats, get_today_thoughts

        stats = get_stats()
        today = get_today_thoughts()
        actions = get_active_actions()

        lines = ["🧠 <b>Braindump Summary</b>", ""]
        lines.append(f"📊 Total: {stats['total']} thoughts | Today: {stats['today']}")
        lines.append(f"⚡ Active actions: {stats['active_actions']}")
        lines.append("")

        if actions:
            lines.append("<b>Top Actions:</b>")
            for a in actions[:5]:
                p_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "someday": "⚪"}.get(a.priority, "🟡")
                c_emoji = {"work": "💼", "home": "🏠"}.get(a.category, "📝")
                lines.append(f"  {p_emoji} {c_emoji} {_e(a.title)}")
                if a.when:
                    lines.append(f"      📅 {_e(a.when)}")
            lines.append("")

        if today:
            lines.append(f"<b>Today's Thoughts ({len(today)}):</b>")
            for t in today[:8]:
                type_emoji = {"action": "⚡", "todo": "✅", "idea": "💡", "reflection": "🪞", "question": "❓"}.get(t.thought_type, "💭")
                lines.append(f"  {type_emoji} {_e(t.title)}")

        if not today and not actions:
            lines.append("💭 No thoughts yet — use /dump to start capturing!")

        await update.message.reply_text("\n".join(lines), parse_mode=PARSE)

    async def _handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle plain text messages — check braindump conversation first, then auto-detect links."""
        text = update.message.text or ""
        if not text or text.startswith("/"):
            return  # skip commands, handled elsewhere

        # Check if we're in a braindump conversation flow
        if await _handle_dump_conversation(update, context):
            return

        from vaishali.telegram_bot.intake import (
            URL_PATTERN, classify_link, process_education_link, CONTENT_CATEGORIES,
        )
        from vaishali.education.insight_writer import (
            extract_insights, save_insight_json, write_obsidian_note, CATEGORY_VAULT_MAP,
        )

        # ── URL detected — run the full insight pipeline ───────────────
        url_match = URL_PATTERN.search(text)
        if url_match:
            url = url_match.group(0)
            category = classify_link(url)
            note = URL_PATTERN.sub("", text).strip()

            cat_emoji, cat_label = CATEGORY_VAULT_MAP.get(category, ("Research", "Research", "🔬"))[2], \
                                   CATEGORY_VAULT_MAP.get(category, ("Research", "Research", "🔬"))[1]

            msg = await update.message.reply_text(
                f"{cat_emoji} <b>{cat_label}</b> link detected — reading and extracting insights...",
                parse_mode=PARSE,
            )

            # Step 1: fetch content
            result = await process_education_link(url, note)
            title = result.get("title", url)[:80]
            raw_content = result.get("content", "")

            # Step 2: Gemini instant analysis (< 5s) → save + Obsidian immediately
            insight = await extract_insights(title, url, raw_content, category)
            save_insight_json(insight)
            obsidian_path = write_obsidian_note(insight)

            # Step 3: Queue for 8pm NLM batch (no immediate NLM call — saves quota + avoids Chrome pop-up)
            from vaishali.education.url_queue import enqueue, queue_summary
            enqueue(url, title, category, insight.id)

            # Step 4: Reply immediately
            vault_folder = CATEGORY_VAULT_MAP.get(category, ("Research", "Research", "🔬"))[0]
            obs_line = f"\n📓 <b>Obsidian:</b> <code>{vault_folder}/</code>" if obsidian_path else "\n📂 Saved to insights store"
            topics_preview = (
                f"\n🏷 <i>{_e('  ·  '.join(insight.key_topics[:5]))}</i>"
                if insight.key_topics and insight.key_topics != [category] else ""
            )

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🧠 All Links", callback_data="edu:urls"),
                InlineKeyboardButton("📖 Insights", callback_data="edu:insights"),
            ]])
            await msg.edit_text(
                f"{cat_emoji} <b>[{cat_label}]</b>  {_e(title)}\n\n"
                f"💡 <i>{_e(insight.summary[:280])}</i>"
                f"{topics_preview}\n"
                f"{obs_line}\n"
                f"🔬 <i>Queued for NLM batch (runs 8pm daily)</i>",
                parse_mode=PARSE, reply_markup=kb,
            )
            return

        # No URL — offer help
        await update.message.reply_text(
            "💡 Drop any link and I'll:\n"
            "  🔍 Classify it (recipe / finance / tech / health / research...)\n"
            "  🤖 Gemini AI analysis — instant\n"
            "  📓 Save to Obsidian vault (correct section)\n"
            "  🔬 Queue for NLM deep analysis at 8pm\n\n"
            "Or try:\n"
            "  📸 Photo of a bank statement → transactions\n"
            "  /log — Quick health check-in\n"
            "  /idea — Save a content idea\n"
            "  /check — System status",
            parse_mode=PARSE,
        )

    # ── NotebookLM background enrichment ───────────────────────────

    async def _enrich_with_notebooklm(update, insight, url: str, title: str, obsidian_path) -> None:
        """Background task: deep analysis via NotebookLM, updates insight + Obsidian note."""
        import sys
        # Import here — this runs as a background task, not a closure over _handle_text_message
        from vaishali.education.insight_writer import (
            save_insight_json, write_obsidian_note, CATEGORY_VAULT_MAP,
        )
        try:
            scripts_dir = settings.base_dir / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))

            from notebooklm_ingest import notebooklm_extract
            nlm = await notebooklm_extract(url)

            nlm_summary = nlm.get("summary", "").strip()
            # Validate NLM summary is real text, not icon glyph noise
            # (NLM UI renders Material Icons as text — "audio_magic_eraser chevron_forward" etc.)
            def _looks_real(s: str) -> bool:
                if len(s) < 40 or " " not in s:
                    return False
                words = s.split()
                icon_like = sum(1 for w in words if "_" in w or (len(w) > 5 and w[0].islower() and any(c.isupper() for c in w[1:])))
                return icon_like / max(len(words), 1) < 0.3

            if nlm.get("status") == "success" and nlm_summary and _looks_real(nlm_summary):
                insight.notebooklm_summary = nlm_summary
                insight.summary = nlm_summary[:400]   # upgrade to NLM's richer summary
                if nlm.get("key_topics"):
                    insight.key_topics = list(dict.fromkeys(
                        insight.key_topics + nlm["key_topics"]
                    ))[:10]

                save_insight_json(insight)
                obsidian_path = write_obsidian_note(insight)

                vault_folder = insight.vault_folder
                cat_entry = CATEGORY_VAULT_MAP.get(insight.category, ("Research", "Research", "🔬"))
                cat_emoji, cat_label = cat_entry[2], cat_entry[1]
                obs_line = f"\n📓 Obsidian updated → <code>{vault_folder}/</code>" if obsidian_path else ""
                topics_line = f"\n🏷 {_e('  ·  '.join(insight.key_topics[:6]))}" if insight.key_topics else ""

                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🧠 All Insights", callback_data="edu:insights"),
                    InlineKeyboardButton("📖 Education", callback_data="edu:list"),
                ]])
                await update.message.reply_text(
                    f"🔬 <b>NotebookLM analysis ready</b>\n\n"
                    f"{cat_emoji} <b>[{cat_label}]</b>  {_e(title[:70])}\n\n"
                    f"💡 <i>{_e(insight.summary[:320])}</i>"
                    f"{topics_line}"
                    f"{obs_line}",
                    parse_mode=PARSE, reply_markup=kb,
                )

            elif nlm.get("status") == "login_required":
                await update.message.reply_text(
                    "🔬 <b>NotebookLM setup needed</b>\n\n"
                    "Not logged into Google. One-time fix:\n"
                    "1. Open Chrome on your Mac\n"
                    "2. Go to <a href='https://notebooklm.google.com'>notebooklm.google.com</a>\n"
                    "3. Sign into your Google account\n"
                    "4. Drop the link again — it'll work automatically from now on\n\n"
                    "<i>Your link was saved to Obsidian with a preview summary.</i>",
                    parse_mode=PARSE,
                )

            elif nlm.get("status") == "no_browser":
                # Playwright not installed — tell user once so they know what to do
                await update.message.reply_text(
                    "🔬 <b>NotebookLM not yet configured</b>\n\n"
                    "One-time setup to enable AI analysis:\n"
                    "<code>./vaf.sh setup</code>\n\n"
                    "This installs the browser automation layer (60 seconds). "
                    "After that, every link you drop gets full NotebookLM analysis → Obsidian.\n\n"
                    "<i>Your link was saved with a preview summary for now.</i>",
                    parse_mode=PARSE,
                )

            elif nlm.get("status") == "error":
                log.warning("NLM error for %s: %s", url, nlm.get("message", ""))
                await update.message.reply_text(
                    f"🔬 <b>NotebookLM error</b> — link saved to Obsidian with preview.\n"
                    f"<i>{_e(nlm.get('message', 'Unknown error')[:120])}</i>",
                    parse_mode=PARSE,
                )

        except Exception as e:
            log.warning("NotebookLM enrichment failed: %s", e)
            # Only surface if it's a meaningful error, not a transient one
            if "playwright" not in str(e).lower():
                await update.message.reply_text(
                    f"⚠️ NotebookLM task failed: <code>{_e(str(e)[:120])}</code>",
                    parse_mode=PARSE,
                )

    # ── Scheduled tasks ────────────────────────────────────────────

    async def _cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new scheduled task from natural language.

        Usage: /schedule every weekday at 7am morning briefing
        """
        from vaishali.core.scheduler_nl import (
            create_task,
            cron_to_readable,
            get_next_run,
        )

        if not context.args or not " ".join(context.args).strip():
            await update.message.reply_text(
                "📅 <b>Schedule a Task</b>\n\n"
                "Usage: /schedule <description>\n\n"
                "<b>Examples:</b>\n"
                "  /schedule every weekday at 7am morning briefing\n"
                "  /schedule every day at 12pm lunch reminder\n"
                "  /schedule every Friday at 5pm weekend check\n"
                "  /schedule every morning at 7 briefing\n\n"
                "<b>Patterns:</b>\n"
                "  • <code>every day</code>\n"
                "  • <code>every weekday / weekdays</code>\n"
                "  • <code>every Monday/Tuesday/etc</code>\n"
                "  • Times: <code>7am</code>, <code>7:30am</code>, <code>noon</code>, <code>9pm</code>",
                parse_mode=PARSE,
            )
            return

        description = " ".join(context.args)
        task = create_task(description)

        if not task:
            await update.message.reply_text(
                "❌ <b>Could not parse schedule</b>\n\n"
                f"Your input: <code>{_e(description)}</code>\n\n"
                "Please try patterns like:\n"
                "  <code>every day at 7am</code>\n"
                "  <code>every weekday at 8:30am</code>\n"
                "  <code>every Monday at 9pm</code>",
                parse_mode=PARSE,
            )
            return

        readable = cron_to_readable(task.cron_expr)
        next_run = get_next_run(task.cron_expr)
        next_run_str = next_run.strftime("%a, %b %d at %I:%M%p") if next_run else "N/A"

        await update.message.reply_text(
            f"✅ <b>Task Scheduled</b>\n\n"
            f"📝 <b>Label:</b> {_e(task.label)}\n"
            f"⚙️ <b>Command:</b> {_e(task.command)}\n"
            f"⏱️ <b>Schedule:</b> {_e(readable)}\n"
            f"🔢 <b>Cron:</b> <code>{_e(task.cron_expr)}</code>\n"
            f"➡️ <b>Next Run:</b> {_e(next_run_str)}\n"
            f"🆔 <b>ID:</b> <code>{task.id}</code>\n\n"
            f"Task ID: <code>{task.id}</code> — use /unschedule {task.id} to remove",
            parse_mode=PARSE,
        )

    async def _cmd_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all scheduled tasks with next run times."""
        from vaishali.core.scheduler_nl import cron_to_readable, get_next_run, list_tasks

        tasks = list_tasks()

        if not tasks:
            await update.message.reply_text("📋 No scheduled tasks configured yet.\n\nUse /schedule to create one.")
            return

        lines = ["📋 <b>Scheduled Tasks</b>\n"]

        for task in tasks:
            if not task.enabled:
                status = "⚫"
            else:
                status = "🟢"

            readable = cron_to_readable(task.cron_expr)
            next_run = get_next_run(task.cron_expr)
            next_run_str = next_run.strftime("%a, %b %d %H:%M") if next_run else "N/A"

            lines.append(
                f"{status} <b>{_e(task.label)}</b>\n"
                f"   ⏱️ {_e(readable)}\n"
                f"   ➡️ {next_run_str}\n"
                f"   🆔 <code>{task.id}</code>"
            )

        lines.append("\n<i>Use /unschedule {id} to remove a task</i>")

        await update.message.reply_text("\n".join(lines), parse_mode=PARSE)

    async def _cmd_unschedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a scheduled task by ID."""
        from vaishali.core.scheduler_nl import list_tasks, remove_task

        if not context.args or not context.args[0].strip():
            tasks = list_tasks()
            if not tasks:
                await update.message.reply_text("No scheduled tasks to remove.")
                return

            task_ids = [t.id for t in tasks]
            await update.message.reply_text(
                f"❌ <b>Which task to remove?</b>\n\n"
                f"Usage: /unschedule <id>\n\n"
                f"<b>Available:</b>\n"
                + "\n".join(f"  <code>{tid}</code>" for tid in task_ids),
                parse_mode=PARSE,
            )
            return

        task_id = context.args[0].strip()
        success = remove_task(task_id)

        if success:
            await update.message.reply_text(f"✅ <b>Task removed</b>\n\nID: <code>{task_id}</code>", parse_mode=PARSE)
        else:
            await update.message.reply_text(f"❌ Task not found: <code>{task_id}</code>", parse_mode=PARSE)

    # ── Admin / remote control ────────────────────────────────────

    async def _run_shell(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
        """Run a shell command asynchronously, return (returncode, stdout, stderr)."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=timeout),
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    async def _admin_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the status of all Agent Force services."""
        vaf = settings.base_dir / "vaf.sh"
        if not vaf.exists():
            await update.message.reply_text("❌ vaf.sh not found")
            return

        code, out, err = await _run_shell(["bash", str(vaf), "status"])
        # Strip ANSI colour codes for clean display
        import re as _re
        clean = _re.sub(r"\033\[[0-9;]*m", "", out or err)
        await update.message.reply_text(
            f"📊 <b>Service Status</b>\n\n<pre>{_e(clean.strip())}</pre>",
            parse_mode=PARSE,
        )

    async def _admin_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Restart all Agent Force services (dashboard + telegram + schedulers)."""
        vaf = settings.base_dir / "vaf.sh"
        if not vaf.exists():
            await update.message.reply_text("❌ vaf.sh not found")
            return

        await update.message.reply_text("🔄 Restarting all services...")

        # Use nohup + background so the bot restart doesn't kill our reply
        import subprocess
        subprocess.Popen(
            ["bash", "-c", f"sleep 2 && '{vaf}' restart"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        await update.message.reply_text(
            "✅ Restart triggered.\n"
            "Services will be back in ~5 seconds.\n"
            "Send /services to check status.",
        )

    async def _admin_rebuild(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Rebuild the React frontend and restart the dashboard."""
        vaf = settings.base_dir / "vaf.sh"
        if not vaf.exists():
            await update.message.reply_text("❌ vaf.sh not found")
            return

        msg = await update.message.reply_text("🔨 Rebuilding frontend...")

        code, out, err = await _run_shell(
            ["bash", str(vaf), "build"], timeout=120,
        )

        if code == 0:
            await msg.edit_text("✅ Frontend rebuilt! Restarting dashboard...")
            # Restart just the dashboard launchagent
            subprocess.Popen(
                ["bash", "-c",
                 "launchctl unload ~/Library/LaunchAgents/com.vaishali.agentforce.dashboard.plist 2>/dev/null;"
                 "sleep 1;"
                 "launchctl load ~/Library/LaunchAgents/com.vaishali.agentforce.dashboard.plist 2>/dev/null"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            await msg.edit_text("✅ Frontend rebuilt and dashboard restarted!")
        else:
            clean_err = err[:500] if err else "Unknown error"
            await msg.edit_text(f"❌ Build failed:\n<pre>{_e(clean_err)}</pre>", parse_mode=PARSE)

    async def _admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send the last 30 lines of the most recent log file."""
        log_dir = settings.base_dir / "logs"
        if not log_dir.exists():
            await update.message.reply_text("📋 No logs directory found.")
            return

        # Find the most recently modified log file
        logs = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            await update.message.reply_text("📋 No log files found.")
            return

        logfile = logs[0]
        lines = logfile.read_text(encoding="utf-8", errors="replace").strip().split("\n")
        tail = "\n".join(lines[-30:])

        await update.message.reply_text(
            f"📋 <b>{_e(logfile.name)}</b> (last 30 lines):\n\n<pre>{_e(tail[:3500])}</pre>",
            parse_mode=PARSE,
        )

    async def _cmd_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show LLM API usage and estimated cost for today."""
        from vaishali.core.llm_client import llm

        if not llm.has_keys():
            await update.message.reply_text(
                "⚙️ <b>LLM Usage</b>\n\n"
                "No Anthropic API keys configured.\n"
                "Set <code>VAF_ANTHROPIC_KEY_1</code> or <code>ANTHROPIC_API_KEY</code> to enable LLM features.",
                parse_mode=PARSE,
            )
            return

        usage = llm.get_usage_today()

        # Format usage breakdown
        msg = "⚙️ <b>LLM Usage (Today)</b>\n\n"
        msg += f"<b>Total Calls:</b> {usage['total_calls']}\n"
        msg += f"<b>Tokens:</b> {usage['total_tokens_in']:,} in / {usage['total_tokens_out']:,} out\n"
        msg += f"<b>Estimated Cost:</b> ${usage['total_cost_usd']:.4f}\n\n"

        # Breakdown by agent
        if usage["by_agent"]:
            msg += "<b>By Agent:</b>\n"
            for agent, stats in sorted(usage["by_agent"].items()):
                msg += (
                    f"  <b>{agent}:</b> {stats['calls']} calls, "
                    f"{stats['tokens_in']:,} in, "
                    f"${stats['cost_usd']:.4f}\n"
                )

        # Key status
        msg += "\n<b>Keys Status:</b>\n"
        for status in llm.keys_status():
            msg += (
                f"  <b>Key {status['index'] + 1}:</b> {status['call_count']} calls"
            )
            if status["last_used"] != "never":
                msg += f", last: {status['last_used'][:10]}"
            msg += "\n"

        await update.message.reply_text(msg, parse_mode=PARSE)

    # ── Build application ──────────────────────────────────────────

    from telegram.ext import MessageHandler, filters

    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("briefing", cmd_briefing))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("finance", _finance))
    application.add_handler(CommandHandler("health", _health))
    application.add_handler(CommandHandler("content", _content))
    application.add_handler(CommandHandler("education", _education))
    application.add_handler(CommandHandler("run_morning", _run_morning))
    application.add_handler(CommandHandler("run_evening", _run_evening))

    # Intake command handlers
    application.add_handler(CommandHandler("log", _handle_log))
    application.add_handler(CommandHandler("idea", _handle_idea))
    application.add_handler(CommandHandler("learn", _handle_learn))

    # Finance handlers
    application.add_handler(CommandHandler("spend", _handle_spend))
    application.add_handler(CommandHandler("import", _handle_import))

    # Braindump handlers
    application.add_handler(CommandHandler("dump", _handle_dump))
    application.add_handler(CommandHandler("thoughts", _handle_thoughts))

    # Drill-down shortcut commands
    application.add_handler(CommandHandler("anomalies", _cmd_anomalies))
    application.add_handler(CommandHandler("drafts", _cmd_drafts))
    application.add_handler(CommandHandler("ideas", _cmd_ideas))
    application.add_handler(CommandHandler("insights", _cmd_insights))
    application.add_handler(CommandHandler("review", _cmd_review))
    application.add_handler(CommandHandler("publish", _cmd_publish))

    # Scheduled tasks
    application.add_handler(CommandHandler("schedule", _cmd_schedule))
    application.add_handler(CommandHandler("schedules", _cmd_schedules))
    application.add_handler(CommandHandler("unschedule", _cmd_unschedule))

    # ── /save — Forward Claude Project output to Obsidian + Dashboard ──
    async def _handle_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save a Claude Project output drop — enriched by orchestrator.

        Usage:
          /save [optional title]
          [followed by the content on the next line]

        OR just paste the full Claude response as text prefixed with /save.

        The handler runs the full golden thread:
          detect agent → orchestrator (Claude Haiku enrichment) → Obsidian → Dashboard
        """
        from vaishali.captures.store import save_capture

        # Get everything after /save
        full_text = update.message.text or ""
        parts = full_text.split("\n", 1)
        header = parts[0].replace("/save", "").strip()
        content_body = parts[1].strip() if len(parts) > 1 else ""

        # If no body, check if this is a reply to a message
        if not content_body and update.message.reply_to_message:
            content_body = update.message.reply_to_message.text or ""

        if not content_body and not header:
            await update.message.reply_text(
                "📎 <b>SAVE TO VAULT</b>\n\n"
                "Usage: <code>/save</code> then paste the Claude output below, or reply to a Claude message with <code>/save</code>\n\n"
                "Or: <code>/save My Title Here\\n[content]</code>",
                parse_mode=PARSE,
            )
            return

        content = content_body or header
        title = header if (header and content_body) else None

        try:
            capture = save_capture(content=content, title=title, enrich=True)
            agent = capture["agent"]
            vault = capture["vault_path"]
            obsidian_ok = capture["obsidian_written"]
            revenue = capture["revenue_angle"]
            signal = capture.get("signal_rating", "🟡")
            is_enriched = capture.get("enriched", 0)
            summary = capture.get("summary", "")

            obsidian_icon = "🟢 Written to Obsidian" if obsidian_ok else "🟡 Saved to SQLite (Obsidian vault not reachable)"
            enriched_icon = "🧠 Enriched by orchestrator" if is_enriched else "⚡ Quick save (no LLM)"

            msg = (
                f"✅ <b>Captured → {_e(agent)}</b> {signal}\n\n"
                f"{enriched_icon}\n"
                f"📁 <code>{_e(vault)}</code>\n"
                f"{obsidian_icon}\n"
            )
            if summary and is_enriched:
                msg += f"\n📋 <i>{_e(summary[:200])}</i>\n"
            msg += f"\n{_e(revenue)}"

            await update.message.reply_text(msg, parse_mode=PARSE)
        except Exception as exc:
            log.exception("Save capture failed: %s", exc)
            await update.message.reply_text(
                f"❌ Save failed: {_e(str(exc))}",
                parse_mode=PARSE,
            )

    application.add_handler(CommandHandler("save", _handle_save))

    # ── /quick — Fast save without LLM enrichment ──
    async def _handle_quick_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Quick save — no LLM enrichment, just detect agent + store.
        /quick [content]
        """
        from vaishali.captures.store import save_capture_quick

        full_text = update.message.text or ""
        content = full_text.replace("/quick", "").strip()
        if not content and update.message.reply_to_message:
            content = update.message.reply_to_message.text or ""
        if not content:
            await update.message.reply_text(
                "⚡ <b>QUICK SAVE</b>\n\n<code>/quick [content]</code> — saves without LLM enrichment",
                parse_mode=PARSE,
            )
            return

        try:
            capture = save_capture_quick(content=content)
            await update.message.reply_text(
                f"⚡ <b>Quick saved → {_e(capture['agent'])}</b>\n"
                f"📁 <code>{_e(capture['vault_path'])}</code>",
                parse_mode=PARSE,
            )
        except Exception as exc:
            await update.message.reply_text(f"❌ Quick save failed: {_e(str(exc))}", parse_mode=PARSE)

    application.add_handler(CommandHandler("quick", _handle_quick_save))

    # ── /weekly — Sunday evening intelligence brief ──
    async def _handle_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Weekly intelligence brief — top insights, patterns, and actions."""
        from vaishali.insights.engine import generate_weekly_brief
        try:
            brief = generate_weekly_brief()
            await update.message.reply_text(brief, parse_mode=PARSE)
        except Exception as exc:
            log.exception("Weekly brief failed: %s", exc)
            await update.message.reply_text(
                f"❌ Weekly brief failed: {_e(str(exc))}",
                parse_mode=PARSE,
            )

    application.add_handler(CommandHandler("weekly", _handle_weekly))

    # /captures — quick summary of recent saves
    async def _handle_captures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from vaishali.captures.store import get_captures
        items = get_captures(limit=10)
        if not items:
            await update.message.reply_text("No captures yet. Use /save to drop Claude outputs.", parse_mode=PARSE)
            return
        lines = ["📎 <b>Recent Captures (last 10)</b>\n"]
        for c in items:
            ts = c["created_at"][:16].replace("T", " ")
            lines.append(f"<b>{_e(c['agent'])}</b> — {_e(c['title'][:50])}\n  <code>{ts}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode=PARSE)

    application.add_handler(CommandHandler("captures", _handle_captures))

    # ── Goggins 5 Non-Negotiables check-in ────────────────────────────────────
    async def _handle_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /checkin [BODY] [BUILD] [LEARN] [AMPLIFY] [BRIEF] [optional note]
        Scores 0–10 each. Example: /checkin 8 10 7 6 9 Great AWS lab today
        No args = show today's status.
        """
        from vaishali.checkins.store import (
            save_checkin, get_today_checkin, get_streak,
            NON_NEGOTIABLES, NEGOTIABLE_EMOJIS, NEGOTIABLE_DESCRIPTIONS,
            motivational_feedback,
        )

        args = context.args or []

        if not args:
            today = get_today_checkin()
            streak = get_streak()
            if today:
                lines = [f"📋 <b>Today's Non-Negotiables</b>  🔥 Streak: <b>{streak} days</b>\n"]
                for k in NON_NEGOTIABLES:
                    v = today["scores"][k]
                    bar = "█" * v + "░" * (10 - v)
                    lines.append(f"{NEGOTIABLE_EMOJIS[k]} <b>{k}</b>  {bar}  {v}/10")
                lines.append(f"\n<b>Total: {today['total']}/50</b>")
                lines.append(f"\n{motivational_feedback(today['total'])}")
            else:
                lines = ["📋 <b>No check-in yet today.</b>\n",
                         "Score your 5 Non-Negotiables (0–10 each):\n"]
                for k in NON_NEGOTIABLES:
                    lines.append(f"{NEGOTIABLE_EMOJIS[k]} <b>{k}</b> — {NEGOTIABLE_DESCRIPTIONS[k]}")
                lines.append(
                    "\nExample: <code>/checkin 8 10 7 6 9</code>"
                    f"\nOrder: {' · '.join(NEGOTIABLE_EMOJIS[k]+k for k in NON_NEGOTIABLES)}"
                )
            await update.message.reply_text("\n".join(lines), parse_mode=PARSE)
            return

        scores_raw: list[int] = []
        note_parts: list[str] = []
        for a in args:
            if len(scores_raw) < 5:
                try:
                    scores_raw.append(int(a))
                    continue
                except ValueError:
                    pass
            note_parts.append(a)

        if len(scores_raw) < 5:
            await update.message.reply_text(
                f"⚠️ Need 5 scores.\nExample: <code>/checkin 8 10 7 6 9</code>\n"
                f"Order: {' '.join(NEGOTIABLE_EMOJIS[k]+k for k in NON_NEGOTIABLES)}",
                parse_mode=PARSE,
            )
            return

        scores = dict(zip(NON_NEGOTIABLES, scores_raw[:5]))
        checkin = save_checkin(scores=scores, note=" ".join(note_parts))
        streak = get_streak()

        lines = [f"✅ <b>Check-in saved!</b>  🔥 Streak: <b>{streak} days</b>\n"]
        for k in NON_NEGOTIABLES:
            v = checkin["scores"][k]
            bar = "█" * v + "░" * (10 - v)
            lines.append(f"{NEGOTIABLE_EMOJIS[k]} <b>{k:<8}</b>  {bar}  {v}/10")
        lines.append(f"\n<b>Total: {checkin['total']}/50</b>")
        lines.append(f"\n{motivational_feedback(checkin['total'])}")
        if note_parts:
            lines.append(f"\n📝 <i>{_e(' '.join(note_parts))}</i>")

        await update.message.reply_text("\n".join(lines), parse_mode=PARSE)

    async def _handle_nonneg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/nonneg — show the 5 non-negotiables + scoring guide"""
        from vaishali.checkins.store import NON_NEGOTIABLES, NEGOTIABLE_EMOJIS, NEGOTIABLE_DESCRIPTIONS
        lines = ["🔥 <b>V's 5 Non-Negotiables — Goggins Protocol</b>\n"]
        for i, k in enumerate(NON_NEGOTIABLES, 1):
            lines.append(f"{i}. {NEGOTIABLE_EMOJIS[k]} <b>{k}</b>\n   {NEGOTIABLE_DESCRIPTIONS[k]}")
        lines.append(
            "\n📊 <b>Scoring:</b> 10 = crushed it · 5 = half measures · 0 = skipped"
            "\n🎯 <b>Streak target:</b> 25+/50 daily · Elite day: 45+/50"
            "\n\n<code>/checkin 8 10 7 6 9</code> to log scores"
        )
        await update.message.reply_text("\n".join(lines), parse_mode=PARSE)

    application.add_handler(CommandHandler("checkin", _handle_checkin))
    application.add_handler(CommandHandler("nonneg", _handle_nonneg))

    # System diagnostics
    application.add_handler(CommandHandler("check", _cmd_check))

    # Remote access
    application.add_handler(CommandHandler("webdash", _cmd_webdash))

    # Admin / remote control
    application.add_handler(CommandHandler("services", _admin_services))
    application.add_handler(CommandHandler("restart", _admin_restart))
    application.add_handler(CommandHandler("rebuild", _admin_rebuild))
    application.add_handler(CommandHandler("logs", _admin_logs))
    application.add_handler(CommandHandler("usage", _cmd_usage))

    # ── Global error handler — ensures ALL exceptions surface as a bot reply ──
    async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Catch unhandled exceptions and report them to the user so nothing vanishes silently."""
        err = context.error
        log.error("Unhandled exception in bot handler", exc_info=err)
        from telegram import Update as _Update
        if isinstance(update, _Update) and update.effective_message:
            short = _e(str(err)[:300]) if err else "unknown error"
            try:
                await update.effective_message.reply_text(
                    f"⚠️ <b>Bot error</b>\n\n<code>{short}</code>\n\n"
                    f"<i>Check logs with /logs for the full traceback.</i>",
                    parse_mode=PARSE,
                )
            except Exception:
                pass  # If reply itself fails, just log and move on

    application.add_error_handler(_error_handler)

    # Inline keyboard callback handler (button taps)
    from telegram.ext import CallbackQueryHandler
    from vaishali.telegram_bot.callbacks import handle_callback
    application.add_handler(CallbackQueryHandler(handle_callback))

    # File upload handler (CSV statements)
    application.add_handler(MessageHandler(filters.Document.ALL, _handle_document))

    # Photo handler (bank statements — fallback)
    application.add_handler(MessageHandler(filters.PHOTO, _handle_photo))

    # Plain text handler (auto-detect links)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text_message))

    # Schedule daily pushes if chat_id is configured
    if chat_id:
        jq = application.job_queue
        jq.run_daily(scheduled_briefing, time=time(hour=7, minute=0), name="morning_push")
        jq.run_daily(scheduled_evening, time=time(hour=21, minute=0), name="evening_push")
        log.info("Scheduled daily pushes to chat_id=%s (07:00 + 21:00)", chat_id)

    return application
