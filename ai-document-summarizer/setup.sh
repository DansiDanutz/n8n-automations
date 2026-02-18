#!/bin/bash
set -e
echo "🚀 Setting up..."
python3 --version >/dev/null 2>&1 || { echo "❌ Python 3 required"; exit 1; }
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate 2>/dev/null || true
pip install -q -r requirements.txt
[ ! -f ".env" ] && cp .env.example .env && echo "📝 Created .env — edit with your settings"
echo "✅ Setup complete! Run: python3 main.py"
