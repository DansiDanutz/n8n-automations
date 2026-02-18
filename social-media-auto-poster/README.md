# Social Media Auto-Poster
> Intelligent social media automation that schedules posts across Twitter, LinkedIn, and Facebook with AI-generated content

## 🎯 What This Does
Automates your social media presence with AI-generated captions, optimal scheduling, and multi-platform posting. Features smart content templates, hashtag optimization, and analytics tracking. Perfect for businesses and content creators who want consistent posting without manual work.

## ✨ Features
- 🌐 **Multi-Platform Posting** - Twitter, LinkedIn, and Facebook automation
- 🤖 **AI-Generated Content** - OpenAI-powered captions and hashtags
- ⏰ **Smart Scheduling** - Optimal timing for maximum engagement
- 📅 **Content Calendar** - Pre-built templates for consistent posting
- 📸 **Media Support** - Images and videos with automatic processing
- 📊 **Analytics Dashboard** - Engagement tracking and performance metrics
- 📡 **RSS Integration** - Auto-post from blog feeds
- 📋 **Bulk Upload** - CSV import for mass scheduling
- 🎯 **Content Optimization** - Platform-specific formatting and limits
- 🔄 **Background Processing** - Queue management for reliable posting

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Fill in API keys:
   - **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
   - **Twitter API**: Apply at [Twitter Developer](https://developer.twitter.com/en/apply-for-access)
   - **LinkedIn API**: Create app at [LinkedIn Developers](https://www.linkedin.com/developers/)
   - **Facebook API**: Setup at [Facebook Developers](https://developers.facebook.com/)
4. Run `./setup.sh` to install dependencies
5. Test with `node test-social-poster.js` to verify all APIs work

## 📡 API Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| POST | `/api/generate-content` | Generate AI content for platforms | `curl -X POST -H "Content-Type: application/json" -d '{"prompt":"Product launch announcement","platforms":["twitter","linkedin"],"tone":"excited"}' http://localhost:3000/api/generate-content` |
| POST | `/api/schedule` | Schedule post for later | `curl -X POST -H "Content-Type: application/json" -d '{"content":{"twitter":"Hello world! #automation"},"platforms":["twitter"],"scheduledTime":"2024-12-01T10:00:00Z"}' http://localhost:3000/api/schedule` |
| POST | `/api/publish-now` | Post immediately | `curl -X POST -H "Content-Type: application/json" -d '{"content":"Breaking news! 🚀","platforms":["twitter"]}' http://localhost:3000/api/publish-now` |
| GET | `/api/scheduled-posts` | List scheduled posts | `curl http://localhost:3000/api/scheduled-posts` |
| GET | `/api/analytics` | Get performance metrics | `curl http://localhost:3000/api/analytics` |
| GET | `/api/templates` | List content templates | `curl http://localhost:3000/api/templates` |
| POST | `/api/bulk-upload` | Upload CSV for bulk posting | `curl -X POST -F "csv=@posts.csv" http://localhost:3000/api/bulk-upload` |
| GET | `/health` | Service health check | `curl http://localhost:3000/health` |

## 💡 Use Cases
- **Content Marketing** - Maintain consistent posting schedule across all platforms with branded content
- **Product Launches** - Coordinate announcement posts with optimal timing and platform-specific messaging
- **Blog Promotion** - Automatically share new blog posts with engaging summaries and relevant hashtags
- **Event Marketing** - Schedule countdown posts, live updates, and follow-up content for events
- **Perfect for** - Businesses, agencies, and creators who want professional social media presence without manual posting

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `OPENAI_API_KEY` | AI content generation (required) | [OpenAI Platform](https://platform.openai.com/api-keys) | - |
| `TWITTER_API_KEY` | Twitter app key (required) | [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard) | - |
| `TWITTER_API_SECRET` | Twitter app secret (required) | Twitter Developer Portal | - |
| `TWITTER_ACCESS_TOKEN` | User access token (required) | Generate in Twitter Developer Portal | - |
| `TWITTER_ACCESS_SECRET` | User access secret (required) | Generate in Twitter Developer Portal | - |
| `LINKEDIN_CLIENT_ID` | LinkedIn app ID (optional) | [LinkedIn Developers](https://www.linkedin.com/developers/apps) | - |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app secret (optional) | LinkedIn Developers | - |
| `LINKEDIN_ACCESS_TOKEN` | User authorization token (optional) | OAuth2 flow with LinkedIn | - |
| `FACEBOOK_APP_ID` | Facebook app ID (optional) | [Facebook Developers](https://developers.facebook.com/apps) | - |
| `FACEBOOK_APP_SECRET` | Facebook app secret (optional) | Facebook Developers | - |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Page posting token (optional) | Facebook Graph API Explorer | - |
| `FACEBOOK_PAGE_ID` | Target page ID (optional) | Found in Facebook Page settings | - |
| `PORT` | Web server port | Any available port | 3000 |
| `DEFAULT_TONE` | Content generation tone | professional, casual, excited, formal | professional |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  social-poster:
    build: .
    ports:
      - "3000:3000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TWITTER_API_KEY=${TWITTER_API_KEY}
      - TWITTER_API_SECRET=${TWITTER_API_SECRET}
      - TWITTER_ACCESS_TOKEN=${TWITTER_ACCESS_TOKEN}
      - TWITTER_ACCESS_SECRET=${TWITTER_ACCESS_SECRET}
      - PORT=3000
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./analytics:/app/analytics
    restart: unless-stopped
```

Commands:
```bash
docker-compose up -d
docker-compose logs -f social-poster
```

## 📊 Architecture
```
Content Input → AI Generation → Platform Optimization
     ↓                ↓                    ↓
Scheduling → Background Queue → Platform APIs
     ↓                ↓                    ↓
Database → Status Updates → Analytics
     ↓                ↓                    ↓
Dashboard ← Performance Metrics ← Engagement Data
```

Components:
- **Content Generator**: OpenAI integration for smart captions
- **Scheduler**: Cron-based posting with optimal timing
- **Platform Adapters**: Twitter, LinkedIn, Facebook API handlers
- **Analytics Engine**: Engagement tracking and performance metrics
- **Media Processor**: Image/video optimization for each platform

## 🆘 Troubleshooting
**Twitter API errors:**
- Verify all 4 Twitter credentials are correct
- Check Twitter Developer account has Essential access level
- Ensure app has Read & Write permissions
- Rate limit: Twitter allows 300 tweets per 3-hour window

**OpenAI content generation fails:**
- Check API key has available credits
- Verify prompt is not too long (model context limits)
- Monitor rate limits at [OpenAI Usage Dashboard](https://platform.openai.com/usage)

**Posts not scheduling:**
- Check server time zone matches `scheduledTime` format
- Verify cron job is running (check logs for "processScheduledPosts")
- Ensure JSON date format is correct: `YYYY-MM-DDTHH:mm:ssZ`

**LinkedIn/Facebook not working:**
- These require OAuth2 setup and app approval
- LinkedIn requires company page admin access
- Facebook needs page management permissions
- Check API versions and endpoint deprecation notices

**Media upload issues:**
- Verify file size limits (Twitter: 5MB images, 512MB videos)
- Check supported formats: JPG, PNG, GIF, MP4, MOV
- Ensure Sharp image processing library is installed
- Check file permissions in `/uploads` directory

**Dashboard shows incorrect stats:**
- Analytics update every hour via cron job
- Real engagement data requires platform webhook setup
- Check browser console for API connection errors

## 📝 License
Private — purchased via MyWork-AI Marketplace