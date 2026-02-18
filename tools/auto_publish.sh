#!/bin/bash
# =============================================================================
# AUTO-PUBLISH: Complete product pipeline
# =============================================================================
# Takes a product from raw code to listed-on-marketplace in one command.
#
# Usage:
#   ./auto_publish.sh <product-directory> [--dry-run] [--skip-stripe] [--skip-github]
#
# What it does:
#   1. Validates product.json exists with required fields
#   2. Ensures all required files (README, .env.example, setup.sh, LICENSE)
#   3. Generates professional HTML guide (docs/guide.html)
#   4. Packages into .tar.gz
#   5. Uploads to GitHub Releases
#   6. Creates Stripe product + price
#   7. Lists on marketplace (mywork-ai-production.up.railway.app)
#   8. Updates package_url in marketplace DB
#
# Requirements:
#   - product.json in the product directory
#   - Python 3 with requests module
#   - GitHub token, Stripe keys, Clerk credentials in ~/.openclaw/workspace/
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PRODUCT_DIR="${1:?Usage: $0 <product-directory> [--dry-run] [--skip-stripe] [--skip-github]}"
PRODUCT_DIR=$(realpath "$PRODUCT_DIR")
PRODUCT_SLUG=$(basename "$PRODUCT_DIR")
TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$TOOLS_DIR")"
ZIPS_DIR="$BASE_DIR/zips"
CREDS_DIR="/home/Memo1981/.openclaw/workspace"

# Flags
DRY_RUN=false
SKIP_STRIPE=false
SKIP_GITHUB=false
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --skip-stripe) SKIP_STRIPE=true ;;
        --skip-github) SKIP_GITHUB=true ;;
    esac
done

# Load credentials
GH_TOKEN=$(cat "$CREDS_DIR/.credentials-dan.json" 2>/dev/null | python3 -c "import sys; print([l.split(': ')[1].strip().strip('\"') for l in sys.stdin if 'ghp_' in l][0])" 2>/dev/null || echo "")
if [ -z "$GH_TOKEN" ]; then
    echo "❌ GitHub token not found. Set GH_TOKEN or add to .credentials-dan.json"
    exit 1
fi

