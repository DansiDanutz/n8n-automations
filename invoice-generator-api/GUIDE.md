# Invoice Generator API - Complete Setup Guide

> Version: 1.0.0 | Last Updated: 2026-02-17

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

The Invoice Generator API is a powerful REST API that automatically creates professional PDF invoices from simple JSON data. Perfect for businesses that need to generate invoices programmatically, automate billing workflows, or integrate invoicing into existing systems.

**Key Features:**
- Generate PDF invoices from JSON
- Customizable templates
- Automatic calculations (subtotal, tax, total)
- Multiple currency support
- Email invoice delivery
- API-based integration

---

## Prerequisites

Before installing, ensure you have:

- **Python 3.8 or higher**
- **pip3** (Python package manager)
- **Resend API Key** - Get from [Resend](https://resend.com/api-keys) (for email delivery)

---

## Installation

### Step 1: Extract the Package

```bash
unzip invoice-generator-api.zip
cd invoice-generator-api
```

### Step 2: Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

### Step 3: Configure Environment Variables

```bash
nano .env
```

```env
# Server Configuration
PORT=8002

# Email Configuration (Resend)
RESEND_API_KEY=re_your-actual-api-key
RESEND_FROM_EMAIL=billing@yourcompany.com

# Invoice Defaults
DEFAULT_CURRENCY=USD
DEFAULT_TAX_RATE=0.10
```

---

## Quick Start

### Start the Server

```bash
source venv/bin/activate
python3 main.py
```

### Generate Your First Invoice

```bash
curl -X POST "http://localhost:8002/invoices" \
  -H "Content-Type: application/json" \
  -d '{
    "client": {
      "name": "Acme Corporation",
      "email": "billing@acme.com",
      "address": "123 Business St, City, Country"
    },
    "items": [
      {"description": "Web Development Services", "quantity": 40, "unit_price": 50},
      {"description": "Hosting Setup", "quantity": 1, "unit_price": 100}
    ],
    "invoice_number": "INV-2026-001",
    "due_date": "2026-03-17"
  }'
```

**Expected Response:**
```json
{
  "invoice_id": "inv_1234567890",
  "invoice_number": "INV-2026-001",
  "pdf_url": "https://your-domain.com/invoices/inv_1234567890.pdf",
  "subtotal": 2100.00,
  "tax": 210.00,
  "total": 2310.00,
  "currency": "USD",
  "created_at": "2026-02-17T00:30:00Z"
}
```

---

## API Reference

### POST /invoices

Generate a new PDF invoice.

**Request:**
```json
{
  "client": {
    "name": "Client Name",
    "email": "client@email.com",
    "address": "Client Address"
  },
  "items": [
    {
      "description": "Service/Product",
      "quantity": 1,
      "unit_price": 100
    }
  ],
  "invoice_number": "INV-001",
  "due_date": "2026-03-01",
  "currency": "USD",
  "tax_rate": 0.10,
  "notes": "Payment due within 30 days"
}
```

**Response:**
```json
{
  "invoice_id": "inv_xxx",
  "invoice_number": "INV-001",
  "pdf_url": "...",
  "subtotal": 100.00,
  "tax": 10.00,
  "total": 110.00
}
```

### GET /invoices/{id}

Retrieve invoice details.

### POST /invoices/{id}/send

Send invoice via email.

---

## Usage Examples

### Example 1: Basic Invoice

```bash
curl -X POST "http://localhost:8002/invoices" \
  -H "Content-Type: application/json" \
  -d '{
    "client": {"name": "John Doe", "email": "john@example.com"},
    "items": [
      {"description": "Consulting Hours", "quantity": 10, "unit_price": 75}
    ],
    "invoice_number": "INV-001"
  }'
```

### Example 2: Multi-Item Invoice with Tax

```bash
curl -X POST "http://localhost:8002/invoices" \
  -H "Content-Type: application/json" \
  -d '{
    "client": {
      "name": "Tech Solutions Inc",
      "email": "accounts@techsolutions.com"
    },
    "items": [
      {"description": "Software License", "quantity": 5, "unit_price": 199},
      {"description": "Support Plan", "quantity": 1, "unit_price": 499}
    ],
    "invoice_number": "INV-2026-045",
    "currency": "EUR",
    "tax_rate": 0.20
  }'
```

### Example 3: Send Invoice via Email

```bash
curl -X POST "http://localhost:8002/invoices/inv_xxx/send" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Your invoice is ready", "message": "Please find attached..."}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PDF generation fails | Check templates directory exists |
| Email not sending | Verify Resend API key |
| Port in use | Change PORT in .env |
| Currency issues | Use valid ISO currency codes |

---

**Happy invoicing! 💰**
