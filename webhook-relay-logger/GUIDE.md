# Webhook Relay Logger - Complete Setup Guide

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

A universal webhook receiver that logs, processes, and relays webhook events to multiple destinations. Perfect for debugging, monitoring, and integrating third-party services.

**Key Features:**
- Universal webhook receiver
- Request/response logging
- Multiple relay destinations
- Webhook replay
- Real-time monitoring
- Filter and transform

---

## Prerequisites

- **Python 3.8+**
- **pip3**

---

## Installation

```bash
unzip webhook-relay-logger.zip
cd webhook-relay-logger
chmod +x setup.sh
./setup.sh
```

Configure `.env`:
```env
PORT=8007
LOG_LEVEL=info
SECRET_KEY=your-secret-key
```

---

## Quick Start

```bash
python3 main.py
```

Test webhook:
```bash
curl -X POST "http://localhost:8007/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": {"key": "value"}}'
```

---

## API Reference

### POST /webhook/{endpoint}
Receive webhook.

### GET /logs
View all logs.

### POST /relay/{id}
Replay logged webhook.

---

**Happy webhooking! 🔗**