STRIPE_SECRET=$(python3 -c "
import json
with open('$CREDS_DIR/.credentials-stripe.json') as f:
    d = json.load(f)
# Use test key if available, otherwise live
print(d.get('stripe_test_secret', d.get('stripe_secret_key', '')))
" 2>/dev/null || echo "")

CLERK_SECRET="${CLERK_SECRET:-}"
MARKETPLACE_URL="https://mywork-ai-production.up.railway.app"
GH_REPO="DansiDanutz/MyWork-AI"
GH_RELEASE_TAG="v2.6.0-products"

# ─── Logging ───
log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
ok()  { echo -e "  ${GREEN}✅ $1${NC}"; }
err() { echo -e "  ${RED}❌ $1${NC}"; }
warn(){ echo -e "  ${YELLOW}⚠️  $1${NC}"; }

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  📦 AUTO-PUBLISH: $PRODUCT_SLUG${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""
$DRY_RUN && warn "DRY RUN MODE — no changes will be made"
echo ""

# ═══════════════════════════════════════════════════
# STEP 1: Validate product.json
# ═══════════════════════════════════════════════════
log "Step 1/8: Validating product.json..."

if [ ! -f "$PRODUCT_DIR/product.json" ]; then
    err "product.json not found! Create one with: name, description, price, category, tags"
    exit 1
fi

# Parse product.json
PRODUCT_NAME=$(python3 -c "import json; print(json.load(open('$PRODUCT_DIR/product.json'))['name'])")
PRODUCT_DESC=$(python3 -c "import json; print(json.load(open('$PRODUCT_DIR/product.json'))['description'])")
PRODUCT_PRICE=$(python3 -c "import json; print(json.load(open('$PRODUCT_DIR/product.json'))['price'])")
PRODUCT_CATEGORY=$(python3 -c "import json; print(json.load(open('$PRODUCT_DIR/product.json')).get('category','automation'))")
PRODUCT_TAGS=$(python3 -c "import json; print(','.join(json.load(open('$PRODUCT_DIR/product.json')).get('tags',[])))")
PRODUCT_VERSION=$(python3 -c "import json; print(json.load(open('$PRODUCT_DIR/product.json')).get('version','1.0.0'))")

ok "Product: $PRODUCT_NAME"
ok "Price: \$$PRODUCT_PRICE"
ok "Category: $PRODUCT_CATEGORY"

# ═══════════════════════════════════════════════════
# STEP 2: Ensure required files
# ═══════════════════════════════════════════════════
log "Step 2/8: Checking required files..."

MISSING=0

# README.md
if [ ! -f "$PRODUCT_DIR/README.md" ]; then
    warn "README.md missing — generating from template..."
    sed "s/{{PRODUCT_NAME}}/$PRODUCT_NAME/g; s/{{SLUG}}/$PRODUCT_SLUG/g; s/{{TAGLINE}}/$PRODUCT_DESC/g" \
        "$TOOLS_DIR/product_template/README.md" > "$PRODUCT_DIR/README.md"
    ok "README.md generated"
else
    ok "README.md exists"
fi

# .env.example
if [ ! -f "$PRODUCT_DIR/.env.example" ]; then
    warn ".env.example missing — generating from template..."
    sed "s/{{PRODUCT_NAME}}/$PRODUCT_NAME/g" \
        "$TOOLS_DIR/product_template/.env.example" > "$PRODUCT_DIR/.env.example"
    ok ".env.example generated"
else
    ok ".env.example exists"
fi

# setup.sh
if [ ! -f "$PRODUCT_DIR/setup.sh" ]; then
    warn "setup.sh missing — generating from template..."
    sed "s/{{PRODUCT_NAME}}/$PRODUCT_NAME/g" \
        "$TOOLS_DIR/product_template/setup.sh" > "$PRODUCT_DIR/setup.sh"
    chmod +x "$PRODUCT_DIR/setup.sh"
    ok "setup.sh generated"
else
    chmod +x "$PRODUCT_DIR/setup.sh"
    ok "setup.sh exists"
fi

# LICENSE
if [ ! -f "$PRODUCT_DIR/LICENSE" ]; then
    cp "$TOOLS_DIR/product_template/LICENSE" "$PRODUCT_DIR/LICENSE"
    ok "LICENSE added"
else
    ok "LICENSE exists"
fi

# Dockerfile
if [ ! -f "$PRODUCT_DIR/Dockerfile" ]; then
    cp "$TOOLS_DIR/product_template/Dockerfile" "$PRODUCT_DIR/Dockerfile"
    ok "Dockerfile added from template"
else
    ok "Dockerfile exists"
fi

# requirements.txt (check root and backend/)
if [ ! -f "$PRODUCT_DIR/requirements.txt" ]; then
    if [ -f "$PRODUCT_DIR/backend/requirements.txt" ]; then
        cp "$PRODUCT_DIR/backend/requirements.txt" "$PRODUCT_DIR/requirements.txt"
        ok "requirements.txt copied from backend/"
    else
        cp "$TOOLS_DIR/product_template/requirements.txt" "$PRODUCT_DIR/requirements.txt"
        warn "requirements.txt generated from template — review dependencies!"
    fi
else
    ok "requirements.txt exists"
fi

# ═══════════════════════════════════════════════════
# STEP 3: Generate HTML guide
# ═══════════════════════════════════════════════════
log "Step 3/8: Generating professional HTML guide..."

mkdir -p "$PRODUCT_DIR/docs"

python3 "$TOOLS_DIR/generate_single_guide.py" "$PRODUCT_DIR" 2>/dev/null
if [ $? -eq 0 ] && [ -f "$PRODUCT_DIR/docs/guide.html" ]; then
    GUIDE_SIZE=$(du -h "$PRODUCT_DIR/docs/guide.html" | cut -f1)
    ok "docs/guide.html generated ($GUIDE_SIZE)"
else
    warn "Guide generation failed — using fallback"
    # Fallback: create minimal guide
    cat > "$PRODUCT_DIR/docs/guide.html" << HTMLEOF
<!DOCTYPE html>
<html><head><title>$PRODUCT_NAME — Guide</title>
<style>body{font-family:system-ui;max-width:800px;margin:40px auto;padding:20px;line-height:1.6}
h1{color:#667eea}pre{background:#1a1a2e;color:#e8ecf1;padding:15px;border-radius:8px;overflow-x:auto}
code{background:#f0f2f5;padding:2px 6px;border-radius:4px}.step{background:#f8f9ff;border:1px solid #e0e4ff;padding:20px;border-radius:10px;margin:15px 0}</style></head>
<body>
<h1>$PRODUCT_NAME</h1>
<p>$PRODUCT_DESC</p>
<h2>Quick Start</h2>
<div class="step"><h3>1. Extract & Configure</h3>
<pre><code>tar -xzf $PRODUCT_SLUG.tar.gz && cd $PRODUCT_SLUG
cp .env.example .env && nano .env</code></pre></div>
<div class="step"><h3>2. Setup & Run</h3>
<pre><code>./setup.sh</code></pre></div>
<div class="step"><h3>3. Verify</h3>
<pre><code>curl http://localhost:8000/docs</code></pre></div>
<p>© 2026 MyWork-AI</p>
</body></html>
HTMLEOF
    ok "Fallback guide created"
fi

# ═══════════════════════════════════════════════════
# STEP 4: Package into .tar.gz
# ═══════════════════════════════════════════════════
log "Step 4/8: Packaging..."

# Clean up
find "$PRODUCT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PRODUCT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PRODUCT_DIR" -type f -name ".DS_Store" -delete 2>/dev/null || true

mkdir -p "$ZIPS_DIR"
OUTPUT_FILE="$ZIPS_DIR/$PRODUCT_SLUG.tar.gz"

tar -czf "$OUTPUT_FILE" \
    -C "$(dirname "$PRODUCT_DIR")" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='node_modules' \
    --exclude='.env' \
    "$PRODUCT_SLUG"

SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
FILE_COUNT=$(tar -tzf "$OUTPUT_FILE" | wc -l)
ok "Packaged: $OUTPUT_FILE ($SIZE, $FILE_COUNT files)"

if $DRY_RUN; then
    log "DRY RUN — stopping before upload/listing"
    echo ""
    echo -e "${GREEN}✅ Package ready at: $OUTPUT_FILE${NC}"
    echo "   Run without --dry-run to upload and list."
    exit 0
fi

# ═══════════════════════════════════════════════════
# STEP 5: Upload to GitHub Releases
# ═══════════════════════════════════════════════════
log "Step 5/8: Uploading to GitHub Releases..."

if $SKIP_GITHUB; then
    warn "Skipped (--skip-github)"
else
    # Get release ID
    RELEASE_ID=$(curl -s -H "Authorization: token $GH_TOKEN" \
        "https://api.github.com/repos/$GH_REPO/releases/tags/$GH_RELEASE_TAG" \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)

    if [ -z "$RELEASE_ID" ]; then
        err "Release $GH_RELEASE_TAG not found"
    else
        # Delete existing asset with same name (if exists)
        EXISTING_ASSET=$(curl -s -H "Authorization: token $GH_TOKEN" \
            "https://api.github.com/repos/$GH_REPO/releases/$RELEASE_ID/assets" \
            | python3 -c "
import sys,json
for a in json.load(sys.stdin):
    if a['name'] == '$PRODUCT_SLUG.tar.gz':
        print(a['id'])
        break
" 2>/dev/null)

        if [ -n "$EXISTING_ASSET" ]; then
            curl -s -X DELETE -H "Authorization: token $GH_TOKEN" \
                "https://api.github.com/repos/$GH_REPO/releases/assets/$EXISTING_ASSET" >/dev/null
            ok "Deleted old asset"
        fi

        # Upload new asset
        UPLOAD_RESULT=$(curl -s -X POST \
            -H "Authorization: token $GH_TOKEN" \
            -H "Content-Type: application/gzip" \
            --data-binary "@$OUTPUT_FILE" \
            "https://uploads.github.com/repos/$GH_REPO/releases/$RELEASE_ID/assets?name=$PRODUCT_SLUG.tar.gz")

        DOWNLOAD_URL=$(echo "$UPLOAD_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('browser_download_url',''))" 2>/dev/null)

        if [ -n "$DOWNLOAD_URL" ]; then
            ok "Uploaded: $DOWNLOAD_URL"
        else
            err "Upload failed"
            echo "$UPLOAD_RESULT" | head -5
        fi
    fi
fi

# ═══════════════════════════════════════════════════
# STEP 6: Create Stripe product + price
# ═══════════════════════════════════════════════════
log "Step 6/8: Creating Stripe product..."

if $SKIP_STRIPE; then
    warn "Skipped (--skip-stripe)"
    STRIPE_PRODUCT_ID=""
    STRIPE_PRICE_ID=""
else
    if [ -z "$STRIPE_SECRET" ]; then
        err "No Stripe key found"
        STRIPE_PRODUCT_ID=""
        STRIPE_PRICE_ID=""
    else
        # Convert price to cents
        PRICE_CENTS=$(python3 -c "print(int(float('$PRODUCT_PRICE') * 100))")

        # Create Stripe product
        STRIPE_RESULT=$(curl -s -X POST "https://api.stripe.com/v1/products" \
            -u "$STRIPE_SECRET:" \
            -d "name=$PRODUCT_NAME" \
            -d "description=$PRODUCT_DESC" \
            -d "metadata[slug]=$PRODUCT_SLUG" \
            -d "metadata[version]=$PRODUCT_VERSION")

        STRIPE_PRODUCT_ID=$(echo "$STRIPE_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)

        if [ -n "$STRIPE_PRODUCT_ID" ]; then
            ok "Stripe product: $STRIPE_PRODUCT_ID"

            # Create price
            PRICE_RESULT=$(curl -s -X POST "https://api.stripe.com/v1/prices" \
                -u "$STRIPE_SECRET:" \
                -d "product=$STRIPE_PRODUCT_ID" \
                -d "unit_amount=$PRICE_CENTS" \
                -d "currency=usd")

            STRIPE_PRICE_ID=$(echo "$PRICE_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
            ok "Stripe price: $STRIPE_PRICE_ID ($PRODUCT_PRICE USD)"
        else
            err "Stripe product creation failed"
            echo "$STRIPE_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','unknown'))" 2>/dev/null
        fi
    fi
fi

# ═══════════════════════════════════════════════════
# STEP 7: List on marketplace
# ═══════════════════════════════════════════════════
log "Step 7/8: Listing on marketplace..."

# Get Clerk JWT token
CLERK_USER_ID="user_38idO1ldVPAqp64F2jpfL9By7Kc"

# Build tags/tech arrays
TAGS_JSON=$(python3 -c "import json; print(json.dumps(json.load(open('$PRODUCT_DIR/product.json')).get('tags',[])))")

# Detect tech stack from requirements
TECH_JSON=$(python3 -c "
import os, json
tech = []
req_path = '$PRODUCT_DIR/requirements.txt'
if os.path.exists(req_path):
    content = open(req_path).read().lower()
    if 'fastapi' in content: tech.append('FastAPI')
    if 'openai' in content: tech.append('OpenAI')
    if 'flask' in content: tech.append('Flask')
    if 'redis' in content: tech.append('Redis')
    if 'sqlalchemy' in content: tech.append('SQLAlchemy')
    tech.insert(0, 'Python')
if os.path.exists('$PRODUCT_DIR/Dockerfile'): tech.append('Docker')
if not tech: tech = ['Python', 'Docker']
print(json.dumps(tech))
")

MARKETPLACE_RESULT=$(python3 << PYEOF
import requests, json, sys

# Step 0: Check if product already exists (prevent duplicates)
existing = requests.get("$MARKETPLACE_URL/api/products").json()
for p in existing.get("products", []):
    if p["title"].lower().strip() == "$PRODUCT_NAME".lower().strip():
        print(f"EXISTS:{p['id']}")
        sys.exit(0)

# Step 1: Create Clerk session
session_r = requests.post("https://api.clerk.com/v1/sessions",
    headers={"Authorization": "Bearer $CLERK_SECRET", "Content-Type": "application/json"},
    json={"user_id": "$CLERK_USER_ID"})

if session_r.status_code != 200:
    print(f"ERROR:clerk_session:{session_r.text[:200]}")
    sys.exit(0)

session_id = session_r.json()["id"]

# Step 2: Get JWT from session
token_r = requests.post(f"https://api.clerk.com/v1/sessions/{session_id}/tokens",
    headers={"Authorization": "Bearer $CLERK_SECRET", "Content-Type": "application/json"})

if token_r.status_code != 200:
    print(f"ERROR:clerk_token:{token_r.text[:200]}")
    sys.exit(0)

jwt_token = token_r.json()["jwt"]

# Step 3: Create product
desc = json.load(open("$PRODUCT_DIR/product.json"))["description"]
product_data = {
    "title": "$PRODUCT_NAME",
    "description": desc,
    "short_description": "$PRODUCT_NAME — $PRODUCT_CATEGORY",
    "category": "$PRODUCT_CATEGORY",
    "tags": $TAGS_JSON,
    "price": float("$PRODUCT_PRICE"),
    "license_type": "mit",
    "tech_stack": $TECH_JSON,
    "version": "$PRODUCT_VERSION",
    "package_url": "${DOWNLOAD_URL:-}",
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {jwt_token}",
}

r = requests.post("$MARKETPLACE_URL/api/products", json=product_data, headers=headers)

if r.status_code in (200, 201):
    result = r.json()
    product_id = result.get("id", "")
    print(f"OK:{product_id}")
    
    # Publish it
    if product_id:
        # Need fresh token (Clerk JWTs are short-lived)
        token_r2 = requests.post(f"https://api.clerk.com/v1/sessions/{session_id}/tokens",
            headers={"Authorization": "Bearer $CLERK_SECRET", "Content-Type": "application/json"})
        jwt2 = token_r2.json()["jwt"]
        headers["Authorization"] = f"Bearer {jwt2}"
        
        r2 = requests.post(f"$MARKETPLACE_URL/api/products/{product_id}/publish", headers=headers)
        if r2.status_code in (200, 201):
            print(f"PUBLISHED:{product_id}")
        else:
            print(f"PUBLISH_FAIL:{r2.status_code}")
else:
    print(f"ERROR:{r.status_code}:{r.text[:200]}")
PYEOF
)

if echo "$MARKETPLACE_RESULT" | grep -q "^EXISTS:"; then
    MARKETPLACE_ID=$(echo "$MARKETPLACE_RESULT" | grep "^EXISTS:" | cut -d: -f2)
    ok "Already listed on marketplace: ID $MARKETPLACE_ID (skipped to prevent duplicate)"
elif echo "$MARKETPLACE_RESULT" | grep -q "^OK:"; then
    MARKETPLACE_ID=$(echo "$MARKETPLACE_RESULT" | grep "^OK:" | cut -d: -f2)
    ok "Listed on marketplace: ID $MARKETPLACE_ID"
    
    if echo "$MARKETPLACE_RESULT" | grep -q "^PUBLISHED:"; then
        ok "Published and visible!"
    fi
else
    warn "Marketplace listing issue: $MARKETPLACE_RESULT"
    warn "Product may need manual listing or auth token refresh"
fi

# ═══════════════════════════════════════════════════
# STEP 8: Summary
# ═══════════════════════════════════════════════════
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅ AUTO-PUBLISH COMPLETE: $PRODUCT_NAME${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  📦 Package: $OUTPUT_FILE ($SIZE)"
echo "  🔗 GitHub:  ${DOWNLOAD_URL:-N/A}"
echo "  💳 Stripe:  ${STRIPE_PRODUCT_ID:-N/A} / ${STRIPE_PRICE_ID:-N/A}"
echo "  🏪 Market:  ${MARKETPLACE_ID:-N/A}"
echo ""
echo "  Price: \$$PRODUCT_PRICE"
echo "  Files: $FILE_COUNT"
echo ""

# Save publish record
cat > "$PRODUCT_DIR/.publish-record.json" << RECEOF
{
    "slug": "$PRODUCT_SLUG",
    "name": "$PRODUCT_NAME",
    "price": $PRODUCT_PRICE,
    "published_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "package_file": "$OUTPUT_FILE",
    "github_url": "${DOWNLOAD_URL:-null}",
    "stripe_product_id": "${STRIPE_PRODUCT_ID:-null}",
    "stripe_price_id": "${STRIPE_PRICE_ID:-null}",
    "marketplace_id": "${MARKETPLACE_ID:-null}"
}
RECEOF
ok "Publish record saved to .publish-record.json"

# ── Step 9: Generate Product Video ──────────────────────
echo ""
echo "🎬 Step 9: Generating product demo video..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/generate_video.sh" ]; then
    bash "$SCRIPT_DIR/generate_video.sh" "$PRODUCT_DIR" && ok "Product video generated and uploaded" || echo "⚠️  Video generation failed (non-fatal, continuing)"
else
    echo "⚠️  generate_video.sh not found, skipping video generation"
fi
