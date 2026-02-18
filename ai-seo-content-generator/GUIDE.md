# AI SEO Content Generator - Complete Setup Guide

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
8. [n8n Integration](#n8n-integration)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)

---

## Introduction

The AI SEO Content Generator is a powerful tool that automatically creates search-engine optimized content for your website, blog, or marketing campaigns. Using advanced AI models, it generates high-quality articles, blog posts, product descriptions, and more that are optimized for specific keywords and SEO best practices.

**Key Benefits:**
- Generate SEO-optimized content in seconds
- Save hours of manual writing and research
- Target specific keywords automatically
- Maintain consistent brand voice
- Scale content production effortlessly

---

## Prerequisites

Before installing, ensure you have:

- **Python 3.8 or higher**
- **pip3** (Python package manager)
- **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys)

---

## Installation

### Step 1: Extract the Package

```bash
unzip ai-seo-content-generator.zip
cd ai-seo-content-generator
```

### Step 2: Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

**What the setup script does:**
- Checks Python 3 installation
- Creates virtual environment
- Installs all required dependencies
- Creates `.env` file from template
- Initializes database

### Step 3: Configure Environment Variables

```bash
nano .env
```

**Required fields:**
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key
OPENAI_MODEL=gpt-4
PORT=8001
DB_PATH=./seo_generator.db
```

---

## Quick Start

### Start the Server

```bash
source venv/bin/activate
python3 main.py
```

### Generate Your First Article

```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "digital marketing strategies",
    "content_type": "blog_post",
    "word_count": 1000
  }'
```

**Expected Response:**
```json
{
  "content_id": 1,
  "title": "7 Digital Marketing Strategies That Will Transform Your Business in 2026",
  "content": "Full article content here...",
  "seo_score": 95,
  "keyword_density": "2.3%",
  "readability_score": "A",
  "generated_at": "2026-02-17T00:30:00Z"
}
```

---

## API Reference

### POST /generate

Generate SEO-optimized content.

**Request:**

```json
{
  "keyword": "your target keyword",
  "content_type": "blog_post|article|product_description|landing_page",
  "word_count": 1000,
  "tone": "professional|casual|enthusiastic",
  "target_audience": "beginners|experts|general"
}
```

**Response:**

```json
{
  "content_id": 1,
  "title": "SEO-Optimized Title",
  "content": "Full generated content...",
  "meta_description": "SEO meta description",
  "seo_score": 95,
  "keyword_density": "2.3%",
  "readability_score": "A",
  "generated_at": "2026-02-17T00:30:00Z"
}
```

### GET /content/{id}

Retrieve generated content by ID.

### GET /health

Health check endpoint.

---

## Usage Examples

### Example 1: Blog Post Generation

```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "content marketing tips",
    "content_type": "blog_post",
    "word_count": 1500,
    "tone": "professional",
    "target_audience": "beginners"
  }'
```

**Response:**

```json
{
  "content_id": 1,
  "title": "10 Content Marketing Tips Every Beginner Should Know",
  "content": "# 10 Content Marketing Tips Every Beginner Should Know\n\nContent marketing is a powerful strategy that can transform your business...",
  "meta_description": "Discover 10 essential content marketing tips that will help beginners create engaging content and grow their audience.",
  "seo_score": 92,
  "keyword_density": "2.1%",
  "readability_score": "A",
  "generated_at": "2026-02-17T00:30:00Z"
}
```

### Example 2: Product Description

```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "wireless headphones",
    "content_type": "product_description",
    "word_count": 300,
    "tone": "enthusiastic"
  }'
```

### Example 3: Landing Page Copy

```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "online fitness coaching",
    "content_type": "landing_page",
    "word_count": 800,
    "tone": "motivational"
  }'
```

---

## Troubleshooting

### Issue: OpenAI API errors

**Solution:**
```bash
# Verify API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check usage at: https://platform.openai.com/usage
```

### Issue: Content generation is slow

**Solution:**
- Use `gpt-3.5-turbo` instead of `gpt-4` for faster generation
- Reduce word count for testing
- Check internet connectivity

---

## Advanced Features

### Custom Templates

Create custom content templates in the `templates/` directory.

### Bulk Generation

Generate multiple pieces of content at once:

```bash
curl -X POST "http://localhost:8001/generate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "content_type": "blog_post",
    "word_count": 800
  }'
```

---

**Happy content creating! ✍️**
