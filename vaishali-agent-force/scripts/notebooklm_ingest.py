#!/usr/bin/env python3
"""notebooklm_ingest.py — Add a URL source to NotebookLM and extract its summary.

Uses your actual Chrome installation so Google auth persists.
A dedicated VAF profile is kept at ~/.vaf_nlm_profile/ — never conflicts
with Chrome being open.

FIRST RUN: A Chrome window opens to notebooklm.google.com. Sign in with your
Google account. After that the session is saved and future calls are silent
(brief Chrome flash, ~5 seconds).

DEBUG: Set VAF_NLM_DEBUG=1 to save screenshots at each step to ~/vaf_nlm_debug/

Requirements:
    pip install playwright
    playwright install chrome

Usage (standalone test):
    python scripts/notebooklm_ingest.py "https://example.com/article"

Called by bot:
    from notebooklm_ingest import notebooklm_extract
    result = await notebooklm_extract(url)
    # returns: {status, summary, key_topics, source_title, notebook}
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

NOTEBOOK_NAME = "VAF Research"
NLM_URL = "https://notebooklm.google.com"
VAF_PROFILE_DIR = Path.home() / ".vaf_nlm_profile"
DEBUG = bool(os.getenv("VAF_NLM_DEBUG", ""))
DEBUG_DIR = Path.home() / "vaf_nlm_debug"
TIMEOUT = 90_000  # ms — overall page timeout


# ── Debug helper ──────────────────────────────────────────────────────────────

async def _snap(page, label: str) -> None:
    """Save a screenshot if debug mode is on."""
    if not DEBUG:
        return
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    path = DEBUG_DIR / f"{ts}_{label}.png"
    try:
        await page.screenshot(path=str(path), full_page=False)
    except Exception:
        pass


# ── JS helpers ────────────────────────────────────────────────────────────────

async def _click_by_text(page, *texts, timeout_ms: int = 5_000) -> bool:
    """Click the first visible element whose text contains any of the given strings.

    Uses JS so it works regardless of DOM nesting or CSS framework changes.
    """
    texts_js = "[" + ", ".join(f'"{t}"' for t in texts) + "]"
    js = f"""
        (texts) => {{
            const all = Array.from(document.querySelectorAll(
                'button, [role="button"], [role="menuitem"], [role="option"], li, a, span'
            ));
            for (const t of texts) {{
                const el = all.find(el => {{
                    const txt = (el.textContent || el.innerText || '').trim();
                    return txt.toLowerCase().includes(t.toLowerCase()) &&
                           el.offsetParent !== null;  // visible
                }});
                if (el) {{ el.click(); return true; }}
            }}
            return false;
        }}
    """
    try:
        found = await page.evaluate(js, [*texts])
        if found:
            await page.wait_for_timeout(600)
        return found
    except Exception:
        return False


async def _fill_input(page, url: str, timeout_ms: int = 5_000) -> bool:
    """Fill the first visible text/url input with the given value."""
    js = f"""
        (url) => {{
            const inputs = Array.from(document.querySelectorAll(
                'input[type="url"], input[type="text"], input[type="search"], textarea'
            ));
            const inp = inputs.find(i => i.offsetParent !== null);
            if (inp) {{
                inp.focus();
                inp.value = url;
                inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }}
            return false;
        }}
    """
    try:
        found = await page.evaluate(js, url)
        if found:
            await page.wait_for_timeout(400)
        return found
    except Exception:
        return False


async def _get_page_snapshot(page) -> str:
    """Return visible text of the page (for error diagnosis)."""
    try:
        return await page.evaluate(
            "() => document.body?.innerText?.slice(0, 2000) || ''"
        )
    except Exception:
        return ""


# ── Main entry ────────────────────────────────────────────────────────────────

async def notebooklm_extract(url: str, notebook_name: str = NOTEBOOK_NAME) -> dict:
    """Add url as a source in NotebookLM and return extracted insights.

    Returns dict:
        status: success | login_required | no_browser | timeout | error
        summary: str
        key_topics: list[str]
        source_title: str
        notebook: str
    """
    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout
    except ImportError:
        return {
            "status": "no_browser",
            "message": "Run: pip install playwright && playwright install chrome",
        }

    VAF_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        # Use real Chrome — Google auth cookies live there
        browser = None
        try:
            browser = await pw.chromium.launch_persistent_context(
                user_data_dir=str(VAF_PROFILE_DIR),
                channel="chrome",
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-position=20,20",
                    "--window-size=1280,900",
                ],
                ignore_default_args=["--enable-automation"],
            )
        except Exception as e_chrome:
            # Chrome not installed — fall back to Playwright Chromium
            try:
                browser = await pw.chromium.launch_persistent_context(
                    user_data_dir=str(VAF_PROFILE_DIR),
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
            except Exception as e2:
                return {
                    "status": "error",
                    "message": f"Browser launch failed. Install Chrome or run: playwright install chromium\nDetails: {e2}",
                }

        page = browser.pages[0] if browser.pages else await browser.new_page()

        try:
            # ── 1. Navigate to NotebookLM ───────────────────────────────
            await page.goto(NLM_URL, timeout=TIMEOUT, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            await _snap(page, "01_home")

            # ── 2. Login check ──────────────────────────────────────────
            if await _is_login_page(page):
                await _snap(page, "02_login_needed")
                # Give user 120s to sign in
                for _ in range(24):
                    await page.wait_for_timeout(5_000)
                    if not await _is_login_page(page):
                        break
                if await _is_login_page(page):
                    await browser.close()
                    return {
                        "status": "login_required",
                        "message": (
                            "A Chrome window opened to NotebookLM.\n"
                            "Sign in with your Google account (one-time only), "
                            "then drop your link again."
                        ),
                    }
                await page.wait_for_timeout(3000)
                await _snap(page, "03_logged_in")

            # ── 3. Find or create the VAF notebook ─────────────────────
            await _ensure_notebook(page, notebook_name)
            await _snap(page, "04_in_notebook")

            # ── 4. Add the URL as a source ─────────────────────────────
            source_title = await _add_url_source(page, url)
            await _snap(page, "05_source_added")

            # ── 5. Extract summary from source ─────────────────────────
            summary, topics = await _extract_summary(page, url)
            await _snap(page, "06_summary_extracted")

            await browser.close()
            return {
                "status": "success",
                "source_title": source_title or url,
                "summary": summary,
                "key_topics": topics,
                "notebook": notebook_name,
            }

        except Exception as e:
            await _snap(page, "error_state")
            snapshot = await _get_page_snapshot(page)
            try:
                await browser.close()
            except Exception:
                pass
            return {
                "status": "error",
                "message": str(e)[:400],
                "page_snapshot": snapshot[:500],
            }


# ── Login detection ───────────────────────────────────────────────────────────

async def _is_login_page(page) -> bool:
    url = page.url
    return (
        "accounts.google.com" in url
        or "signin" in url.lower()
        or "login" in url.lower()
    )


# ── Notebook navigation ───────────────────────────────────────────────────────

async def _ensure_notebook(page, name: str) -> None:
    """Open an existing notebook named `name` or create a new one."""
    from playwright.async_api import TimeoutError as PWTimeout

    # Try clicking existing notebook by title
    try:
        nb = page.get_by_text(name, exact=True).first
        await nb.wait_for(state="visible", timeout=5_000)
        await nb.click()
        await page.wait_for_load_state("domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(2000)
        return
    except PWTimeout:
        pass

    # Also try partial text match via JS
    found = await _click_by_text(page, name)
    if found:
        await page.wait_for_load_state("domcontentloaded", timeout=20_000)
        await page.wait_for_timeout(2000)
        return

    # Create new notebook
    await _create_notebook(page, name)


async def _create_notebook(page, name: str) -> None:
    """Click New Notebook and set its title."""
    from playwright.async_api import TimeoutError as PWTimeout

    # Try various button labels for "create new"
    clicked = await _click_by_text(
        page,
        "New notebook", "New Notebook", "Create notebook",
        "Create new", "New", "+ New",
    )
    if not clicked:
        # Try aria/data selectors
        for sel in [
            '[aria-label*="new notebook" i]',
            '[data-testid*="new" i]',
            'button[class*="new" i]',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=3_000):
                    await btn.click()
                    clicked = True
                    break
            except PWTimeout:
                pass

    await page.wait_for_timeout(2000)

    # Fill title if a dialog appeared
    for sel in [
        'input[placeholder*="title" i]',
        'input[placeholder*="name" i]',
        'input[placeholder*="notebook" i]',
        'input[aria-label*="title" i]',
        'input[type="text"]',
    ]:
        try:
            inp = page.locator(sel).first
            if await inp.is_visible(timeout=2_000):
                await inp.clear()
                await inp.fill(name)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
                return
        except PWTimeout:
            pass


# ── Add URL source ────────────────────────────────────────────────────────────

async def _add_url_source(page, url: str) -> str:
    """Click Add Source → Website/URL → paste url → confirm. Returns source title."""
    from playwright.async_api import TimeoutError as PWTimeout

    # Step A: open the "Add source" panel
    # NLM uses "Add sources" (plural) in its current UI
    await _snap(page, "add_src_a_before")
    clicked = await _click_by_text(
        page,
        "Add sources", "Add source", "Add Source", "Add a source",
        "+ Add source", "+ Add sources", "add", "＋", "Upload source",
    )
    if not clicked:
        for sel in [
            '[aria-label*="add source" i]',
            '[data-testid*="add-source"]',
            '[data-testid*="addSource"]',
            'button[class*="add" i]',
            'mat-icon:has-text("add")',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=3_000):
                    await btn.click()
                    clicked = True
                    break
            except PWTimeout:
                pass

    await page.wait_for_timeout(1500)
    await _snap(page, "add_src_b_panel_open")

    # Step B: choose "Website" / "URL" option
    # NLM shows: Docs, Google Drive, Link (with language icon), YouTube, etc.
    clicked_web = await _click_by_text(
        page,
        "Link", "Website", "URL", "Web URL", "Website URL",
        "website url", "Paste URL", "web page", "Copied link",
    )
    if not clicked_web:
        for sel in [
            '[aria-label*="website" i]',
            '[aria-label*="url" i]',
            '[data-testid*="website"]',
            '[data-testid*="url"]',
            'li:has-text("URL")',
            'li:has-text("Website")',
        ]:
            try:
                opt = page.locator(sel).first
                if await opt.is_visible(timeout=2_000):
                    await opt.click()
                    clicked_web = True
                    break
            except PWTimeout:
                pass

    await page.wait_for_timeout(1000)
    await _snap(page, "add_src_c_url_dialog")

    # Step C: fill the URL into the input field
    # First try Playwright's type (most reliable for React controlled inputs)
    filled = False
    for sel in [
        'input[type="url"]',
        'input[placeholder*="URL" i]',
        'input[placeholder*="http" i]',
        'input[placeholder*="link" i]',
        'input[placeholder*="paste" i]',
        'input[type="text"]',
    ]:
        try:
            inp = page.locator(sel).first
            if await inp.is_visible(timeout=3_000):
                await inp.click()
                await inp.clear()
                await inp.type(url, delay=20)
                filled = True
                break
        except PWTimeout:
            pass

    # JS fallback if Playwright selectors missed it
    if not filled:
        filled = await _fill_input(page, url)

    await page.wait_for_timeout(500)
    await _snap(page, "add_src_d_url_typed")

    # Step D: submit / confirm
    submitted = await _click_by_text(
        page,
        "Insert", "Add", "Confirm", "Submit", "Done",
        "Insert source", "Add source",
    )
    if not submitted:
        # Try keyboard submit
        await page.keyboard.press("Enter")

    await _snap(page, "add_src_e_submitted")

    # Step E: wait for NLM to process the source (spinner disappears)
    await page.wait_for_timeout(3000)
    for _ in range(12):  # up to 60 seconds
        processing = await page.evaluate(
            "() => !!document.querySelector('[aria-label*=\"processing\" i], "
            "[aria-label*=\"loading\" i], .loading, .spinner, [class*=\"progress\" i]')"
        )
        if not processing:
            break
        await page.wait_for_timeout(5000)

    await _snap(page, "add_src_f_processed")

    # Return best title we can find for the newly added source
    try:
        # Last source item
        source_title = await page.evaluate(
            """() => {
                const items = document.querySelectorAll(
                    '[data-testid="source-item"], [class*="source-item"], '
                    '[class*="sourceItem"], [class*="source_item"]'
                );
                if (items.length > 0) {
                    const last = items[items.length - 1];
                    return (last.getAttribute('aria-label') || last.textContent || '').trim().slice(0, 120);
                }
                return '';
            }"""
        )
        return source_title or ""
    except Exception:
        return ""


# ── Extract summary ───────────────────────────────────────────────────────────

def _is_real_sentence(text: str) -> bool:
    """Return True if text looks like a real sentence, not an icon name or UI label.

    Material Icons render as camelCase single-word strings like 'audio_magic_eraser',
    'chevron_forward', 'expand_more'. Real content has spaces, punctuation, multiple words.
    """
    text = text.strip()
    if len(text) < 30:
        return False
    # Must contain spaces (real sentences have words)
    if " " not in text:
        return False
    # Must have at least 4 words
    words = text.split()
    if len(words) < 4:
        return False
    # Reject if most words are icon-style (snake_case, camelCase, all-caps short)
    icon_like = sum(
        1 for w in words
        if "_" in w or (w == w.upper() and len(w) <= 4) or (len(w) > 6 and w[0].islower() and any(c.isupper() for c in w[1:]))
    )
    if icon_like > len(words) * 0.3:
        return False
    return True


async def _extract_summary(page, hint: str) -> tuple[str, list[str]]:
    """Get a meaningful summary from NotebookLM using its chat interface.

    Strategy (most reliable to least):
      1. Use NLM's chat to ask "Summarise this source" — direct AI response
      2. Scrape the source detail panel with icon-noise filtering
      3. Return empty string (Gemini summary is already stored — NLM is enrichment only)
    """
    from playwright.async_api import TimeoutError as PWTimeout

    summary = ""
    topics: list[str] = []

    # ── Strategy 1: Ask NLM via chat ──────────────────────────────────────
    # NLM's chat is the gold standard — ask it to summarise the source we just added
    try:
        chat_result = await _chat_ask_nlm(
            page,
            "In 3-4 sentences, summarise the key points and main argument of the source I just added. "
            "Focus on what's most useful and actionable. Be specific, not generic."
        )
        if chat_result and _is_real_sentence(chat_result[:100] + " x x x x"):
            summary = chat_result
            await _snap(page, "summary_from_chat")
    except Exception as e:
        pass  # fall through to scrape

    # ── Strategy 2: Scrape source detail panel with noise filtering ────────
    if not summary:
        try:
            summary = await page.evaluate(
                """() => {
                    function isRealText(t) {
                        t = t.trim();
                        if (t.length < 40) return false;
                        if (!t.includes(' ')) return false;  // icon names have no spaces
                        const words = t.split(/\\s+/);
                        if (words.length < 5) return false;
                        // Reject if >30% of words are icon-like
                        const iconLike = words.filter(w =>
                            w.includes('_') ||
                            (w.length > 5 && w[0] === w[0].toLowerCase() && /[A-Z]/.test(w.slice(1)))
                        ).length;
                        return iconLike / words.length < 0.3;
                    }

                    // Try specific selectors first
                    const selectors = [
                        '[data-testid="source-summary"]', '[data-testid="source-overview"]',
                        '.source-overview', '[class*="Overview"]', '[class*="Summary"]',
                        '.source-content'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) {
                            const t = el.innerText || el.textContent || '';
                            if (isRealText(t)) return t.trim().slice(0, 600);
                        }
                    }

                    // Fallback: walk all text nodes, collect real sentences
                    const all = Array.from(document.querySelectorAll('p, li, span, div'))
                        .filter(el => {
                            if (el.offsetParent === null) return false;
                            if (el.children.length > 3) return false; // skip containers
                            const t = (el.innerText || el.textContent || '').trim();
                            return isRealText(t);
                        })
                        .map(el => (el.innerText || el.textContent || '').trim());

                    // Deduplicate and sort by length (longest = most content)
                    const unique = [...new Set(all)].sort((a, b) => b.length - a.length);
                    return unique.slice(0, 3).join(' ').slice(0, 600);
                }"""
            )
            if summary and not _is_real_sentence(summary[:100] + " x x x x"):
                summary = ""
        except Exception:
            pass

    # Topics: look for chip/tag elements, filter out icon noise
    try:
        raw_topics = await page.evaluate(
            """() => {
                const els = document.querySelectorAll(
                    '[data-testid*="topic"], [class*="chip"], [class*="tag"], [class*="label"]'
                );
                return Array.from(els)
                    .filter(e => e.offsetParent !== null)
                    .map(e => (e.textContent || '').trim())
                    .filter(t => t.length > 2 && t.length < 40 && t.includes(' ') || (t.length > 3 && !t.includes('_')))
                    .slice(0, 8);
            }"""
        )
        topics = [t for t in (raw_topics or []) if t and "_" not in t and len(t.split()) >= 1][:8]
    except Exception:
        pass

    return summary, topics


async def _chat_ask_nlm(page, question: str) -> str:
    """Type a question into NLM's chat box and return the response text."""
    from playwright.async_api import TimeoutError as PWTimeout

    # Find the chat input
    chat_input = None
    for sel in [
        'textarea[placeholder*="Ask" i]',
        'textarea[placeholder*="question" i]',
        'textarea[placeholder*="chat" i]',
        'textarea[aria-label*="chat" i]',
        'div[contenteditable="true"]',
        'textarea',
    ]:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=2_000):
                chat_input = el
                break
        except PWTimeout:
            continue

    if not chat_input:
        return ""

    # Type question
    await chat_input.click()
    await chat_input.fill(question)
    await page.wait_for_timeout(300)

    # Submit
    submitted = False
    for sel in ['button[aria-label*="send" i]', 'button[type="submit"]', '[data-testid*="send"]']:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1_500):
                await btn.click()
                submitted = True
                break
        except PWTimeout:
            continue
    if not submitted:
        await page.keyboard.press("Enter")

    # Wait for response (up to 30s — NLM can be slow)
    await page.wait_for_timeout(3000)
    for _ in range(9):  # 3s × 9 = 27s max
        response = await page.evaluate(
            """() => {
                // NLM response bubbles — find the last assistant message
                const responses = document.querySelectorAll(
                    '[data-testid*="response"], [class*="response"], '
                    '[class*="assistant"], [class*="answer"], '
                    '[role="article"]:last-child'
                );
                if (responses.length > 0) {
                    const last = responses[responses.length - 1];
                    return (last.innerText || last.textContent || '').trim().slice(0, 800);
                }
                return '';
            }"""
        )
        if response and len(response.split()) > 10:
            return response
        await page.wait_for_timeout(3000)

    return ""

    # Topics
    try:
        chips = await page.evaluate(
            """() => {
                const els = document.querySelectorAll(
                    '[data-testid*="topic"], [class*="chip"], [class*="tag"], [class*="topic"]'
                );
                return Array.from(els)
                    .filter(e => e.offsetParent !== null)
                    .map(e => e.textContent.trim())
                    .filter(t => t.length > 2 && t.length < 40)
                    .slice(0, 8);
            }"""
        )
        topics = chips if isinstance(chips, list) else []
    except Exception:
        pass

    return summary, topics


# ── CLI entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/notebooklm_ingest.py <url> [notebook_name]")
        print("       VAF_NLM_DEBUG=1 python scripts/notebooklm_ingest.py <url>  (saves screenshots)")
        sys.exit(1)

    target_url = sys.argv[1]
    nb_name = sys.argv[2] if len(sys.argv) > 2 else NOTEBOOK_NAME

    import json
    result = asyncio.run(notebooklm_extract(target_url, nb_name))
    print(json.dumps(result, indent=2))
