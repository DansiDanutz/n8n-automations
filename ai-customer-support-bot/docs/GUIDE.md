# AI Customer Support Bot
## Complete User Guide

---

<div align="center">

**Version 1.0.0** | February 2026

A Professional Guide to Setting Up and Using
the AI Customer Support Bot

</div>

---

## 📋 Table of Contents

| Section | Page |
|---------|------|
| 1. Introduction | 3 |
| 2. System Requirements | 4 |
| 3. Installation Guide | 5 |
| 4. Configuration | 7 |
| 5. First Steps | 10 |
| 6. API Reference | 12 |
| 7. Usage Examples | 16 |
| 8. n8n Integration | 20 |
| 9. Troubleshooting | 24 |
| 10. Advanced Configuration | 28 |

---

## 1. Introduction

### 1.1 Overview

The AI Customer Support Bot is a sophisticated automation tool designed to handle customer inquiries across multiple communication channels. Powered by OpenAI's advanced language models, it delivers intelligent, context-aware responses while automatically identifying complex issues that require human intervention.

### 1.2 Key Features

- **Multi-Channel Support**: Email, Telegram, and Slack integration
- **AI-Powered Responses**: Context-aware, natural language understanding
- **Smart Escalation**: Automatic routing of complex issues to human agents
- **Analytics Dashboard**: Real-time performance metrics and insights
- **Customizable Workflows**: Tailor responses to your business needs
- **24/7 Availability**: Continuous operation without fatigue

### 1.3 Business Benefits

| Benefit | Impact |
|---------|--------|
| Reduced Workload | 70% reduction in routine inquiries |
| Faster Response Times | Instant replies, 24/7 |
| Consistency | Uniform quality across all interactions |
| Cost Savings | Eliminate need for overnight staff |
| Customer Satisfaction | Improved with instant responses |

---

## 2. System Requirements

### 2.1 Minimum Requirements

| Component | Minimum Version |
|-----------|-----------------|
| Python | 3.8+ |
| RAM | 512MB |
| Disk Space | 100MB |
| Network | Stable internet connection |

### 2.2 API Requirements

| Service | Purpose |
|---------|---------|
| OpenAI API | AI response generation (Required) |
| Gmail | Email support (Required) |
| Telegram | Optional chat support |
| Slack | Optional team integration |

### 2.3 Verification Commands

```bash
# Check Python version
python3 --version

# Check pip availability
pip3 --version

# Test network connectivity
ping api.openai.com
```

---

## 3. Installation Guide

### Step 1: Obtain the Package

Extract the downloaded archive:

```bash
unzip ai-customer-support-bot.zip
cd ai-customer-support-bot
```

### Step 2: Run the Setup Script

Execute the automated setup:

```bash
chmod +x setup.sh
./setup.sh
```

**Setup Process:**

1. Python version verification
2. Virtual environment creation
3. Dependency installation
4. Environment file generation
5. Database initialization
6. Knowledge base setup

### Step 3: Verify Installation

Check that all components are ready:

```bash
# Verify virtual environment exists
ls -la venv/

# Verify database was created
ls -la support_bot.db

# Verify knowledge base directory
ls -la knowledge_base/
```

---

## 4. Configuration

### 4.1 Environment Variables

Edit the `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Server Configuration
PORT=8000

# Database Configuration
DB_PATH=./support_bot.db

# Knowledge Base
KB_DIR=./knowledge_base
```

### 4.2 OpenAI API Setup

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create account
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Paste into `.env` file

### 4.3 Gmail Configuration

**Enable IMAP:**

1. Go to Gmail Settings
2. Select "Forwarding and POP/IMAP"
3. Enable IMAP access
4. Save changes

**Create App Password:**

