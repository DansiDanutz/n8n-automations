# Invoice Generator API
## Complete User Guide

---

<div align="center">

**Version 1.0.0** | February 2026

Professional PDF Invoice Generation via REST API

</div>

---

## Table of Contents

1. Introduction
2. System Requirements
3. Installation
4. Configuration
5. API Reference
6. Usage Examples
7. Troubleshooting

---

## 1. Introduction

Generate professional PDF invoices programmatically. Perfect for:
- SaaS billing automation
- Freelance invoicing
- E-commerce platforms
- Service businesses

## 2. API Reference

### POST /invoices

Generate a new invoice.

```bash
curl -X POST "http://localhost:8002/invoices" \
  -H "Content-Type: application/json" \
  -d '{
    "client": {
      "name": "Acme Corporation",
      "email": "billing@acme.com"
    },
    "items": [
      {"description": "Service", "quantity": 10, "unit_price": 50}
    ],
    "invoice_number": "INV-001"
  }'
```

Response:
```json
{
  "invoice_id": "inv_xxx",
  "pdf_url": "https://...",
  "subtotal": 500.00,
  "total": 550.00
}
```

---

<div align="center">

© 2026 MyWork-AI Marketplace

</div>
