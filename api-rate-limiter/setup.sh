#!/bin/bash
set -e

echo "🚦 Setting up API Rate Limiter..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate venv
source venv/bin/activate 2>/dev/null || true

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Create .env if missing
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "📝 Created .env from template"
    echo "   Edit .env to customize your settings:"
    echo "   - ADMIN_API_KEY: Set a secure admin key"
    echo "   - DEFAULT_RATE_LIMIT: Requests per window (default: 100)"
    echo "   - REDIS_URL: Add Redis for production use"
    echo ""
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ Setup complete!"
echo "═══════════════════════════════════════════"
echo ""
echo "  Start the server:"
echo "    python3 main.py"
echo ""
echo "  Or with Docker:"
echo "    docker build -t api-rate-limiter ."
echo "    docker run -p 8000:8000 --env-file .env api-rate-limiter"
echo ""
echo "  Then visit:"
echo "    📊 Dashboard: http://localhost:8000/dashboard"
echo "    📖 API Docs:  http://localhost:8000/docs"
echo ""