1. Visit [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" as the app
3. Generate password (16 characters)
4. Use this password (NOT your Gmail password)

### 4.4 Telegram Bot Setup (Optional)

1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Choose a name (e.g., "My Support Bot")
5. Choose a username (must end in `bot`)
6. Copy the token provided
7. Add to `.env` as `TELEGRAM_BOT_TOKEN`

### 4.5 Slack App Setup (Optional)

1. Visit [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name and select workspace
5. Navigate to "OAuth & Permissions"
6. Add scopes: `chat:write`, `channels:history`
7. Install to workspace
8. Copy Bot Token and Signing Secret

---

## 5. First Steps

### 5.1 Starting the Bot

```bash
# Activate virtual environment
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

### 5.2 Health Check

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{
  "status": "healthy",
  "uptime": 123.456,
  "version": "1.0.0"
}
```

### 5.3 First Test Message

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test"}'
```

**Expected Response:**

```json
{
  "response": "Hello! How can I help you today?",
  "conversation_id": 1,
  "timestamp": "2026-02-17T00:30:00Z",
  "escalated": false
}
```

---

## 6. API Reference

### 6.1 POST /chat

Send a message to the AI bot.

**Request:**

```json
{
  "message": "Your customer's message",
  "user_id": "unique-user-identifier"
}
```

**Response:**

```json
{
  "response": "AI-generated response",
  "conversation_id": 123,
  "timestamp": "2026-02-17T00:30:00Z",
  "escalated": false
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your refund policies?",
    "user_id": "customer-456"
  }'
```

### 6.2 GET /conversations

List all conversations.

**Response:**

```json
{
  "conversations": [
    {
      "id": 1,
      "user_id": "customer-456",
      "started_at": "2026-02-17T00:30:00Z",
      "last_message_at": "2026-02-17T00:35:00Z",
      "status": "active",
      "message_count": 5
    }
  ],
  "total": 1
}
```

### 6.3 GET /conversations/{id}

Get details of a specific conversation.

**Response:**

```json
{
  "id": 1,
  "user_id": "customer-456",
  "status": "active",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What are your refund policies?",
      "timestamp": "2026-02-17T00:30:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Our refund policy allows returns within 30 days...",
      "timestamp": "2026-02-17T00:30:05Z"
    }
  ]
}
```

### 6.4 POST /feedback

Submit feedback on a bot response.

**Request:**

```json
{
  "conversation_id": 1,
  "message_id": 2,
  "rating": 5,
  "comment": "Very helpful!"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Feedback recorded successfully",
  "feedback_id": 1
}
```

### 6.5 GET /analytics

View performance analytics.

**Response:**

```json
{
  "total_conversations": 150,
  "total_messages": 450,
  "avg_response_time": 1.2,
  "escalation_rate": 0.13,
  "avg_satisfaction": 4.5,
  "resolved_automatically": 130,
  "escalated_to_human": 20
}
```

### 6.6 GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "uptime": 12345.678,
  "version": "1.0.0"
}
```

---

## 7. Usage Examples

### 7.1 Customer Inquiry - Order Status

**Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I ordered last week but haven\'t received my package yet. Order #12345",
    "user_id": "customer-789"
  }'
```

**Response:**

```json
{
  "response": "I'm sorry to hear about the delay with your order #12345. Let me check the status for you. Based on our records, your order was shipped on February 10th and is currently in transit. The estimated delivery date is February 18th. You can track your package using the tracking number that was emailed to you. Is there anything else I can help you with?",
  "conversation_id": 45,
  "timestamp": "2026-02-17T00:40:00Z",
  "escalated": false
}
```

### 7.2 Complex Issue - Escalation

**Request:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "This is ridiculous! I want a full refund AND I\'m contacting my lawyer about this scam!",
    "user_id": "customer-101"
  }'
```

**Response:**

```json
{
  "response": "I understand your frustration and I want to help resolve this issue for you. This matter requires personal attention from our customer service team. I've escalated your case and a human agent will contact you within 2 hours. Your ticket ID is #ESCALATE-2026-001. In the meantime, could you provide more details about the specific issue you're experiencing?",
  "conversation_id": 46,
  "timestamp": "2026-02-17T00:45:00Z",
  "escalated": true,
  "ticket_id": "ESCALATE-2026-001"
}
```

### 7.3 Multiple Conversations

```bash
# Start conversation 1
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi", "user_id": "user-1"}'

# Start conversation 2
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "user-2"}'

# List all conversations
curl http://localhost:8000/conversations
```

---

## 8. n8n Integration

### 8.1 Importing the Workflow

1. Open n8n dashboard
2. Click "Import from File"
3. Select `ai-support-workflow.json`
4. Review the workflow structure

### 8.2 Configuring Email Node

1. Select the Gmail/IMAP node
2. Add credentials:
   - User: your email address
   - Password: App Password (not regular password)
3. Set polling interval (e.g., 300 seconds)

### 8.3 Configuring OpenAI Node

1. Select the OpenAI Chat node
2. Add API key
3. Configure model:
   - Model: `gpt-3.5-turbo` or `gpt-4`
   - Temperature: `0.7`
   - Max tokens: `500`

### 8.4 Testing the Workflow

1. Click "Execute Workflow"
2. Send test email to support address
3. Monitor execution in n8n
4. Verify AI response is generated

---

## 9. Troubleshooting

### 9.1 Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure venv is activated |
| OpenAI errors | Check API key and credits |
| Database locked | Kill extra processes |
| Port in use | Change PORT in .env |
| No email received | Check IMAP settings |

### 9.2 Debug Commands

```bash
# Check logs
tail -f support_bot.log

# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"

# Check port availability
netstat -tuln | grep 8000
```

### 9.3 Getting Help

- Check this guide
- Review logs
- Check OpenAI status
- Contact support

---

## 10. Advanced Configuration

### 10.1 Custom Knowledge Base

Create files in `knowledge_base/`:

```json
{
  "greeting": "Welcome to our support!",
  "hours": "Mon-Fri 9AM-6PM EST",
  "shipping": "Free shipping over $50"
}
```

### 10.2 Custom Escalation Rules

Modify `main.py`:

```python
ESCALATION_KEYWORDS = [
    "refund",
    "complaint",
    "lawyer",
    "scam",
    "fraud"
]
```

### 10.3 Performance Tuning

```env
# Increase response speed
OPENAI_MODEL=gpt-3.5-turbo-0125

# Or improve quality
OPENAI_MODEL=gpt-4-turbo
```

---

<div align="center">

**End of Guide**

For questions, visit support.mywork-ai.com

© 2026 MyWork-AI Marketplace

</div>
