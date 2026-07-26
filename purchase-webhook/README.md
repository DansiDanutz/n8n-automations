# Purchase Webhook Service

Automated Stripe webhook handler that grants GitHub repository access to customers upon successful purchase.

## Overview

This FastAPI service listens for Stripe `checkout.session.completed` webhook events and automatically:

1. ✅ Receives and verifies Stripe webhook signatures
2. 🔍 Extracts buyer email and product information
3. 🔗 Maps products to GitHub repositories
4. 👥 Adds buyers as read-only collaborators to private repos
5. 📊 Tracks all purchases and access grants

## Features

- **Secure Webhook Handling**: Stripe signature verification
- **Automatic GitHub Access**: Read-only repository invitations
- **Purchase Tracking**: In-memory storage of all transactions
- **Error Handling**: Comprehensive logging and error recovery
- **Health Monitoring**: Built-in health check and metrics
- **Docker Support**: Ready for containerized deployment

## Quick Start

### 1. Clone and Setup

```bash
cd /home/Memo1981/n8n-automations/purchase-webhook
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env` file with your credentials:

```env
STRIPE_SECRET_KEY=sk_live_your_actual_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
GITHUB_TOKEN=ghp_your_github_token
GITHUB_OWNER=DansiDanutz
MANAGEMENT_API_KEY=replace-with-at-least-32-random-characters
```

### 4. Run the Service

```bash
# Development
python main.py

# Production with Docker
docker build -t purchase-webhook .
docker run -d -p 8000:8000 --env-file .env purchase-webhook
```

## API Endpoints

### Webhook Endpoint
- **POST** `/webhook/stripe` - Receives Stripe webhook events
  - Validates signatures
  - Processes `checkout.session.completed` events
  - Grants GitHub repository access

### Management Endpoints
- **GET** `/health` - Service health and status
- **GET** `/purchases` - List all purchases (supports `?email=` filter)
- **GET** `/purchases/{id}` - Get specific purchase details
- **GET** `/products/mappings` - View product-to-repo mappings

Purchase management endpoints require `MANAGEMENT_API_KEY` in the `X-API-Key` header. Startup fails when the Stripe webhook secret, GitHub token, or management key is missing or too short. Stripe event IDs are deduplicated before fulfillment to prevent concurrent and retry replays from granting access twice within a running service instance.

## Product → Repository Mapping

The service automatically maps these products to GitHub repositories:

```python
PRODUCT_REPO_MAPPING = {
    "ai-customer-support-bot": "DansiDanutz/ai-customer-support-bot",
    "invoice-generator-api": "DansiDanutz/invoice-generator-api", 
    "social-media-auto-poster": "DansiDanutz/social-media-auto-poster",
    "ai-email-assistant": "DansiDanutz/ai-email-assistant",
    "webhook-relay-logger": "DansiDanutz/webhook-relay-logger",
    "ai-seo-content-generator": "DansiDanutz/ai-seo-content-generator",
    "appointment-booking-system": "DansiDanutz/appointment-booking-system",
    "ai-data-scraper": "DansiDanutz/ai-data-scraper",
    "smart-lead-nurture": "DansiDanutz/smart-lead-nurture",
}
```

## Stripe Webhook Configuration

1. **Create Webhook Endpoint** in your Stripe Dashboard:
   - URL: `https://your-domain.com/webhook/stripe`
   - Events: `checkout.session.completed`

2. **Get Webhook Secret** from Stripe and add to `.env`

3. **Product Metadata**: Ensure your Stripe products include:
   ```json
   {
     "metadata": {
       "product_id": "ai-customer-support-bot"
     }
   }
   ```

## GitHub Token Setup

1. **Create Personal Access Token** with these scopes:
   - `repo` (full control of private repositories)
   - `user:email` (access to user email addresses)

2. **Add token** to `.env` as `GITHUB_TOKEN`

## Example Webhook Flow

```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_1234567890",
      "customer_details": {
        "email": "buyer@example.com"
      },
      "metadata": {
        "product_id": "ai-customer-support-bot"
      },
      "payment_status": "paid",
      "amount_total": 4999,
      "currency": "usd"
    }
  }
}
```

**Service Response:**
1. ✅ Verifies webhook signature
2. 🔍 Extracts email: `buyer@example.com`
3. 🔗 Maps to repo: `DansiDanutz/ai-customer-support-bot`
4. 👥 Adds user as collaborator with read access
5. 📝 Records purchase in database

## Monitoring and Logs

Check service health:
```bash
curl https://your-domain.com/health
```

View recent purchases:
```bash
curl https://your-domain.com/purchases?limit=10
```

## Security Features

- ✅ **Webhook Signature Verification**: All Stripe events are cryptographically verified
- 🔒 **Read-Only Access**: Users get pull access only, cannot push changes
- 🛡️ **Input Validation**: All inputs validated with Pydantic models
- 📊 **Audit Trail**: All purchases and access grants are logged
- 🚫 **Rate Limiting**: GitHub API requests are handled responsibly

## Production Deployment

### Environment Variables Required:
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
GITHUB_TOKEN=ghp_...
GITHUB_OWNER=DansiDanutz
```

### Deploy with Docker:
```bash
docker build -t purchase-webhook .
docker run -d \
  --name purchase-webhook \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  purchase-webhook
```

### Health Check:
```bash
curl -f http://localhost:8000/health || exit 1
```

## Error Handling

The service handles these scenarios:

- ❌ **Invalid Stripe signature**: Returns 400 error
- 🔍 **GitHub user not found**: Logs warning, records error in purchase
- 🔐 **GitHub API errors**: Retries and logs detailed error messages
- 📧 **Missing email**: Skips processing, logs warning
- 🏷️ **Unknown product**: Records purchase but notes missing repo mapping

## Development

### Run in Development Mode:
```bash
python main.py
# Service runs on http://localhost:8000
```

### Test Webhook Locally:
```bash
# Use ngrok or similar to expose local port
ngrok http 8000
# Configure Stripe webhook URL to ngrok URL + /webhook/stripe
```

### Add New Products:
Edit the `PRODUCT_REPO_MAPPING` dictionary in `main.py` and restart the service.

## Support

- **Author**: Memo
- **Contact**: memo@mywork-ai.dev
- **Repository**: DansiDanutz/purchase-webhook

## License

Private - All rights reserved.
