#!/bin/bash

# Invoice Generator API Setup Script
# Version: 1.0.0

set -e

echo "📄 Invoice Generator API Setup"
echo "==============================="

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

# Install system dependencies for PDF generation
echo "🔧 Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
elif command -v yum &> /dev/null; then
    sudo yum install -y python3-devel python3-pip python3-cffi pango harfbuzz
elif command -v brew &> /dev/null; then
    brew install python3 pango
fi

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
    echo "🔧 Please edit .env and configure your company information"
fi

# Create templates directory if it doesn't exist
if [ ! -d "templates" ]; then
    echo "📁 Creating templates directory..."
    mkdir -p templates
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
import sqlite3
import os

DB_PATH = './invoices.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Invoices table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        client_email TEXT,
        client_address TEXT,
        issue_date TEXT NOT NULL,
        due_date TEXT,
        currency TEXT DEFAULT 'USD',
        tax_rate REAL DEFAULT 0.0,
        subtotal REAL NOT NULL,
        tax_amount REAL NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'draft',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Invoice items table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        description TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
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
echo "1. Edit .env file and configure your company information"
echo "2. Start the server: python3 main.py"
echo "3. Visit http://localhost:8000 to test the API"
echo ""
echo "API endpoints:"
echo "- POST /invoices - Create new invoice"
echo "- GET /invoices/{id} - Get invoice details"
echo "- GET /invoices/{id}/pdf - Download invoice as PDF"
echo "- GET /invoices/{id}/html - View invoice as HTML"
echo "- GET /invoices - List all invoices"
echo ""
echo "Example curl command to create invoice:"
echo 'curl -X POST "http://localhost:8000/invoices" -H "Content-Type: application/json" -d '\''{"client_name": "ACME Corp", "items": [{"description": "Web Development", "quantity": 1, "unit_price": 1000}]}'\'''
echo ""
echo "PDF Generation: Using weasyprint and reportlab for PDF export"