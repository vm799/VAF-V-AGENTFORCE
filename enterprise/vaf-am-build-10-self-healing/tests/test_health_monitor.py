"""
Tests for VAF AM Build 10 — Health Monitor
"""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from health_monitor import SelfHealingMonitor


class TestScanBuildLogs(unittest.TestCase):
    """Tests for scan_build_logs."""

    def test_scan_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = SelfHealingMonitor()
            logs = monitor.scan_build_logs(tmpdir)
            self.assertEqual(logs, [])

    def test_scan_nonexistent_directory(self):
        monitor = SelfHealingMonitor()
        logs = monitor.scan_build_logs("/nonexistent/path")
        self.assertEqual(logs, [])

    def test_scan_plain_text_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "build_01.log"
            log_file.write_text(
                "INFO Starting ingestion\n"
                "ERROR connection refused to source: reuters\n"
                "INFO Completed\n"
            )
            monitor = SelfHealingMonitor()
            logs = monitor.scan_build_logs(tmpdir)
            self.assertEqual(len(logs), 3)
            self.assertEqual(logs[0]["level"], "INFO")
            self.assertEqual(logs[1]["level"], "ERROR")
            self.assertEqual(logs[0]["build"], "01")

    def test_scan_json_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "build_03.json"
            entries = [
                {"timestamp": "2026-03-27T09:00:00", "level": "INFO", "message": "ok"},
                {"timestamp": "2026-03-27T09:01:00", "level": "ERROR", "message": "fail"},
            ]
            log_file.write_text(json.dumps(entries))

            monitor = SelfHealingMonitor()
            logs = monitor.scan_build_logs(tmpdir)
            self.assertEqual(len(logs), 2)
            self.assertEqual(logs[0]["build"], "03")
            self.assertEqual(logs[1]["level"], "ERROR")


class TestDiagnoseFailures(unittest.TestCase):
    """Tests for diagnose_failures."""

    def setUp(self):
        self.monitor = SelfHealingMonitor()

    def test_no_failures(self):
        logs = [
            {"message": "INFO Pipeline started successfully"},
            {"message": "INFO All records processed"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(diagnoses, [])

    def test_source_unreachable(self):
        logs = [
            {"message": "ERROR connection refused to source: reuters"},
            {"message": "ERROR failed to fetch from bloomberg API"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(len(diagnoses), 1)
        self.assertEqual(diagnoses[0]["failure_type"], "source_unreachable")
        self.assertEqual(diagnoses[0]["occurrence_count"], 2)
        self.assertEqual(diagnoses[0]["auto_response"], "reduce_source_weight")

    def test_high_quarantine_rate(self):
        logs = [
            {"message": "WARN quarantine rate 45% for source: dodgy_feed"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(len(diagnoses), 1)
        self.assertEqual(diagnoses[0]["failure_type"], "high_quarantine_rate")

    def test_zero_patterns(self):
        logs = [
            {"message": "WARN patterns found: 0 in analysis run"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(len(diagnoses), 1)
        self.assertEqual(diagnoses[0]["failure_type"], "zero_patterns")

    def test_council_timeout(self):
        logs = [
            {"message": "ERROR council timeout after 300s"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(len(diagnoses), 1)
        self.assertEqual(diagnoses[0]["failure_type"], "council_timeout")

    def test_delivery_failure(self):
        logs = [
            {"message": "ERROR telegram error: chat not found"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(len(diagnoses), 1)
        self.assertEqual(diagnoses[0]["failure_type"], "delivery_failure")

    def test_multiple_failure_types(self):
        logs = [
            {"message": "ERROR connection refused"},
            {"message": "ERROR council timeout"},
            {"message": "WARN delivery failed on slack"},
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(len(diagnoses), 3)
        # High severity should come first
        self.assertIn(diagnoses[0]["severity"], ("high",))

    def test_severity_ordering(self):
        logs = [
            {"message": "WARN patterns found: 0"},  # medium
            {"message": "ERROR connection refused"},  # high
        ]
        diagnoses = self.monitor.diagnose_failures(logs)
        self.assertEqual(diagnoses[0]["severity"], "high")
        self.assertEqual(diagnoses[1]["severity"], "medium")


class TestGeneratePatches(unittest.TestCase):
    """Tests for generate_patches."""

    def setUp(self):
        self.monitor = SelfHealingMonitor()

    def test_source_unreachable_patch(self):
        diagnoses = [{
            "failure_type": "source_unreachable",
            "severity": "high",
            "description": "Data source could not be reached",
            "auto_response": "reduce_source_weight",
            "matched_entries": [{"message": "failed to fetch from source: reuters"}],
            "occurrence_count": 3,
        }]
        patches = self.monitor.generate_patches(diagnoses)
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["action"], "reduce_weight")
        self.assertEqual(patches[0]["adjustment"], -0.2)
        self.assertTrue(patches[0]["alert_operator"])

    def test_zero_patterns_patch(self):
        diagnoses = [{
            "failure_type": "zero_patterns",
            "severity": "medium",
            "description": "Analysis produced zero patterns",
            "auto_response": "widen_thresholds",
            "matched_entries": [{"message": "patterns found: 0"}],
            "occurrence_count": 1,
        }]
        patches = self.monitor.generate_patches(diagnoses)
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["target_file"], "analysis_config.json")
        self.assertEqual(patches[0]["action"], "adjust_threshold")


class TestApplyPatches(unittest.TestCase):
    """Tests for apply_patches."""

    def test_apply_weight_reduction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-populate config
            config_file = Path(tmpdir) / "source_config.json"
            config_file.write_text(json.dumps({
                "sources": {"reuters": {"weight": 1.0}}
            }))

            patches = [{
                "failure_type": "source_unreachable",
                "target_file": "source_config.json",
                "action": "reduce_weight",
                "key": "sources.reuters.weight",
                "adjustment": -0.2,
                "min_value": 0.1,
                "reason": "Source unreachable",
                "alert_operator": True,
            }]

            monitor = SelfHealingMonitor()
            summary = monitor.apply_patches(patches, tmpdir)

            self.assertEqual(summary["applied_count"], 1)
            self.assertEqual(summary["skipped_count"], 0)
            self.assertEqual(len(summary["operator_alerts"]), 1)

            # Verify the config was written
            updated = json.loads(config_file.read_text())
            self.assertAlmostEqual(updated["sources"]["reuters"]["weight"], 0.8)

    def test_apply_creates_config_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "new_config"
            patches = [{
                "failure_type": "delivery_failure",
                "target_file": "delivery_config.json",
                "action": "enable_fallback",
                "key": "delivery.use_fallback",
                "value": True,
                "reason": "Delivery failed",
                "alert_operator": False,
            }]

            monitor = SelfHealingMonitor()
            summary = monitor.apply_patches(patches, str(config_dir))
            self.assertEqual(summary["applied_count"], 1)
            self.assertTrue(config_dir.exists())


if __name__ == "__main__":
    unittest.main()
