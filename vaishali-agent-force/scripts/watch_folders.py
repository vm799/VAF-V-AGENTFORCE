#!/usr/bin/env python3
"""Watch folders for new files and trigger agents.

Monitors:
  - data/uploads/statements/ → SENTINEL (finance parser)
  - data/learning/sources/ → NEXUS (education ingest)
  - data/content/ideas/ → AMPLIFY (content generator)
  - data/knowledge_add/ → knowledge sync to Obsidian

Usage:
    python3 scripts/watch_folders.py
"""

import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def get_vaf_root() -> Path:
    """Get VAF project root."""
    return Path(__file__).parent.parent


class FolderWatcher:
    """Watch folders for new files and trigger agents."""

    def __init__(self):
        self.vaf_root = get_vaf_root()
        self.data_dir = self.vaf_root / "data"
        self.seen_files = set()
        self.check_interval = 5  # seconds

    def watch(self):
        """Main watch loop."""
        log.info(f"🔍 Starting folder watcher (checking every {self.check_interval}s)...")
        log.info(f"   📁 Watching: {self.data_dir}")

        try:
            while True:
                self._check_folders()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            log.info("✋ Watcher stopped.")

    def _check_folders(self):
        """Check each workflow folder for new files."""
        # 1. Check statements
        self._check_statements()

        # 2. Check learning sources
        self._check_learning()

        # 3. Check content ideas
        self._check_content()

        # 4. Check knowledge add
        self._check_knowledge()

    def _check_statements(self):
        """Check data/uploads/statements/ for new bank statements."""
        stmt_dir = self.data_dir / "uploads" / "statements"
        if not stmt_dir.exists():
            return

        for file in stmt_dir.glob("*"):
            if file.is_file() and file.suffix in [".csv", ".pdf", ".xlsx"]:
                file_key = f"stmt:{file.absolute()}"
                if file_key not in self.seen_files:
                    self.seen_files.add(file_key)
                    log.info(f"📊 New statement detected: {file.name}")
                    self._process_statement(file)

    def _process_statement(self, file_path: Path):
        """Trigger SENTINEL to process statement."""
        try:
            from vaishali.finance.parsers.generic_csv import parse_csv_statement
            from vaishali.captures.store import save_capture

            log.info(f"   ⏳ Processing {file_path.name}...")

            # Parse the statement
            transactions = parse_csv_statement(file_path)

            # Save as capture
            summary = f"Bank statement: {len(transactions)} transactions from {file_path.name}"
            capture = save_capture(
                content=summary,
                agent="SENTINEL",
                enrich=True,
                source_url=str(file_path)
            )

            log.info(f"   ✅ Processed: {capture['title']}")

        except Exception as e:
            log.error(f"   ❌ Failed to process statement: {e}")

    def _check_learning(self):
        """Check data/learning/sources/ for new content."""
        learn_dir = self.data_dir / "learning" / "sources"
        if not learn_dir.exists():
            return

        for file in learn_dir.glob("*"):
            if file.is_file() and file.suffix in [".pdf", ".txt", ".md"]:
                file_key = f"learn:{file.absolute()}"
                if file_key not in self.seen_files:
                    self.seen_files.add(file_key)
                    log.info(f"📚 New learning material: {file.name}")
                    self._process_learning(file)

    def _process_learning(self, file_path: Path):
        """Trigger NEXUS to ingest learning material."""
        try:
            from vaishali.captures.store import save_capture

            log.info(f"   ⏳ Ingesting {file_path.name}...")

            # Extract text
            if file_path.suffix == ".pdf":
                text = f"PDF: {file_path.name} (auto-extract)"
            else:
                text = file_path.read_text()[:500]

            # Save as capture
            capture = save_capture(
                content=text,
                agent="NEXUS",
                enrich=True,
                source_url=str(file_path)
            )

            log.info(f"   ✅ Ingested: {capture['title']}")

        except Exception as e:
            log.error(f"   ❌ Failed to ingest learning: {e}")

    def _check_content(self):
        """Check data/content/ideas/ for new teaching content."""
        content_dir = self.data_dir / "content" / "ideas"
        if not content_dir.exists():
            return

        for file in content_dir.glob("*"):
            if file.is_file() and file.suffix in [".md", ".txt"]:
                file_key = f"content:{file.absolute()}"
                if file_key not in self.seen_files:
                    self.seen_files.add(file_key)
                    log.info(f"📝 New content idea: {file.name}")
                    self._process_content(file)

    def _process_content(self, file_path: Path):
        """Trigger AMPLIFY to enhance content."""
        try:
            from vaishali.captures.store import save_capture

            log.info(f"   ⏳ Enhancing {file_path.name}...")

            text = file_path.read_text()[:500]

            # Save as capture
            capture = save_capture(
                content=text,
                agent="AMPLIFY",
                enrich=True,
                source_url=str(file_path)
            )

            log.info(f"   ✅ Enhanced: {capture['title']}")

        except Exception as e:
            log.error(f"   ❌ Failed to enhance content: {e}")

    def _check_knowledge(self):
        """Check data/knowledge_add/ for new knowledge to sync."""
        knowledge_dir = self.data_dir / "knowledge_add"
        if not knowledge_dir.exists():
            return

        for file in knowledge_dir.glob("*"):
            if file.is_file() and file.suffix in [".md", ".txt"]:
                file_key = f"knowledge:{file.absolute()}"
                if file_key not in self.seen_files:
                    self.seen_files.add(file_key)
                    log.info(f"🧠 New knowledge: {file.name}")
                    self._sync_knowledge(file)

    def _sync_knowledge(self, file_path: Path):
        """Sync knowledge to Obsidian vault."""
        try:
            import shutil

            vault_root = Path.home() / "Documents" / "VAF-Vault" / "INSIGHTS"
            vault_root.mkdir(parents=True, exist_ok=True)

            dest = vault_root / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
            shutil.copy2(file_path, dest)

            log.info(f"   ✅ Synced to Obsidian: {dest.name}")

            # Move processed file
            processed = file_path.parent / "processed" / file_path.name
            processed.parent.mkdir(exist_ok=True)
            file_path.rename(processed)

        except Exception as e:
            log.error(f"   ❌ Failed to sync knowledge: {e}")


def main():
    watcher = FolderWatcher()
    watcher.watch()


if __name__ == "__main__":
    main()
