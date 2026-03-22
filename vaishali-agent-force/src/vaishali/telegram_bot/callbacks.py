"""Telegram inline keyboard callbacks — drill-down into agent data from your phone.

This module provides:
  - Inline keyboard builders for briefings, anomalies, content drafts, education
  - CallbackQuery handler that routes button taps to the right action
  - Deep-link commands: /anomalies, /drafts, /insights, /ideas

All keyboards use a simple prefix-routing scheme:
  "fin:anomalies"     → list finance anomalies
  "fin:anom:3"        → show anomaly detail #3
  "fin:anom:3:ack"    → acknowledge anomaly #3
  "cnt:drafts"        → list content drafts
  "cnt:draft:abc123"  → show draft detail
  "cnt:approve:abc123"→ approve draft → status=ready
  "cnt:reject:abc123" → reject draft → status=idea
  "edu:insights"      → list education insights
  "edu:item:0"        → show education item detail
"""

from __future__ import annotations

import html
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger
from vaishali.core.summaries import read_summary

log = get_logger(__name__)

PARSE = "HTML"


def _e(text: Any) -> str:
    return html.escape(str(text))


# ── Keyboard builders ─────────────────────────────────────────────────

def briefing_keyboard():
    """Build inline keyboard with drill-down buttons for the daily briefing."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        [
            InlineKeyboardButton("🦉 Anomalies", callback_data="fin:anomalies"),
            InlineKeyboardButton("✍️ Drafts", callback_data="cnt:drafts"),
        ],
        [
            InlineKeyboardButton("📚 Insights", callback_data="edu:insights"),
            InlineKeyboardButton("💡 Top Ideas", callback_data="cnt:ideas"),
        ],
        [
            InlineKeyboardButton("🧠 Actions", callback_data="bd:actions"),
            InlineKeyboardButton("📊 Spending", callback_data="fin:spending"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def anomaly_list_keyboard(anomalies: list[dict]) -> Any:
    """Build keyboard with one button per anomaly (up to 8)."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for i, a in enumerate(anomalies[:8]):
        severity = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(a.get("severity", ""), "⚪")
        desc = a.get("description", "Unknown")[:25]
        amt = abs(a.get("amount", 0))
        buttons.append([
            InlineKeyboardButton(
                f"{severity} {desc} — £{amt:,.2f}",
                callback_data=f"fin:anom:{i}",
            )
        ])
    buttons.append([InlineKeyboardButton("« Back to briefing", callback_data="back:briefing")])
    return InlineKeyboardMarkup(buttons)


def anomaly_detail_keyboard(idx: int) -> Any:
    """Action buttons for a single anomaly."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Acknowledge", callback_data=f"fin:anom:{idx}:ack"),
            InlineKeyboardButton("🔍 Show Context", callback_data=f"fin:anom:{idx}:ctx"),
        ],
        [InlineKeyboardButton("« Back to list", callback_data="fin:anomalies")],
    ])


def draft_list_keyboard(drafts: list) -> Any:
    """Build keyboard with one button per content draft needing review."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for item in drafts[:8]:
        title = item.title[:30] if hasattr(item, "title") else str(item.get("title", ""))[:30]
        item_id = item.id if hasattr(item, "id") else item.get("id", "")
        buttons.append([
            InlineKeyboardButton(f"📝 {title}", callback_data=f"cnt:draft:{item_id}")
        ])
    if not drafts:
        buttons.append([InlineKeyboardButton("💡 View Ideas Instead", callback_data="cnt:ideas")])
    buttons.append([InlineKeyboardButton("« Back", callback_data="back:briefing")])
    return InlineKeyboardMarkup(buttons)


def draft_action_keyboard(item_id: str) -> Any:
    """Approve / reject / edit buttons for a single draft."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"cnt:approve:{item_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"cnt:reject:{item_id}"),
        ],
        [
            InlineKeyboardButton("📝 Move to Drafting", callback_data=f"cnt:todraft:{item_id}"),
        ],
        [InlineKeyboardButton("« Back to drafts", callback_data="cnt:drafts")],
    ])


def idea_list_keyboard(ideas: list) -> Any:
    """Top content ideas with action buttons."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for item in ideas[:6]:
        title = item.title[:28] if hasattr(item, "title") else str(item)[:28]
        item_id = item.id if hasattr(item, "id") else ""
        impact = item.impact_estimate if hasattr(item, "impact_estimate") else 5
        buttons.append([
            InlineKeyboardButton(
                f"{'⭐' * min(3, impact // 3)} {title}",
                callback_data=f"cnt:idea:{item_id}",
            )
        ])
    buttons.append([InlineKeyboardButton("« Back", callback_data="back:briefing")])
    return InlineKeyboardMarkup(buttons)


