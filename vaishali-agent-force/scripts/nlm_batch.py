#!/usr/bin/env python3
"""nlm_batch.py — Evening batch: process queued URLs through NotebookLM.

Runs at 8pm daily via LaunchAgent / scheduled task.
For each pending URL:
  1. Add to NotebookLM "VAF Research" notebook as a source
  2. Ask NLM chat for 2-sentence actionable insight
  3. Update the insight JSON with nlm_summary
  4. Rewrite the Obsidian note with the enriched content
  5. Mark queue entry as done

Usage:
    python scripts/nlm_batch.py           # process all pending
    python scripts/nlm_batch.py --dry-run # show queue without processing
    VAF_NLM_DEBUG=1 python scripts/nlm_batch.py  # save screenshots
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Make src importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


async def run_batch(dry_run: bool = False) -> None:
    from vaishali.education.url_queue import get_pending, mark_done, mark_failed
    from vaishali.education.insight_writer import (
        load_insight_json, save_insight_json, write_obsidian_note,
    )
    from vaishali.core.logging_utils import get_logger
    log = get_logger("nlm_batch")

    pending = get_pending()
    if not pending:
        print("✅ NLM queue is empty — nothing to process.")
        return

    print(f"🔬 Processing {len(pending)} queued URLs through NotebookLM...")
    if dry_run:
        for item in pending:
            print(f"  [DRY RUN] Would process: {item['title'][:60]} — {item['url'][:80]}")
        return

    # Import NLM extractor
    try:
        from notebooklm_ingest import notebooklm_extract
    except ImportError:
        print("❌ notebooklm_ingest not found. Run from project root.")
        return

    success = 0
    failed = 0

    for item in pending:
        url = item["url"]
        title = item.get("title", url)[:60]
        insight_id = item.get("insight_id", "")

        print(f"\n  → {title}")
        print(f"    {url[:80]}")

        try:
            result = await notebooklm_extract(url)

            if result.get("status") == "success" and result.get("summary"):
                summary = result["summary"]
                print(f"    ✅ NLM summary: {summary[:100]}...")

                # Update insight JSON
                if insight_id:
                    try:
                        insight = load_insight_json(insight_id)
                        if insight:
                            insight.notebooklm_summary = summary
                            # Only upgrade main summary if it's better (longer, more words)
                            if len(summary.split()) > len(insight.summary.split()):
                                insight.summary = summary[:400]
                            if result.get("key_topics"):
                                insight.key_topics = list(dict.fromkeys(
                                    insight.key_topics + result["key_topics"]
                                ))[:10]
                            save_insight_json(insight)
                            write_obsidian_note(insight)
                            print(f"    📓 Obsidian updated")
                    except Exception as e:
                        log.warning("Could not update insight %s: %s", insight_id, e)

                mark_done(url, summary)
                success += 1

            elif result.get("status") == "login_required":
                print("    ⚠️ Not logged in to NotebookLM. Open Chrome and sign in.")
                mark_failed(url, "login_required")
                failed += 1
                break  # stop batch — all will fail until login done

            else:
                err = result.get("message", result.get("status", "unknown"))
                print(f"    ❌ Failed: {err[:80]}")
                mark_failed(url, err)
                failed += 1

        except Exception as e:
            print(f"    ❌ Exception: {e}")
            mark_failed(url, str(e)[:200])
            failed += 1

        # Small delay between sources — avoid hammering NLM
        await asyncio.sleep(3)

    print(f"\n✅ Batch complete: {success} processed, {failed} failed")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(run_batch(dry_run=dry_run))
