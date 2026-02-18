# AI Customer Support Bot - Complete Setup Guide

> Version: 1.0.0 | Last Updated: 2026-02-17

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Testing the Bot](#testing-the-bot)
6. [API Usage Examples](#api-usage-examples)
7. [Integration with n8n](#integration-with-n8n)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Features](#advanced-features)

---

## Introduction

The AI Customer Support Bot is an intelligent automation tool that handles customer inquiries across multiple channels (Email, Telegram, Slack) using OpenAI's GPT models. It provides instant, context-aware responses while automatically escalating complex issues to human agents.

**Key Benefits:**
- Reduce customer support workload by 70%
- 24/7 availability without hiring additional staff
- Consistent, professional responses
- Smart escalation for complex issues
- Built-in analytics and performance tracking

---

## Prerequisites

Before installing, ensure you have:

- **Python 3.8 or higher**
- **pip3** (Python package manager)
- **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Gmail Account** (for email support)
- **Telegram Bot Token** (optional - from [@BotFather](https://t.me/botfather))
- **Slack App** (optional - from [Slack API](https://api.slack.com/apps))

**To check Python version:**
```bash
python3 --version
```

---

## Installation

### Step 1: Clone or Download

```bash
# If you have the ZIP file, extract it to your preferred location
unzip ai-customer-support-bot.zip
cd ai-customer-support-bot

# Or if cloning from git:
git clone <repository-url>
cd ai-customer-support-bot
```

### Step 2: Run Setup Script

The automated setup script handles everything:

```bash
chmod +x setup.sh
./setup.sh
```

**What the setup script does:**
- Checks Python 3 installation
- Creates virtual environment
- Installs all required dependencies
- Creates `.env` file from template
- Initializes SQLite database
- Creates knowledge_base directory

**Expected Output:**
```
🤖 AI Customer Support Bot Setup
=================================
✅ Python 3.10.12 found
📦 Installing dependencies...
🔧 Creating virtual environment...
📥 Installing Python packages...
⚙️ Creating .env file from template...
📚 Creating knowledge base directory...
🗄️ Initializing database...
✅ Database initialized successfully

🎉 Setup completed successfully!
```

### Step 3: Configure Environment Variables

Edit the `.env` file with your API keys:

```bash
nano .env  # or use your preferred editor
```

**Required fields:**
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
PORT=8000
DB_PATH=./support_bot.db
KB_DIR=./knowledge_base
```

### Step 4: Start the Bot

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start the server
python3 main.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Configuration

### OpenAI Setup

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account or log in
3. Generate an API key
4. Add to `.env` file as `OPENAI_API_KEY`

### Gmail Setup (for Email Support)

1. Go to [Google Account Settings](https://myaccount.google.com/apppasswords)
2. Enable 2-factor authentication
3. Generate an "App Password" for mail
4. Use that password (not your Gmail password) in `.env`

### Telegram Bot Setup (Optional)

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the bot token and add to `.env` as `TELEGRAM_BOT_TOKEN`

### Slack App Setup (Optional)

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app
3. Enable Bot permissions
4. Install to workspace
5. Copy Bot Token and Signing Secret to `.env`

---

## Testing the Bot

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "uptime": 123.456,
  "version": "1.0.0"
}
```

### Test 2: Send a Chat Message

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my order",
    "user_id": "test-user-123"
  }'
```

**Expected Response:**
```json
{
  "response": "Hello! I'd be happy to help you with your order. Could you please provide your order number so I can look up the details for you?",
  "conversation_id": 1,
  "timestamp": "2026-02-17T00:30:00Z",
  "escalated": false
}
```

### Test 3: View Conversations

```bash
curl http://localhost:8000/conversations
```

**Expected Response:**
```json
{
  "conversations": [
    {
      "id": 1,
      "user_id": "test-user-123",
      "started_at": "2026-02-17T00:30:00Z",
      "last_message_at": "2026-02-17T00:31:00Z",
      "status": "active",
      "message_count": 2
    }
  ],
  "total": 1
}
```

---

## API Usage Examples

### Sending Messages

**Basic Message:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your business hours?",
    "user_id": "customer-456"
  }'
```

**Response:**
```json
{
  "response": "Our business hours are Monday-Friday, 9 AM to 6 PM EST. We're also available 24/7 through our AI support system for urgent inquiries.",
  "conversation_id": 2,
  "timestamp": "2026-02-17T00:35:00Z",
  "escalated": false
}
```

### Submitting Feedback

```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "message_id": 1,
    "rating": 5,
    "comment": "Very helpful response!"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback recorded successfully",
  "feedback_id": 1
}
```

### Viewing Analytics

```bash
curl http://localhost:8000/analytics
```

**Response:**
```json
{
  "total_conversations": 15,
  "total_messages": 47,
  "avg_response_time": 1.2,
  "escalation_rate": 0.13,
  "avg_satisfaction": 4.5,
  "resolved_automatically": 13,
  "escalated_to_human": 2
}
```

---

## Integration with n8n

### Import the Workflow

1. Open n8n dashboard
2. Click "Import from File" or "Import from URL"
3. Select `ai-support-workflow.json` (if included)
4. Configure the webhook nodes

### Configure Email Nodes

1. Find the Gmail/IMAP node
2. Add your Gmail credentials
3. Set polling interval (e.g., every 5 minutes)

### Configure OpenAI Node

1. Find the OpenAI Chat node
2. Add your OpenAI API key
3. Select model (gpt-3.5-turbo or gpt-4)

### Test the Workflow

1. Click "Execute Workflow"
2. Send a test email to your support address
3. Verify the response is generated correctly

---

## Troubleshooting

### Issue: Bot not responding to emails

**Possible Causes:**
1. IMAP not enabled in Gmail
2. Wrong password (use App Password)
3. Port 993 blocked

**Solutions:**
```bash
# Check if port 993 is accessible
telnet imap.gmail.com 993

# Enable IMAP in Gmail:
# Settings → Forwarding and POP/IMAP → Enable IMAP
# Use App Password, NOT regular password
```

### Issue: OpenAI API errors

**Possible Causes:**
1. Invalid API key
2. Insufficient credits
3. Rate limit exceeded

**Solutions:**
```bash
# Test API key directly:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check usage at: https://platform.openai.com/usage
# Add billing if needed: https://platform.openai.com/account/billing
```

### Issue: Database locked errors

**Possible Causes:**
1. Multiple processes accessing database
2. Database file permission issues

**Solutions:**
```bash
# Check for locked database
lsof support_bot.db

# Fix permissions
chmod 664 support_bot.db
```

### Issue: Telegram bot not receiving messages

**Possible Causes:**
1. Bot not started by user
2. Wrong bot token
3. Webhook not configured

**Solutions:**
```bash
# Start the bot by sending /start command
# Verify token with:
curl https://api.telegram.org/bot<TOKEN>/getMe
```

### Issue: Module not found errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Advanced Features

### Custom Knowledge Base

Add custom responses in `knowledge_base/`:

```json
{
  "greeting": {
    "patterns": ["hello", "hi", "hey"],
    "response": "Welcome! How can I assist you today?"
  },
  "hours": {
    "patterns": ["hours", "open", "when"],
    "response": "We're open Mon-Fri 9-6 EST"
  }
}
```

### Custom Escalation Rules

Edit the escalation logic in `main.py`:

```python
def should_escalate(message, context):
    # Keywords that trigger escalation
    escalate_keywords = ["refund", "complaint", "lawyer", "scam"]
    return any(keyword in message.lower() for keyword in escalate_keywords)
```

### Analytics Dashboard

Visit `http://localhost:8000` to see:
- Conversation trends
- Response time metrics
- Satisfaction ratings
- Escalation statistics

---

## Support

For issues or questions:
- Check this guide first
- Review logs in `support_bot.log`
- Open an issue on GitHub
- Contact MyWork-AI Marketplace support

---

**Happy automating! 🤖**
