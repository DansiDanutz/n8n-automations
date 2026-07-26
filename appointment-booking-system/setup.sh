#!/bin/bash

# Appointment Booking System Setup Script
# This script sets up the development environment

set -e  # Exit on any error

echo "📅 Setting up Appointment Booking System..."

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
python -m pip install --upgrade "pip>=26.1.2"

# Install requirements
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
    print_status "Dependencies installed ✓"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before running the service"
else
    print_status ".env file already exists ✓"
fi

# Create necessary directories
print_status "Creating application directories..."
mkdir -p logs
mkdir -p data
print_status "Directories created ✓"

# Check if Docker is available (optional)
if command -v docker &> /dev/null; then
    print_status "Docker found ✓"
    print_status "You can run 'docker build -t appointment-system .' to build Docker image"
else
    print_warning "Docker not found. Install Docker for containerized deployment"
fi

# Test imports
print_status "Testing Python imports..."
python3 -c "
import fastapi
import uvicorn
import pydantic
from dotenv import load_dotenv
print('All imports successful ✓')
" 2>/dev/null && print_status "Import test passed ✓" || {
    print_error "Import test failed. Some dependencies may be missing."
    exit 1
}

# Create sample configuration
print_status "Creating sample configuration files..."

# Create sample time slots configuration
cat > sample_business_config.json << EOL
{
  "business_name": "Your Business Name",
  "timezone": "UTC",
  "working_hours": {
    "monday": {"start": "09:00", "end": "17:00"},
    "tuesday": {"start": "09:00", "end": "17:00"},
    "wednesday": {"start": "09:00", "end": "17:00"},
    "thursday": {"start": "09:00", "end": "17:00"},
    "friday": {"start": "09:00", "end": "17:00"},
    "saturday": {"start": "10:00", "end": "14:00"},
    "sunday": {"start": "closed", "end": "closed"}
  },
  "default_duration": 60,
  "buffer_time": 15,
  "service_types": [
    "consultation",
    "meeting",
    "appointment",
    "follow-up"
  ]
}
EOL

print_status "Sample configuration created ✓"

print_status "Setup completed successfully! 🎉"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit .env file with your configuration"
echo "2. Configure email settings if you want notifications"
echo "3. Run the service: python main.py"
echo "4. Visit http://localhost:8001/docs for API documentation"
echo "5. Test health endpoint: curl http://localhost:8001/health"
echo
echo -e "${YELLOW}Configuration needed:${NC}"
echo "- Business hours in .env file"
echo "- Email SMTP settings (optional)"
echo "- Database URL (optional, defaults to in-memory)"
echo
echo -e "${GREEN}Service will run on: http://localhost:8001${NC}"
echo
echo -e "${BLUE}Example API calls:${NC}"
echo "# Check availability"
echo "curl 'http://localhost:8001/availability?date=2026-02-20'"
echo
echo "# Create booking"
echo "curl -X POST 'http://localhost:8001/bookings' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"client_name\":\"John Doe\",\"client_email\":\"john@example.com\",\"service_type\":\"consultation\",\"date\":\"2026-02-20\",\"time\":\"14:00\"}'"
