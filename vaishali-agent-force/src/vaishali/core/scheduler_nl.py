"""Natural language scheduled task parser and manager.

Converts natural language like "every weekday at 8am" to cron expressions.
Persists tasks to data/scheduled_tasks.json.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────

COMMANDS = {
    "morning_briefing",
    "evening_briefing",
    "finance_report",
    "health_check",
    "content_score",
    "braindump_summary",
    "custom_shell",
}

DAY_NAMES = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 0,
}

# ── Data model ──────────────────────────────────────────────────────


@dataclass
class ScheduledTask:
    """Represents a scheduled task with cron expression."""

    id: str  # uuid hex[:8]
    label: str  # human description, e.g. "morning briefing"
    command: str  # one of COMMANDS
    cron_expr: str  # e.g. "0 7 * * 1-5"
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run: str | None = None
    next_run: str | None = None  # ISO datetime computed from cron_expr

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScheduledTask:
        """Create from dict."""
        return cls(**data)


# ── Natural language parsing ────────────────────────────────────────


def parse_schedule(text: str) -> list[dict[str, str]]:
    """Parse natural language schedule description to cron expressions.

    Args:
        text: e.g. "every weekday at 7am morning briefing"

    Returns:
        List of dicts with {cron_expr, label, command}
        May return multiple entries for "twice daily 7am and 9pm"
    """
    text = text.lower().strip()
    results: list[dict[str, str]] = []

    # Check for multiple times (e.g., "twice daily" or "7am and 9pm")
    if " and " in text and any(
        time_word in text for time_word in ["am", "pm", "o'clock"]
    ):
        # Handle "twice daily at 7am and 9pm" pattern
        parts = text.split(" and ")
        if len(parts) == 2:
            # Parse first part normally
            first_part = parts[0].strip()
            # Extract time from second part
            second_part = parts[1].strip()

            # Get command and label
            command = _detect_command(text)
            label = _extract_label(text, command)

            # Parse first time
            cron1 = _parse_time_to_cron(first_part)
            if cron1:
                results.append({
                    "cron_expr": cron1,
                    "label": f"{label} (first)",
                    "command": command,
                })

            # Parse second time
            cron2 = _parse_time_to_cron(second_part)
            if cron2:
                results.append({
                    "cron_expr": cron2,
                    "label": f"{label} (second)",
                    "command": command,
                })

            if results:
                return results

    # Single time entry
    command = _detect_command(text)
    label = _extract_label(text, command)
    cron = _parse_time_to_cron(text)

    if cron:
        return [{"cron_expr": cron, "label": label, "command": command}]

    return []


def _parse_time_to_cron(text: str) -> str | None:
    """Extract time and frequency from text, return cron expression."""
    text = text.lower().strip()

    # Extract hour and minute
    hour, minute = _extract_time(text)
    if hour is None:
        return None

    # Determine frequency (day of week)
    dow = _extract_frequency(text)

    # Format cron: min hour dom month dow
    return f"{minute} {hour} * * {dow}"


def _extract_time(text: str) -> tuple[int | None, int]:
    """Extract hour and minute from text.

    Returns: (hour, minute) where hour is 0-23, minute is 0-59.
    Returns (None, 0) if time not found.
    """
    # Match "7am", "7:30am", "7:30", "noon", "midnight"
    patterns = [
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",  # "7:30am" or "7:30"
        r"(\d{1,2})\s*(am|pm)",  # "7am" or "7 am"
        r"(\d{1,2})(?:\s*o'clock)?",  # "7" or "7 o'clock"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if "noon" in text:
                return 12, 0
            if "midnight" in text:
                return 0, 0

            hour = int(match.group(1))
            minute = int(match.group(2)) if match.lastindex and match.lastindex >= 2 and match.group(2).isdigit() else 0

            # Handle AM/PM
            ampm = None
            if match.lastindex and match.lastindex >= 3:
                ampm = match.group(3)
            elif match.lastindex and match.lastindex >= 2 and match.group(2) in ("am", "pm"):
                ampm = match.group(2)

            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            if 0 <= hour < 24 and 0 <= minute < 60:
                return hour, minute

    # Special cases
    if "noon" in text:
        return 12, 0
    if "midnight" in text:
        return 0, 0
    if "morning" in text and "7" not in text and "8" not in text:
        return 7, 0
    if "evening" in text and "9" not in text and "21" not in text:
        return 21, 0

    return None, 0


def _extract_frequency(text: str) -> str:
    """Extract day-of-week from text.

    Returns: cron day-of-week field (0=Sunday, 1=Monday, ..., 6=Saturday)
             or "1-5" for weekdays, "*" for daily
    """
    text = text.lower()

    # Weekdays: mon-fri
    if "weekday" in text or "week day" in text:
        return "1-5"

    # Specific day
    for day_name, day_num in DAY_NAMES.items():
        if day_name in text:
            return str(day_num)

    # Every day (default)
    return "*"


def _detect_command(text: str) -> str:
    """Detect command from keywords in text."""
    text = text.lower()

    # Priority order: check specific keywords first, then broader ones
    keywords = [
        ("evening briefing", "evening_briefing"),
        ("evening", "evening_briefing"),
        ("morning briefing", "morning_briefing"),
        ("morning", "morning_briefing"),
        ("briefing", "morning_briefing"),
        ("finance", "finance_report"),
        ("spending", "finance_report"),
        ("health", "health_check"),
        ("content", "content_score"),
        ("score", "content_score"),
        ("braindump", "braindump_summary"),
        ("thoughts", "braindump_summary"),
    ]

    for keyword, command in keywords:
        if keyword in text:
            return command

    return "morning_briefing"  # Default


def _extract_label(text: str, command: str) -> str:
    """Extract human-readable label from text."""
    # Remove common words
    words_to_remove = {
        "every", "at", "on", "daily", "day", "weekday", "weekdays",
        "morning", "evening", "am", "pm", "o'clock", "and",
        "monday", "tuesday", "wednesday", "thursday", "friday",
        "saturday", "sunday", "run", "trigger", "execute",
    }

    words = [w for w in text.lower().split() if w not in words_to_remove and w not in COMMANDS]
    label = " ".join(words).strip()

    if not label:
        # Use command name as fallback
        label = command.replace("_", " ").title()

    return label


# ── Cron utilities ──────────────────────────────────────────────────


def get_next_run(cron_expr: str) -> datetime | None:
    """Compute next run time from cron expression.

    Args:
        cron_expr: Standard 5-field cron format "min hour dom month dow"

    Returns:
        Next datetime when this cron will trigger, or None if invalid
    """
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return None

        minute_field, hour_field, dom_field, month_field, dow_field = parts

        # For simplicity, iterate forward from now
        now = datetime.now()
        # Check up to 1 year in the future
        for days_ahead in range(366):
            test_time = now + timedelta(days=days_ahead)

            # Reset to start of day for easier checking
            test_time = test_time.replace(hour=0, minute=0, second=0, microsecond=0)

            # Try each hour and minute combination
            for hour in range(24):
                for minute in range(60):
                    test_dt = test_time.replace(hour=hour, minute=minute)

                    if _cron_matches(test_dt, minute_field, hour_field, dom_field, month_field, dow_field):
                        # Ensure it's in the future
                        if test_dt > now:
                            return test_dt

    except Exception as e:
        log.warning("Error computing next run for cron '%s': %s", cron_expr, e)

    return None


def _cron_matches(dt: datetime, min_field: str, hour_field: str, dom_field: str, month_field: str, dow_field: str) -> bool:
    """Check if datetime matches cron expression."""
    # Check minute
    if not _field_matches(dt.minute, min_field, 0, 59):
        return False

    # Check hour
    if not _field_matches(dt.hour, hour_field, 0, 23):
        return False

    # Check day of month
    if not _field_matches(dt.day, dom_field, 1, 31):
        return False

    # Check month
    if not _field_matches(dt.month, month_field, 1, 12):
        return False

    # Check day of week (0=Sunday, 6=Saturday)
    if not _field_matches((dt.weekday() + 1) % 7, dow_field, 0, 6):
        return False

    return True


def _field_matches(value: int, field: str, min_val: int, max_val: int) -> bool:
    """Check if a value matches a cron field."""
    # Wildcard
    if field == "*":
        return True

    # Range "1-5"
    if "-" in field:
        try:
            parts = field.split("-")
            start = int(parts[0])
            end = int(parts[1])
            return start <= value <= end
        except (ValueError, IndexError):
            return False

    # List "0,6" (day of week)
    if "," in field:
        try:
            values = [int(v.strip()) for v in field.split(",")]
            return value in values
        except ValueError:
            return False

    # Step */5 (every 5 minutes)
    if field.startswith("*/"):
        try:
            step = int(field[2:])
            return value % step == 0
        except ValueError:
            return False

    # Single value
    try:
        return value == int(field)
    except ValueError:
        return False


def cron_to_readable(cron_expr: str) -> str:
    """Convert cron expression to human-readable format."""
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return cron_expr

        minute, hour, dom, month, dow = parts

        # Build readable string
        if dow == "*":
            freq = "every day"
        elif dow == "1-5":
            freq = "every weekday"
        else:
            # Map day number to name
            day_map = {
                "0": "Sunday",
                "1": "Monday",
                "2": "Tuesday",
                "3": "Wednesday",
                "4": "Thursday",
                "5": "Friday",
                "6": "Saturday",
            }
            freq = f"every {day_map.get(dow, 'day')}"

        # Format time
        hour_int = int(hour)
        minute_int = int(minute)

        if hour_int == 0 and minute_int == 0:
            time_str = "midnight"
        elif hour_int == 12 and minute_int == 0:
            time_str = "noon"
        else:
            if hour_int > 12:
                period = "pm"
                display_hour = hour_int - 12
            elif hour_int == 12:
                period = "pm"
                display_hour = 12
            else:
                period = "am"
                display_hour = hour_int if hour_int != 0 else 12

            if minute_int == 0:
                time_str = f"{display_hour}{period}"
            else:
                time_str = f"{display_hour}:{minute_int:02d}{period}"

        return f"{freq} at {time_str}"

    except Exception:
        return cron_expr


# ── Task persistence ──────────────────────────────────────────────────


def _get_tasks_file() -> Path:
    """Get path to scheduled_tasks.json."""
    settings.ensure_dirs()
    return settings.data_dir / "scheduled_tasks.json"


def load_tasks() -> list[ScheduledTask]:
    """Load all scheduled tasks from disk."""
    tasks_file = _get_tasks_file()
    if not tasks_file.exists():
        return []

    try:
        data = json.loads(tasks_file.read_text())
        return [ScheduledTask.from_dict(t) for t in data]
    except Exception as e:
        log.error("Failed to load scheduled tasks: %s", e)
        return []


def save_tasks(tasks: list[ScheduledTask]) -> None:
    """Save all scheduled tasks to disk."""
    tasks_file = _get_tasks_file()
    tasks_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = [t.to_dict() for t in tasks]
        tasks_file.write_text(json.dumps(data, indent=2))
        log.info("Saved %d scheduled tasks", len(tasks))
    except Exception as e:
        log.error("Failed to save scheduled tasks: %s", e)


def add_task(task: ScheduledTask) -> ScheduledTask:
    """Add a new task and save."""
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    return task


def remove_task(task_id: str) -> bool:
    """Remove a task by ID and save."""
    tasks = load_tasks()
    original_count = len(tasks)
    tasks = [t for t in tasks if t.id != task_id]

    if len(tasks) < original_count:
        save_tasks(tasks)
        return True
    return False


def list_tasks() -> list[ScheduledTask]:
    """List all scheduled tasks."""
    return load_tasks()


def create_task(description: str, command: str | None = None) -> ScheduledTask | None:
    """Parse natural language description and create a task.

    Args:
        description: e.g. "every weekday at 7am morning briefing"
        command: Override detected command

    Returns:
        Created ScheduledTask or None if parsing failed
    """
    parsed_list = parse_schedule(description)
    if not parsed_list:
        return None

    parsed = parsed_list[0]  # Use first result
    if command:
        parsed["command"] = command

    task = ScheduledTask(
        id=uuid.uuid4().hex[:8],
        label=parsed["label"],
        command=parsed["command"],
        cron_expr=parsed["cron_expr"],
        next_run=get_next_run(parsed["cron_expr"]).isoformat()
        if get_next_run(parsed["cron_expr"])
        else None,
    )

    return add_task(task)


def write_launchagent(task: ScheduledTask, base_dir: Path | None = None) -> Path | None:
    """Create a LaunchAgent plist file for the task.

    Args:
        task: ScheduledTask to schedule
        base_dir: Base directory (defaults to ~/Library/LaunchAgents)

    Returns:
        Path to created plist file, or None if failed
    """
    if base_dir is None:
        base_dir = Path.home() / "Library" / "LaunchAgents"

    base_dir.mkdir(parents=True, exist_ok=True)

    # Generate plist file
    plist_path = base_dir / f"com.vaishali.agentforce.task.{task.id}.plist"

    # Map command to script path
    scripts_dir = settings.scripts_dir
    script_map = {
        "morning_briefing": "morning_briefing.sh",
        "evening_briefing": "evening_briefing.sh",
        "finance_report": "finance_report.sh",
        "health_check": "health_check.sh",
        "content_score": "content_score.sh",
        "braindump_summary": "braindump_summary.sh",
    }

    script_name = script_map.get(task.command, "custom.sh")
    script_path = scripts_dir / script_name

    # Parse cron to get StartCalendarInterval
    parts = task.cron_expr.split()
    minute = int(parts[0]) if parts[0] != "*" else 0
    hour = int(parts[1]) if parts[1] != "*" else 0
    dow = parts[4]

    # Build WeekDay list
    if dow == "*":
        weekdays = [0, 1, 2, 3, 4, 5, 6]
    elif dow == "1-5":
        weekdays = [1, 2, 3, 4, 5]
    else:
        try:
            weekdays = [int(dow)]
        except ValueError:
            weekdays = [0]

    # Build plist content
    intervals = "\n".join(
        f"""        <dict>
            <key>Minute</key>
            <integer>{minute}</integer>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Weekday</key>
            <integer>{wd}</integer>
        </dict>"""
        for wd in weekdays
    )

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vaishali.agentforce.task.{task.id}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{script_path}</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
{intervals}
    </array>
    <key>StandardOutPath</key>
    <string>{settings.base_dir}/logs/task.{task.id}.out.log</string>
    <key>StandardErrorPath</key>
    <string>{settings.base_dir}/logs/task.{task.id}.err.log</string>
</dict>
</plist>"""

    try:
        plist_path.write_text(plist_content)
        log.info("Created LaunchAgent plist: %s", plist_path)
        return plist_path
    except Exception as e:
        log.error("Failed to create LaunchAgent plist: %s", e)
        return None


def remove_launchagent(task_id: str) -> bool:
    """Remove a LaunchAgent plist file for a task.

    Args:
        task_id: ID of the task

    Returns:
        True if removed successfully
    """
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"com.vaishali.agentforce.task.{task_id}.plist"

    try:
        if plist_path.exists():
            plist_path.unlink()
            log.info("Removed LaunchAgent plist: %s", plist_path)
            return True
    except Exception as e:
        log.error("Failed to remove LaunchAgent plist: %s", e)

    return False
