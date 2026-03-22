# iOS Shortcut: "Drop to VAF" — One-Tap Capture

## What This Does

Creates an iOS Shortcut that appears in your Share Sheet on iPhone/iPad. When you share ANY content (a URL from Safari, text from Notes, output from Claude Mobile), it sends it directly to your VAF API where:

1. The **Orchestrator** detects which agent should handle it
2. **Claude Haiku** enriches it with structured insights + revenue angle
3. It's written to **Obsidian** as a formatted note
4. It appears on your **VAF Dashboard** immediately

**No Telegram needed. No copy-paste. One tap.**

---

## Prerequisites

1. VAF services running: `./vaf.sh restart`
2. Your Mac's local IP address (run: `ipconfig getifaddr en0`)
3. Optional: Set `VAF_CAPTURE_API_KEY` in your `.env` for security

---

## Step-by-Step: Build the Shortcut

### Open Shortcuts App → + New Shortcut

### Step 1: Accept Share Input
- Add action: **Receive** → select "Any" input from Share Sheet
- This captures whatever you're sharing (URL, text, etc.)

### Step 2: Get Text from Input
- Add action: **Get Text from Input**
- This normalises whatever you shared into text

### Step 3: Set Variable
- Add action: **Set Variable** → name it `captured_content`

### Step 4: Build the JSON Body
- Add action: **Text**
- Enter this (replace YOUR_MAC_IP with your IP):

```
{"content": "[captured_content]", "source_url": "[captured_content]"}
```

- Tap `[captured_content]` and select the variable from Step 3

### Step 5: Get Contents of URL (HTTP POST)
- Add action: **Get Contents of URL**
- URL: `http://YOUR_MAC_IP:8000/api/capture`
- Method: **POST**
- Headers:
  - `Content-Type`: `application/json`
  - `Authorization`: `Bearer YOUR_API_KEY` (if you set VAF_CAPTURE_API_KEY)
- Request Body: **File** → select the Text from Step 4

### Step 6: Get Dictionary Value
- Add action: **Get Dictionary Value** from the response
- Key: `agent`

### Step 7: Show Notification
- Add action: **Show Notification**
- Title: `VAF Captured`
- Body: `[agent] took it. Check your dashboard.`

### Step 8: Name & Icon
- Name: **Drop to VAF**
- Icon: 🧠 (or ⚡)
- Color: Gold/Orange
- Enable: **Show in Share Sheet**

---

## Alternative: Quick Shortcut (No Enrichment)

For rapid-fire brain dumps where speed matters more than depth:

Same steps as above but change:
- Step 5 URL: `http://YOUR_MAC_IP:8000/api/capture/quick`

This skips LLM enrichment — just detects agent, saves to SQLite + Obsidian.

---

## Testing

1. Open Safari on your iPhone
2. Navigate to any article
3. Tap Share → "Drop to VAF"
4. Check your VAF Dashboard → Captures panel
5. Check Obsidian → the note should be in the right vault folder

---

## Troubleshooting

| Issue | Fix |
|---|---|
| "Could not connect" | Make sure VAF is running (`./vaf.sh restart`) and phone is on same WiFi |
| 401 error | Check your Bearer token matches `VAF_CAPTURE_API_KEY` in `.env` |
| 403 error | API key mismatch — regenerate in `.env` and update shortcut |
| Slow response | Normal — enrichment takes 2-4s (Claude Haiku call). Use `/capture/quick` for speed |
| No Obsidian note | Check `VAF_OBSIDIAN_VAULT_DIR` is set in `.env` |

---

## .env Setup

Add these to your `vaishali-agent-force/.env`:

```bash
# iOS Shortcut authentication (generate any random string)
VAF_CAPTURE_API_KEY=vaf_sk_your_random_secret_key_here

# Your Obsidian vault path (for writing enriched notes)
VAF_OBSIDIAN_VAULT_DIR=/Users/mcmehmios/path/to/your/obsidian/vault
```

---

## curl Test (from your Mac terminal)

```bash
# Test enriched capture
curl -X POST http://localhost:8000/api/capture \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer vaf_sk_your_random_secret_key_here" \
  -d '{"content": "Just discovered LangGraph supports parallel fan-out with checkpointing. Could speed up morning pipeline 3x.", "source_url": ""}'

# Test quick capture
curl -X POST http://localhost:8000/api/capture/quick \
  -H "Content-Type: application/json" \
  -d '{"content": "Brain dump: need to review the AWS Claude course module 3 on tool use"}'
```

Expected response:
```json
{
  "status": "saved",
  "enriched": true,
  "agent": "FORGE",
  "title": "LangGraph Parallel Fan-Out for Morning Pipeline",
  "signal_rating": "🟢",
  "vault_path": "03 Builds/Captures/2026-03-22-LangGraph-Parallel-Fan-Out-for-Morning.md",
  "obsidian_written": true,
  "revenue_angle": "💰 Build → teach → portfolio → consulting",
  "summary": "LangGraph's parallel fan-out could reduce morning pipeline from 90s to 30s..."
}
```
