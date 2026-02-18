# Webhook Relay & Logger
> Advanced webhook debugging and relay service with real-time inspection and powerful filtering

## 🎯 What This Does
Catches, inspects, forwards, and replays webhooks with comprehensive debugging capabilities. Perfect for integration testing, webhook development, and monitoring third-party services. Features real-time logging, payload transformation, and analytics dashboard.

## ✨ Features
- 🎯 **Universal Webhook Catcher** - Accepts any HTTP method from any service
- 🔍 **Real-time Inspection** - Live webhook monitoring and detailed logging
- 🔄 **Smart Relay & Forwarding** - Route webhooks to multiple endpoints with rules
- 🎭 **Payload Transformation** - Modify webhook data before forwarding
- 🔁 **Webhook Replay** - Resend webhooks for testing and debugging
- 📊 **Advanced Analytics** - Performance monitoring and pattern analysis
- 🛡️ **Rate Limiting** - Protection against webhook spam and abuse
- 🔐 **Authentication Support** - API keys, signatures, and custom auth
- 📱 **Web Dashboard** - Easy debugging interface with search and filters
- 💾 **Data Export** - Export webhook data for analysis and reporting

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Configure database:
   - PostgreSQL: Set `DATABASE_URL=postgresql://user:pass@localhost/webhooks`
   - Redis (optional): Set `REDIS_URL=redis://localhost:6379`
4. Run `pip install -r requirements.txt` to install dependencies
5. Test with `python -m pytest tests/` and visit `http://localhost:8000/dashboard`

## 📡 API Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| POST/PUT/GET | `/catch/{id}` | Universal webhook catcher | `curl -X POST -d '{"test":"data"}' http://localhost:8000/catch/my-endpoint-id` |
| GET | `/webhooks/{id}` | Get webhook details | `curl http://localhost:8000/webhooks/wh_abc123` |
| GET | `/webhooks` | List webhooks with filters | `curl http://localhost:8000/webhooks?endpoint=my-endpoint&status=200&limit=50` |
| POST | `/webhooks/{id}/replay` | Replay webhook | `curl -X POST http://localhost:8000/webhooks/wh_abc123/replay` |
| POST | `/relay-rules` | Create forwarding rule | `curl -X POST -H "Content-Type: application/json" -d '{"name":"Forward to Slack","endpoint":"my-endpoint","target_url":"https://hooks.slack.com/...","active":true}' http://localhost:8000/relay-rules` |
| GET | `/relay-rules` | List forwarding rules | `curl http://localhost:8000/relay-rules` |
| POST | `/transform-rules` | Create transformation rule | `curl -X POST -H "Content-Type: application/json" -d '{"name":"Add timestamp","endpoint":"my-endpoint","script":"payload.timestamp = Date.now(); return payload;"}' http://localhost:8000/transform-rules` |
| GET | `/analytics` | Get webhook analytics | `curl http://localhost:8000/analytics?period=7d&endpoint=my-endpoint` |
| GET | `/export/{format}` | Export webhook data | `curl http://localhost:8000/export/csv?start_date=2024-01-01&end_date=2024-01-31` |
| GET | `/health` | Service health check | `curl http://localhost:8000/health` |

## 💡 Use Cases
- **API Integration Testing** - Debug webhook flows without affecting production systems
- **Third-party Monitoring** - Track reliability and performance of external webhook services
- **Development & Debugging** - Inspect payload structure and test webhook handling logic
- **Webhook Transformation** - Modify webhook data format before forwarding to internal systems
- **Perfect for** - Developers integrating with payment processors, CI/CD systems, or any webhook-based services

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:password@localhost:5432/webhooks` | `sqlite:///webhooks.db` |
| `REDIS_URL` | Redis cache (optional) | `redis://localhost:6379/0` | - |
| `SECRET_KEY` | API security key | Generate random 256-bit string | - |
| `WEBHOOK_STORAGE_DAYS` | Data retention period | Number of days to keep webhook logs | 30 |
| `MAX_PAYLOAD_SIZE` | Maximum webhook size | Size in bytes | 10485760 (10MB) |
| `RATE_LIMIT_PER_MINUTE` | Rate limiting | Requests per minute per IP | 100 |
| `ENABLE_AUTHENTICATION` | API key requirement | true/false | false |
| `CORS_ORIGINS` | Allowed origins | Comma-separated list of domains | "*" |
| `LOG_LEVEL` | Logging verbosity | DEBUG, INFO, WARNING, ERROR | INFO |
| `DASHBOARD_USERNAME` | Dashboard login (optional) | Any username | - |
| `DASHBOARD_PASSWORD` | Dashboard password (optional) | Secure password | - |
| `SMTP_HOST` | Email alerts (optional) | SMTP server address | - |
| `SMTP_USER` | Email username | SMTP credentials | - |
| `SMTP_PASSWORD` | Email password | SMTP credentials | - |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  webhook-relay:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/webhooks
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key-here
      - WEBHOOK_STORAGE_DAYS=30
      - MAX_PAYLOAD_SIZE=10485760
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=webhooks
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Commands:
```bash
docker-compose up -d
docker-compose logs -f webhook-relay
```

## 📊 Architecture
```
Incoming Webhooks → Rate Limiter → Authentication
        ↓                             ↓
   Payload Capture → Database Storage → Real-time Logging
        ↓                             ↓
Transformation Rules → Forwarding Engine → Target Endpoints
        ↓                             ↓
   Analytics Engine ← Performance Metrics ← Delivery Tracking
        ↓                             ↓
   Dashboard UI ← Search & Filters ← Export Functions
```

Core Components:
- **Webhook Catcher**: Universal endpoint accepting all HTTP methods
- **Storage Engine**: PostgreSQL with Redis caching for performance
- **Relay System**: Rule-based forwarding with retry logic
- **Transformation Engine**: JavaScript-based payload modification
- **Analytics Dashboard**: Real-time monitoring and historical analysis

## 🆘 Troubleshooting
**Webhooks not being received:**
- Check firewall allows incoming traffic on port 8000
- Verify webhook endpoint URL is correct: `http://your-server:8000/catch/your-endpoint-id`
- Check rate limiting settings if webhooks are being dropped
- Monitor logs for authentication errors

**Database connection errors:**
- Verify PostgreSQL is running and accessible
- Check connection string format and credentials
- Run database migrations: `alembic upgrade head`
- Ensure database user has CREATE, SELECT, INSERT, UPDATE permissions

**Webhook forwarding failures:**
- Check target URL is accessible from your server
- Verify SSL certificates for HTTPS endpoints
- Monitor relay rule configuration for typos
- Check network connectivity and DNS resolution

**Dashboard not loading:**
- Verify web server is running on correct port
- Check browser console for JavaScript errors
- Clear browser cache and cookies
- Verify dashboard authentication credentials if enabled

**High memory usage:**
- Check webhook retention period (reduce WEBHOOK_STORAGE_DAYS)
- Monitor payload sizes for unusually large webhooks
- Consider increasing MAX_PAYLOAD_SIZE limits
- Enable Redis caching to improve performance

**Webhook replay issues:**
- Ensure original webhook data is still in database
- Check target endpoint is responding correctly
- Verify replay rules and authentication settings
- Monitor rate limits on target services

**Performance issues:**
- Enable Redis caching for better response times
- Check database indexes are properly created
- Monitor PostgreSQL performance and query optimization
- Consider horizontal scaling with load balancer

## 📝 License
Private — purchased via MyWork-AI Marketplace