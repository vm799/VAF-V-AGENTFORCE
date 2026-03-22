"""Ingest education sources from sources.yml — RSS/Atom feeds and static URLs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from vaishali.core.config import settings
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class SourceItem:
    """A single fetched content item."""

    id: str
    title: str
    url: str
    source_name: str
    source_type: str  # "rss", "atom", "url"
    content: str = ""
    fetched_at: str = ""
    published_at: str = ""
    tags: list[str] = field(default_factory=list)


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def load_sources_config() -> list[dict[str, Any]]:
    """Load sources.yml if it exists, return list of source definitions."""
    path = settings.education_sources_path
    if not path.exists():
        log.warning("No sources.yml found at %s — creating example", path)
        _create_example_sources(path)

    # Use a simple YAML-like parser to avoid pyyaml dependency
    return _parse_simple_yaml(path)


def _create_example_sources(path: Path) -> None:
    """Write a starter sources.yml with example feeds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Education & Research Sources
# Supported types: rss, url
# Add your feeds and URLs here.

sources:
  - name: Hacker News Best
    type: rss
    url: https://hnrss.org/best
    tags: [tech, engineering]

  - name: Simon Willison
    type: rss
    url: https://simonwillison.net/atom/everything/
    tags: [ai, python]

  - name: Python Weekly
    type: url
    url: https://www.pythonweekly.com
    tags: [python, learning]
""",
        encoding="utf-8",
    )
    log.info("Created example sources.yml at %s", path)


def _parse_simple_yaml(path: Path) -> list[dict[str, Any]]:
    """Minimal YAML-subset parser for sources.yml (avoids pyyaml dependency).

    Handles the flat list-of-dicts format used in our sources file.
    """
    sources: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    text = path.read_text(encoding="utf-8")

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- name:"):
            if current:
                sources.append(current)
            current = {"name": stripped.split(":", 1)[1].strip()}
        elif current is not None and ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                # Parse simple list: [a, b, c]
                items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                current[key] = items
            else:
                current[key] = val

    if current:
        sources.append(current)

    return sources


def fetch_source(source_def: dict[str, Any]) -> list[SourceItem]:
    """Fetch content from a single source definition.

    For RSS/Atom: parses the feed XML.
    For URLs: fetches the page text.

    Returns a list of SourceItems (may be empty if fetch fails).
    """
    source_type = source_def.get("type", "url")
    url = source_def.get("url", "")
    name = source_def.get("name", url)
    tags = source_def.get("tags", [])

    if not url:
        log.warning("Source '%s' has no URL — skipping", name)
        return []

    try:
        import httpx

        resp = httpx.get(url, timeout=15.0, follow_redirects=True)
        resp.raise_for_status()
        raw = resp.text
    except Exception as e:
        log.warning("Failed to fetch '%s' (%s): %s", name, url, e)
        return []

    now = datetime.utcnow().isoformat()

    if source_type in ("rss", "atom"):
        return _parse_feed(raw, name, source_type, tags, now)
    else:
        # Treat as single page
        item = SourceItem(
            id=_hash_url(url),
            title=name,
            url=url,
            source_name=name,
            source_type="url",
            content=raw[:5000],  # Truncate large pages
            fetched_at=now,
            tags=tags,
        )
        return [item]


def _parse_feed(xml_text: str, source_name: str, source_type: str, tags: list[str], fetched_at: str) -> list[SourceItem]:
    """Minimal RSS/Atom XML parsing without external dependencies."""
    import re

    items: list[SourceItem] = []

    # Extract <item> (RSS) or <entry> (Atom) blocks
    if source_type == "atom":
        entries = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)
    else:
        entries = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)

    for entry_xml in entries[:20]:  # Limit to 20 items per feed
        title = _xml_tag(entry_xml, "title") or "Untitled"
        link = _xml_tag(entry_xml, "link") or _xml_attr(entry_xml, "link", "href") or ""
        content = _xml_tag(entry_xml, "description") or _xml_tag(entry_xml, "content") or _xml_tag(entry_xml, "summary") or ""
        pub_date = _xml_tag(entry_xml, "pubDate") or _xml_tag(entry_xml, "published") or _xml_tag(entry_xml, "updated") or ""

        # Strip HTML tags from content
        content = re.sub(r"<[^>]+>", " ", content).strip()[:2000]

        item_id = _hash_url(link or title)
        items.append(
            SourceItem(
                id=item_id,
                title=title,
                url=link,
                source_name=source_name,
                source_type=source_type,
                content=content,
                fetched_at=fetched_at,
                published_at=pub_date,
                tags=tags,
            )
        )

    log.info("Parsed %d items from '%s'", len(items), source_name)
    return items


def _xml_tag(xml: str, tag: str) -> str:
    """Extract text content of a simple XML tag."""
    import re

    # Handle CDATA
    m = re.search(rf"<{tag}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", xml, re.DOTALL)
    return m.group(1).strip() if m else ""


def _xml_attr(xml: str, tag: str, attr: str) -> str:
    """Extract an attribute value from a self-closing or opening XML tag."""
    import re

    m = re.search(rf'<{tag}\s[^>]*{attr}="([^"]*)"', xml)
    return m.group(1) if m else ""


def ingest_all(day: date | None = None) -> list[SourceItem]:
    """Fetch all configured sources, save raw items to notes dir."""
    day = day or date.today()
    sources = load_sources_config()
    all_items: list[SourceItem] = []

    for src in sources:
        items = fetch_source(src)
        all_items.extend(items)

    # Save raw items as JSON for downstream processing
    if all_items:
        notes_dir = settings.data_dir / "education" / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        out_path = notes_dir / f"{day.isoformat()}_raw.json"
        out_path.write_text(
            json.dumps([asdict(i) for i in all_items], indent=2, default=str),
            encoding="utf-8",
        )
        log.info("Saved %d raw items → %s", len(all_items), out_path.name)

    return all_items
