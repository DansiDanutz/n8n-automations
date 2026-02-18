#!/bin/bash

# MyWork-AI Bundle - Universal Setup Script
# Sets up all 10 automation tools at once

set -e

echo "🚀 MyWork-AI Bundle Universal Setup"
echo "===================================="
echo ""
echo "Setting up 10 professional automation tools:"
echo "- AI Customer Support Bot"
echo "- Invoice Generator API"  
echo "- Social Media Auto-Poster"
echo "- AI Data Scraper"
echo "- AI Email Assistant"
echo "- AI SEO Content Generator"
echo "- Appointment Booking System"
echo "- Smart Lead Nurture"
echo "- Webhook Relay Logger"
echo "- AI Purchase Webhook Handler"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
NODE_VERSION=$(node -v)
echo "✅ Python $PYTHON_VERSION found"
echo "✅ Node.js $NODE_VERSION found"
echo ""

# Function to setup Python-based tools
setup_python_tool() {
    local tool_name=$1
    local tool_dir=$2
    local port=$3
    
    echo "🔧 Setting up $tool_name..."
    
    if [ ! -d "../$tool_dir" ]; then
        echo "⚠️  Directory ../$tool_dir not found, skipping"
        return
    fi
    
    cd "../$tool_dir"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install requirements
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
    fi
    
    # Update port in .env if specified
    if [ -n "$port" ] && [ -f ".env" ]; then
        sed -i "s/PORT=.*/PORT=$port/" .env 2>/dev/null || echo "PORT=$port" >> .env
    fi
    
    # Initialize database (for tools that have it)
    if grep -q "init_db" main.py 2>/dev/null; then
        python3 -c "
try:
    from main import init_db
    init_db()
    print('Database initialized')
except Exception as e:
    print(f'Database init skipped: {e}')
" 2>/dev/null || echo "Database initialization skipped"
    fi
    
    echo "✅ $tool_name setup complete"
    cd - > /dev/null
}

# Function to setup Node.js-based tools
setup_node_tool() {
    local tool_name=$1
    local tool_dir=$2
    local port=$3
    
    echo "🔧 Setting up $tool_name..."
    
    if [ ! -d "../$tool_dir" ]; then
        echo "⚠️  Directory ../$tool_dir not found, skipping"
        return
    fi
    
    cd "../$tool_dir"
    
    # Install dependencies
    npm install > /dev/null 2>&1
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
    fi
    
    # Update port in .env if specified
    if [ -n "$port" ] && [ -f ".env" ]; then
        sed -i "s/PORT=.*/PORT=$port/" .env 2>/dev/null || echo "PORT=$port" >> .env
    fi
    
    echo "✅ $tool_name setup complete"
    cd - > /dev/null
}

# Setup Python-based tools (FastAPI)
echo "📦 Setting up Python-based tools..."
setup_python_tool "AI Customer Support Bot" "ai-customer-support-bot" "8000"
setup_python_tool "Invoice Generator API" "invoice-generator-api" "8001"
setup_python_tool "Social Media Auto-Poster" "social-media-auto-poster" "8002"
setup_python_tool "AI Data Scraper" "ai-data-scraper" "8003"
setup_python_tool "AI Email Assistant" "ai-email-assistant" "8004"
setup_python_tool "AI SEO Content Generator" "ai-seo-content-generator" "8005"
setup_python_tool "Appointment Booking System" "appointment-booking-system" "8006"

echo ""
echo "📦 Setting up Node.js-based tools..."
setup_node_tool "Smart Lead Nurture" "smart-lead-nurture" "3000"
setup_node_tool "Webhook Relay Logger" "webhook-relay-logger" "3001"

# Handle the AI Purchase Webhook Handler (might be in purchase-webhook directory)
if [ -d "../purchase-webhook" ]; then
    setup_node_tool "AI Purchase Webhook Handler" "purchase-webhook" "3002"
else
    echo "⚠️  purchase-webhook directory not found, skipping AI Purchase Webhook Handler"
fi

# Create startup scripts
echo ""
echo "📝 Creating startup scripts..."

# Create Python services startup script
cat > start_python_services.sh << 'EOF'
#!/bin/bash
# Start all Python-based services

echo "🐍 Starting Python services..."

# Array of Python tools and their ports
declare -A python_tools=(
    ["ai-customer-support-bot"]="8000"
    ["invoice-generator-api"]="8001"
    ["social-media-auto-poster"]="8002"
    ["ai-data-scraper"]="8003"
    ["ai-email-assistant"]="8004"
    ["ai-seo-content-generator"]="8005"
    ["appointment-booking-system"]="8006"
)

for tool in "${!python_tools[@]}"; do
    port=${python_tools[$tool]}
    if [ -d "../$tool" ]; then
        echo "Starting $tool on port $port..."
        cd "../$tool"
        source venv/bin/activate
        nohup python3 main.py > "logs/$tool.log" 2>&1 &
        echo $! > "$tool.pid"
        cd - > /dev/null
        echo "✅ $tool started (PID: $(cat ../$tool/$tool.pid))"
    fi
done

echo ""
echo "🎉 All Python services started!"
echo "View logs: tail -f ../tool-name/logs/tool-name.log"
echo "Stop services: ./stop_python_services.sh"
EOF

