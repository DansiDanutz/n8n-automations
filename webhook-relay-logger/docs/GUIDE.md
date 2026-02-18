# Webhook Relay Logger
## Complete User Guide

---

<div align="center">

**Version 1.0.0** | February 2026

Universal Webhook Receiver & Logger

</div>

---

## API Reference

### POST /webhook/{endpoint}

```bash
curl -X POST "http://localhost:8007/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": {"key": "value"}}'
```

### GET /logs

```bash
curl http://localhost:8007/logs
```

---

© 2026 MyWork-AI Marketplace
