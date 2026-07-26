# Appointment Booking System
> Complete appointment scheduling with real-time availability and automated notifications

## 🎯 What This Does
Professional appointment booking system with real-time availability checking, email confirmations, and comprehensive management features. Perfect for healthcare professionals, consultants, service providers, and any business that needs reliable appointment scheduling.

## ✨ Features
- 📅 **Real-time Booking** - Instant appointment scheduling with availability checking
- ⏰ **Flexible Time Slots** - Customizable duration and working hours configuration
- 📧 **Email Notifications** - Automatic confirmations, reminders, and cancellation notices
- 🔄 **Booking Management** - Create, update, cancel, and reschedule appointments
- 🏥 **Multi-Service Support** - Different appointment types with custom settings
- 📊 **Comprehensive Statistics** - Booking analytics and business insights
- 🗓️ **Calendar Integration** - Google Calendar sync and iCal export
- 💳 **Payment Ready** - Stripe/PayPal integration hooks for paid bookings
- 🚫 **Smart Availability** - Automatic blocking of booked slots and holidays
- 📱 **Mobile Friendly** - Responsive booking interface for all devices

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Configure settings:
   - Set business hours and time zones
   - Add SMTP email settings for notifications
   - Configure appointment types and durations
4. Run `pip install -r requirements.txt` to install dependencies
5. Test with `python main.py` and visit `http://localhost:8000/docs`

## 📡 API Endpoints

Administrative endpoints (`GET /bookings`, `POST /slots`, booking updates/cancellation,
and `GET /stats`) require `X-API-Key: $ADMIN_API_KEY`.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| POST | `/bookings` | Create new appointment | `curl -X POST -H "Content-Type: application/json" -d '{"client_name":"John Doe","client_email":"john@example.com","service_type":"consultation","date":"2024-03-15","time":"14:00","duration":60}' http://localhost:8000/bookings` |
| GET | `/bookings` | List bookings with filters | `curl http://localhost:8000/bookings?date=2024-03-15&status=confirmed&limit=10` |
| GET | `/bookings/{id}` | Get specific booking details | `curl http://localhost:8000/bookings/apt_abc123` |
| PUT | `/bookings/{id}` | Update existing booking | `curl -X PUT -H "Content-Type: application/json" -d '{"date":"2024-03-16","time":"15:00"}' http://localhost:8000/bookings/apt_abc123` |
| DELETE | `/bookings/{id}` | Cancel appointment | `curl -X DELETE http://localhost:8000/bookings/apt_abc123` |
| GET | `/availability` | Check available slots | `curl http://localhost:8000/availability?date=2024-03-15&service_type=consultation` |
| POST | `/slots` | Create custom time slots | `curl -X POST -H "Content-Type: application/json" -d '{"date":"2024-03-15","start_time":"09:00","end_time":"17:00","slot_duration":30}' http://localhost:8000/slots` |
| GET | `/services` | List appointment types | `curl http://localhost:8000/services` |
| GET | `/stats` | Booking statistics | `curl http://localhost:8000/stats?period=month` |
| GET | `/health` | Service health check | `curl http://localhost:8000/health` |