def education_list_keyboard(insights: list[dict]) -> Any:
    """Education insights with detail buttons."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for i, item in enumerate(insights[:6]):
        title = item.get("title", "Untitled")[:30]
        buttons.append([
            InlineKeyboardButton(f"📖 {title}", callback_data=f"edu:item:{i}")
        ])
    buttons.append([InlineKeyboardButton("« Back", callback_data="back:briefing")])
    return InlineKeyboardMarkup(buttons)


# ── Callback query router ─────────────────────────────────────────────

async def handle_callback(update, context) -> None:
    """Route all inline keyboard button taps."""
    query = update.callback_query
    await query.answer()  # acknowledge the tap instantly

    data = query.data or ""
    log.info("Callback: %s", data)

    try:
        if data == "back:briefing":
            await _show_briefing(query)
        elif data == "fin:anomalies":
            await _show_anomalies(query)
        elif data.startswith("fin:anom:"):
            await _handle_anomaly(query, data)
        elif data == "fin:spending":
            await _show_spending(query)
        elif data == "cnt:drafts":
            await _show_drafts(query)
        elif data.startswith("cnt:draft:"):
            await _show_draft_detail(query, data)
        elif data.startswith("cnt:approve:"):
            await _approve_draft(query, data)
        elif data.startswith("cnt:reject:"):
            await _reject_draft(query, data)
        elif data.startswith("cnt:todraft:"):
            await _move_to_drafting(query, data)
        elif data == "cnt:ideas":
            await _show_ideas(query)
        elif data.startswith("cnt:idea:"):
            await _show_idea_detail(query, data)
        elif data == "edu:insights":
            await _show_education(query)
        elif data.startswith("edu:item:"):
            await _show_education_item(query, data)
        elif data == "bd:actions":
            await _show_braindump_actions(query)
        else:
            await query.edit_message_text(f"Unknown action: {_e(data)}", parse_mode=PARSE)
    except Exception as e:
        log.exception("Callback error for %s", data)
        err_msg = _e(str(e)[:200])
        await query.edit_message_text(f"❌ Error: {err_msg}", parse_mode=PARSE)


# ── Callback implementations ──────────────────────────────────────────

async def _show_briefing(query) -> None:
    """Return to main briefing view."""
    from vaishali.telegram_bot.bot import format_briefing, load_today_briefing

    briefing = load_today_briefing()
    if briefing:
        await query.edit_message_text(
            format_briefing(briefing),
            parse_mode=PARSE,
            reply_markup=briefing_keyboard(),
        )
    else:
        await query.edit_message_text("No briefing yet — run /run_morning first.")


async def _show_anomalies(query) -> None:
    """Show finance anomaly list with detail buttons."""
    summary = read_summary("finance", date.today())
    anomalies = (summary or {}).get("anomalies", [])

    if not anomalies:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await query.edit_message_text(
            "🦉 <b>Finance Anomalies</b>\n\n✅ No anomalies detected today!",
            parse_mode=PARSE,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="back:briefing")]
            ]),
        )
        return

    lines = [f"🦉 <b>Finance Anomalies</b> — {len(anomalies)} flagged\n"]
    for i, a in enumerate(anomalies[:8]):
        severity = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(a.get("severity", ""), "⚪")
        lines.append(
            f"{i + 1}. {severity} <b>{_e(a.get('description', '')[:35])}</b>\n"
            f"   £{abs(a.get('amount', 0)):,.2f} — {_e(a.get('reason', ''))}"
        )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=PARSE,
        reply_markup=anomaly_list_keyboard(anomalies),
    )


async def _handle_anomaly(query, data: str) -> None:
    """Handle anomaly detail or action."""
    parts = data.split(":")
    idx = int(parts[2])

    summary = read_summary("finance", date.today())
    anomalies = (summary or {}).get("anomalies", [])

    if idx >= len(anomalies):
        await query.edit_message_text("Anomaly not found.")
        return

    a = anomalies[idx]

    # Action: acknowledge
    if len(parts) > 3 and parts[3] == "ack":
        # Mark as acknowledged in the summary
        a["acknowledged"] = True
        _write_summary("finance", summary)
        await query.edit_message_text(
            f"✅ Acknowledged: {_e(a.get('description', ''))}",
            parse_mode=PARSE,
            reply_markup=anomaly_list_keyboard(anomalies),
        )
        return

    # Action: show context (recent transactions from same merchant)
    if len(parts) > 3 and parts[3] == "ctx":
        desc = a.get("description", "")
        ctx_lines = [f"🔍 <b>Context for:</b> {_e(desc)}\n"]

        try:
            from vaishali.finance.analytics import detect_recurring
            recurring = detect_recurring(min_occurrences=2)
            matches = [r for r in recurring if desc.lower() in r.get("description", "").lower()]
            if matches:
                for m in matches[:3]:
                    ctx_lines.append(
                        f"  Seen {m['count']}x, avg £{abs(m['avg_amount']):,.2f}, "
                        f"last: {m.get('last_date', 'unknown')}"
                    )
            else:
                ctx_lines.append("  No recurring pattern found — this may be a new merchant.")
        except Exception:
            ctx_lines.append("  Could not load transaction history.")

        await query.edit_message_text(
            "\n".join(ctx_lines),
            parse_mode=PARSE,
            reply_markup=anomaly_detail_keyboard(idx),
        )
        return

    # Default: show detail
    severity = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(a.get("severity", ""), "⚪")
    detail = (
        f"{severity} <b>Anomaly #{idx + 1}</b>\n\n"
        f"📅 Date: {_e(a.get('date', 'Unknown'))}\n"
        f"🏪 Merchant: <b>{_e(a.get('description', ''))}</b>\n"
        f"💷 Amount: £{abs(a.get('amount', 0)):,.2f}\n"
        f"⚠️ Reason: {_e(a.get('reason', ''))}\n"
        f"📊 Severity: {_e(a.get('severity', 'unknown'))}"
    )
    ack_status = "  ✅ <i>Acknowledged</i>" if a.get("acknowledged") else ""

    await query.edit_message_text(
        detail + ack_status,
        parse_mode=PARSE,
        reply_markup=anomaly_detail_keyboard(idx),
    )


async def _show_spending(query) -> None:
    """Show today's spending summary with category breakdown."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    summary = read_summary("finance", date.today())
    accounts = (summary or {}).get("accounts", [])

    lines = ["🦉 <b>Spending Overview</b>\n"]

    total = (summary or {}).get("total_balance_gbp")
    if total is not None:
        lines.append(f"💰 Total Balance: <b>£{total:,.2f}</b>\n")

    for acc in accounts:
        net7 = acc.get("net_7d", 0)
        arrow = "📈" if net7 >= 0 else "📉"
        lines.append(
            f"  <b>{_e(acc['id'])}</b>: £{acc['balance']:,.2f}  "
            f"{arrow} £{abs(net7):,.2f} (7d)"
        )

    if not accounts:
        lines.append("No account data yet. Upload a CSV or photo first!")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=PARSE,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🦉 Anomalies", callback_data="fin:anomalies"),
                InlineKeyboardButton("« Back", callback_data="back:briefing"),
            ]
        ]),
    )


