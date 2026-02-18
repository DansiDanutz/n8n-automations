# 🚀 MyWork-AI Bundle - Quick Start Guide

## Overview
This guide will help you get all 10 automation tools up and running quickly.

---

## 🛠️ Prerequisites

### System Requirements
- **Python 3.8+** and pip3
- **Node.js 16+** and npm
- **Git** (for version control)
- **Docker** (optional but recommended)

### Install Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm git docker.io

# macOS (with Homebrew)
brew install python3 node git docker

# Windows (use WSL2 recommended)
# Install Python from python.org
# Install Node.js from nodejs.org
# Install Git from git-scm.com
# Install Docker Desktop
```

---

## ⚡ One-Command Setup (All Tools)

```bash
# Make the setup script executable and run it
chmod +x setup_all.sh
./setup_all.sh
```

This will set up all 10 tools automatically. **Skip to [Testing Your Setup](#-testing-your-setup) if you use this method.**

---

## 📋 Individual Tool Setup

### 1. 🤖 AI Customer Support Bot

```bash
cd ai-customer-support-bot

# Run setup
chmod +x setup.sh
./setup.sh

# Configure API key
nano .env
# Add: OPENAI_API_KEY=your-key-here

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8000
```

**Test the API:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help", "user_id": "test-user"}'
```

---

### 2. 📄 Invoice Generator API

```bash
cd invoice-generator-api

# Run setup
chmod +x setup.sh
./setup.sh

# Configure company info
nano .env
# Edit company details

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8001
```

**Test the API:**
```bash
curl -X POST "http://localhost:8001/invoices" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "ACME Corp",
    "items": [
      {
        "description": "Web Development",
        "quantity": 1,
        "unit_price": 1000
      }
    ]
  }'
```

---

### 3. 📱 Social Media Auto-Poster

```bash
cd social-media-auto-poster

# Run setup
chmod +x setup.sh
./setup.sh

# Configure social media APIs
nano .env
# Add your Twitter API keys

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8002
```

**Test the API:**
```bash
curl -X POST "http://localhost:8002/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello from the automation bot! 🚀",
    "platforms": ["twitter"]
  }'
```

---

### 4. 🔗 AI Data Scraper

```bash
cd ai-data-scraper

# Run setup
chmod +x setup.sh
./setup.sh

# Configure if needed
cp .env.example .env

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8003
```

**Test the API:**
```bash
curl -X POST "http://localhost:8003/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "extractors": ["title", "text"]
  }'
```

---

### 5. ✉️ AI Email Assistant

```bash
cd ai-email-assistant

# Run setup
chmod +x setup.sh
./setup.sh

# Configure email settings
nano .env
# Add email credentials and OpenAI key

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8004
```

---

### 6. 📝 AI SEO Content Generator

```bash
cd ai-seo-content-generator

# Run setup
chmod +x setup.sh
./setup.sh

# Configure API keys
nano .env
# Add OpenAI API key

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8005
```

---

### 7. 📅 Appointment Booking System

```bash
cd appointment-booking-system

# Run setup
chmod +x setup.sh
./setup.sh

# Configure settings
cp .env.example .env

# Start the service
source venv/bin/activate
python3 main.py
# Access: http://localhost:8006
```

---

### 8. 🧠 Smart Lead Nurture

```bash
cd smart-lead-nurture

# Install dependencies
npm install

# Configure settings
cp .env.example .env

# Start the service
npm start
# Access: http://localhost:3000
```

---

### 9. 🔄 Webhook Relay Logger

```bash
cd webhook-relay-logger

# Install dependencies
npm install

# Configure if needed
cp .env.example .env

# Start the service
npm start
# Access: http://localhost:3001
```

---

### 10. 💸 AI Purchase Webhook Handler

```bash
cd ai-purchase-webhook-handler

# Install dependencies
npm install

# Configure webhook settings
cp .env.example .env

# Start the service
npm start
# Access: http://localhost:3002
```

---

## 🧪 Testing Your Setup

### Health Check All Services
```bash
# Python-based services (ports 8000-8006)
for port in {8000..8006}; do
  echo "Testing port $port..."
  curl -s "http://localhost:$port" | head -1
done

# Node.js services (ports 3000-3002)
for port in {3000..3002}; do
  echo "Testing port $port..."
  curl -s "http://localhost:$port" | head -1
done
```

### Access API Documentation
Each FastAPI service has interactive docs:
- **AI Customer Support:** http://localhost:8000/docs
- **Invoice Generator:** http://localhost:8001/docs
- **Social Media Poster:** http://localhost:8002/docs
- **Data Scraper:** http://localhost:8003/docs
- **Email Assistant:** http://localhost:8004/docs
- **SEO Content Gen:** http://localhost:8005/docs
- **Appointment System:** http://localhost:8006/docs

---

## 🐳 Docker Deployment (Recommended)

### Individual Tool with Docker
```bash
cd ai-customer-support-bot

# Build image
docker build -t mywork-ai-support .

# Run container
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  --name ai-support \
  mywork-ai-support
```

### Docker Compose (All Tools)
```bash
# Create docker-compose.yml with all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## 🔧 Configuration Guide

### Required API Keys

1. **OpenAI API Key** (for AI tools)
   - Get from: https://platform.openai.com
   - Used by: Customer Support, Email Assistant, SEO Generator

2. **Twitter API Keys** (for Social Media Poster)
   - Get from: https://developer.twitter.com
   - Required: API Key, Secret, Access Token, Access Secret

3. **Email Credentials** (for Email Assistant)
   - SMTP settings for sending emails
   - IMAP settings for reading emails

### Environment Configuration

Each tool has an `.env.example` file. Copy it to `.env` and customize:

```bash
# For each tool directory
cp .env.example .env
nano .env  # Edit with your settings
```

---

## 🚀 Production Deployment

### Option 1: VPS/Cloud Server
```bash
# On your server
git clone your-repo
cd mywork-ai-bundle

# Set up with production settings
./setup_all.sh

# Use process manager (PM2)
npm install -g pm2

# Start all Node.js services
pm2 start ecosystem.config.js

# Start Python services with gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Option 2: Docker Swarm/Kubernetes
```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml mywork-ai

# Kubernetes
kubectl apply -f k8s-deployment.yml
```

### Option 3: Serverless (Selected Tools)
```bash
# Deploy FastAPI apps to Vercel
npm install -g vercel
vercel

# Deploy to AWS Lambda
pip install serverless
serverless deploy
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Python services
tail -f logs/app.log

# Node.js services with PM2
pm2 logs

# Docker containers
docker logs container-name
```

### Health Monitoring
```bash
# Simple health check script
curl -f http://localhost:8000/health || alert "Service down"
```

---

## 🔍 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 PID
```

**Python Module Not Found:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

**Node.js Module Issues:**
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules
npm install
```

**Database Issues:**
```bash
# Reset database
rm *.db
python3 -c "from main import init_db; init_db()"
```

---

## 📞 Need Help?

1. **Check the README.md** in each tool directory
2. **Review the API docs** at `/docs` endpoint
3. **Check logs** for error messages
4. **Join our Discord** for community support
5. **Email support** at support@mywork-ai.com

---

## 🎯 Next Steps

1. **Customize** the tools for your needs
2. **Set up monitoring** and alerts
3. **Configure backups** for databases
4. **Set up SSL certificates** for production
5. **Create your own integrations**

**Happy automating! 🚀**