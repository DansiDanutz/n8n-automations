#!/bin/bash
# =============================================================================
# GENERATE PRODUCT VIDEO - One command: product dir → AI prompt → Veo2 video → GitHub → marketplace
# =============================================================================
# Usage: bash tools/generate_video.sh <product-dir>
# Example: bash tools/generate_video.sh voice-ai-platform
# =============================================================================
set -e

PRODUCT_DIR="$1"
if [ -z "$PRODUCT_DIR" ] || [ ! -d "$PRODUCT_DIR" ]; then
    echo "Usage: bash tools/generate_video.sh <product-dir>"
    echo "Example: bash tools/generate_video.sh voice-ai-platform"
    exit 1
fi

# Load credentials
CREDS_DIR="$HOME/.openclaw/workspace"
FAL_KEY="6e917d89-2e70-4bae-9569-940f0da1d27b:5556f0a5204af5fa291a3b0d380c4595"
GH_TOKEN=$(cat "$CREDS_DIR/.credentials-dan.json" 2>/dev/null | grep -o 'ghp_[a-zA-Z0-9]*' || echo "")
if [ -z "$GH_TOKEN" ]; then
    echo "❌ GitHub token not found. Set GH_TOKEN env var or add to .credentials-dan.json"
    exit 1
fi
DEEPSEEK_KEY="sk-909741cb4e0943c994d22103f76b87d0"
RELEASE_ID=287025925
GH_REPO="DansiDanutz/MyWork-AI"

SLUG=$(basename "$PRODUCT_DIR")
PRODUCT_JSON="$PRODUCT_DIR/product.json"
OUT_DIR="$(dirname "$0")/../product-videos"
mkdir -p "$OUT_DIR"

echo "🎬 Product Video Generator"
echo "=========================="
echo "Product: $SLUG"

# Step 1: Read product info
if [ -f "$PRODUCT_JSON" ]; then
    NAME=$(python3 -c "import json; print(json.load(open('$PRODUCT_JSON')).get('name','$SLUG'))")
    DESC=$(python3 -c "import json; print(json.load(open('$PRODUCT_JSON')).get('description','A software product')[:200])")
else
    NAME="$SLUG"
    DESC="A professional software automation product"
fi
echo "  Name: $NAME"

# Step 2: Generate cinematic prompt with AI
echo "🤖 Step 1/5: Generating video prompt..."
PROMPT=$(curl -s -X POST "https://api.deepseek.com/chat/completions" \
    -H "Authorization: Bearer $DEEPSEEK_KEY" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"deepseek-chat\",
        \"messages\": [
            {\"role\": \"system\", \"content\": \"You create cinematic video prompts for AI product demos. Output ONLY the prompt text, nothing else. Make it vivid and professional: dark theme UI, smooth animations, data flowing, tech aesthetic. 2-3 sentences max.\"},
            {\"role\": \"user\", \"content\": \"Create a video prompt for: $NAME - $DESC\"}
        ],
        \"max_tokens\": 200,
        \"temperature\": 0.8
    }" | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])")

echo "  Prompt: ${PROMPT:0:100}..."

# Step 3: Submit to fal.ai Veo2
echo "🎥 Step 2/5: Submitting to fal.ai Veo2..."
SUBMIT=$(curl -s -X POST "https://queue.fal.run/fal-ai/veo2" \
    -H "Authorization: Key $FAL_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": $(python3 -c "import json; print(json.dumps('$PROMPT'))"), \"duration\": \"8s\", \"aspect_ratio\": \"16:9\"}")

REQUEST_ID=$(echo "$SUBMIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['request_id'])")
RESPONSE_URL="https://queue.fal.run/fal-ai/veo2/requests/$REQUEST_ID"
echo "  Job ID: $REQUEST_ID"

# Step 4: Poll until done
echo "⏳ Step 3/5: Waiting for video generation..."
MAX_WAIT=300
ELAPSED=0
VIDEO_URL=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep 15
    ELAPSED=$((ELAPSED + 15))
    
    RESULT=$(curl -s "$RESPONSE_URL" -H "Authorization: Key $FAL_KEY")
    VIDEO_URL=$(echo "$RESULT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
v=d.get('video',{})
print(v.get('url','') if isinstance(v,dict) else (v if isinstance(v,str) else ''))
" 2>/dev/null)
    
    if [ -n "$VIDEO_URL" ]; then
        echo "  ✅ Video ready! (${ELAPSED}s)"
        break
    fi
    echo "  ... ${ELAPSED}s elapsed"
done

if [ -z "$VIDEO_URL" ]; then
    echo "❌ Video generation timed out after ${MAX_WAIT}s"
    exit 1
fi

# Step 5: Download
echo "📥 Step 4/5: Downloading video..."
curl -s -o "$OUT_DIR/$SLUG.mp4" "$VIDEO_URL"
SIZE=$(ls -lh "$OUT_DIR/$SLUG.mp4" | awk '{print $5}')
DUR=$(ffprobe "$OUT_DIR/$SLUG.mp4" 2>&1 | grep Duration | awk '{print $2}' | tr -d ',')
echo "  Saved: $OUT_DIR/$SLUG.mp4 ($SIZE, $DUR)"

# Step 6: Upload to GitHub
echo "☁️ Step 5/5: Uploading to GitHub Releases..."
# Delete existing asset if any
OLD_ASSET=$(curl -s -H "Authorization: token $GH_TOKEN" \
    "https://api.github.com/repos/$GH_REPO/releases/$RELEASE_ID/assets" | \
    python3 -c "import sys,json; [print(a['id']) for a in json.load(sys.stdin) if a['name']=='$SLUG.mp4']" 2>/dev/null)
if [ -n "$OLD_ASSET" ]; then
    curl -s -X DELETE -H "Authorization: token $GH_TOKEN" \
        "https://api.github.com/repos/$GH_REPO/releases/assets/$OLD_ASSET" > /dev/null
fi

GH_URL=$(curl -s -X POST \
    -H "Authorization: token $GH_TOKEN" \
    -H "Content-Type: video/mp4" \
    --data-binary @"$OUT_DIR/$SLUG.mp4" \
    "https://uploads.github.com/repos/$GH_REPO/releases/$RELEASE_ID/assets?name=$SLUG.mp4" | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('browser_download_url','FAILED'))")

echo "  URL: $GH_URL"

echo ""
echo "✅ DONE!"
echo "  Video: $OUT_DIR/$SLUG.mp4"
echo "  GitHub: $GH_URL"
echo "  Duration: $DUR | Size: $SIZE"