async def _show_drafts(query) -> None:
    """Show content drafts awaiting review."""
    from vaishali.content.backlog import get_drafts_waiting_review

    drafts = get_drafts_waiting_review()

    if not drafts:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await query.edit_message_text(
            "✍️ <b>Content Drafts</b>\n\n"
            "No drafts waiting for review.\n"
            "Use /idea to add content ideas, then promote them to drafting.",
            parse_mode=PARSE,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💡 View Ideas", callback_data="cnt:ideas"),
                    InlineKeyboardButton("« Back", callback_data="back:briefing"),
                ]
            ]),
        )
        return

    lines = [f"✍️ <b>Content Drafts</b> — {len(drafts)} awaiting review\n"]
    for d in drafts[:8]:
        type_emoji = {"linkedin": "💼", "long_form": "📄", "video_script": "🎬"}.get(d.type, "📝")
        lines.append(f"  {type_emoji} <b>{_e(d.title[:40])}</b> → {_e(d.target_channel)}")

    lines.append("\nTap a draft to review and approve/reject:")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=PARSE,
        reply_markup=draft_list_keyboard(drafts),
    )


async def _show_draft_detail(query, data: str) -> None:
    """Show full detail of a single content draft."""
    item_id = data.split(":")[-1]

    from vaishali.content.backlog import load_backlog
    items = load_backlog()
    item = next((i for i in items if i.id == item_id), None)

    if not item:
        await query.edit_message_text(f"Draft {item_id} not found.")
        return

    type_emoji = {"linkedin": "💼", "long_form": "📄", "video_script": "🎬"}.get(item.type, "📝")
    detail = (
        f"{type_emoji} <b>{_e(item.title[:60])}</b>\n\n"
        f"Type: {_e(item.type)}\n"
        f"Channel: {_e(item.target_channel)}\n"
        f"Status: <b>{_e(item.status)}</b>\n"
        f"Effort: {_e(item.effort_estimate)} | Impact: {item.impact_estimate}/10\n"
    )
    if item.tags:
        detail += f"Tags: {_e(', '.join(item.tags))}\n"
    if item.notes:
        detail += f"\n📋 Notes:\n{_e(item.notes[:500])}\n"

    detail += "\n<b>What would you like to do?</b>"

    await query.edit_message_text(
        detail,
        parse_mode=PARSE,
        reply_markup=draft_action_keyboard(item_id),
    )


