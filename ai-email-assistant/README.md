# AI Email Assistant
> Intelligent email management with AI-powered summarization, categorization, and automated responses

## 🎯 What This Does
Transforms your email workflow with AI that summarizes messages, categorizes emails, generates replies, detects spam, and prioritizes important communications. Integrates with Gmail, Outlook, and IMAP providers for seamless email automation and productivity enhancement.

## ✨ Features
- 📧 **Smart Email Summarization** - AI-powered email content summaries
- 🤖 **Automated Reply Generation** - Context-aware response suggestions
- 🏷️ **Intelligent Categorization** - Automatic email classification and labeling
- ⚡ **Priority Scoring** - Important emails surface first
- 🛡️ **Advanced Spam Detection** - AI-enhanced spam and phishing protection
- 🔔 **Webhook Integration** - Real-time notifications for important emails
- 📊 **Email Analytics** - Productivity insights and email statistics
- 🔗 **Multi-Provider Support** - Gmail, Outlook, and IMAP compatibility
- 🎛️ **Custom Rules Engine** - Automated actions based on email content
- 🔒 **Secure Authentication** - OAuth2 and token-based security

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Fill in API keys:
   - **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
   - **Gmail OAuth**: Setup at [Google Cloud Console](https://console.cloud.google.com/)
   - **Outlook API**: Configure at [Azure Portal](https://portal.azure.com/)
4. Run `pip install -r requirements.txt` to install dependencies
5. Test with `python -m pytest tests/` to verify setup works

## 📡 API Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| POST | `/emails/connect` | Connect email account | `curl -X POST -H "Content-Type: application/json" -d '{"provider":"gmail","credentials":{"client_id":"...","client_secret":"..."}}' http://localhost:8000/emails/connect` |
| GET | `/emails/inbox` | Get inbox with AI summaries | `curl -H "Authorization: Bearer TOKEN" http://localhost:8000/emails/inbox?limit=10` |
| POST | `/emails/{id}/summarize` | Generate email summary | `curl -X POST -H "Authorization: Bearer TOKEN" http://localhost:8000/emails/123/summarize` |
| POST | `/emails/{id}/reply` | Generate AI reply | `curl -X POST -H "Content-Type: application/json" -d '{"tone":"professional","context":"meeting follow-up"}' http://localhost:8000/emails/123/reply` |
| POST | `/emails/{id}/categorize` | Categorize email | `curl -X POST -H "Authorization: Bearer TOKEN" http://localhost:8000/emails/123/categorize` |
| POST | `/emails/{id}/priority` | Calculate priority score | `curl -X POST -H "Authorization: Bearer TOKEN" http://localhost:8000/emails/123/priority` |
| POST | `/emails/{id}/spam-check` | Check spam/phishing | `curl -X POST -H "Authorization: Bearer TOKEN" http://localhost:8000/emails/123/spam-check` |
| GET | `/analytics/dashboard` | Email productivity stats | `curl -H "Authorization: Bearer TOKEN" http://localhost:8000/analytics/dashboard` |
| POST | `/webhooks` | Setup webhook notifications | `curl -X POST -H "Content-Type: application/json" -d '{"url":"https://mysite.com/webhook","events":["high_priority","spam_detected"]}' http://localhost:8000/webhooks` |

## 💡 Use Cases
- **Executive Assistants** - Automatically summarize and prioritize emails for busy executives
- **Customer Support Teams** - Categorize support emails and generate response drafts
- **Sales Professionals** - Identify hot leads and automatically follow up on important prospects
- **Legal Professionals** - Detect urgent matters and classify emails by case or client
- **Perfect for** - Anyone who receives 50+ emails daily and wants AI-powered email management

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `OPENAI_API_KEY` | AI processing engine (required) | [OpenAI Platform](https://platform.openai.com/api-keys) | - |
| `DATABASE_URL` | Database connection | `postgresql://user:pass@localhost/db` or `sqlite:///emails.db` | `sqlite:///emails.db` |
| `GMAIL_CLIENT_ID` | Gmail OAuth client ID | [Google Cloud Console](https://console.cloud.google.com/) | - |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth secret | Google Cloud Console | - |
| `OUTLOOK_CLIENT_ID` | Microsoft Graph app ID | [Azure Portal](https://portal.azure.com/) | - |
| `OUTLOOK_CLIENT_SECRET` | Microsoft Graph secret | Azure Portal | - |
| `JWT_SECRET_KEY` | Token signing key (minimum 32 characters) | Generate random 256-bit key | - |
| `WEBHOOK_SECRET` | `X-Webhook-Secret` authentication value (minimum 32 characters) | Generate random 256-bit key | - |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Optional bootstrap login (password minimum 12 characters) | Operator-provided credentials | - |
| `EMAIL_SYNC_INTERVAL` | Auto-sync frequency (minutes) | Any positive integer | 15 |
| `MAX_EMAILS_PER_SYNC` | Sync batch size | 50-500 emails | 100 |
| `AI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` or `gpt-4` | `gpt-3.5-turbo` |
| `REDIS_URL` | Cache server (optional) | `redis://localhost:6379` | - |
| `LOG_LEVEL` | Logging verbosity | DEBUG, INFO, WARNING, ERROR | INFO |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  ai-email-assistant:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/emails
      - GMAIL_CLIENT_ID=${GMAIL_CLIENT_ID}
      - GMAIL_CLIENT_SECRET=${GMAIL_CLIENT_SECRET}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=emails
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Commands:
```bash
docker-compose up -d
docker-compose exec ai-email-assistant python -m alembic upgrade head
```

## 📊 Architecture
```
Email Providers → OAuth2 Auth → Email Sync Service
     ↓                              ↓
Database Storage ← AI Processing ← Content Analysis
     ↓                              ↓
WebSocket Updates → API Endpoints → Client Apps
     ↓                              ↓
Analytics Engine ← Webhook Events ← Action Triggers
```

Key Components:
- **Email Service**: Multi-provider email connectivity (Gmail, Outlook, IMAP)
- **AI Service**: OpenAI integration for summarization, categorization, replies
- **Auth Service**: OAuth2 flows and JWT token management
- **Webhook Service**: Real-time notifications for important events
- **Background Workers**: Async email processing and sync tasks

## 🆘 Troubleshooting
**Gmail OAuth setup issues:**
- Enable Gmail API in Google Cloud Console
- Add authorized redirect URIs: `http://localhost:8000/auth/gmail/callback`
- Create OAuth2 credentials for web application
- Verify scopes include `https://www.googleapis.com/auth/gmail.modify`

**Outlook/Office365 connection problems:**
- Register app in Azure Active Directory
- Configure API permissions: Mail.Read, Mail.Send, Mail.ReadWrite
- Admin consent may be required for organization accounts
- Check tenant ID and app registration status

**AI processing errors:**
- Verify OpenAI API key has sufficient credits
- Check rate limits and quota usage
- Large emails may hit token limits - consider chunking
- Monitor model availability (GPT-4 vs GPT-3.5-turbo)

**Database connection issues:**
- Run migrations: `python -m alembic upgrade head`
- Check database credentials and network connectivity
- Ensure PostgreSQL extensions are installed
- Verify database user has CREATE/ALTER permissions

**Email sync not working:**
- Check email provider API quotas and rate limits
- Verify OAuth tokens are still valid (refresh if needed)
- Monitor sync logs for specific error messages
- Gmail: Ensure "Less secure app access" is disabled (use OAuth2)

**Webhook delivery failures:**
- Verify webhook endpoint is publicly accessible
- Check SSL certificate validity for HTTPS endpoints
- Monitor webhook retry logic and failure patterns
- Validate webhook signature verification

## 📝 License
Private — purchased via MyWork-AI Marketplace
