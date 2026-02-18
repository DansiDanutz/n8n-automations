# AI Email Assistant
## Complete User Guide

---

<div align="center">

**Version 1.0.0** | February 2026

AI-Powered Email Management

</div>

---

## API Reference

### POST /draft

Generate email draft.

```bash
curl -X POST "http://localhost:8003/draft" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "john@example.com",
    "subject": "Meeting Follow-up",
    "context": "Follow up on yesterday meeting",
    "tone": "professional"
  }'
```

Response:
```json
{
  "subject": "Follow-up: Yesterday's Meeting",
  "body": "Dear John,\n\nThank you for...",
  "generated_at": "2026-02-17T00:30:00Z"
}
```

---

© 2026 MyWork-AI Marketplace
