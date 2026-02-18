# Social Media Auto Poster - Complete Setup Guide

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

Automatically post content across multiple social media platforms with AI-generated captions, optimal scheduling, and hashtag suggestions. Supports Twitter, LinkedIn, Instagram, Facebook, and more.

**Key Features:**
- Multi-platform posting
- AI caption generation
- Optimal time scheduling
- Hashtag suggestions
- Bulk upload support
- Analytics tracking

---

## Prerequisites

- **Python 3.8+**
- **pip3**
- **OpenAI API Key**
- **Platform API Keys** (Twitter, LinkedIn, etc.)

---

## Installation

```bash
unzip social-media-auto-poster.zip
cd social-media-auto-poster
chmod +x setup.sh
./setup.sh
```

Configure `.env`:
```env
OPENAI_API_KEY=sk-your-key
TWITTER_API_KEY=your-key
LINKEDIN_CLIENT_ID=your-id
FACEBOOK_PAGE_ID=your-id
PORT=8006
```

---

## Quick Start

```bash
python3 main.py
```

Create post:
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

## API Reference

### POST /posts
Create scheduled post.

### GET /posts
List all posts.

### POST /generate-caption
Generate AI caption.

---

**Happy posting! 📱**
