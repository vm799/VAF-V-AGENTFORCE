"""
VAF AM Build 10 — Self-Healing Health Monitor
Scans build logs, diagnoses failures, and generates config patches.

Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Asset Management Series
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional


# Known failure patterns and their auto-response strategies
FAILURE_PATTERNS = {
    "source_unreachable": {
        "signatures": [
            r"connection\s*(refused|timed?\s*out|reset)",
            r"source.*unreachable",
            r"failed\s+to\s+(fetch|connect|reach)",
            r"HTTPError.*5\d{2}",
            r"DNS\s*resolution\s*failed",
        ],
        "severity": "high",
        "auto_response": "reduce_source_weight",
        "description": "Data source could not be reached",
    },
    "high_quarantine_rate": {
        "signatures": [
            r"quarantine.*rate.*(?:3[0-9]|[4-9]\d|100)%",
            r"quarantined\s+(\d+)\s*/\s*(\d+)",
            r"sanitisation.*reject.*rate.*high",
        ],
        "severity": "high",
        "auto_response": "flag_schema_review",
        "description": "Sanitisation quarantine rate exceeds 30%",
    },
    "zero_patterns": {
        "signatures": [
            r"patterns?\s*(found|detected|extracted)\s*:\s*0\b",
            r"no\s+patterns?\s+(found|detected|extracted)",
            r"analysis.*produced?\s+0\s+results?",
            r"empty\s+pattern\s+set",
        ],
        "severity": "medium",
        "auto_response": "widen_thresholds",
        "description": "Analysis produced zero patterns",
    },
    "council_timeout": {
        "signatures": [
            r"council.*timeout",
            r"agent.*council.*exceeded.*time",
            r"LLM.*timeout",
            r"council.*deadline.*exceeded",
        ],
        "severity": "medium",
        "auto_response": "reduce_batch_size",
        "description": "Investment council exceeded time limit",
    },
    "delivery_failure": {
        "signatures": [
            r"delivery.*failed",
            r"channel.*unavailable",
            r"(telegram|slack|email).*error",
            r"distribution.*failed",
            r"send.*failed",
        ],
        "severity": "high",
        "auto_response": "switch_fallback_channel",
        "description": "Output delivery failed on one or more channels",
    },
}


class SelfHealingMonitor:
    """Scans pipeline logs, diagnoses failures, and generates config patches."""

    def __init__(self):
        self._compiled_patterns: dict = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for failure_type, info in FAILURE_PATTERNS.items():
            self._compiled_patterns[failure_type] = [
                re.compile(sig, re.IGNORECASE) for sig in info["signatures"]
            ]

    def scan_build_logs(self, logs_dir: str) -> List[dict]:
        """Read all build logs from a pipeline run directory.

        Scans for .log and .json files in the given directory.
        Returns a list of log entries with build number, timestamp, and content.
        """
        logs_path = Path(logs_dir)
        entries: List[dict] = []

        if not logs_path.exists():
            return entries

        log_files = sorted(
            list(logs_path.glob("*.log")) + list(logs_path.glob("*.json"))
        )

        for log_file in log_files:
            try:
                content = log_file.read_text(encoding="utf-8")

                # Try to parse as JSON first (structured logs)
                if log_file.suffix == ".json":
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            for item in data:
                                entries.append({
                                    "source_file": str(log_file),
                                    "build": _extract_build_number(log_file.name),
                                    "timestamp": item.get("timestamp", ""),
                                    "level": item.get("level", "INFO"),
                                    "message": item.get("message", str(item)),
                                    "raw": item,
                                })
                        elif isinstance(data, dict):
                            entries.append({
                                "source_file": str(log_file),
                                "build": _extract_build_number(log_file.name),
                                "timestamp": data.get("timestamp", ""),
                                "level": data.get("level", "INFO"),
                                "message": data.get("message", str(data)),
                                "raw": data,
                            })
                        continue
                    except json.JSONDecodeError:
                        pass

                # Plain text logs: one entry per line
                for line_num, line in enumerate(content.splitlines(), 1):
                    line = line.strip()
                    if not line:
                        continue
                    entries.append({
                        "source_file": str(log_file),
                        "build": _extract_build_number(log_file.name),
                        "line": line_num,
                        "level": _infer_log_level(line),
                        "message": line,
                    })

            except (OSError, UnicodeDecodeError) as e:
                entries.append({
                    "source_file": str(log_file),
                    "build": _extract_build_number(log_file.name),
                    "level": "ERROR",
                    "message": f"Failed to read log file: {e}",
                })

        return entries

    def diagnose_failures(self, logs: List[dict]) -> List[dict]:
        """Pattern-match log entries against known failure types.

        Returns a list of diagnoses, each containing the failure type,
        matched log entries, severity, and recommended auto-response.
        """
        diagnoses: List[dict] = []
        seen_types: dict = {}  # failure_type -> diagnosis index

        for entry in logs:
            message = entry.get("message", "")
            if not message:
                continue

            for failure_type, compiled_sigs in self._compiled_patterns.items():
                for pattern in compiled_sigs:
                    if pattern.search(message):
                        info = FAILURE_PATTERNS[failure_type]

                        if failure_type in seen_types:
                            # Append to existing diagnosis
                            idx = seen_types[failure_type]
                            diagnoses[idx]["matched_entries"].append(entry)
                            diagnoses[idx]["occurrence_count"] += 1
                        else:
                            diagnosis = {
                                "failure_type": failure_type,
                                "severity": info["severity"],
                                "description": info["description"],
                                "auto_response": info["auto_response"],
                                "matched_entries": [entry],
                                "occurrence_count": 1,
                                "diagnosed_at": datetime.utcnow().isoformat(),
                            }
                            seen_types[failure_type] = len(diagnoses)
                            diagnoses.append(diagnosis)
                        break  # One match per failure type per entry

        # Sort by severity (high first)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        diagnoses.sort(key=lambda d: severity_order.get(d["severity"], 99))

        return diagnoses

    def generate_patches(self, diagnoses: List[dict]) -> List[dict]:
        """Create config patches for each diagnosed issue.

        Each patch describes what config file to modify, what key to change,
        and what the new value should be.
        """
        patches: List[dict] = []

        for diagnosis in diagnoses:
            failure_type = diagnosis["failure_type"]
            response = diagnosis["auto_response"]

            if response == "reduce_source_weight":
                # Extract source name from log entries if possible
                source = _extract_source_name(diagnosis["matched_entries"])
                patches.append({
                    "failure_type": failure_type,
                    "target_file": "source_config.json",
                    "action": "reduce_weight",
                    "key": f"sources.{source}.weight",
                    "adjustment": -0.2,
                    "min_value": 0.1,
                    "reason": diagnosis["description"],
                    "alert_operator": True,
                })

            elif response == "flag_schema_review":
                source = _extract_source_name(diagnosis["matched_entries"])
                patches.append({
                    "failure_type": failure_type,
                    "target_file": "source_config.json",
                    "action": "flag_review",
                    "key": f"sources.{source}.needs_schema_review",
                    "value": True,
                    "reason": diagnosis["description"],
                    "alert_operator": True,
                })

            elif response == "widen_thresholds":
                patches.append({
                    "failure_type": failure_type,
                    "target_file": "analysis_config.json",
                    "action": "adjust_threshold",
                    "key": "pattern_detection.min_confidence",
                    "adjustment": -0.05,
                    "min_value": 0.3,
                    "reason": diagnosis["description"],
                    "alert_operator": False,
                })

            elif response == "reduce_batch_size":
                patches.append({
                    "failure_type": failure_type,
                    "target_file": "council_config.json",
                    "action": "reduce_batch",
                    "key": "council.batch_size",
                    "adjustment": -5,
                    "min_value": 1,
                    "reason": diagnosis["description"],
                    "alert_operator": False,
                })

            elif response == "switch_fallback_channel":
                patches.append({
                    "failure_type": failure_type,
                    "target_file": "delivery_config.json",
                    "action": "enable_fallback",
                    "key": "delivery.use_fallback",
                    "value": True,
                    "reason": diagnosis["description"],
                    "alert_operator": True,
                })

        return patches

    def apply_patches(self, patches: List[dict], config_dir: str) -> dict:
        """Write patches to config files. Returns a summary of changes made.

        Creates config files if they don't exist. Applies adjustments
        respecting min/max bounds. Never overwrites non-patch keys.
        """
        config_path = Path(config_dir)
        config_path.mkdir(parents=True, exist_ok=True)

        applied: List[dict] = []
        skipped: List[dict] = []
        alerts: List[str] = []

        for patch in patches:
            target = config_path / patch["target_file"]

            # Load existing config or start fresh
            config: dict = {}
            if target.exists():
                try:
                    config = json.loads(target.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    config = {}

            action = patch["action"]
            key_parts = patch["key"].split(".")

            try:
                if action in ("reduce_weight", "adjust_threshold", "reduce_batch"):
                    current = _nested_get(config, key_parts, default=1.0)
                    new_value = current + patch["adjustment"]
                    min_val = patch.get("min_value", 0)
                    new_value = max(new_value, min_val)
                    _nested_set(config, key_parts, new_value)

                    applied.append({
                        "file": patch["target_file"],
                        "key": patch["key"],
                        "old_value": current,
                        "new_value": new_value,
                        "reason": patch["reason"],
                    })

                elif action in ("flag_review", "enable_fallback"):
                    _nested_set(config, key_parts, patch["value"])
                    applied.append({
                        "file": patch["target_file"],
                        "key": patch["key"],
                        "value": patch["value"],
                        "reason": patch["reason"],
                    })

                # Write updated config
                target.write_text(
                    json.dumps(config, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

                if patch.get("alert_operator"):
                    alerts.append(
                        f"[{patch['failure_type']}] {patch['reason']} — "
                        f"patched {patch['key']}"
                    )

            except Exception as e:
                skipped.append({
                    "file": patch["target_file"],
                    "key": patch["key"],
                    "error": str(e),
                })

        return {
            "applied_count": len(applied),
            "skipped_count": len(skipped),
            "applied": applied,
            "skipped": skipped,
            "operator_alerts": alerts,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _extract_build_number(filename: str) -> Optional[str]:
    """Try to extract a build number from a filename like 'build_03.log'."""
    match = re.search(r"build[_-]?(\d{1,2})", filename, re.IGNORECASE)
    return match.group(1) if match else None


def _infer_log_level(line: str) -> str:
    """Infer log level from a plain-text log line."""
    upper = line.upper()
    if "ERROR" in upper or "FATAL" in upper or "CRITICAL" in upper:
        return "ERROR"
    if "WARN" in upper:
        return "WARN"
    if "DEBUG" in upper:
        return "DEBUG"
    return "INFO"


def _extract_source_name(entries: List[dict]) -> str:
    """Try to extract a data source name from matched log entries."""
    for entry in entries:
        msg = entry.get("message", "")
        match = re.search(r"source[:\s]+['\"]?(\w+)['\"]?", msg, re.IGNORECASE)
        if match:
            return match.group(1)
    return "unknown"


def _nested_get(d: dict, keys: List[str], default=None):
    """Get a value from a nested dict using a list of keys."""
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def _nested_set(d: dict, keys: List[str], value) -> None:
    """Set a value in a nested dict, creating intermediate dicts as needed."""
    current = d
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
