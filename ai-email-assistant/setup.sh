#!/bin/bash

# AI Email Assistant Setup Script
# Automated installation and configuration

set -e

echo "🚀 AI Email Assistant Setup Starting..."
echo "========================================"

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

# Download NLTK data
log_info "Downloading NLTK data..."
python3 -c "
import nltk
import os
os.makedirs('nltk_data', exist_ok=True)
nltk.data.path.append('./nltk_data')
try:
    nltk.download('punkt', download_dir='./nltk_data', quiet=True)
    nltk.download('stopwords', download_dir='./nltk_data', quiet=True)
    nltk.download('vader_lexicon', download_dir='./nltk_data', quiet=True)
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'NLTK download warning: {e}')
"

# Try to download spaCy model
log_info "Attempting to download spaCy model..."
python3 -m spacy download en_core_web_sm || log_warning "spaCy model not available, will use fallback"

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
log_success "Directories created"

# Setup database (if PostgreSQL is available)
if command -v psql &> /dev/null; then
    log_info "PostgreSQL found, setting up database..."
    read -p "Create database? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        createdb ai_email_assistant || log_warning "Database might already exist"
        log_success "Database setup completed"
    fi
else
    log_warning "PostgreSQL not found. Please install and configure manually"
fi

# Setup Redis (if available)
if command -v redis-cli &> /dev/null; then
    log_success "Redis found"
else
    log_warning "Redis not found. Please install Redis for full functionality"
fi

# Generate default screenshots directory structure
log_info "Setting up screenshots directory..."
mkdir -p screenshots
echo "Placeholder for dashboard screenshot" > screenshots/dashboard.png.txt
echo "Placeholder for email summary screenshot" > screenshots/email-summary.png.txt
echo "Placeholder for reply generation screenshot" > screenshots/reply-generation.png.txt

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
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_email_assistant
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    env_file:
      - .env

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_email_assistant
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
  postgres_data:
EOF
log_success "Docker Compose file created"

# Create systemd service file (optional)
log_info "Creating systemd service file (optional)..."
cat > ai-email-assistant.service << EOF
[Unit]
Description=AI Email Assistant
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
log_info "Systemd service file created at ai-email-assistant.service"

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

# Final instructions
echo
log_success "🎉 Setup completed successfully!"
echo
log_info "Next steps:"
echo "1. Edit the .env file with your configuration:"
echo "   - Add your OpenAI API key"
echo "   - Configure email provider credentials"
echo "   - Set database and Redis URLs"
echo
echo "2. Start the application:"
echo "   Option A - Docker (recommended):"
echo "   docker-compose up -d"
echo
echo "   Option B - Local development:"
echo "   source venv/bin/activate"
echo "   uvicorn backend.main:app --reload --port 8000"
echo
echo "3. Visit http://localhost:8000/docs for API documentation"
echo
log_info "For support, visit: https://github.com/mywork-ai/ai-email-assistant"
echo
log_warning "Don't forget to configure your email provider OAuth applications!"

echo
echo "🚀 Ready to revolutionize your email management!"