# Create Node.js services startup script
cat > start_node_services.sh << 'EOF'
#!/bin/bash
# Start all Node.js-based services

echo "📦 Starting Node.js services..."

# Check if PM2 is available
if command -v pm2 &> /dev/null; then
    echo "Using PM2 for process management..."
    
    # Smart Lead Nurture
    if [ -d "../smart-lead-nurture" ]; then
        cd "../smart-lead-nurture"
        pm2 start ecosystem.config.js --name "smart-lead-nurture" 2>/dev/null || pm2 start npm --name "smart-lead-nurture" -- start
        cd - > /dev/null
    fi
    
    # Webhook Relay Logger
    if [ -d "../webhook-relay-logger" ]; then
        cd "../webhook-relay-logger"
        pm2 start ecosystem.config.js --name "webhook-relay" 2>/dev/null || pm2 start npm --name "webhook-relay" -- start
        cd - > /dev/null
    fi
    
    # Purchase Webhook Handler
    if [ -d "../purchase-webhook" ]; then
        cd "../purchase-webhook"
        pm2 start ecosystem.config.js --name "purchase-webhook" 2>/dev/null || pm2 start npm --name "purchase-webhook" -- start
        cd - > /dev/null
    fi
    
    pm2 save
    echo "✅ Node.js services started with PM2"
    echo "Manage with: pm2 status, pm2 logs, pm2 stop all"
    
else
    echo "PM2 not found, starting with nohup..."
    
    # Smart Lead Nurture
    if [ -d "../smart-lead-nurture" ]; then
        cd "../smart-lead-nurture"
        nohup npm start > logs/smart-lead-nurture.log 2>&1 &
        echo $! > smart-lead-nurture.pid
        cd - > /dev/null
        echo "✅ Smart Lead Nurture started"
    fi
    
    # Webhook Relay Logger
    if [ -d "../webhook-relay-logger" ]; then
        cd "../webhook-relay-logger"
        nohup npm start > logs/webhook-relay.log 2>&1 &
        echo $! > webhook-relay.pid
        cd - > /dev/null
        echo "✅ Webhook Relay Logger started"
    fi
    
    # Purchase Webhook Handler
    if [ -d "../purchase-webhook" ]; then
        cd "../purchase-webhook"
        nohup npm start > logs/purchase-webhook.log 2>&1 &
        echo $! > purchase-webhook.pid
        cd - > /dev/null
        echo "✅ Purchase Webhook Handler started"
    fi
    
    echo "Install PM2 for better process management: npm install -g pm2"
fi
EOF

# Create stop scripts
cat > stop_all_services.sh << 'EOF'
#!/bin/bash
# Stop all services

echo "🛑 Stopping all services..."

# Stop PM2 services if available
if command -v pm2 &> /dev/null; then
    pm2 stop all
    pm2 delete all
    echo "✅ PM2 services stopped"
fi

# Stop Python services
for pidfile in ../*/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo "✅ Stopped service (PID: $pid)"
        fi
        rm "$pidfile"
    fi
done

echo "🎉 All services stopped"
EOF

# Make scripts executable
chmod +x start_python_services.sh
chmod +x start_node_services.sh
chmod +x stop_all_services.sh

# Create master config file
cat > config.json << 'EOF'
{
  "bundle": {
    "name": "MyWork-AI Automation Bundle",
    "version": "1.0.0",
    "tools": 10
  },
  "services": {
    "python": {
      "ai-customer-support-bot": {"port": 8000, "docs": "/docs"},
      "invoice-generator-api": {"port": 8001, "docs": "/docs"},
      "social-media-auto-poster": {"port": 8002, "docs": "/docs"},
      "ai-data-scraper": {"port": 8003, "docs": "/docs"},
      "ai-email-assistant": {"port": 8004, "docs": "/docs"},
      "ai-seo-content-generator": {"port": 8005, "docs": "/docs"},
      "appointment-booking-system": {"port": 8006, "docs": "/docs"}
    },
    "nodejs": {
      "smart-lead-nurture": {"port": 3000},
      "webhook-relay-logger": {"port": 3001},
      "purchase-webhook": {"port": 3002}
    }
  }
}
EOF

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "✅ All 10 tools are configured and ready to use"
echo ""
echo "🚀 Quick Start:"
echo "1. Configure your API keys in each tool's .env file"
echo "2. Start all services:"
echo "   ./start_python_services.sh"
echo "   ./start_node_services.sh"
echo ""
echo "3. Stop all services:"
echo "   ./stop_all_services.sh"
echo ""
echo "📚 API Documentation (when services are running):"
for port in {8000..8006}; do
    echo "   http://localhost:$port/docs"
done
echo ""
echo "🔧 Configuration needed:"
echo "- Add OPENAI_API_KEY to AI tools (.env files)"
echo "- Add Twitter API keys to social-media-auto-poster/.env"
echo "- Add email credentials to ai-email-assistant/.env"
echo "- Customize company info in invoice-generator-api/.env"
echo ""
echo "📖 Read QUICK_START.md for detailed instructions"
echo ""
echo "🎯 Happy automating!"