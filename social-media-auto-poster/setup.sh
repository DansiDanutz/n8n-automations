#!/bin/bash

# Social Media Auto-Poster Setup Script
# Version: 1.0.0

set -e

echo "📱 Social Media Auto-Poster Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Installing pip..."
    python3 -m ensurepip --upgrade
fi

echo "📦 Installing dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "🔑 Please edit .env and add your social media API credentials"
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
import sqlite3
import os

DB_PATH = './social_media.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Posts table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT UNIQUE NOT NULL,
        content TEXT NOT NULL,
        platforms TEXT NOT NULL,
        media_urls TEXT,
        scheduled_time TEXT,
        status TEXT DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        published_at TIMESTAMP,
        error_message TEXT,
        engagement_metrics TEXT
    )
''')

# Analytics table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT,
        platform TEXT NOT NULL,
        metric_type TEXT NOT NULL,
        metric_value INTEGER DEFAULT 0,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts (post_id)
    )
''')

# Platform credentials table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS platform_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT UNIQUE NOT NULL,
        credentials TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print('✅ Database initialized successfully')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your social media API credentials:"
echo "   - Twitter: Get API keys from https://developer.twitter.com"
echo "   - Instagram: Requires Facebook Graph API setup"
echo "   - LinkedIn: Requires LinkedIn API OAuth 2.0 setup"
echo "2. Start the server: python3 main.py"
echo "3. Visit http://localhost:8000 to test the API"
echo ""
echo "API endpoints:"
echo "- POST /posts - Create/schedule social media posts"
echo "- GET /posts - List all posts"
echo "- POST /posts/{id}/publish - Publish post immediately"
echo "- GET /analytics - View posting analytics"
echo "- GET /platforms - Check platform configuration status"
echo ""
echo "Example curl command to schedule a post:"
echo 'curl -X POST "http://localhost:8000/posts" -H "Content-Type: application/json" -d '\''{"content": "Hello social media! 🚀", "platforms": ["twitter"], "scheduled_time": "2024-12-25T10:00:00Z"}'\'''
echo ""
echo "Note: Only Twitter posting is fully implemented. Instagram and LinkedIn are placeholders requiring additional API setup."