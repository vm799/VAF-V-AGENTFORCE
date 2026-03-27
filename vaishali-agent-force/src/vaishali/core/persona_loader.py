"""Load and cache agent persona definitions from markdown files.

Personas are defined in agents/{agent}/PERSONA.md with YAML frontmatter.
This module parses the frontmatter and extracts response templates without
external dependencies (no PyYAML, just regex).

Usage:
    from vaishali.core.persona_loader import load_persona, get_persona_emoji

    persona = load_persona("finance")
    if persona:
        print(f"{persona.name} {persona.emoji}")
        print(f"Templates: {list(persona.templates.keys())}")

    emoji = get_persona_emoji("health")  # "🐼" or "🤖" if not found
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Module-level cache
_persona_cache: dict[str, AgentPersona] = {}


@dataclass
class AgentPersona:
    """Loaded agent persona definition."""

    name: str
    emoji: str
    agent: str
    personality: str
    tone: str
    raw_content: str  # Full markdown after frontmatter
    templates: dict[str, str]  # Extracted from ## Response Templates


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter from markdown.

    Expects format:
        ---
        key: value
        key2: value2
        ---
        Rest of markdown...

    Returns:
        Tuple of (frontmatter_dict, remaining_markdown)
    """
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = match.group(2)

    # Parse YAML-like key: value lines
    frontmatter = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        frontmatter[key.strip()] = val.strip()

    return frontmatter, body


def _extract_templates(content: str) -> dict[str, str]:
    """Extract all ### Template sections from markdown.

    Looks for:
        ### Template Name
        Template content with {placeholders}
        And more content until the next ### or ##

    Returns dict mapping "Template Name" → "template content"
    """
    templates = {}

    # Find all ### heading sections
    sections = re.findall(r"^### (.+?)$\n((?:(?!^##)[^\n].*\n?)*)", content, re.MULTILINE)

    for template_name, template_content in sections:
        template_name = template_name.strip()
        # Remove trailing whitespace and empty lines
        template_content = template_content.rstrip()
        if template_content:
            templates[template_name] = template_content

    return templates


def load_persona(agent: str) -> AgentPersona | None:
    """Load PERSONA.md for a given agent.

    Looks in {base_dir}/agents/{agent}/PERSONA.md where base_dir is the
    vaishali-agent-force root (parent of src/).

    Returns:
        AgentPersona if found and valid, None otherwise.
        Results are cached in module-level dict to avoid re-reading disk.

    Args:
        agent: Agent key (finance, health, content, education, research, braindump)
    """
    # Check cache first
    if agent in _persona_cache:
        return _persona_cache[agent]

    # Find base directory (parent of src/)
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "src" / "vaishali").exists():
            base_dir = current
            break
        current = current.parent
    else:
        # Fallback to working directory
        base_dir = Path.cwd()

    persona_file = base_dir / "agents" / agent / "PERSONA.md"

    if not persona_file.exists():
        _persona_cache[agent] = None
        return None

    try:
        content = persona_file.read_text(encoding="utf-8")
    except Exception:
        _persona_cache[agent] = None
        return None

    frontmatter, body = _parse_frontmatter(content)

    # Validate required fields
    required = {"name", "emoji", "agent", "personality", "tone"}
    if not required.issubset(frontmatter.keys()):
        _persona_cache[agent] = None
        return None

    # Extract templates
    templates = _extract_templates(body)

    persona = AgentPersona(
        name=frontmatter["name"],
        emoji=frontmatter["emoji"],
        agent=frontmatter["agent"],
        personality=frontmatter["personality"],
        tone=frontmatter["tone"],
        raw_content=body,
        templates=templates,
    )

    _persona_cache[agent] = persona
    return persona


def get_persona_emoji(agent: str) -> str:
    """Get emoji for an agent, falling back to 🤖.

    Args:
        agent: Agent key

    Returns:
        Agent emoji or "🤖" if persona not found
    """
    persona = load_persona(agent)
    if persona:
        return persona.emoji
    return "🤖"


def get_persona_headline(agent: str, **kwargs) -> str | None:
    """Render the 'Briefing Headline' template with provided kwargs.

    If the template is not found or rendering fails, returns None.
    If a placeholder is missing from kwargs, the template is returned
    with the unfilled placeholder (e.g., "{balance:,.2f}") rather than crashing.

    Args:
        agent: Agent key
        **kwargs: Template variables (e.g., status_emoji="🟢", status="healthy")

    Returns:
        Rendered template string or None if template not found
    """
    persona = load_persona(agent)
    if not persona or "Briefing Headline" not in persona.templates:
        return None

    template = persona.templates["Briefing Headline"]
    return _render_template(template, **kwargs)


def _render_template(template: str, **kwargs) -> str:
    """Safely render template with placeholders.

    Handles format strings like:
        {field}               → simple substitution
        {field:,.2f}          → format with thousands sep, 2 decimals
        {field_emoji}         → simple substitution

    If a key is missing from kwargs, the placeholder is left unfilled
    (e.g., "{balance:,.2f}") rather than raising KeyError.

    Args:
        template: Template string with {placeholders}
        **kwargs: Variables to substitute

    Returns:
        Rendered template with filled placeholders
    """
    result = template

    # Find all placeholders: {key} or {key:format}
    placeholders = re.findall(r"\{([^}:]+)(?::([^}]+))?\}", template)

    for key, format_spec in placeholders:
        if key not in kwargs:
            # Leave unfilled placeholder as-is
            continue

        value = kwargs[key]

        # Apply format spec if provided
        if format_spec:
            try:
                if format_spec.endswith("f"):
                    # Number formatting
                    formatted = format(float(value), format_spec)
                else:
                    # Other format specs
                    formatted = format(value, format_spec)
            except (ValueError, TypeError):
                # If formatting fails, use string representation
                formatted = str(value)
        else:
            # No format spec, just convert to string
            formatted = str(value)

        # Replace all occurrences of this placeholder with formatted value
        placeholder_pattern = r"\{" + re.escape(key) + r"(?::[^}]+)?\}"
        result = re.sub(placeholder_pattern, formatted, result)

    return result


def list_personas() -> list[AgentPersona]:
    """Load all available agent personas.

    Returns:
        List of loaded AgentPersona objects (skips missing personas)
    """
    agents = ["finance", "content", "education", "research", "health", "braindump"]
    personas = []

    for agent in agents:
        persona = load_persona(agent)
        if persona:
            personas.append(persona)

    return personas


if __name__ == "__main__":
    # Quick test
    print("Testing persona loader...\n")

    for agent in ["finance", "health", "content", "education", "research", "braindump"]:
        persona = load_persona(agent)
        if persona:
            print(f"{persona.emoji} {persona.name}")
            print(f"   Agent: {persona.agent}")
            print(f"   Personality: {persona.personality}")
            print(f"   Tone: {persona.tone}")
            print(f"   Templates: {list(persona.templates.keys())}")
            print()
        else:
            print(f"❌ Could not load {agent}")
            print()
