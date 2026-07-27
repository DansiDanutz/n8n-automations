#!/bin/bash

# AI SEO Content Generator Setup Script
# This script sets up the development environment

set -e  # Exit on any error

echo "🚀 Setting up AI SEO Content Generator..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is available
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        print_error "Python 3.11+ required, found $PYTHON_VERSION"
        exit 1
    else
        print_status "Python $PYTHON_VERSION found ✓"
    fi
else
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 not found. Please install pip"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created ✓"
else
    print_status "Virtual environment already exists ✓"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade "pip>=26.1.2"

# Install requirements
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Dependencies installed ✓"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys before running the service"
else
    print_status ".env file already exists ✓"
fi

# Check if Docker is available (optional)
if command -v docker &> /dev/null; then
    print_status "Docker found ✓"
    print_status "You can run 'docker build -t ai-seo-generator .' to build Docker image"
else
    print_warning "Docker not found. Install Docker for containerized deployment"
fi

# Check API keys in .env file
if [ -f ".env" ]; then
    if grep -q "replace-with-at-least-32-random-characters" .env; then
        print_warning "The caller API key is not configured yet. Edit .env before starting the service."
    elif grep -q "your_openrouter_api_key_here" .env && grep -q "your_openai_api_key_here" .env; then
        print_warning "An AI provider key is not configured yet. Edit .env before starting the service."
    else
        print_status "API keys appear to be configured ✓"
    fi
fi

# Create logs directory
mkdir -p logs
print_status "Logs directory created ✓"

# Test imports
print_status "Testing Python imports..."
python3 -c "
import fastapi
import uvicorn
import aiohttp
import pydantic
from dotenv import load_dotenv
print('All imports successful ✓')
" 2>/dev/null && print_status "Import test passed ✓" || {
    print_error "Import test failed. Some dependencies may be missing."
    exit 1
}

print_status "Setup completed successfully! 🎉"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit .env file with your API keys"
echo "2. Run the service: python main.py"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo "4. Test health endpoint: curl http://localhost:8000/health"
echo
echo -e "${YELLOW}API Keys needed:${NC}"
echo "- OpenRouter API key: https://openrouter.ai/"
echo "- OR OpenAI API key: https://platform.openai.com/"
echo
echo -e "${GREEN}Service will run on: http://localhost:8000${NC}"
