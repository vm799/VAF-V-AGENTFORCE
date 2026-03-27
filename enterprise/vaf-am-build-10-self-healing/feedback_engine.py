"""
VAF AM Build 10 — Feedback Engine
Scores data source quality and tunes pipeline thresholds based on output quality.

Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Asset Management Series
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FeedbackEngine:
    """Uses pipeline outputs to improve pipeline inputs on the next run.

    Tracks which data sources consistently produce high-quality enriched
    records, which thresholds produce actionable insights, and adjusts
    configuration accordingly.
    """

    def __init__(self):
        self._adjustments: List[dict] = []

    def score_source_quality(self, staging_dir: str) -> dict:
        """Score each data source based on records that survived all 9 builds.

        Looks at build reports in the staging directory to measure how many
        records from each source made it through ingestion, sanitisation,
        enrichment, analysis, council review, compliance, synthesis, and
        delivery without being dropped or quarantined.
        """
        staging = Path(staging_dir)
        scores: Dict[str, dict] = {}

        # Collect per-source stats from build reports
        report_files = sorted(staging.glob("**/build_*.json")) if staging.exists() else []

        # Track records per source across builds
        source_stats: Dict[str, dict] = {}

        for report_file in report_files:
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            # Handle both list and dict report formats
            records = data if isinstance(data, list) else data.get("records", [])
            if isinstance(records, list):
                for record in records:
                    source = record.get("source", record.get("data_source", "unknown"))
                    if source not in source_stats:
                        source_stats[source] = {
                            "ingested": 0,
                            "survived": 0,
                            "quarantined": 0,
                            "builds_seen": set(),
                        }
                    source_stats[source]["ingested"] += 1
                    status = record.get("status", "")
                    if status in ("delivered", "complete", "synthesised", "approved"):
                        source_stats[source]["survived"] += 1
                    elif status in ("quarantined", "rejected", "dropped"):
                        source_stats[source]["quarantined"] += 1
                    build = record.get("build", _extract_build(report_file.name))
                    if build:
                        source_stats[source]["builds_seen"].add(str(build))

        # Calculate quality scores
        for source, stats in source_stats.items():
            ingested = stats["ingested"]
            survived = stats["survived"]
            quarantined = stats["quarantined"]

            survival_rate = survived / ingested if ingested > 0 else 0.0
            quarantine_rate = quarantined / ingested if ingested > 0 else 0.0
            build_coverage = len(stats["builds_seen"]) / 9.0  # 9 builds

            # Composite score: weighted combination
            quality_score = (
                survival_rate * 0.5
                + (1.0 - quarantine_rate) * 0.3
                + build_coverage * 0.2
            )

            scores[source] = {
                "quality_score": round(quality_score, 4),
                "survival_rate": round(survival_rate, 4),
                "quarantine_rate": round(quarantine_rate, 4),
                "build_coverage": round(build_coverage, 4),
                "records_ingested": ingested,
                "records_survived": survived,
                "records_quarantined": quarantined,
                "builds_seen": sorted(stats["builds_seen"]),
            }

        return {
            "source_count": len(scores),
            "scores": scores,
            "scored_at": datetime.utcnow().isoformat(),
        }

    def update_source_weights(self, quality_scores: dict, config_path: str) -> dict:
        """Adjust source weights in config based on quality history.

        Sources with higher quality scores get higher weights in the next
        pipeline run. Sources below the minimum threshold get flagged.
        """
        config_file = Path(config_path)
        config: dict = {}

        if config_file.exists():
            try:
                config = json.loads(config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                config = {}

        if "sources" not in config:
            config["sources"] = {}

        scores = quality_scores.get("scores", {})
        updates: List[dict] = []
        flagged: List[str] = []

        min_quality_threshold = 0.3

        for source, score_data in scores.items():
            quality = score_data.get("quality_score", 0.5)

            if source not in config["sources"]:
                config["sources"][source] = {}

            old_weight = config["sources"][source].get("weight", 1.0)

            # Adjust weight proportionally to quality score
            # High quality (>0.7) -> increase weight
            # Low quality (<0.3) -> decrease weight
            # Middle range -> small adjustment toward quality
            if quality >= 0.7:
                new_weight = min(old_weight * 1.1, 2.0)
            elif quality <= min_quality_threshold:
                new_weight = max(old_weight * 0.7, 0.1)
                flagged.append(source)
            else:
                # Nudge toward neutral
                new_weight = old_weight + (quality - 0.5) * 0.1

            new_weight = round(new_weight, 3)
            config["sources"][source]["weight"] = new_weight
            config["sources"][source]["last_quality_score"] = quality
            config["sources"][source]["last_updated"] = datetime.utcnow().isoformat()

            if abs(new_weight - old_weight) > 0.001:
                update = {
                    "source": source,
                    "old_weight": old_weight,
                    "new_weight": new_weight,
                    "quality_score": quality,
                }
                updates.append(update)
                self._adjustments.append({
                    "type": "source_weight",
                    **update,
                })

        # Write updated config
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return {
            "updates": updates,
            "flagged_sources": flagged,
            "total_sources": len(scores),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def tune_thresholds(self, insights_dir: str, config_path: str) -> dict:
        """Adjust pattern detection thresholds based on insight quality scores.

        Reads insight quality data (from Build 06/07/08 outputs) and adjusts
        thresholds to produce more actionable, less trivial insights.
        """
        insights_path = Path(insights_dir)
        config_file = Path(config_path)

        config: dict = {}
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                config = {}

        if "pattern_detection" not in config:
            config["pattern_detection"] = {}

        # Collect insight quality data
        insight_files = (
            sorted(insights_path.glob("**/*.json")) if insights_path.exists() else []
        )

        total_insights = 0
        actionable_count = 0
        trivial_count = 0
        quality_sum = 0.0

        for f in insight_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            items = data if isinstance(data, list) else data.get("insights", [])
            if not isinstance(items, list):
                continue

            for item in items:
                total_insights += 1
                q = item.get("quality_score", item.get("confidence", 0.5))
                quality_sum += q
                if q >= 0.7:
                    actionable_count += 1
                elif q <= 0.3:
                    trivial_count += 1

        adjustments: List[dict] = []

        if total_insights > 0:
            avg_quality = quality_sum / total_insights
            actionable_rate = actionable_count / total_insights
            trivial_rate = trivial_count / total_insights

            old_confidence = config["pattern_detection"].get("min_confidence", 0.5)
            old_relevance = config["pattern_detection"].get("min_relevance", 0.4)

            # If too many trivial insights, raise thresholds
            if trivial_rate > 0.4:
                new_confidence = min(old_confidence + 0.05, 0.9)
                new_relevance = min(old_relevance + 0.05, 0.8)
            # If too few actionable insights, lower thresholds slightly
            elif actionable_rate < 0.2:
                new_confidence = max(old_confidence - 0.03, 0.3)
                new_relevance = max(old_relevance - 0.03, 0.2)
            else:
                new_confidence = old_confidence
                new_relevance = old_relevance

            new_confidence = round(new_confidence, 3)
            new_relevance = round(new_relevance, 3)

            config["pattern_detection"]["min_confidence"] = new_confidence
            config["pattern_detection"]["min_relevance"] = new_relevance
            config["pattern_detection"]["last_tuned"] = datetime.utcnow().isoformat()

            if abs(new_confidence - old_confidence) > 0.001:
                adj = {
                    "threshold": "min_confidence",
                    "old_value": old_confidence,
                    "new_value": new_confidence,
                }
                adjustments.append(adj)
                self._adjustments.append({"type": "threshold", **adj})

            if abs(new_relevance - old_relevance) > 0.001:
                adj = {
                    "threshold": "min_relevance",
                    "old_value": old_relevance,
                    "new_value": new_relevance,
                }
                adjustments.append(adj)
                self._adjustments.append({"type": "threshold", **adj})
        else:
            config["pattern_detection"]["last_tuned"] = datetime.utcnow().isoformat()

        # Write updated config
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return {
            "total_insights_analysed": total_insights,
            "actionable_count": actionable_count,
            "trivial_count": trivial_count,
            "avg_quality": round(quality_sum / total_insights, 4) if total_insights else None,
            "adjustments": adjustments,
            "tuned_at": datetime.utcnow().isoformat(),
        }

    def get_feedback_report(self) -> dict:
        """Return a summary of all adjustments made during this session."""
        return {
            "total_adjustments": len(self._adjustments),
            "adjustments": self._adjustments,
            "generated_at": datetime.utcnow().isoformat(),
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _extract_build(filename: str) -> Optional[str]:
    """Extract build number from a filename."""
    import re

    match = re.search(r"build[_-]?(\d{1,2})", filename, re.IGNORECASE)
    return match.group(1) if match else None
