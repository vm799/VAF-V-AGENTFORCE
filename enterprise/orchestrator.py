#!/usr/bin/env python3
"""
VAF AM Series — Production Orchestrator & CLI
Runs the 9-step pipeline end-to-end with clean output and dashboard generation.

Usage:
    python orchestrator.py run --mode full                # Run all 9 steps
    python orchestrator.py run --mode ingestion-only      # Just step 1
    python orchestrator.py run --mode with-dashboard      # All steps + HTML dashboard
    python orchestrator.py show-status                    # Check build statuses
    python orchestrator.py export --format json           # Export results as JSON
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
import subprocess


class BuildStatus(Enum):
    READY = "✅"
    RUNNING = "🔄"
    COMPLETE = "✓"
    FAILED = "❌"
    NOT_IMPLEMENTED = "⏳"


@dataclass
class BuildResult:
    build_num: int
    name: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    document_count: Optional[int] = None
    error: Optional[str] = None


class VAFOrchestrator:
    """Orchestrates the 9-step VAF AM pipeline."""

    BUILDS = {
        1: {"name": "Ingestion", "path": "vaf-am-build-01-ingestion", "implemented": True},
        2: {"name": "Sanitisation", "path": "vaf-am-build-02-sanitisation", "implemented": True},
        3: {"name": "Identity", "path": "vaf-am-build-03-identity", "implemented": True},
        4: {"name": "RAG", "path": "vaf-am-build-04-rag", "implemented": True},
        5: {"name": "Self-Evolving", "path": "vaf-am-build-05-self-evolving", "implemented": True},
        6: {"name": "Council", "path": "vaf-am-build-06-council", "implemented": True},
        7: {"name": "Compliance", "path": "vaf-am-build-07-compliance", "implemented": True},
        8: {"name": "Synthesis", "path": "vaf-am-build-08-synthesis", "implemented": True},
        9: {"name": "Output", "path": "vaf-am-build-09-output", "implemented": True},
        10: {"name": "Self-Healing", "path": "vaf-am-build-10-self-healing", "implemented": True},
    }

    def __init__(self, root_dir: Path = Path(".")):
        self.root = Path(root_dir)
        self.results: list[BuildResult] = []
        self.output_dir = self.root / "outputs"
        self.output_dir.mkdir(exist_ok=True)

    async def run_build(self, build_num: int, silent: bool = False) -> BuildResult:
        """Run a single build step and capture results."""
        build_info = self.BUILDS.get(build_num)
        if not build_info:
            return BuildResult(
                build_num=build_num,
                name="Unknown",
                status=BuildStatus.FAILED.value,
                error="Build number not found"
            )

        build_path = self.root / build_info["path"]
        if not build_path.exists():
            return BuildResult(
                build_num=build_num,
                name=build_info["name"],
                status=BuildStatus.FAILED.value,
                error=f"Build directory not found: {build_path}"
            )

        result = BuildResult(
            build_num=build_num,
            name=build_info["name"],
            status=BuildStatus.RUNNING.value,
            started_at=datetime.utcnow().isoformat(),
        )

        if not silent:
            print(f"\n[{build_num}] {build_info['name']} {result.status}")
            print("─" * 50)

        try:
            start = datetime.utcnow()

            # Run the build's run.py
            proc = await asyncio.create_subprocess_exec(
                "uv", "run", "python", "run.py",
                cwd=str(build_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            if proc.returncode != 0:
                result.status = BuildStatus.FAILED.value
                result.error = stderr.decode()
                if not silent:
                    print(f"❌ FAILED: {result.error[:200]}")
            else:
                result.status = BuildStatus.COMPLETE.value
                result.completed_at = datetime.utcnow().isoformat()
                result.duration_seconds = (datetime.utcnow() - start).total_seconds()

                # Try to extract document count from reports
                report_path = build_path / "reports" / f"{build_info['path'].split('-')[-1]}_report.json"
                if report_path.exists():
                    try:
                        with open(report_path) as f:
                            report_data = json.load(f)
                            if isinstance(report_data, list):
                                result.document_count = len(report_data)
                            elif "documents" in report_data:
                                result.document_count = len(report_data["documents"])
                    except:
                        pass

                if not silent:
                    duration = f"{result.duration_seconds:.1f}s"
                    doc_info = f" | {result.document_count} docs" if result.document_count else ""
                    print(f"✅ COMPLETE ({duration}){doc_info}")

        except asyncio.TimeoutError:
            result.status = BuildStatus.FAILED.value
            result.error = "Build exceeded 5-minute timeout"
            if not silent:
                print(f"❌ TIMEOUT")
        except Exception as e:
            result.status = BuildStatus.FAILED.value
            result.error = str(e)
            if not silent:
                print(f"❌ ERROR: {e}")

        self.results.append(result)
        return result

    async def run_pipeline(self, mode: str = "full", self_heal: bool = False):
        """Run the full 9-step pipeline."""
        print("\n" + "=" * 60)
        print("🚀 VAF AM Series — Production Pipeline")
        print(f"📅 Started: {datetime.utcnow().isoformat()}")
        print("=" * 60)

        if mode == "ingestion-only":
            builds_to_run = [1]
        elif mode == "full":
            builds_to_run = list(range(1, 10))
        elif mode == "with-dashboard":
            builds_to_run = list(range(1, 10))
        else:
            builds_to_run = list(range(1, 10))

        # Run builds sequentially
        for build_num in builds_to_run:
            await self.run_build(build_num)

        # Run Build 10 self-healing loop if requested
        if self_heal:
            print("\n🔄 Running Build 10 — Self-Healing Loop")
            await self.run_build(10)

        # Summary
        await self.print_summary()

        # Generate dashboard if requested
        if mode == "with-dashboard":
            await self.generate_dashboard()

    async def print_summary(self):
        """Print pipeline summary."""
        print("\n" + "=" * 60)
        print("📊 Pipeline Summary")
        print("=" * 60)

        completed = sum(1 for r in self.results if r.status == BuildStatus.COMPLETE.value)
        total = len(self.results)
        total_time = sum(r.duration_seconds for r in self.results if r.duration_seconds)

        for result in self.results:
            status = result.status
            duration = f"({result.duration_seconds:.1f}s)" if result.duration_seconds else ""
            print(f"  {status} [{result.build_num}] {result.name:20} {duration}")

        print("─" * 60)
        print(f"✨ Result: {completed}/{total} builds completed in {total_time:.1f}s")

        # Save results
        results_file = self.output_dir / "pipeline_results.json"
        with open(results_file, "w") as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2,
                default=str
            )
        print(f"💾 Results saved: {results_file}")

    async def generate_dashboard(self):
        """Generate HTML dashboard from results."""
        dashboard_file = self.output_dir / "dashboard.html"

        # This will be populated by dashboard generation
        print(f"\n📊 Generating dashboard: {dashboard_file}")
        # (Dashboard generation code will follow)

    def show_status(self):
        """Show status of all builds."""
        print("\n" + "=" * 60)
        print("📋 VAF AM Series Build Status")
        print("=" * 60)

        for build_num, build_info in self.BUILDS.items():
            build_path = self.root / build_info["path"]
            if build_path.exists():
                status = "✅ Ready"
            else:
                status = "❌ Missing"
            print(f"  {status} [{build_num}] {build_info['name']:20} ({build_info['path']})")

        print("=" * 60)

    def export_results(self, format_type: str = "json"):
        """Export results in specified format."""
        if not self.results:
            print("⚠️  No results to export. Run pipeline first with: python orchestrator.py run")
            return

        if format_type == "json":
            export_file = self.output_dir / "pipeline_export.json"
            with open(export_file, "w") as f:
                json.dump([asdict(r) for r in self.results], f, indent=2, default=str)
            print(f"✅ Exported to {export_file}")

        elif format_type == "markdown":
            export_file = self.output_dir / "pipeline_report.md"
            with open(export_file, "w") as f:
                f.write("# VAF AM Series Pipeline Report\n\n")
                f.write(f"Generated: {datetime.utcnow().isoformat()}\n\n")
                for result in self.results:
                    f.write(f"## [{result.build_num}] {result.name}\n\n")
                    f.write(f"- **Status**: {result.status}\n")
                    if result.duration_seconds:
                        f.write(f"- **Duration**: {result.duration_seconds:.1f}s\n")
                    if result.document_count:
                        f.write(f"- **Documents**: {result.document_count}\n")
                    if result.error:
                        f.write(f"- **Error**: {result.error}\n")
                    f.write("\n")
            print(f"✅ Exported to {export_file}")


async def main():
    parser = argparse.ArgumentParser(
        description="VAF AM Series Production Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrator.py run --mode full
  python orchestrator.py run --mode ingestion-only
  python orchestrator.py run --mode with-dashboard
  python orchestrator.py show-status
  python orchestrator.py export --format json
        """
    )

    parser.add_argument(
        "command",
        choices=["run", "show-status", "export"],
        help="Command to execute"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "ingestion-only", "with-dashboard"],
        default="full",
        help="Pipeline execution mode (default: full)"
    )
    parser.add_argument(
        "--self-heal",
        action="store_true",
        default=False,
        help="Run Build 10 self-healing loop after pipeline completes"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Export format (default: json)"
    )

    args = parser.parse_args()

    orchestrator = VAFOrchestrator(Path.cwd())

    if args.command == "run":
        await orchestrator.run_pipeline(mode=args.mode, self_heal=args.self_heal)
    elif args.command == "show-status":
        orchestrator.show_status()
    elif args.command == "export":
        orchestrator.export_results(format_type=args.format)


if __name__ == "__main__":
    asyncio.run(main())
