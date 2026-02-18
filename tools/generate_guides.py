#!/usr/bin/env python3
"""Generate professional HTML guides for all marketplace products."""

import os
from datetime import datetime

PRODUCTS = {
    "ai-customer-support-bot": {
        "title": "AI Customer Support Bot",
        "price": "$49.99",
        "tagline": "Intelligent customer support powered by OpenAI",
        "description": "A production-ready FastAPI backend that handles customer conversations with AI-powered responses, knowledge base integration, conversation history, analytics, and satisfaction tracking.",
        "tech": ["Python 3.10+", "FastAPI", "OpenAI GPT", "SQLite", "Docker"],
        "env_vars": [
            ("OPENAI_API_KEY", "Your OpenAI API key", "sk-your-key-here"),
            ("OPENAI_MODEL", "GPT model to use", "gpt-3.5-turbo"),
            ("PORT", "Server port", "8000"),
            ("DB_PATH", "SQLite database path", "./support_bot.db"),
            ("KB_DIR", "Knowledge base directory", "./knowledge_base"),
        ],
        "endpoints": [
            ("POST /chat", "Send a message and get AI response", '{"user_id": "user123", "message": "How do I reset my password?"}', '{"conversation_id": 1, "response": "To reset your password, go to Settings > Security > Reset Password. Click the reset link and follow the instructions.", "confidence": 0.92}'),
            ("GET /conversations", "List all conversations", None, '[{"id": 1, "user_id": "user123", "status": "active", "message_count": 3}]'),
            ("GET /conversations/{id}", "Get full conversation history", None, '{"id": 1, "messages": [{"role": "user", "content": "How do I reset my password?"}, {"role": "assistant", "content": "To reset your password..."}]}'),
            ("POST /feedback", "Submit satisfaction rating", '{"conversation_id": 1, "rating": 5, "feedback": "Very helpful!"}', '{"status": "success", "message": "Feedback recorded"}'),
            ("GET /analytics", "Get support analytics", None, '{"total_conversations": 150, "avg_satisfaction": 4.7, "resolution_rate": 0.89}'),
        ],
        "use_cases": ["SaaS customer support", "E-commerce help desk", "Internal IT helpdesk", "Documentation Q&A bot"],
    },
    "ai-seo-content-generator": {
        "title": "AI SEO Content Generator",
        "price": "$39.99",
        "tagline": "Generate SEO-optimized content with AI",
        "description": "A FastAPI backend that generates SEO-optimized blog posts, meta descriptions, keyword analysis, and competitor insights using OpenAI. Perfect for content marketers and agencies.",
        "tech": ["Python 3.10+", "FastAPI", "OpenAI GPT", "Docker"],
        "env_vars": [
            ("OPENAI_API_KEY", "Your OpenAI API key", "sk-your-key-here"),
            ("PORT", "Server port", "8000"),
        ],
        "endpoints": [
            ("POST /generate/blog-post", "Generate an SEO blog post", '{"topic": "Best practices for remote team management", "keywords": ["remote work", "team management", "productivity"], "tone": "professional", "word_count": 1500}', '{"title": "10 Best Practices for Remote Team Management in 2026", "content": "Remote work has transformed how teams collaborate...", "meta_description": "Discover 10 proven strategies for managing remote teams effectively...", "seo_score": 87}'),
            ("POST /generate/meta-description", "Generate meta description", '{"page_title": "Our Pricing Plans", "page_content": "We offer three tiers..."}', '{"meta_description": "Compare our Starter, Pro, and Enterprise pricing plans. Start free, scale as you grow."}'),
            ("POST /analyze/keywords", "Analyze keyword opportunities", '{"seed_keyword": "project management software", "max_results": 10}', '{"keywords": [{"keyword": "project management software", "difficulty": 78, "volume": 12000}, {"keyword": "best project management tools", "difficulty": 65, "volume": 8500}]}'),
            ("POST /analyze/competitors", "Analyze competitor content", '{"url": "https://competitor.com/blog/topic", "keywords": ["project management"]}', '{"word_count": 2300, "keyword_density": 2.1, "headings": 8, "suggestions": ["Add more internal links", "Include FAQ section"]}'),
            ("GET /stats", "Get generation statistics", None, '{"total_generated": 45, "avg_seo_score": 82, "top_topics": ["marketing", "SaaS", "productivity"]}'),
        ],
        "use_cases": ["Content marketing agencies", "SEO teams", "Blog automation", "E-commerce product descriptions"],
    },
    "invoice-generator-api": {
        "title": "Invoice Generator API",
        "price": "$19.99",
        "tagline": "Professional invoices with PDF export",
        "description": "A complete invoice management API with PDF/HTML generation, CRUD operations, and professional templates. Perfect for SaaS billing or freelancer tools.",
        "tech": ["Python 3.10+", "FastAPI", "Jinja2", "WeasyPrint", "SQLite", "Docker"],
        "env_vars": [
            ("PORT", "Server port", "8000"),
            ("DB_PATH", "Database path", "./invoices.db"),
            ("COMPANY_NAME", "Your company name", "MyCompany LLC"),
            ("COMPANY_EMAIL", "Company email", "billing@mycompany.com"),
        ],
        "endpoints": [
            ("POST /invoices", "Create a new invoice", '{"client_name": "Acme Corp", "client_email": "billing@acme.com", "items": [{"description": "Web Development", "quantity": 40, "unit_price": 150.00}, {"description": "Design Work", "quantity": 10, "unit_price": 120.00}], "due_days": 30, "notes": "Thank you for your business!"}', '{"id": "INV-2026-0001", "client_name": "Acme Corp", "total": 7200.00, "status": "draft", "due_date": "2026-03-17"}'),
            ("GET /invoices/{id}/pdf", "Download invoice as PDF", None, "(Binary PDF file)"),
            ("GET /invoices/{id}/html", "Preview invoice as HTML", None, "(Rendered HTML invoice)"),
            ("GET /invoices", "List all invoices", None, '[{"id": "INV-2026-0001", "client_name": "Acme Corp", "total": 7200.00, "status": "draft"}]'),
            ("PUT /invoices/{id}", "Update an invoice", '{"status": "sent"}', '{"id": "INV-2026-0001", "status": "sent"}'),
            ("DELETE /invoices/{id}", "Delete an invoice", None, '{"message": "Invoice deleted"}'),
        ],
        "use_cases": ["Freelancer billing", "SaaS subscription invoices", "Agency client billing", "E-commerce order receipts"],
    },
    "ai-email-assistant": {
        "title": "AI Email Assistant",
        "price": "$39.99",
        "tagline": "AI-powered email management and automation",
        "description": "A FastAPI backend that connects to your email, summarizes messages, auto-categorizes, generates smart replies, detects spam, and provides analytics. Automate your inbox.",
        "tech": ["Python 3.10+", "FastAPI", "OpenAI GPT", "IMAP/SMTP", "SQLite", "Docker"],
        "env_vars": [
            ("OPENAI_API_KEY", "Your OpenAI API key", "sk-your-key-here"),
            ("EMAIL_HOST", "IMAP server", "imap.gmail.com"),
            ("EMAIL_USER", "Email address", "you@gmail.com"),
            ("EMAIL_PASSWORD", "Email password or app password", "your-app-password"),
            ("SMTP_HOST", "SMTP server", "smtp.gmail.com"),
            ("SMTP_PORT", "SMTP port", "587"),
            ("PORT", "Server port", "8000"),
        ],
        "endpoints": [
            ("POST /emails/connect", "Connect to email account", '{"host": "imap.gmail.com", "email": "you@gmail.com", "password": "app-password"}', '{"status": "connected", "inbox_count": 243}'),
            ("GET /emails/inbox", "Fetch inbox emails", None, '[{"id": "msg001", "from": "boss@company.com", "subject": "Q1 Report Review", "date": "2026-02-16", "preview": "Please review the attached..."}]'),
            ("POST /emails/{id}/summarize", "AI-summarize an email", None, '{"summary": "Boss requests review of Q1 report by Friday. Key metrics attached. Action needed: approve or suggest changes.", "key_points": ["Q1 report ready", "Review needed by Friday", "Metrics attached"]}'),
            ("POST /emails/{id}/reply", "Generate smart reply", '{"tone": "professional", "intent": "acknowledge and confirm"}', '{"draft": "Hi John,\\n\\nThank you for sending the Q1 report. I will review it thoroughly and provide my feedback by Friday.\\n\\nBest regards"}'),
            ("POST /emails/{id}/categorize", "Auto-categorize email", None, '{"category": "work/reports", "confidence": 0.94}'),
            ("GET /analytics/summary", "Email analytics", None, '{"total_processed": 500, "categories": {"work": 210, "personal": 85, "promotions": 150, "spam": 55}}'),
        ],
        "use_cases": ["Executive inbox management", "Customer email triage", "Support ticket routing", "Newsletter management"],
    },
    "appointment-booking-system": {
        "title": "Appointment Booking System",
        "price": "$29.99",
        "tagline": "Full booking system with availability management",
        "description": "A complete appointment booking API with availability checking, slot management, booking CRUD, reminders, and analytics. Ready to embed in any frontend.",
        "tech": ["Python 3.10+", "FastAPI", "SQLite", "Docker"],
        "env_vars": [
            ("PORT", "Server port", "8000"),
            ("DB_PATH", "Database path", "./bookings.db"),
            ("BUSINESS_NAME", "Your business name", "MyBusiness"),
            ("BUSINESS_HOURS_START", "Opening hour (24h)", "9"),
            ("BUSINESS_HOURS_END", "Closing hour (24h)", "17"),
            ("SLOT_DURATION_MINUTES", "Appointment duration", "30"),
        ],
        "endpoints": [
            ("GET /availability", "Check available time slots", None, '{"date": "2026-02-18", "available_slots": [{"start": "09:00", "end": "09:30"}, {"start": "09:30", "end": "10:00"}, {"start": "10:00", "end": "10:30"}]}'),
            ("POST /bookings", "Create a booking", '{"customer_name": "Jane Smith", "customer_email": "jane@example.com", "date": "2026-02-18", "time": "10:00", "service": "Consultation", "notes": "First visit"}', '{"id": 1, "customer_name": "Jane Smith", "date": "2026-02-18", "time": "10:00", "status": "confirmed", "confirmation_code": "BK-A7F3"}'),
            ("GET /bookings", "List all bookings", None, '[{"id": 1, "customer_name": "Jane Smith", "date": "2026-02-18", "time": "10:00", "status": "confirmed"}]'),
            ("PUT /bookings/{id}", "Update a booking", '{"time": "11:00"}', '{"id": 1, "time": "11:00", "status": "rescheduled"}'),
            ("DELETE /bookings/{id}", "Cancel a booking", None, '{"message": "Booking cancelled"}'),
            ("GET /stats", "Booking statistics", None, '{"total_bookings": 89, "upcoming": 12, "cancellation_rate": 0.08}'),
        ],
        "use_cases": ["Clinic/doctor appointments", "Salon booking", "Consultation scheduling", "Service business booking"],
    },
    "smart-lead-nurture": {
        "title": "Smart Lead Nurture",
        "price": "$29.99",
        "tagline": "n8n workflow for automated lead nurturing",
        "description": "A pre-built n8n workflow that automates lead nurturing — from capture to conversion. Includes email sequences, lead scoring, CRM integration, and automated follow-ups.",
        "tech": ["n8n", "Webhook triggers", "Email (SMTP/SendGrid)", "HTTP nodes"],
        "env_vars": [
            ("N8N_URL", "Your n8n instance URL", "http://localhost:5678"),
            ("SMTP_HOST", "SMTP server", "smtp.gmail.com"),
            ("SMTP_USER", "SMTP username", "you@gmail.com"),
            ("SMTP_PASSWORD", "SMTP password", "app-password"),
            ("CRM_API_KEY", "CRM API key (optional)", "your-crm-key"),
        ],
        "endpoints": [
            ("Webhook: /lead-capture", "Receive new leads", '{"name": "John Doe", "email": "john@example.com", "source": "landing-page", "interest": "premium-plan"}', '{"status": "captured", "lead_id": "LD-001", "next_action": "welcome-email-in-5min"}'),
            ("Workflow: Welcome Email", "Auto-sent after capture", None, "Personalized welcome email sent with product info"),
            ("Workflow: Follow-up Sequence", "3-email drip campaign", None, "Day 1: Welcome → Day 3: Case study → Day 7: Special offer"),
            ("Workflow: Lead Scoring", "Score leads based on engagement", None, '{"lead_id": "LD-001", "score": 75, "status": "warm", "recommended_action": "schedule-call"}'),
        ],
        "use_cases": ["SaaS onboarding sequences", "Real estate lead follow-up", "Course/webinar nurturing", "E-commerce abandoned cart"],
    },
    "social-media-auto-poster": {
        "title": "Social Media Auto-Poster",
        "price": "$49.99",
        "tagline": "Schedule and auto-post to multiple platforms",
        "description": "A FastAPI backend for creating, scheduling, and publishing social media posts across multiple platforms. Includes AI content generation, analytics, and bulk scheduling.",
        "tech": ["Python 3.10+", "FastAPI", "OpenAI GPT", "Twitter/X API", "SQLite", "Docker"],
        "env_vars": [
            ("OPENAI_API_KEY", "Your OpenAI API key", "sk-your-key-here"),
            ("TWITTER_API_KEY", "Twitter API key", "your-twitter-key"),
            ("TWITTER_API_SECRET", "Twitter API secret", "your-twitter-secret"),
            ("TWITTER_ACCESS_TOKEN", "Twitter access token", "your-access-token"),
            ("TWITTER_ACCESS_SECRET", "Twitter access secret", "your-access-secret"),
            ("PORT", "Server port", "8000"),
        ],
        "endpoints": [
            ("POST /posts", "Create a new post", '{"content": "Exciting news! We just launched our new AI feature 🚀", "platforms": ["twitter", "linkedin"], "schedule_at": "2026-02-18T10:00:00Z", "hashtags": ["#AI", "#Launch"]}', '{"id": 1, "content": "Exciting news! We just launched...", "status": "scheduled", "scheduled_for": "2026-02-18T10:00:00Z", "platforms": ["twitter", "linkedin"]}'),
            ("GET /posts", "List all posts", None, '[{"id": 1, "content": "Exciting news...", "status": "scheduled"}, {"id": 2, "content": "Weekly tip...", "status": "published"}]'),
            ("POST /posts/{id}/publish", "Publish immediately", None, '{"id": 1, "status": "published", "published_at": "2026-02-17T15:30:00Z", "platform_ids": {"twitter": "1892456789"}}'),
            ("GET /analytics", "Get posting analytics", None, '{"total_posts": 45, "published": 38, "scheduled": 7, "engagement": {"likes": 1250, "retweets": 340, "clicks": 890}}'),
            ("GET /platforms", "List connected platforms", None, '[{"name": "twitter", "connected": true, "username": "@mycompany"}, {"name": "linkedin", "connected": false}]'),
        ],
        "use_cases": ["Marketing teams", "Social media agencies", "Personal brand management", "Multi-platform content distribution"],
    },
    "webhook-relay-logger": {
        "title": "Webhook Relay & Logger",
        "price": "$19.99",
        "tagline": "Capture, inspect, replay, and relay webhooks",
        "description": "A complete webhook management system with endpoint creation, payload logging, relay rules, replay functionality, and a built-in dashboard. Debug and route webhooks with ease.",
        "tech": ["Python 3.10+", "FastAPI", "SQLite", "HTML Dashboard", "Docker"],
        "env_vars": [
            ("PORT", "Server port", "8000"),
            ("DB_PATH", "Database path", "./webhooks.db"),
            ("MAX_PAYLOAD_SIZE", "Max payload size in bytes", "1048576"),
            ("RETENTION_DAYS", "Days to keep webhook logs", "30"),
        ],
        "endpoints": [
            ("POST /endpoints", "Create a webhook endpoint", '{"name": "Stripe Payments", "description": "Capture Stripe webhook events"}', '{"id": "ep_a1b2c3", "name": "Stripe Payments", "url": "/webhook/ep_a1b2c3", "created_at": "2026-02-17"}'),
            ("GET /webhooks", "List captured webhooks", None, '[{"id": "wh_001", "endpoint": "Stripe Payments", "method": "POST", "status": 200, "timestamp": "2026-02-17T14:30:00Z"}]'),
            ("GET /webhooks/{id}", "Inspect webhook payload", None, '{"id": "wh_001", "headers": {"content-type": "application/json", "stripe-signature": "..."}, "body": {"type": "payment_intent.succeeded", "amount": 2999}}'),
            ("POST /relays", "Create a relay rule", '{"endpoint_id": "ep_a1b2c3", "target_url": "https://myapp.com/api/payments", "filter": {"type": "payment_intent.succeeded"}}', '{"id": "rl_001", "status": "active", "endpoint": "Stripe Payments", "target": "https://myapp.com/api/payments"}'),
            ("POST /webhooks/{id}/replay", "Replay a webhook", None, '{"status": "replayed", "response_code": 200, "response_time_ms": 145}'),
            ("GET /dashboard", "Visual dashboard (HTML)", None, "(Interactive HTML dashboard with charts and logs)"),
        ],
        "use_cases": ["Webhook debugging during development", "Payment webhook routing", "Multi-service event distribution", "API integration testing"],
    },
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Setup Guide</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; line-height: 1.7; color: #1a1a2e; background: #fafbfc; }}
        .cover {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 40px; text-align: center; }}
        .cover h1 {{ font-size: 2.8rem; margin-bottom: 10px; }}
        .cover .tagline {{ font-size: 1.3rem; opacity: 0.9; margin-bottom: 20px; }}
        .cover .price {{ font-size: 1.5rem; background: rgba(255,255,255,0.2); display: inline-block; padding: 8px 24px; border-radius: 30px; }}
        .cover .version {{ margin-top: 20px; opacity: 0.7; font-size: 0.9rem; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        h2 {{ color: #667eea; font-size: 1.8rem; margin: 50px 0 20px; padding-bottom: 10px; border-bottom: 2px solid #e8ecf1; }}
        h3 {{ color: #333; font-size: 1.3rem; margin: 30px 0 15px; }}
        p {{ margin-bottom: 15px; color: #444; }}
        .step {{ background: white; border: 1px solid #e8ecf1; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
        .step-number {{ background: #667eea; color: white; width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; }}
        .step h3 {{ display: inline; vertical-align: middle; margin: 0; }}
        code {{ background: #f0f2f5; padding: 2px 8px; border-radius: 4px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 0.9em; }}
        pre {{ background: #1a1a2e; color: #e8ecf1; padding: 20px; border-radius: 10px; overflow-x: auto; margin: 15px 0; font-size: 0.9rem; line-height: 1.5; }}
        pre code {{ background: none; padding: 0; color: inherit; }}
        .highlight {{ color: #7bed9f; }}
        .comment {{ color: #636e72; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #667eea; color: white; padding: 12px 16px; text-align: left; }}
        td {{ padding: 12px 16px; border-bottom: 1px solid #e8ecf1; }}
        tr:hover td {{ background: #f8f9ff; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin: 2px; }}
        .badge-blue {{ background: #e3f2fd; color: #1565c0; }}
        .badge-green {{ background: #e8f5e9; color: #2e7d32; }}
        .badge-orange {{ background: #fff3e0; color: #e65100; }}
        .tip {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
        .warning {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
        .example {{ background: #f8f9ff; border: 1px solid #e0e4ff; border-radius: 10px; padding: 20px; margin: 20px 0; }}
        .example h4 {{ color: #667eea; margin-bottom: 10px; }}
        .arrow {{ color: #667eea; font-size: 1.5rem; text-align: center; margin: 10px 0; }}
        .use-cases {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 15px 0; }}
        .use-case {{ background: white; border: 1px solid #e8ecf1; border-radius: 8px; padding: 15px; }}
        .use-case::before {{ content: "✅ "; }}
        .footer {{ text-align: center; padding: 40px; color: #888; font-size: 0.9rem; border-top: 1px solid #e8ecf1; margin-top: 60px; }}
        .toc {{ background: white; border: 1px solid #e8ecf1; border-radius: 12px; padding: 25px; margin: 30px 0; }}
        .toc a {{ color: #667eea; text-decoration: none; display: block; padding: 5px 0; }}
        .toc a:hover {{ text-decoration: underline; }}
        @media print {{ .cover {{ padding: 60px 20px; }} pre {{ font-size: 0.8rem; }} }}
        @media (max-width: 600px) {{ .cover h1 {{ font-size: 2rem; }} .use-cases {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>{title}</h1>
        <p class="tagline">{tagline}</p>
        <span class="price">{price}</span>
        <p class="version">Setup Guide • v1.0 • {date}</p>
    </div>
    <div class="container">
        <div class="toc">
            <h3>📖 Table of Contents</h3>
            <a href="#overview">1. Overview</a>
            <a href="#requirements">2. Requirements</a>
            <a href="#quickstart">3. Quick Start (5 minutes)</a>
            <a href="#configuration">4. Configuration</a>
            <a href="#api-reference">5. API Reference & Examples</a>
            <a href="#use-cases">6. Use Cases</a>
            <a href="#docker">7. Docker Deployment</a>
            <a href="#troubleshooting">8. Troubleshooting</a>
        </div>

        <h2 id="overview">1. Overview</h2>
        <p>{description}</p>
        <h3>Tech Stack</h3>
        <p>{tech_badges}</p>

        <h2 id="requirements">2. Requirements</h2>
        <div class="step">
            <ul>
                <li>Python 3.10 or higher</li>
                <li>pip (Python package manager)</li>
                <li>An OpenAI API key (if AI features are used)</li>
                <li>Docker (optional, for containerized deployment)</li>
            </ul>
        </div>

        <h2 id="quickstart">3. Quick Start</h2>
        <p>Get up and running in under 5 minutes:</p>

        <div class="step">
            <span class="step-number">1</span>
            <h3>Unzip the package</h3>
            <pre><code>tar -xzf {slug}.tar.gz
cd {slug}/</code></pre>
        </div>

        <div class="step">
            <span class="step-number">2</span>
            <h3>Configure environment</h3>
            <pre><code>cp .env.example .env
<span class="comment"># Edit .env with your API keys and settings</span>
nano .env</code></pre>
        </div>

        <div class="step">
            <span class="step-number">3</span>
            <h3>Run setup</h3>
            <pre><code>chmod +x setup.sh
./setup.sh</code></pre>
            <p>This installs dependencies, validates your config, and starts the server.</p>
        </div>

        <div class="step">
            <span class="step-number">4</span>
            <h3>Verify it's running</h3>
            <pre><code>curl http://localhost:8000/
<span class="comment"># or open http://localhost:8000/docs in your browser</span></code></pre>
        </div>

        <div class="tip">
            💡 <strong>Tip:</strong> Visit <code>http://localhost:8000/docs</code> for the interactive Swagger UI where you can test all endpoints directly in your browser.
        </div>

        <h2 id="configuration">4. Configuration</h2>
        <table>
            <tr><th>Variable</th><th>Description</th><th>Default</th></tr>
            {env_table_rows}
        </table>

        <h2 id="api-reference">5. API Reference & Examples</h2>
        <p>Below are all available endpoints with real request/response examples.</p>
        {endpoint_sections}

        <h2 id="use-cases">6. Use Cases</h2>
        <div class="use-cases">
            {use_case_cards}
        </div>

        <h2 id="docker">7. Docker Deployment</h2>
        <div class="step">
            <span class="step-number">1</span>
            <h3>Build the image</h3>
            <pre><code>docker build -t {slug} .</code></pre>
        </div>
        <div class="step">
            <span class="step-number">2</span>
            <h3>Run the container</h3>
            <pre><code>docker run -d --name {slug} \\
  --env-file .env \\
  -p 8000:8000 \\
  {slug}</code></pre>
        </div>
        <div class="tip">
            💡 <strong>Tip:</strong> For production, use <code>docker-compose up -d</code> if a <code>docker-compose.yml</code> is included.
        </div>

        <h2 id="troubleshooting">8. Troubleshooting</h2>
        <div class="warning">
            ⚠️ <strong>"Module not found" error:</strong> Make sure you ran <code>./setup.sh</code> or <code>pip install -r requirements.txt</code>
        </div>
        <div class="warning">
            ⚠️ <strong>"OPENAI_API_KEY not set":</strong> Check your <code>.env</code> file has a valid API key (starts with <code>sk-</code>)
        </div>
        <div class="warning">
            ⚠️ <strong>Port already in use:</strong> Change the <code>PORT</code> in <code>.env</code> or stop the conflicting service: <code>lsof -i :8000</code>
        </div>
        <div class="warning">
            ⚠️ <strong>Docker permission denied:</strong> Run with <code>sudo</code> or add your user to the docker group: <code>sudo usermod -aG docker $USER</code>
        </div>

        <h3>Getting Help</h3>
        <p>If you encounter issues:</p>
        <ul>
            <li>Check the <code>/docs</code> endpoint for API documentation</li>
            <li>Review logs: <code>docker logs {slug}</code></li>
            <li>Contact support: <a href="mailto:support@mywork-ai.dev">support@mywork-ai.dev</a></li>
        </ul>
    </div>
    <div class="footer">
        <p>© 2026 MyWork-AI • <a href="https://mywork-ai.dev">mywork-ai.dev</a></p>
        <p>Thank you for your purchase! 🚀</p>
    </div>
</body>
</html>"""


def generate_html(slug, product):
    tech_badges = " ".join(f'<span class="badge badge-blue">{t}</span>' for t in product["tech"])
    
    env_rows = "\n".join(
        f'<tr><td><code>{name}</code></td><td>{desc}</td><td><code>{default}</code></td></tr>'
        for name, desc, default in product["env_vars"]
    )
    
    endpoint_html = ""
    for i, (method, desc, req_body, resp_body) in enumerate(product["endpoints"], 1):
        endpoint_html += f"""
        <div class="example">
            <h4>{method}</h4>
            <p>{desc}</p>
"""
        if req_body:
            endpoint_html += f"""
            <strong>Request:</strong>
            <pre><code>curl -X {method.split()[0]} http://localhost:8000{method.split()[1] if '/' in method.split()[1] else ''} \\
  -H "Content-Type: application/json" \\
  -d '{req_body}'</code></pre>
"""
        endpoint_html += f"""
            <div class="arrow">⬇️ Response</div>
            <pre><code>{resp_body}</code></pre>
        </div>
"""
    
    use_case_cards = "\n".join(f'<div class="use-case">{uc}</div>' for uc in product["use_cases"])
    
    html = HTML_TEMPLATE.format(
        title=product["title"],
        tagline=product["tagline"],
        price=product["price"],
        description=product["description"],
        slug=slug,
        date=datetime.now().strftime("%B %Y"),
        tech_badges=tech_badges,
        env_table_rows=env_rows,
        endpoint_sections=endpoint_html,
        use_case_cards=use_case_cards,
    )
    return html


def main():
    base = "/home/Memo1981/n8n-automations"
    
    for slug, product in PRODUCTS.items():
        product_dir = os.path.join(base, slug)
        docs_dir = os.path.join(product_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Generate HTML guide
        html = generate_html(slug, product)
        guide_path = os.path.join(docs_dir, "guide.html")
        with open(guide_path, "w") as f:
            f.write(html)
        
        print(f"✅ {slug}/docs/guide.html")
    
    print(f"\nDone! Generated guides for {len(PRODUCTS)} products.")


if __name__ == "__main__":
    main()
