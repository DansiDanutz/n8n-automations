# Appointment Booking System - Complete Setup Guide

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

A complete appointment booking system with calendar integration, automated reminders, and booking management. Perfect for service businesses, healthcare providers, and consultants.

**Key Features:**
- Online booking widget
- Calendar sync (Google, Outlook)
- Automated email/SMS reminders
- Time zone handling
- Staff management

---

## Prerequisites

- **Python 3.8+**
- **pip3**
- **Google Calendar API Key** (optional)
- **Twilio API Key** (optional, for SMS reminders)

---

## Installation

```bash
unzip appointment-booking-system.zip
cd appointment-booking-system
chmod +x setup.sh
./setup.sh
```

Configure `.env`:
```env
PORT=8004
GOOGLE_CALENDAR_API_KEY=your-key
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
```

---

## Quick Start

```bash
python3 main.py
```

Create booking:
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

## API Reference

### POST /bookings
Create new booking.

### GET /bookings
List all bookings.

### GET /availability/{date}
Check availability.

---

**Happy booking! 📅**
