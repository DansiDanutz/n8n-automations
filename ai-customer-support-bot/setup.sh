#!/bin/bash

# AI Customer Support Bot Setup Script
# Version: 1.0.0

set -e

echo "🤖 AI Customer Support Bot Setup"
echo "================================="

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
python -m pip install --upgrade "pip>=26.1.2"
python -m pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "🔑 Please edit .env and add your OPENAI_API_KEY"
fi

# Create knowledge_base directory if it doesn't exist
if [ ! -d "knowledge_base" ]; then
    echo "📚 Creating knowledge base directory..."
    mkdir -p knowledge_base
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
import sqlite3
import os

DB_PATH = './support_bot.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Conversations table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        satisfaction_rating INTEGER,
        feedback TEXT
    )
''')

# Messages table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
''')

# Feedback table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        message_id INTEGER,
        rating INTEGER NOT NULL,
        comment TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id),
        FOREIGN KEY (message_id) REFERENCES messages (id)
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
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. Start the server: python3 main.py"
echo "3. Visit http://localhost:8000 to test the API"
echo ""
echo "API endpoints:"
echo "- POST /chat - Send messages to AI"
echo "- GET /conversations - List conversations"
echo "- POST /feedback - Submit feedback"
echo "- GET /analytics - View analytics"
echo ""
echo "Example curl command:"
echo 'curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '\''{"message": "Hello, I need help", "user_id": "test-user"}'\'''
