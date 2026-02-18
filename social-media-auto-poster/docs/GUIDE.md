# Social Media Auto Poster
## Complete User Guide

---

<div align="center">

**Version 1.0.0** | February 2026

Multi-Platform Social Media Automation

</div>

---

## API Reference

### POST /posts

```bash
curl -X POST "http://localhost:8006/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["twitter", "linkedin"],
    "content": "Check out our new product launch!",
    "media_url": "https://example.com/image.jpg",
    "scheduled_for": "2026-02-18T10:00:00Z"
  }'
```

---

© 2026 MyWork-AI Marketplace