async def _approve_draft(query, data: str) -> None:
    """Approve a draft → move to 'ready' status."""
    item_id = data.split(":")[-1]

    from vaishali.content.backlog import update_item
    item = update_item(item_id, status="ready")

    if item:
        await query.edit_message_text(
            f"✅ <b>Approved!</b> '{_e(item.title[:50])}' is now <b>ready</b> to publish.\n\n"
            f"When you publish it, mark as published with:\n"
            f"<code>/publish {item_id}</code>",
            parse_mode=PARSE,
            reply_markup=draft_list_keyboard([]),  # refresh to show remaining
        )
    else:
        await query.edit_message_text(f"❌ Could not find draft {item_id}")


async def _reject_draft(query, data: str) -> None:
    """Reject a draft → move back to 'idea' status."""
    item_id = data.split(":")[-1]

    from vaishali.content.backlog import update_item
    item = update_item(item_id, status="idea")

    if item:
        await query.edit_message_text(
            f"↩️ Moved '{_e(item.title[:50])}' back to <b>ideas</b>.\n"
            f"It will be re-prioritised in the next content scoring run.",
            parse_mode=PARSE,
        )
    else:
        await query.edit_message_text(f"❌ Could not find draft {item_id}")


async def _move_to_drafting(query, data: str) -> None:
    """Move an idea to 'drafting' status."""
    item_id = data.split(":")[-1]

    from vaishali.content.backlog import update_item
    item = update_item(item_id, status="drafting")

    if item:
        await query.edit_message_text(
            f"📝 '{_e(item.title[:50])}' is now in <b>drafting</b>.\n"
            f"Work on it, then send /review {item_id} when ready for review.",
            parse_mode=PARSE,
        )
    else:
        await query.edit_message_text(f"❌ Could not find item {item_id}")


async def _show_ideas(query) -> None:
    """Show top content ideas ranked by score."""
    from vaishali.content.backlog import get_ideas

    ideas = get_ideas()

    if not ideas:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await query.edit_message_text(
            "💡 <b>Content Ideas</b>\n\nNo ideas yet! Use /idea to add some.",
            parse_mode=PARSE,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="back:briefing")]
            ]),
        )
        return

    lines = [f"💡 <b>Top Content Ideas</b> — {len(ideas)} total\n"]
    for i, idea in enumerate(ideas[:6], 1):
        type_emoji = {"linkedin": "💼", "long_form": "📄", "video_script": "🎬"}.get(idea.type, "📝")
        stars = "⭐" * min(3, idea.impact_estimate // 3)
        lines.append(
            f"{i}. {type_emoji} {stars} <b>{_e(idea.title[:40])}</b>\n"
            f"   Effort: {idea.effort_estimate} | Impact: {idea.impact_estimate}/10"
        )

    lines.append("\nTap an idea to start working on it:")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=PARSE,
        reply_markup=idea_list_keyboard(ideas),
    )


