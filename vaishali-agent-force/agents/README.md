# Agent Persona System

The Vaishali Agent Force uses **markdown-based persona definitions** to give each agent a distinct personality, voice, and behaviour rules. This system allows tweaking agent personalities without touching Python code.

## How It Works

Each agent has a `PERSONA.md` file in its directory:

```
agents/
├── README.md
├── finance/
│   └── PERSONA.md
├── health/
│   └── PERSONA.md
├── content/
│   └── PERSONA.md
├── education/
│   └── PERSONA.md
├── research/
│   └── PERSONA.md
└── braindump/
    └── PERSONA.md
```

## Persona File Format

Each `PERSONA.md` starts with YAML frontmatter followed by markdown sections:

```markdown
---
name: Owlbert
emoji: 🦉
agent: finance
personality: precise, cautious, no-nonsense
tone: professional but warm
---
# Owlbert — Finance Agent Persona

## Identity
[Description of who this agent is and what they care about]

## Voice & Tone
[Bullet points describing how the agent communicates]

## Response Templates
### Briefing Headline
Template text with {placeholders} matching JSON summary fields

### Anomaly Alert
Template text with {placeholders}

### Good News
Template text with {placeholders}

## Triggers & Priorities
[Bullet points describing when and what the agent focuses on]
```

## Frontmatter Fields

| Field | Type | Purpose |
|-------|------|---------|
| `name` | string | Agent's display name (e.g., "Owlbert") |
| `emoji` | string | Single emoji representing the agent (e.g., "🦉") |
| `agent` | string | Internal agent key (finance, health, content, etc.) |
| `personality` | string | Comma-separated personality traits |
| `tone` | string | Description of how the agent speaks |

## Response Templates

Templates use `{placeholder}` syntax matching JSON summary fields:

- `{field}` — Basic value replacement
- `{field:,.2f}` — Number formatting (comma thousands sep, 2 decimals)
- `{field_emoji}` — Emoji from trend mapping

**Safety:** If a placeholder is missing from the data, the template returns with the placeholder unfilled rather than crashing.

## Loading Personas

Use the `persona_loader` module to load personas in code:

```python
from vaishali.core.persona_loader import load_persona, get_persona_emoji, get_persona_headline

# Load a full persona
persona = load_persona("finance")
if persona:
    print(f"Agent: {persona.name} {persona.emoji}")
    print(f"Templates: {list(persona.templates.keys())}")

# Get emoji for an agent (with fallback)
emoji = get_persona_emoji("health")  # Returns "🐼" or "🤖" if not found

# Render a template with data
headline = get_persona_headline("finance",
    status_emoji="🟢",
    status="healthy",
    balance="1,234.56",
    anomaly_count="3"
)
```

## Integration Points

### Telegram Bot
The Telegram bot (`src/vaishali/telegram_bot/bot.py`) uses persona emojis as fallbacks when formatting briefings and agent status messages.

### Agent Briefings
Agents can load their own personas to customize response formatting before sending to briefings.

### Example: Finance Agent
The Finance Agent can load its Owlbert persona and use templates to format anomaly alerts with consistent voice and tone.

## Guidelines for Writing Personas

1. **Be specific to the domain**: Finance personas should reference GBP amounts, balance trends, and anomalies. Health personas should reference body scores and streaks.

2. **Use realistic templates**: Templates should have `{placeholders}` that match actual JSON summary field names.

3. **Keep templates concise**: They're meant to be brief, punchy headlines and alerts for briefings.

4. **Be consistent**: All personas use the same YAML frontmatter keys and section structure.

5. **Avoid dependencies**: Personas are loaded without the full bot running, so don't assume external services.

## Example Personas

### Owlbert (Finance)
- **Personality**: Precise, cautious, no-nonsense
- **Tone**: Professional but warm
- **Focus**: Flagging anomalies, celebrating savings, precise with numbers

### Bamboo (Health)
- **Personality**: Encouraging, celebratory, supportive
- **Tone**: Warm and enthusiastic
- **Focus**: Celebrating streaks, encouraging movement, body score trends

### Foxy (Content)
- **Personality**: Creative, strategic, ROI-focused
- **Tone**: Energetic, idea-driven
- **Focus**: Impact scores, high-effort ideas, drafts needing review

### Whiskers (Education / Research)
- **Personality**: Curious, knowledge-linking, exploratory
- **Tone**: Inquisitive and thoughtful
- **Focus**: New insights, entity/topic trends, deep-dive recommendations

### Brain (Braindump)
- **Personality**: Non-judgmental, action-oriented, organizer
- **Tone**: Neutral, matter-of-fact
- **Focus**: Inbox counts, inbox status, action priority

## Testing

Use the `dev_seed_example_data.py` script to verify persona loading:

```bash
python scripts/dev_seed_example_data.py
```

This generates sample data and tests persona loading.
