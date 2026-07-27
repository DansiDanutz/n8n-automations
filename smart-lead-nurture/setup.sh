#!/bin/bash
# Smart Lead Nurture - Quick Setup
set -e

echo "🚀 Setting up Smart Lead Nurture automation..."

# Check dependencies
command -v mw >/dev/null 2>&1 || { echo "❌ MyWork-AI not installed. Run: pip install mywork-ai"; exit 1; }

# Check for .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env from template. Please fill in your credentials:"
    echo "   - N8N_API_URL and N8N_API_KEY"
    echo "   - LEAD_WEBHOOK_SECRET (configure as Lead Webhook Auth in n8n)"
    echo "   - OPENAI_API_KEY"
    echo "   - SMTP credentials"
    echo "   - (Optional) SLACK_WEBHOOK_URL"
    echo ""
    echo "Then run this script again."
    exit 0
fi

# Source env
source .env

# Validate required vars
for var in N8N_API_URL N8N_API_KEY OPENAI_API_KEY; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required: $var in .env"
        exit 1
    fi
done

# Import workflow to n8n
echo "📦 Importing workflow to n8n..."
RESPONSE=$(curl -s -X POST "${N8N_API_URL}/api/v1/workflows" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    -H "Content-Type: application/json" \
    -d @src/workflow.json)

WORKFLOW_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)

if [ -n "$WORKFLOW_ID" ]; then
    echo "✅ Workflow imported! ID: $WORKFLOW_ID"
    
    # Activate it
    curl -s -X PATCH "${N8N_API_URL}/api/v1/workflows/${WORKFLOW_ID}" \
        -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"active": true}' > /dev/null
    
    echo "✅ Workflow activated!"
    echo ""
    echo "🎯 Your webhook endpoint: ${N8N_API_URL}/webhook/lead-capture"
    echo "   Send POST requests with: name, email, company, role, source, message"
else
    echo "❌ Failed to import workflow. Check your N8N_API_URL and N8N_API_KEY"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Test with:"
echo "   curl -X POST ${N8N_API_URL}/webhook/lead-capture \\"
echo "     -H 'X-Lead-Secret: YOUR_LEAD_WEBHOOK_SECRET' \\"
echo "     -H 'Content-Type: application/json' \\"
echo '     -d '"'"'{"name":"Test User","email":"test@example.com","company":"Acme","role":"CTO","source":"website","message":"Interested in your product"}'"'"