## 💡 Use Cases
- **Medical Practices** - Patient appointment scheduling with automated reminders and confirmations
- **Legal Consultations** - Client meeting booking with case type classification and billing integration
- **Beauty Salons** - Service appointments with stylist assignment and treatment duration management
- **Business Consultants** - Meeting scheduling with client onboarding and follow-up automation
- **Perfect for** - Service-based businesses needing professional appointment management without complex software

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `BUSINESS_NAME` | Your business name | Your company registration | "My Business" |
| `BUSINESS_EMAIL` | Contact email address | Your business email | - |
| `BUSINESS_PHONE` | Contact phone number | Your business phone | - |
| `BUSINESS_ADDRESS` | Physical address | Your business address | - |
| `BUSINESS_TIMEZONE` | Operating timezone | Timezone identifier (e.g., "America/New_York") | "UTC" |
| `WORKING_HOURS_START` | Daily start time | 24-hour format (e.g., "09:00") | "09:00" |
| `WORKING_HOURS_END` | Daily end time | 24-hour format (e.g., "17:00") | "17:00" |
| `WORKING_DAYS` | Operating days | Comma-separated (e.g., "monday,tuesday,wednesday") | "monday,tuesday,wednesday,thursday,friday" |
| `DEFAULT_SLOT_DURATION` | Appointment length | Minutes | 60 |
| `BOOKING_LEAD_TIME` | Minimum advance booking | Hours | 2 |
| `MAX_BOOKING_DAYS` | Maximum days in advance | Days | 90 |
| `SMTP_HOST` | Email server | Gmail: smtp.gmail.com | - |
| `SMTP_PORT` | Email server port | Gmail: 587 | 587 |
| `SMTP_USER` | Email username | Your email address | - |
| `SMTP_PASSWORD` | Email password | App password for Gmail | - |
| `DATABASE_URL` | Data storage | `sqlite:///bookings.db` or PostgreSQL | `sqlite:///bookings.db` |
| `ADMIN_API_KEY` | Administrative API key | Generate at least 32 random characters | - |
| `CORS_ALLOWED_ORIGINS` | Credentialed browser origins | Comma-separated origins | `http://localhost:3000` |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  booking-system:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BUSINESS_NAME=Your Business Name
      - BUSINESS_EMAIL=bookings@yourbusiness.com
      - BUSINESS_TIMEZONE=America/New_York
      - WORKING_HOURS_START=09:00
      - WORKING_HOURS_END=17:00
      - DATABASE_URL=postgresql://postgres:password@db:5432/bookings
      - SMTP_HOST=smtp.gmail.com
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=bookings
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Commands:
```bash
docker-compose up -d
docker-compose logs -f booking-system
```

## 📊 Architecture
```
Booking Request → Availability Check → Conflict Detection
       ↓                                    ↓
Database Storage ← Booking Creation ← Email Notification
       ↓                                    ↓
Calendar Sync ← Status Management ← Reminder Scheduling
       ↓                                    ↓
Analytics Dashboard ← Reports ← Performance Metrics
```

Key Components:
- **Availability Engine**: Real-time slot checking with conflict prevention
- **Notification System**: Email templates for confirmations, reminders, cancellations
- **Calendar Integration**: Two-way sync with Google Calendar and other providers
- **Business Logic**: Configurable rules for booking policies and restrictions
- **Analytics Engine**: Booking trends, no-show rates, and revenue tracking

## 🆘 Troubleshooting
**Bookings not saving:**
- Check database connection and permissions
- Verify all required fields are provided
- Monitor disk space for SQLite databases
- Check business hours configuration

**Email notifications not sending:**
- Verify SMTP credentials and server settings
- For Gmail: Enable 2FA and use app password
- Check firewall allows SMTP port (587/465)
- Test email settings with a simple send test

**Availability conflicts:**
- Check timezone settings match your location
- Verify working hours configuration
- Monitor for overlapping appointment times
- Check holiday and blocked date settings

**Calendar sync issues:**
- Verify Google Calendar API credentials
- Check OAuth2 permissions and scopes
- Monitor API rate limits and quotas
- Ensure calendar sharing permissions are correct

**Booking form validation errors:**
- Check required field configurations
- Verify email format validation
- Monitor date and time format requirements
- Ensure service types are properly configured

**Performance issues with many bookings:**
- Add database indexes for date and status queries
- Implement caching for availability checks
- Consider pagination for booking lists
- Monitor database query performance

**Time zone problems:**
- Set correct BUSINESS_TIMEZONE in config
- Ensure client and server time zones align
- Use UTC for internal storage, local for display
- Test booking times across time zone changes

## 📝 License
Private — purchased via MyWork-AI Marketplace
