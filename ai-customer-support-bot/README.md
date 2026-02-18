# AI Customer Support Bot
> Intelligent customer support automation that reduces workload by 70% while maintaining customer satisfaction

## 🎯 What This Does
Automatically handles customer support across email, Telegram, and Slack using AI-powered responses. Smart escalation ensures complex issues reach human agents while routine questions get instant, accurate replies. Perfect for businesses wanting 24/7 support coverage without the cost.

## ✨ Features
- 📧 **Multi-platform Support** - Email, Telegram, and Slack integration
- 🤖 **OpenAI-Powered Responses** - Intelligent, context-aware replies
- 🚀 **Smart Escalation** - Automatically forwards complex issues to humans
- 📝 **Customizable Templates** - Pre-built responses for common questions
- 📊 **Analytics Dashboard** - Track performance and engagement metrics
- ⚡ **Real-time Processing** - Instant responses to customer inquiries
- 🔄 **n8n Workflow** - Easy setup with visual workflow automation
- 📈 **Performance Tracking** - Monitor response times and satisfaction

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Fill in API keys:
   - **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
   - **Email Credentials**: Gmail app password from [Google Account Settings](https://myaccount.google.com/apppasswords)
   - **Telegram Bot Token**: Create bot with [@BotFather](https://t.me/botfather)
   - **Slack App**: Create at [Slack API](https://api.slack.com/apps)
4. Run `./setup.sh` to install dependencies and create bot
5. Test with `node support-bot.js` and send test email/message

## 📡 API Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| GET | `/health` | Health check and uptime | `curl http://localhost:3001/health` |
| GET | `/stats` | Bot statistics and metrics | `curl http://localhost:3001/stats` |
| GET | `/` | Dashboard and bot overview | Visit in browser |

## 💡 Use Cases
- **E-commerce Support** - Handle order status, shipping, and return questions automatically
- **SaaS Customer Success** - Answer billing, feature, and troubleshooting questions 24/7
- **Service Businesses** - Manage appointment inquiries, pricing questions, and general info
- **Perfect for** - Small to medium businesses wanting professional support without hiring agents
- **Ideal when** - You get repetitive questions that could be automated

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `OPENAI_API_KEY` | AI response generation (required) | [OpenAI Platform](https://platform.openai.com/api-keys) | - |
| `EMAIL_USER` | Support email address (required) | Your Gmail account | - |
| `EMAIL_PASS` | Gmail app password (required) | [Google App Passwords](https://myaccount.google.com/apppasswords) | - |
| `HUMAN_AGENT_EMAIL` | Escalation target email | Your agent's email | Same as EMAIL_USER |
| `TELEGRAM_BOT_TOKEN` | Telegram integration (optional) | [@BotFather](https://t.me/botfather) | - |
| `SLACK_BOT_TOKEN` | Slack integration (optional) | [Slack API](https://api.slack.com/apps) | - |
| `SLACK_SIGNING_SECRET` | Slack verification (optional) | Slack app settings | - |
| `PORT` | Web dashboard port | Any available port | 3001 |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  ai-support-bot:
    build: .
    ports:
      - "3001:3001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EMAIL_USER=${EMAIL_USER}
      - EMAIL_PASS=${EMAIL_PASS}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

Run with: `docker-compose up -d`

## 📊 Architecture
```
Customer Email/Telegram/Slack
         ↓
    Bot Listener (IMAP/Polling)
         ↓
    Content Analysis → Escalation Check
         ↓                    ↓
    OpenAI Response      Human Agent
         ↓                    ↓
    Auto Reply          Escalation Email
         ↓
    Analytics Update
```

## 🆘 Troubleshooting
**Bot not responding to emails:**
- Check Gmail IMAP is enabled: Settings → Forwarding and POP/IMAP
- Verify app password (not regular password)
- Check `support-bot.log` for connection errors

**OpenAI errors:**
- Verify API key has credits remaining
- Check rate limits at [OpenAI Usage](https://platform.openai.com/usage)

**Telegram not working:**
- Ensure bot token is correct
- Bot must be started by sending `/start` command first

**n8n workflow issues:**
- Import `ai-support-workflow.json` into n8n
- Configure email nodes with your credentials
- Set OpenAI API key in n8n settings

## 📝 License
Private — purchased via MyWork-AI Marketplace