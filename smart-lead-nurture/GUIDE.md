# Smart Lead Nurture - Complete Setup Guide

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

Smart Lead Nurture automatically engages and nurtures leads through personalized email sequences, SMS campaigns, and social media interactions. Uses AI to score leads and personalize communications.

**Key Features:**
- Automated email drip campaigns
- Lead scoring with AI
- Personalized messaging
- Multi-channel outreach
- Analytics and reporting

---

## Prerequisites

- **Python 3.8+**
- **pip3**
- **OpenAI API Key**
- **SendGrid API Key** (email)
- **Twilio API Key** (SMS)

---

## Installation

```bash
unzip smart-lead-nurture.zip
cd smart-lead-nurture
chmod +x setup.sh
./setup.sh
```

Configure `.env`:
```env
OPENAI_API_KEY=sk-your-key
SENDGRID_API_KEY=SG.your-key
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
PORT=8005
```

---

## Quick Start

```bash
python3 main.py
```

Add lead:
```bash
curl -X POST "http://localhost:8005/leads" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+1234567890",
    "source": "website",
    "interests": ["product_a", "consulting"]
  }'
```

---

## API Reference

### POST /leads
Add new lead.

### GET /leads/{id}
Get lead details.

### POST /campaigns/{id}/start
Start nurturing campaign.

---

**Happy nurturing! 🌱**
