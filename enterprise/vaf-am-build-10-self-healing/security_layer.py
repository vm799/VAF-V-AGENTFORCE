"""
VAF AM Build 10 — Security Layer (MAESTRO-Inspired)
Prompt injection detection, PII scanning, audit trail validation, compliance checks.

Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Asset Management Series
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ─── Prompt injection patterns ────────────────────────────────────────────────

INJECTION_PATTERNS = [
    # Direct instruction override attempts
    (r"ignore\s+(all\s+)?previous\s+instructions?", "instruction_override"),
    (r"forget\s+(all\s+)?previous\s+(context|instructions?|rules?)", "instruction_override"),
    (r"disregard\s+(all\s+)?(above|previous|prior)", "instruction_override"),
    # Role hijacking
    (r"you\s+are\s+now\s+a", "role_hijack"),
    (r"act\s+as\s+(if\s+you\s+are\s+)?a?\s*(different|new)", "role_hijack"),
    (r"pretend\s+(to\s+be|you\s+are)", "role_hijack"),
    (r"switch\s+to\s+.*(mode|persona|role)", "role_hijack"),
    # System prompt extraction
    (r"(show|reveal|print|output|display)\s+(me\s+)?(your\s+)?(system\s+)?prompt", "prompt_extraction"),
    (r"what\s+(are|is)\s+your\s+(system\s+)?(instructions?|rules?|prompt)", "prompt_extraction"),
    (r"repeat\s+(the\s+)?(text|words?)\s+above", "prompt_extraction"),
    # Data exfiltration via prompt
    (r"(send|post|fetch|curl|wget)\s+.{0,30}https?://", "data_exfiltration"),
    (r"(encode|base64|hex)\s+.*\s+(and\s+)?(send|output)", "data_exfiltration"),
    # Jailbreak markers
    (r"DAN\s*(mode)?", "jailbreak"),
    (r"developer\s+mode", "jailbreak"),
    (r"(bypass|override|disable)\s+(safety|filter|guard|content)", "jailbreak"),
]

# ─── PII patterns ────────────────────────────────────────────────────────────

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_uk": r"\b(?:0|\+44)\s*\d[\d\s]{8,12}\b",
    "phone_international": r"\b\+\d{1,3}[\s-]?\d[\d\s-]{6,14}\b",
    "ni_number": r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
    "account_number_uk": r"\b\d{8}\b",  # UK bank account (8 digits)
    "sort_code": r"\b\d{2}-\d{2}-\d{2}\b",
    "credit_card": r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
    "postcode_uk": r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b",
}


class SecurityLayer:
    """MAESTRO-inspired security validation at every build boundary.

    Checks for prompt injection, PII leakage, audit trail integrity,
    and compliance with configurable rule sets (FCA, GDPR).
    """

    def __init__(self):
        self._compiled_injections = [
            (re.compile(pat, re.IGNORECASE), cat) for pat, cat in INJECTION_PATTERNS
        ]
        self._compiled_pii = {
            name: re.compile(pat, re.IGNORECASE if name != "ni_number" else 0)
            for name, pat in PII_PATTERNS.items()
        }
        self._findings: List[dict] = []

    def check_prompt_injection(self, text: str) -> dict:
        """Scan text for common prompt injection patterns before passing to LLM.

        Returns detection results with matched patterns and risk level.
        """
        detections: List[dict] = []

        for compiled_re, category in self._compiled_injections:
            matches = compiled_re.findall(text)
            if matches:
                for match in matches:
                    match_str = match if isinstance(match, str) else match[0]
                    detections.append({
                        "category": category,
                        "matched_text": match_str.strip(),
                        "pattern": compiled_re.pattern,
                    })

        is_suspicious = len(detections) > 0
        risk_level = "none"
        if len(detections) >= 3:
            risk_level = "critical"
        elif len(detections) >= 2:
            risk_level = "high"
        elif len(detections) == 1:
            risk_level = "medium"

        result = {
            "is_suspicious": is_suspicious,
            "risk_level": risk_level,
            "detections": detections,
            "detection_count": len(detections),
            "scanned_length": len(text),
            "scanned_at": datetime.utcnow().isoformat(),
        }

        if is_suspicious:
            self._findings.append({
                "type": "prompt_injection",
                "risk_level": risk_level,
                "count": len(detections),
            })

        return result

    def detect_pii(self, text: str) -> dict:
        """Find PII in text before external delivery.

        Detects emails, phone numbers, NI numbers, account numbers,
        sort codes, credit card numbers, and postcodes.
        """
        found: Dict[str, List[dict]] = {}
        total_count = 0

        for pii_type, compiled_re in self._compiled_pii.items():
            matches = compiled_re.findall(text)
            if matches:
                found[pii_type] = [
                    {
                        "value": _redact(m, pii_type),
                        "original_length": len(m),
                    }
                    for m in matches
                ]
                total_count += len(matches)

        has_pii = total_count > 0
        result = {
            "has_pii": has_pii,
            "total_pii_count": total_count,
            "pii_types_found": list(found.keys()),
            "details": found,
            "scanned_length": len(text),
            "scanned_at": datetime.utcnow().isoformat(),
        }

        if has_pii:
            self._findings.append({
                "type": "pii_detected",
                "count": total_count,
                "types": list(found.keys()),
            })

        return result

    def validate_audit_trail(self, staging_dir: str) -> dict:
        """Verify that an immutable log exists at every build boundary.

        Checks that each build (01-09) has produced a log or report file
        in the staging directory, ensuring no gaps in the audit trail.
        """
        staging = Path(staging_dir)
        expected_builds = list(range(1, 10))
        found_builds: List[int] = []
        missing_builds: List[int] = []
        build_logs: Dict[int, dict] = {}

        for build_num in expected_builds:
            # Look for logs in several naming conventions
            patterns = [
                f"build_{build_num:02d}*",
                f"build_{build_num}*",
                f"*build{build_num:02d}*",
                f"*build{build_num}*",
            ]

            log_found = False
            for pattern in patterns:
                matches = list(staging.glob(pattern)) if staging.exists() else []
                if matches:
                    log_found = True
                    log_file = matches[0]
                    build_logs[build_num] = {
                        "file": str(log_file),
                        "size_bytes": log_file.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            log_file.stat().st_mtime
                        ).isoformat(),
                    }
                    found_builds.append(build_num)
                    break

            if not log_found:
                missing_builds.append(build_num)

        is_complete = len(missing_builds) == 0
        result = {
            "is_complete": is_complete,
            "builds_found": found_builds,
            "builds_missing": missing_builds,
            "coverage": f"{len(found_builds)}/{len(expected_builds)}",
            "build_logs": build_logs,
            "validated_at": datetime.utcnow().isoformat(),
        }

        if not is_complete:
            self._findings.append({
                "type": "audit_trail_gap",
                "missing_builds": missing_builds,
            })

        return result

    def check_compliance(self, data: dict, rules_path: str) -> dict:
        """Validate data against configurable compliance rules (FCA, GDPR).

        Rules are loaded from a JSON file with the structure:
        {
            "rules": [
                {
                    "id": "FCA_FP_001",
                    "framework": "FCA",
                    "description": "...",
                    "check_type": "forbidden_phrase|required_field|max_length",
                    "parameters": {...}
                }
            ]
        }
        """
        rules_file = Path(rules_path)
        if not rules_file.exists():
            return {
                "compliant": True,
                "violations": [],
                "rules_checked": 0,
                "note": f"Rules file not found: {rules_path}",
                "checked_at": datetime.utcnow().isoformat(),
            }

        try:
            rules_data = json.loads(rules_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            return {
                "compliant": False,
                "violations": [],
                "rules_checked": 0,
                "error": f"Failed to load rules: {e}",
                "checked_at": datetime.utcnow().isoformat(),
            }

        rules = rules_data.get("rules", [])
        violations: List[dict] = []
        rules_checked = 0

        # Flatten data to searchable text
        text_content = _flatten_to_text(data)

        for rule in rules:
            rules_checked += 1
            rule_id = rule.get("id", "UNKNOWN")
            check_type = rule.get("check_type", "")
            params = rule.get("parameters", {})

            violation = None

            if check_type == "forbidden_phrase":
                phrases = params.get("phrases", [])
                for phrase in phrases:
                    if phrase.lower() in text_content.lower():
                        violation = {
                            "rule_id": rule_id,
                            "framework": rule.get("framework", ""),
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "matched_phrase": phrase,
                        }
                        break

            elif check_type == "required_field":
                fields = params.get("fields", [])
                for field in fields:
                    if field not in data or not data[field]:
                        violation = {
                            "rule_id": rule_id,
                            "framework": rule.get("framework", ""),
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "missing_field": field,
                        }
                        break

            elif check_type == "max_length":
                field = params.get("field", "")
                max_len = params.get("max_length", 0)
                value = data.get(field, "")
                if isinstance(value, str) and len(value) > max_len:
                    violation = {
                        "rule_id": rule_id,
                        "framework": rule.get("framework", ""),
                        "severity": rule.get("severity", "low"),
                        "description": rule.get("description", ""),
                        "field": field,
                        "actual_length": len(value),
                        "max_length": max_len,
                    }

            elif check_type == "pii_check":
                pii_result = self.detect_pii(text_content)
                if pii_result["has_pii"]:
                    violation = {
                        "rule_id": rule_id,
                        "framework": rule.get("framework", ""),
                        "severity": rule.get("severity", "high"),
                        "description": rule.get("description", ""),
                        "pii_types": pii_result["pii_types_found"],
                        "pii_count": pii_result["total_pii_count"],
                    }

            if violation:
                violations.append(violation)

        is_compliant = len(violations) == 0
        result = {
            "compliant": is_compliant,
            "violations": violations,
            "violation_count": len(violations),
            "rules_checked": rules_checked,
            "checked_at": datetime.utcnow().isoformat(),
        }

        if not is_compliant:
            self._findings.append({
                "type": "compliance_violation",
                "count": len(violations),
                "rule_ids": [v["rule_id"] for v in violations],
            })

        return result

    def get_security_report(self) -> dict:
        """Return a full security scan summary of all findings."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for finding in self._findings:
            risk = finding.get("risk_level", "medium")
            if risk in severity_counts:
                severity_counts[risk] += 1

            # Count compliance violations by severity
            if finding["type"] == "compliance_violation":
                severity_counts["high"] += finding.get("count", 0)

            if finding["type"] == "pii_detected":
                severity_counts["high"] += 1

            if finding["type"] == "audit_trail_gap":
                severity_counts["medium"] += 1

        overall_status = "pass"
        if severity_counts["critical"] > 0:
            overall_status = "fail"
        elif severity_counts["high"] > 0:
            overall_status = "warn"

        return {
            "overall_status": overall_status,
            "total_findings": len(self._findings),
            "severity_counts": severity_counts,
            "findings": self._findings,
            "generated_at": datetime.utcnow().isoformat(),
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _redact(value: str, pii_type: str) -> str:
    """Redact a PII value, keeping only enough to identify it."""
    if not value:
        return "***"
    if pii_type == "email":
        parts = value.split("@")
        if len(parts) == 2:
            return f"{parts[0][:2]}***@{parts[1]}"
    if pii_type in ("credit_card", "account_number_uk"):
        clean = value.replace(" ", "").replace("-", "")
        return f"***{clean[-4:]}"
    if pii_type == "ni_number":
        return f"{value[:2]}******{value[-1:]}"
    if pii_type in ("phone_uk", "phone_international"):
        clean = value.replace(" ", "").replace("-", "")
        return f"***{clean[-4:]}"
    return f"{value[:2]}***"


def _flatten_to_text(data, depth: int = 0) -> str:
    """Recursively flatten a dict/list into searchable text."""
    if depth > 10:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, (int, float, bool)):
        return str(data)
    if isinstance(data, list):
        return " ".join(_flatten_to_text(item, depth + 1) for item in data)
    if isinstance(data, dict):
        parts = []
        for key, value in data.items():
            parts.append(str(key))
            parts.append(_flatten_to_text(value, depth + 1))
        return " ".join(parts)
    return ""
