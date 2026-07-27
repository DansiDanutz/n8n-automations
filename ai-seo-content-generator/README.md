# AI SEO Content Generator
> Professional AI-powered SEO content generation with keyword analysis and competitor research

## 🎯 What This Does
Creates SEO-optimized blog posts, meta descriptions, and marketing content using advanced AI models. Features keyword difficulty analysis, competitor research, and real-time content optimization. Perfect for content marketers, SEO specialists, and digital agencies scaling content production.

## ✨ Features
- ✍️ **AI Blog Post Generation** - SEO-optimized long-form content creation
- 📝 **Meta Description Generator** - Compelling, search-friendly descriptions
- 🔍 **Keyword Difficulty Analysis** - Research and evaluate keyword opportunities
- 🏆 **Competitor Content Analysis** - Study competitor strategies and gaps
- 🤖 **Multi-Model AI Support** - Claude, GPT-4, and other advanced models via OpenRouter
- 📊 **Real-time Optimization** - Content scoring and improvement suggestions
- 🚀 **Bulk Processing** - Generate multiple pieces of content simultaneously
- 📈 **Performance Metrics** - Track content effectiveness and search rankings
- 🎯 **Target Audience Analysis** - Content tailored to specific demographics
- 🔧 **Custom Templates** - Branded content formats and styles

