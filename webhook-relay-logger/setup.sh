#!/bin/bash

# Webhook Relay & Logger Setup Script
# Automated installation and configuration

set -e

echo "🔗 Webhook Relay & Logger Setup Starting..."
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

# Check system requirements
log_info "Checking system requirements..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3.11+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 not found. Please install pip"
    exit 1
fi

# Create virtual environment
log_info "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_warning "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
log_info "Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..
log_success "Dependencies installed"

# Setup environment file
log_info "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    log_success "Environment file created from template"
    log_warning "Please edit .env file with your configuration"
else
    log_warning "Environment file already exists"
fi

# Create necessary directories
log_info "Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p screenshots
mkdir -p exports
log_success "Directories created"

# Setup database (if PostgreSQL is available)
if command -v psql &> /dev/null; then
    log_info "PostgreSQL found, setting up database..."
    read -p "Create database? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        createdb webhook_relay_logger || log_warning "Database might already exist"
        log_success "Database setup completed"
    fi
else
    log_warning "PostgreSQL not found. Please install and configure manually"
fi

# Setup Redis (if available)
if command -v redis-cli &> /dev/null; then
    log_success "Redis found"
else
    log_warning "Redis not found. Redis is optional but recommended for better performance"
fi

# Create Docker Compose file
log_info "Creating Docker Compose configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/webhook_relay_logger
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    env_file:
      - .env

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: webhook_relay_logger
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF
log_success "Docker Compose file created"

# Create systemd service file (optional)
log_info "Creating systemd service file (optional)..."
cat > webhook-relay-logger.service << EOF
[Unit]
Description=Webhook Relay & Logger
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
log_info "Systemd service file created at webhook-relay-logger.service"

# Create test scripts
log_info "Creating test scripts..."
mkdir -p scripts

cat > scripts/test_webhook.py << 'EOF'
#!/usr/bin/env python3
"""Test webhook catching functionality."""

import requests
import json
import time
from datetime import datetime

def test_webhook_catch():
    base_url = "http://localhost:8000"
    
    # Test data
    test_payload = {
        "event": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "Hello from test script!",
            "count": 42
        }
    }
    
    print("🧪 Testing webhook catch functionality...")
    
    # Send test webhook
    response = requests.post(
        f"{base_url}/webhook/demo-endpoint",
        json=test_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Webhook caught successfully!")
        print(f"   Webhook ID: {result.get('webhook_id')}")
        print(f"   Timestamp: {result.get('timestamp')}")
    else:
        print(f"❌ Test failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_webhook_catch()
EOF

chmod +x scripts/test_webhook.py

log_success "Test scripts created"

# Generate default screenshots directory structure
log_info "Setting up screenshots directory..."
echo "Dashboard screenshot placeholder" > screenshots/dashboard.png.txt
echo "Webhook logs screenshot placeholder" > screenshots/webhook-logs.png.txt
echo "Relay rules screenshot placeholder" > screenshots/relay-rules.png.txt
echo "Analytics screenshot placeholder" > screenshots/analytics.png.txt

# Test installation
log_info "Testing installation..."
python3 -c "
import sys
sys.path.append('./backend')
try:
    from main import app
    print('✅ Import test passed')
except ImportError as e:
    print(f'❌ Import test failed: {e}')
    sys.exit(1)
"

# Generate JWT secret if not provided
log_info "Generating JWT secret..."
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i.bak "s/your-jwt-secret-key-change-in-production/$JWT_SECRET/g" .env || true

# Final instructions
echo
log_success "🎉 Setup completed successfully!"
echo
log_info "Next steps:"
echo "1. Review and edit the .env file:"
echo "   - Database connection (if using external DB)"
echo "   - Redis URL (if using external Redis)"
echo "   - Rate limits and security settings"
echo
echo "2. Start the application:"
echo "   Option A - Docker (recommended):"
echo "   docker-compose up -d"
echo
echo "   Option B - Local development:"
echo "   source venv/bin/activate"
echo "   uvicorn backend.main:app --reload --port 8000"
echo
echo "3. Access the service:"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Web Dashboard: http://localhost:8000/dashboard"
echo "   Health Check: http://localhost:8000/health"
echo
echo "4. Test the webhook catcher:"
echo "   python3 scripts/test_webhook.py"
echo
log_info "Demo credentials:"
echo "   Email: demo@webhook.dev"
echo "   Password: webhook123"
echo
log_warning "Remember to change default passwords in production!"

echo
echo "🔗 Ready to catch and relay webhooks like a pro!"