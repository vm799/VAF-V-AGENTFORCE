"""CIPHER URL Processor — fetch, extract, and rate web content.

Handles the URL enrichment step in the golden thread:
  V drops a URL → CIPHER fetches the page → extracts readable text →
  returns clean content for the orchestrator to enrich with LLM.

Uses httpx (async-capable, already in the project) + lightweight HTML
extraction via stdlib html.parser (no BeautifulSoup dependency).

Usage:
    from vaishali.cipher.url_processor import fetch_and_extract

    text = fetch_and_extract("https://arxiv.org/abs/2403.12345")
    # Returns: "Title: ... \n\n Content extracted from the page..."
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────

MAX_FETCH_BYTES = 500_000   # 500KB max download
FETCH_TIMEOUT = 8.0         # seconds
MAX_OUTPUT_CHARS = 4_000    # max chars returned to orchestrator
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 "
    "VAF-CIPHER/1.0"
)

# Tags whose content we skip entirely
_SKIP_TAGS = frozenset([
    "script", "style", "noscript", "nav", "footer", "header",
    "aside", "form", "svg", "iframe", "button",
])

# ── YouTube transcript support ────────────────────────────────────────

_YT_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?.*v=|youtu\.be/)([\w-]{11})"),
]


def _extract_youtube_id(url: str) -> str | None:
    """Extract YouTube video ID from URL, or None."""
    for pat in _YT_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1)
    return None


def _fetch_youtube_transcript(video_id: str) -> str:
    """Fetch YouTube transcript using youtube_transcript_api if available."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(entry["text"] for entry in transcript)
        return f"[YouTube Transcript]\n\n{text[:MAX_OUTPUT_CHARS]}"
    except ImportError:
        log.info("youtube_transcript_api not installed — skipping transcript")
        return ""
    except Exception as e:
        log.warning("YouTube transcript fetch failed for %s: %s", video_id, e)
        return ""


# ── Lightweight HTML text extractor ───────────────────────────────────

class _TextExtractor(HTMLParser):
    """Minimal HTML→text parser. Skips scripts, styles, navs."""

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth: int = 0
        self._title: str = ""
        self._in_title: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower_tag = tag.lower()
        if lower_tag in _SKIP_TAGS:
            self._skip_depth += 1
        if lower_tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        lower_tag = tag.lower()
        if lower_tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if lower_tag == "title":
            self._in_title = False
        # Add whitespace after block elements
        if lower_tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                          "li", "tr", "br", "article", "section"):
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title and not self._title:
            self._title = data.strip()
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._pieces.append(text)

    @property
    def title(self) -> str:
        return self._title

    @property
    def text(self) -> str:
        raw = " ".join(self._pieces)
        # Collapse excessive whitespace
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r"  +", " ", raw)
        return raw.strip()


def _extract_text_from_html(html: str) -> tuple[str, str]:
    """Extract (title, body_text) from raw HTML.

    Returns:
        (page_title, readable_text)
    """
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass  # Malformed HTML — return whatever we got
    return parser.title, parser.text


# ── Main fetch + extract ──────────────────────────────────────────────

def fetch_and_extract(url: str) -> str:
    """Fetch a URL and return clean, readable text content.

    Handles:
    - YouTube URLs → transcript extraction
    - Regular URLs → HTTP GET → HTML text extraction
    - Timeout / error → empty string (caller handles gracefully)

    Args:
        url: The URL to fetch.

    Returns:
        Readable text content (max MAX_OUTPUT_CHARS), or empty string on failure.
    """
    # YouTube shortcut
    yt_id = _extract_youtube_id(url)
    if yt_id:
        transcript = _fetch_youtube_transcript(yt_id)
        if transcript:
            return transcript
        # Fall through to regular fetch if transcript fails

    # Regular HTTP fetch
    try:
        import httpx

        with httpx.Client(
            timeout=FETCH_TIMEOUT,
            follow_redirects=True,
            max_redirects=5,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.get(url)
            response.raise_for_status()

            # Check content type — only process text/html
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                log.info("Skipping non-HTML content: %s", content_type)
                return f"[Non-HTML content: {content_type}]"

            # Limit response size
            raw_html = response.text[:MAX_FETCH_BYTES]

    except Exception as e:
        log.warning("HTTP fetch failed for %s: %s", url, e)
        return ""

    # Extract text
    title, body = _extract_text_from_html(raw_html)
    if not body:
        return f"[Page title: {title}]" if title else ""

    # Format output
    output = f"Title: {title}\n\n{body}" if title else body
    return output[:MAX_OUTPUT_CHARS]


def fetch_and_rate(url: str) -> dict[str, Any]:
    """Fetch URL and return structured data including content + metadata.

    Returns dict with: url, title, content, char_count, fetch_ok.
    Used by dashboard and insight engine for richer metadata.
    """
    yt_id = _extract_youtube_id(url)
    content = fetch_and_extract(url)

    return {
        "url": url,
        "is_youtube": yt_id is not None,
        "youtube_id": yt_id,
        "content": content,
        "char_count": len(content),
        "fetch_ok": bool(content),
    }
