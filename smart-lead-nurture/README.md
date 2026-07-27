# Smart Lead Nurture Automation

AI-powered lead nurturing workflow that automatically scores, segments, and follows up with leads using n8n + MyWork-AI.

## What It Does
1. **Lead Capture** — Webhook receives new leads from any form/CRM
2. **AI Scoring** — LLM analyzes lead data, assigns priority score (1-10)
3. **Smart Segmentation** — Routes leads to hot/warm/cold pipelines
4. **Auto Follow-up** — Sends personalized emails based on segment
5. **CRM Update** — Pushes enriched data back to your CRM
6. **Slack Alerts** — Notifies sales team for hot leads in real-time

## Quick Start
```bash
# Install MyWork-AI
pip install mywork-ai

# Setup n8n integration
mw n8n setup

# Import this automation
mw n8n import ./src/workflow.json

# Configure your credentials
mw n8n config
```

Create an n8n **Header Auth** credential named `Lead Webhook Auth` with header
`X-Lead-Secret` and a random value. Attach it to the imported webhook node;
callers must send this header before any OpenAI or email work begins.

## Requirements
- MyWork-AI v2.3+
- n8n instance (self-hosted or cloud)
- OpenAI API key (for AI scoring)
- SMTP or SendGrid (for emails)

## Architecture
```
Webhook → AI Score → Segment → [Hot] → Slack + Priority Email
                              → [Warm] → Nurture Sequence
                              → [Cold] → Monthly Newsletter
```

## Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your-key
LEAD_WEBHOOK_SECRET=replace-with-a-random-webhook-secret
OPENAI_API_KEY=your-key
SMTP_HOST=smtp.gmail.com
SLACK_WEBHOOK=https://hooks.slack.com/...
```

## License
Commercial — Purchased via MyWork-AI Marketplace

## Support
- Issues: File on this repo
- Docs: https://mywork-ai.dev/automations/smart-lead-nurture