## 🚀 Quick Start
1. Clone the repo: `git clone <repo-url>`
2. Copy `.env.example` to `.env`
3. Fill in API keys:
   - **OpenRouter API Key**: Get from [OpenRouter](https://openrouter.ai/keys) for multi-model access
   - **OpenAI API Key**: Alternative from [OpenAI Platform](https://platform.openai.com/api-keys)
   - **API Key**: Generate at least 32 random characters for caller authentication
   - **SEO Tools API**: Optional for advanced keyword data
4. Run `pip install -r requirements.txt` to install dependencies
5. Test with `uvicorn main:app --reload` and visit `http://localhost:8000/docs`

## 📡 API Endpoints

Except for `/health`, requests must include `X-API-Key: <API_KEY>`.

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| POST | `/generate/blog-post` | Generate SEO-optimized blog post | `curl -X POST -H "Content-Type: application/json" -d '{"topic":"AI marketing trends","target_keywords":["AI marketing","automation"],"word_count":1500,"tone":"professional"}' http://localhost:8000/generate/blog-post` |
| POST | `/generate/meta-description` | Create compelling meta descriptions | `curl -X POST -H "Content-Type: application/json" -d '{"page_title":"Best CRM Software 2024","target_keyword":"CRM software","max_length":160}' http://localhost:8000/generate/meta-description` |
| POST | `/analyze/keywords` | Analyze keyword difficulty and volume | `curl -X POST -H "Content-Type: application/json" -d '{"keywords":["content marketing","SEO tools","blog writing"],"country":"US"}' http://localhost:8000/analyze/keywords` |
| POST | `/analyze/competitors` | Research competitor content strategies | `curl -X POST -H "Content-Type: application/json" -d '{"domain":"competitor.com","topic":"email marketing","analysis_depth":"detailed"}' http://localhost:8000/analyze/competitors` |
| POST | `/optimize/content` | Optimize existing content for SEO | `curl -X POST -H "Content-Type: application/json" -d '{"content":"Your article content...","target_keywords":["SEO","optimization"]}' http://localhost:8000/optimize/content` |
| GET | `/templates` | List available content templates | `curl http://localhost:8000/templates` |
| GET | `/health` | Service health check | `curl http://localhost:8000/health` |
| GET | `/stats` | Generation statistics | `curl http://localhost:8000/stats` |

## 💡 Use Cases
- **Content Marketing Agencies** - Scale blog production for multiple clients with consistent quality
- **E-commerce SEO** - Generate product descriptions and category pages optimized for search
- **SaaS Content Teams** - Create educational content that drives organic traffic and leads
- **Digital Publishers** - Produce high-volume, SEO-friendly articles across multiple niches
- **Perfect for** - Businesses needing 10+ pieces of SEO content per month with professional quality

## 🔧 Configuration

| Variable | Description | Where to Get | Default |
|----------|-------------|--------------|---------|
| `OPENROUTER_API_KEY` | Multi-model AI access (recommended) | [OpenRouter Keys](https://openrouter.ai/keys) | - |
| `OPENAI_API_KEY` | Direct OpenAI access (alternative) | [OpenAI Platform](https://platform.openai.com/api-keys) | - |
| `API_KEY` | Caller authentication key (32+ random characters) | Generate locally | - |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins | Deployment configuration | `http://localhost:3000,http://localhost:8000` |
| `DEFAULT_MODEL` | AI model for content generation | `anthropic/claude-3-sonnet`, `openai/gpt-4` | `anthropic/claude-3-sonnet` |
| `MAX_WORD_COUNT` | Maximum content length | Words per article | 5000 |
| `DEFAULT_TONE` | Content writing tone | professional, casual, authoritative, friendly | professional |
| `SEO_TOOLS_API_KEY` | Advanced keyword data (optional) | SEMrush, Ahrefs, or similar | - |
| `CONTENT_STORAGE_DAYS` | Data retention period | Days to keep generated content | 90 |
| `RATE_LIMIT_PER_HOUR` | API rate limiting | Requests per hour | 100 |
| `ENABLE_ANALYTICS` | Usage tracking | true/false | true |
| `WEBHOOK_URL` | Completion notifications (optional) | Your webhook endpoint | - |
| `DATABASE_URL` | Content storage (optional) | PostgreSQL connection string | In-memory |
| `REDIS_URL` | Caching layer (optional) | Redis connection string | - |

## 🐳 Docker Deployment
```yaml
version: '3.8'
services:
  seo-content-generator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - API_KEY=${API_KEY}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
      - DEFAULT_MODEL=anthropic/claude-3-sonnet
      - MAX_WORD_COUNT=5000
      - DATABASE_URL=postgresql://postgres:password@db:5432/seo_content
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=seo_content
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Commands:
```bash
docker-compose up -d
curl http://localhost:8000/health
```

## 📊 Architecture
```
Content Request → AI Model Router → Content Generation
      ↓                              ↓
Keyword Analysis ← SEO Optimization ← Quality Scoring
      ↓                              ↓
Template Engine → Content Assembly → Post-processing
      ↓                              ↓
Database Storage ← Analytics ← Performance Tracking
```

Key Components:
- **AI Router**: Intelligent model selection based on content type
- **SEO Analyzer**: Keyword density, readability, and optimization scoring
- **Content Templates**: Structured formats for different content types
- **Quality Controller**: Automated content review and improvement suggestions
- **Performance Tracker**: Content effectiveness and search ranking monitoring

## 🆘 Troubleshooting
**AI model errors:**
- Check API key has sufficient credits
- Verify model availability on OpenRouter/OpenAI
- Monitor rate limits and quota usage
- Try different models if one is unavailable

**Poor content quality:**
- Adjust AI model parameters (temperature, max_tokens)
- Refine prompts and target keywords
- Use more specific content briefs
- Enable content quality scoring and filtering

**Slow content generation:**
- Check AI API response times
- Consider using faster models like GPT-3.5-turbo
- Implement request caching for repeated queries
- Use async processing for bulk content generation

**SEO optimization issues:**
- Verify target keywords are properly formatted
- Check keyword density calculations
- Ensure readability scoring is working
- Validate meta tag length requirements

**Keyword analysis failures:**
- Check SEO tools API credentials and quotas
- Verify keyword list format and limits
- Monitor API rate limits for keyword tools
- Fallback to basic analysis if external APIs fail

**Database connection problems:**
- Verify PostgreSQL connection string
- Check database permissions and schema
- Monitor storage usage and cleanup old content
- Ensure proper indexing for search performance

**Competitor analysis errors:**
- Verify target domain accessibility
- Check robots.txt compliance
- Monitor rate limits for web scraping
- Implement respectful crawling delays

## 📝 License
Private — purchased via MyWork-AI Marketplace
