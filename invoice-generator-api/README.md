# Invoice Generator API
> Professional invoice generation with PDF export, multi-currency support, and webhook notifications

## 🎯 What This Does
Creates beautiful, branded invoices programmatically with automatic tax calculation, 150+ currencies, and PDF generation. Perfect for SaaS apps, e-commerce platforms, and service businesses that need to automate billing workflows.

## ✨ Features
- 🏗️ **RESTful FastAPI** - Modern, fast, and fully documented API
- 📄 **Professional PDF Templates** - Beautiful, customizable invoice designs
- 💱 **Multi-Currency Support** - 150+ currencies with exchange rates
- 🧮 **Smart Tax Calculation** - VAT, sales tax, and custom rates
- 🔔 **Webhook Notifications** - Real-time status updates
- 📊 **Invoice Tracking** - Status management (draft, sent, paid, overdue)
- 🎨 **Custom Branding** - Add your logo, colors, and company details
- 🗃️ **Database Storage** - SQLite or PostgreSQL support
- 📈 **Analytics Dashboard** - Revenue tracking and payment analytics
- 🔄 **Background Processing** - Async PDF generation and notifications

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Fill in configuration:
   - Set `DATABASE_URL` (defaults to SQLite)
   - Add company branding details
   - Configure SMTP for email notifications (optional)
4. Run `./setup.sh` to create virtual environment and install dependencies
5. Test with `python test_api.py` - creates sample invoice and PDF

## 📡 API Endpoints

All invoice endpoints require `X-API-Key: $API_KEY`.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| POST | `/api/v1/invoices` | Create new invoice | `curl -X POST -H "Content-Type: application/json" -d '{"client":{"name":"Acme Corp","email":"billing@acme.com"},"items":[{"description":"Web Design","quantity":1,"rate":500.00}]}' http://localhost:8000/api/v1/invoices` |
| GET | `/api/v1/invoices` | List invoices with filters | `curl http://localhost:8000/api/v1/invoices?status=paid&limit=10` |
| GET | `/api/v1/invoices/{id}` | Get invoice details | `curl http://localhost:8000/api/v1/invoices/inv-123` |
| GET | `/api/v1/invoices/{id}/pdf` | Download invoice PDF | `curl -o invoice.pdf http://localhost:8000/api/v1/invoices/inv-123/pdf` |
| PATCH | `/api/v1/invoices/{id}/status` | Update invoice status | `curl -X PATCH -d '{"status":"paid"}' http://localhost:8000/api/v1/invoices/inv-123/status` |
| POST | `/api/v1/webhooks` | Create webhook | `curl -X POST -d '{"url":"https://mysite.com/webhook","events":["invoice.paid"]}' http://localhost:8000/api/v1/webhooks` |
| GET | `/api/v1/analytics/dashboard` | Get revenue analytics | `curl http://localhost:8000/api/v1/analytics/dashboard` |
| GET | `/api/v1/currencies` | List supported currencies | `curl http://localhost:8000/api/v1/currencies` |

## 💡 Use Cases
- **SaaS Billing** - Automatically generate invoices when subscriptions renew or upgrades happen
- **E-commerce Orders** - Create invoices for high-value B2B orders with custom payment terms
- **Service Businesses** - Bill clients for consulting, design, or professional services
- **Marketplace Platforms** - Generate seller payouts and buyer invoices automatically
- **Perfect for** - Any business that needs programmatic invoice generation with professional appearance

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `API_KEY` | `X-API-Key` credential (minimum 32 characters) | Generate a random 256-bit value | - |
| `CORS_ALLOWED_ORIGINS` | Credentialed browser origins | Comma-separated origins | `http://localhost:3000` |
| `DATABASE_URL` | Database connection string | Local: `sqlite:///./invoices.db` PostgreSQL: `postgresql://user:pass@localhost/db` | `sqlite:///./invoices.db` |
| `SECRET_KEY` | API security key | Generate random string | - |
| `COMPANY_NAME` | Your business name | Your business registration | - |
| `COMPANY_ADDRESS` | Business address for invoices | Your business address | - |
| `COMPANY_EMAIL` | Contact email | Your business email | - |
| `COMPANY_LOGO_URL` | Logo for invoices | Upload logo and get URL | - |
| `SMTP_HOST` | Email server for notifications | Gmail: `smtp.gmail.com` | - |
| `SMTP_USER` | Email username | Your email address | - |
| `SMTP_PASSWORD` | Email password | App password for Gmail | - |
| `EXCHANGERATE_API_KEY` | Currency exchange rates | [ExchangeRate API](https://app.exchangerate-api.com/sign-up/free) | Built-in rates |
| `API_PORT` | Server port | Any available port | 8000 |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  invoice-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/invoices
      - COMPANY_NAME=Your Company
      - COMPANY_EMAIL=billing@yourcompany.com
    depends_on:
      - db
    volumes:
      - ./invoices:/app/invoices
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=invoices
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Commands:
```bash
docker-compose up -d
docker-compose logs -f invoice-api
```

## 📊 Architecture
```
Client Request → FastAPI Router → Business Logic
     ↓                              ↓
PDF Generation ← Database Models ← Validation
     ↓                              ↓
File Storage → Background Tasks → Webhooks
     ↓                              ↓
Response ← Analytics ← Email Notifications
```

## 🆘 Troubleshooting
**PDF generation fails:**
- Check disk space in `/invoices` directory
- Ensure ReportLab dependencies are installed: `pip install reportlab pillow`
- Verify write permissions to invoices folder

**Database connection errors:**
- SQLite: Check file permissions and disk space
- PostgreSQL: Verify connection string format and database exists
- Run `alembic upgrade head` for schema updates

**Webhook delivery fails:**
- Check target URL is reachable
- Verify webhook endpoint accepts POST requests
- Check webhook logs in database for retry attempts

**Currency conversion issues:**
- Free tier of ExchangeRate API has limits
- Fallback to built-in rates if API unavailable
- Check API key is valid and active

**Email notifications not sending:**
- Verify SMTP credentials and server settings
- For Gmail: Enable 2FA and use app password
- Check firewall allows SMTP port (587/465)

## 📝 License
Private — purchased via MyWork-AI Marketplace
