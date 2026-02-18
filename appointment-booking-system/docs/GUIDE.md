# Appointment Booking System
## Complete User Guide

---

<div align="center">

**Version 1.0.0** | February 2026

Online Booking with Calendar Integration

</div>

---

## API Reference

### POST /bookings

```bash
curl -X POST "http://localhost:8004/bookings" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Jane Doe",
    "client_email": "jane@example.com",
    "service": "Consultation",
    "datetime": "2026-02-18T14:00:00Z",
    "duration_minutes": 60
  }'
```

---

© 2026 MyWork-AI Marketplace
