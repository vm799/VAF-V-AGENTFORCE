# VAF Enterprise — Client Deployment Guide

**For:** Technical lead or implementation partner deploying VAF for a client
**Time to deploy:** 2–4 hours for a standard deployment

---

## What the Client Gets

- 9-build AI pipeline (Ingestion → Output)
- Orchestrator with CLI interface
- Interactive HTML dashboard
- Delivery to Slack / Teams / Telegram
- Compliance checking layer (configurable rules)
- Full source code, no vendor lock-in

---

## Step 1: Configure the Knowledge Source

Edit `.env` in the root directory:

```bash
# Choose ONE knowledge source

# Option A: Obsidian (demo/personal)
KB_TYPE=obsidian
OBSIDIAN_PATH=/path/to/their/vault

# Option B: Confluence (enterprise)
KB_TYPE=confluence
CONFLUENCE_URL=https://their-company.atlassian.net
CONFLUENCE_SPACE=ENG
CONFLUENCE_USER=api-user@company.com
CONFLUENCE_TOKEN=their-api-token

# Option C: SharePoint (enterprise)
KB_TYPE=sharepoint
SHAREPOINT_TENANT=their-company.sharepoint.com
SHAREPOINT_SITE=MainSite
SHAREPOINT_CLIENT_ID=azure-app-client-id
SHAREPOINT_CLIENT_SECRET=azure-app-secret
```

---

## Step 2: Configure Delivery Channels

```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ

# Telegram
VAF_TELEGRAM_TOKEN=bot-token
VAF_TELEGRAM_CHAT_ID=chat-id

# Microsoft Teams
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

---

## Step 3: Customise Compliance Rules

Edit `vaf-am-build-07-compliance/src/rules.py` — or hand off to the client's compliance team with the template:

```python
COMPLIANCE_RULES = [
    {"id": "FCA-001", "pattern": "...", "action": "flag"},
    {"id": "GDPR-001", "pattern": "...", "action": "redact"},
    # Add client-specific rules here
]
```

---

## Step 4: Run the Pipeline

```bash
# Test run (ingestion only)
python3 orchestrator.py run --mode ingestion-only

# Full run with dashboard
python3 orchestrator.py run --mode with-dashboard

# Check status
python3 orchestrator.py show-status
```

---

## Step 5: Schedule Runs (optional)

Add to crontab or client's task scheduler:

```bash
# Run every weekday at 6am
0 6 * * 1-5 cd /path/to/deployment && python3 orchestrator.py run --mode with-dashboard
```

---

## Handover Checklist

- [ ] Knowledge source connected and tested (`orchestrator.py run --mode ingestion-only` passes)
- [ ] At least one delivery channel configured and tested
- [ ] Compliance rules reviewed and customised for client's industry
- [ ] Full pipeline run completes: `orchestrator.py run --mode with-dashboard`
- [ ] Dashboard displays correctly in client's browser
- [ ] Client team member trained on: running pipeline, reading dashboard, adjusting rules
- [ ] Scheduled run configured (if required)
- [ ] Source code committed to client's repository (they own it)
- [ ] 30-day support window agreed and communicated

---

## Maintenance & Support

The system is self-contained. After deployment:

- **Routine:** Scheduled runs happen automatically. Client monitors dashboard.
- **Rule updates:** Client adjusts compliance rules in `rules.py` (training provided).
- **New data sources:** Add new source in Build 01 `ingestion.py` — template provided.
- **Breaking changes:** Slack/Teams API changes may require webhook URL updates.

---

## Client Training (2 hours)

| Session | Content | Who attends |
|---------|---------|-------------|
| 1 | Pipeline overview + run the demo together | Technical lead + one business stakeholder |
| 2 | Dashboard walkthrough + how to read outputs | Business stakeholders |
| 3 | Compliance rules — how to add/modify | Compliance team |
| 4 | Troubleshooting + common errors | Technical lead only |
