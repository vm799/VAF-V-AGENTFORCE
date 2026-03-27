"""
VAF AM Build 10 — Self-Healing Loop
Closes the feedback loop for the 9-build enterprise pipeline.
Runs health monitor, feedback engine, and security layer in sequence.

Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Asset Management Series

Usage: uv run python run.py
       uv run python run.py --pipeline-dir ../outputs --config-dir ../config
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from health_monitor import SelfHealingMonitor
from feedback_engine import FeedbackEngine
from security_layer import SecurityLayer


def run_self_healing(
    pipeline_run_dir: str,
    config_dir: str,
    rules_path: Optional[str] = None,
) -> dict:
    """Orchestrate all three Build 10 components in sequence.

    1. Health Monitor — scan logs, diagnose failures, generate and apply patches
    2. Feedback Engine — score sources, update weights, tune thresholds
    3. Security Layer — check audit trail, run compliance checks

    Args:
        pipeline_run_dir: Root directory of the pipeline run (contains logs/,
                          staging/, reports/, insights/ subdirectories).
        config_dir: Directory where config files live and patches are written.
        rules_path: Optional path to compliance rules JSON file.

    Returns:
        Combined report with patches applied, quality scores, and security findings.
    """
    run_dir = Path(pipeline_run_dir)
    cfg_dir = Path(config_dir)

    print("=" * 60)
    print("  VAF AM Build 10 — Self-Healing Loop")
    print(f"  Started: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    report: dict = {
        "build": 10,
        "name": "Self-Healing Loop",
        "started_at": datetime.utcnow().isoformat(),
    }

    # ─── Phase 1: Health Monitor ──────────────────────────────────────────

    print("\n[1/3] Health Monitor")
    print("-" * 40)

    monitor = SelfHealingMonitor()

    logs_dir = run_dir / "logs"
    logs = monitor.scan_build_logs(str(logs_dir))
    print(f"  Scanned {len(logs)} log entries")

    diagnoses = monitor.diagnose_failures(logs)
    print(f"  Diagnosed {len(diagnoses)} failure patterns")
    for d in diagnoses:
        print(f"    [{d['severity'].upper()}] {d['failure_type']}: "
              f"{d['occurrence_count']} occurrences")

    patches = monitor.generate_patches(diagnoses)
    print(f"  Generated {len(patches)} config patches")

    patch_summary = monitor.apply_patches(patches, str(cfg_dir))
    print(f"  Applied {patch_summary['applied_count']} patches "
          f"({patch_summary['skipped_count']} skipped)")

    if patch_summary["operator_alerts"]:
        print("  Operator alerts:")
        for alert in patch_summary["operator_alerts"]:
            print(f"    ! {alert}")

    report["health_monitor"] = {
        "logs_scanned": len(logs),
        "diagnoses": diagnoses,
        "patches_generated": len(patches),
        "patch_summary": patch_summary,
    }

    # ─── Phase 2: Feedback Engine ─────────────────────────────────────────

    print("\n[2/3] Feedback Engine")
    print("-" * 40)

    feedback = FeedbackEngine()

    staging_dir = run_dir / "staging"
    quality_scores = feedback.score_source_quality(str(staging_dir))
    print(f"  Scored {quality_scores['source_count']} data sources")
    for source, score in quality_scores.get("scores", {}).items():
        print(f"    {source}: quality={score['quality_score']:.3f} "
              f"(survival={score['survival_rate']:.1%})")

    source_config_path = cfg_dir / "source_config.json"
    weight_updates = feedback.update_source_weights(
        quality_scores, str(source_config_path)
    )
    print(f"  Updated {len(weight_updates['updates'])} source weights")
    if weight_updates["flagged_sources"]:
        print(f"  Flagged sources: {', '.join(weight_updates['flagged_sources'])}")

    insights_dir = run_dir / "insights"
    analysis_config_path = cfg_dir / "analysis_config.json"
    threshold_updates = feedback.tune_thresholds(
        str(insights_dir), str(analysis_config_path)
    )
    print(f"  Analysed {threshold_updates['total_insights_analysed']} insights")
    print(f"  Threshold adjustments: {len(threshold_updates['adjustments'])}")

    feedback_report = feedback.get_feedback_report()

    report["feedback_engine"] = {
        "quality_scores": quality_scores,
        "weight_updates": weight_updates,
        "threshold_updates": threshold_updates,
        "feedback_summary": feedback_report,
    }

    # ─── Phase 3: Security Layer ──────────────────────────────────────────

    print("\n[3/3] Security Layer")
    print("-" * 40)

    security = SecurityLayer()

    # Validate audit trail
    audit_result = security.validate_audit_trail(str(run_dir / "reports"))
    print(f"  Audit trail: {audit_result['coverage']} builds logged "
          f"({'complete' if audit_result['is_complete'] else 'GAPS FOUND'})")

    # Run compliance check if rules file exists
    effective_rules_path = rules_path or str(cfg_dir / "maestro-rules.json")
    compliance_data = _load_pipeline_outputs(run_dir)
    compliance_result = security.check_compliance(compliance_data, effective_rules_path)
    print(f"  Compliance: {compliance_result['rules_checked']} rules checked, "
          f"{compliance_result['violation_count']} violations")

    security_report = security.get_security_report()
    print(f"  Security status: {security_report['overall_status'].upper()}")

    report["security_layer"] = {
        "audit_trail": audit_result,
        "compliance": compliance_result,
        "security_report": security_report,
    }

    # ─── Final Summary ────────────────────────────────────────────────────

    report["completed_at"] = datetime.utcnow().isoformat()
    report["status"] = "complete"

    print("\n" + "=" * 60)
    print("  Build 10 Complete")
    print(f"  Patches applied: {patch_summary['applied_count']}")
    print(f"  Sources scored: {quality_scores['source_count']}")
    print(f"  Security status: {security_report['overall_status'].upper()}")
    print(f"  Total findings: {security_report['total_findings']}")
    print("=" * 60)

    # Save report
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "build_10.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"\n  Report saved: {report_path}")

    return report


def _load_pipeline_outputs(run_dir: Path) -> dict:
    """Load pipeline output data for compliance checking."""
    outputs: dict = {"texts": [], "records": []}

    # Collect text content from reports and outputs
    for pattern in ["reports/*.json", "outputs/*.json", "staging/*.json"]:
        for f in run_dir.glob(pattern):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    outputs["records"].append(data)
                    # Extract any text fields for scanning
                    for key in ("body", "text", "content", "message", "summary"):
                        if key in data and isinstance(data[key], str):
                            outputs["texts"].append(data[key])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            outputs["records"].append(item)
            except (json.JSONDecodeError, OSError):
                continue

    return outputs


def main():
    parser = argparse.ArgumentParser(
        description="VAF AM Build 10 — Self-Healing Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--pipeline-dir",
        default=str(Path(__file__).parent.parent / "outputs"),
        help="Root directory of the pipeline run (default: ../outputs)",
    )
    parser.add_argument(
        "--config-dir",
        default=str(Path(__file__).parent.parent / "config"),
        help="Config directory for patches (default: ../config)",
    )
    parser.add_argument(
        "--rules-path",
        default=None,
        help="Path to compliance rules JSON (default: config/maestro-rules.json)",
    )

    args = parser.parse_args()

    result = run_self_healing(
        pipeline_run_dir=args.pipeline_dir,
        config_dir=args.config_dir,
        rules_path=args.rules_path,
    )

    # Exit with non-zero if security failed
    if result.get("security_layer", {}).get("security_report", {}).get(
        "overall_status"
    ) == "fail":
        sys.exit(1)


if __name__ == "__main__":
    main()
