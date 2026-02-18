# AI Email Assistant - Complete Setup Guide

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

The AI Email Assistant automatically drafts professional emails, manages inbox organization, and provides smart responses using AI. Perfect for busy professionals who want to save time on email management.

**Key Features:**
- AI-powered email drafting
- Smart reply suggestions
- Inbox categorization
- Follow-up reminders
- Email scheduling

---

## Prerequisites

- **Python 3.8+**
- **pip3**
- **OpenAI API Key**

---

## Installation

```bash
unzip ai-email-assistant.zip
cd ai-email-assistant
chmod +x setup.sh
./setup.sh
```

Configure `.env`:
```env
OPENAI_API_KEY=sk-your-key
PORT=8003
```

---

## Quick Start

```bash
python3 main.py
```

Generate email:
```bash
curl -X POST "http://localhost:8003/draft" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "john@example.com",
    "subject": "Project Update",
    "context": "Send a weekly progress update",
    "tone": "professional"
  }'
```

---

## API Reference

### POST /draft

Generate email draft.

### POST /reply

Generate reply suggestion.

### POST /schedule

Schedule email sending.

---

**Happy emailing! 📧**