async def _show_idea_detail(query, data: str) -> None:
    """Show idea detail with action to move to drafting."""
    item_id = data.split(":")[-1]

    from vaishali.content.backlog import load_backlog
    items = load_backlog()
    item = next((i for i in items if i.id == item_id), None)

    if not item:
        await query.edit_message_text(f"Idea {item_id} not found.")
        return

    detail = (
        f"💡 <b>{_e(item.title[:60])}</b>\n\n"
        f"Type: {_e(item.type)} → {_e(item.target_channel)}\n"
        f"Impact: {'⭐' * min(5, item.impact_estimate // 2)} ({item.impact_estimate}/10)\n"
        f"Effort: {_e(item.effort_estimate)}\n"
    )
    if item.notes:
        detail += f"\n📋 {_e(item.notes[:400])}\n"

    detail += "\nReady to start working on this?"

    await query.edit_message_text(
        detail,
        parse_mode=PARSE,
        reply_markup=draft_action_keyboard(item_id),
    )


async def _show_education(query) -> None:
    """Show today's education insights."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    summary = read_summary("education", date.today())

    if not summary:
        await query.edit_message_text(
            "📚 <b>Education Insights</b>\n\n"
            "No learning data today.\n"
            "Drop a YouTube/article link, or use /learn to add content!",
            parse_mode=PARSE,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="back:briefing")]
            ]),
        )
        return

    items_processed = summary.get("items_processed", 0)
    top_topics = summary.get("top_topics", [])
    insights = summary.get("insights", [])

    lines = [
        f"📚 <b>Education Insights</b> — {items_processed} items processed\n",
    ]

    if top_topics:
        lines.append(f"🏷 <b>Topics:</b> {_e(', '.join(top_topics[:8]))}\n")

    if insights:
        lines.append("<b>Key Insights:</b>")
        for i, ins in enumerate(insights[:6]):
            title = ins.get("title", "")[:40] if isinstance(ins, dict) else str(ins)[:40]
            lines.append(f"  {i + 1}. {_e(title)}")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=PARSE,
        reply_markup=education_list_keyboard(insights if isinstance(insights, list) else []),
    )


async def _show_education_item(query, data: str) -> None:
    """Show detail of a single education insight."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    idx = int(data.split(":")[-1])
    summary = read_summary("education", date.today())
    insights = (summary or {}).get("insights", [])

    if idx >= len(insights):
        await query.edit_message_text("Insight not found.")
        return

    item = insights[idx]

    if isinstance(item, dict):
        title = item.get("title", "Untitled")
        summary_text = item.get("summary", item.get("content", "No details available."))
        entities = item.get("key_entities", [])
        topics = item.get("key_topics", [])

        detail = f"📖 <b>{_e(title[:60])}</b>\n\n"
        detail += f"{_e(summary_text[:800])}\n"
        if entities:
            detail += f"\n🏷 Entities: {_e(', '.join(entities[:10]))}"
        if topics:
            detail += f"\n📌 Topics: {_e(', '.join(topics[:10]))}"
    else:
        detail = f"📖 {_e(str(item)[:800])}"

    await query.edit_message_text(
        detail,
        parse_mode=PARSE,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("« Back to insights", callback_data="edu:insights")]
        ]),
    )


async def _show_braindump_actions(query) -> None:
    """Show active braindump actions."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    try:
        from vaishali.braindump.storage import get_active_actions, get_stats
        actions = get_active_actions()
        stats = get_stats()
    except Exception:
        actions = []
        stats = {}

    lines = ["🧠 <b>Braindump Actions</b>\n"]

    total = stats.get("total", 0)
    today_count = stats.get("today", 0)
    lines.append(f"📊 {total} total thoughts, {today_count} today\n")

    if actions:
        priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "someday": "⚪"}
        for a in actions[:8]:
            p = priority_emoji.get(a.priority, "⚪")
            when = f" (by {a.when})" if a.when else ""
            lines.append(f"  {p} {_e(a.title[:40])}{when}")
    else:
        lines.append("✅ No pending actions! Use /dump to capture thoughts.")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=PARSE,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("« Back", callback_data="back:briefing")]
        ]),
    )


# ── Helper ─────────────────────────────────────────────────────────────

def _write_summary(agent: str, data: dict) -> None:
    """Write updated summary back to disk."""
    today = date.today()
    path = settings.summaries_dir / agent / f"{today.isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
