#!/bin/bash

# Product Setup Script
# Version: 1.0.0

set -e

echo "🚀 Product Setup"
echo "================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python $(python3 --version)"

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python packages..."
    pip3 install -r requirements.txt
elif [ -f "package.json" ]; then
    echo "📦 Installing Node packages..."
    npm install
fi

# Create .env file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "🔑 Please edit .env with your configuration"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your settings"
echo "2. Run: python3 main.py"
