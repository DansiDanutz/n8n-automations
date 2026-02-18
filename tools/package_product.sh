#!/bin/bash

# Product Packaging Script
# Validates and packages a product for distribution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if product directory is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No product directory specified${NC}"
    echo "Usage: $0 <product-directory>"
    echo "Example: $0 ./ai-customer-support-bot"
    exit 1
fi

PRODUCT_DIR="$1"
PRODUCT_NAME=$(basename "$PRODUCT_DIR")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Product Packaging Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Product: $PRODUCT_NAME"
echo "Directory: $PRODUCT_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Validate product directory exists
if [ ! -d "$PRODUCT_DIR" ]; then
    echo -e "${RED}Error: Product directory does not exist: $PRODUCT_DIR${NC}"
    exit 1
fi

# Check required files
echo -e "${YELLOW}Checking required files...${NC}"

REQUIRED_FILES=(
    "README.md"
    "GUIDE.md"
    ".env.example"
    "setup.sh"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$PRODUCT_DIR/$file" ]; then
        MISSING_FILES+=("$file")
        echo -e "  ${RED}✗ Missing: $file${NC}"
    else
        echo -e "  ${GREEN}✓ Found: $file${NC}"
    fi
done

# Check docs directory
if [ ! -d "$PRODUCT_DIR/docs" ]; then
    echo -e "  ${RED}✗ Missing: docs/ directory${NC}"
    MISSING_FILES+=("docs/")
else
    echo -e "  ${GREEN}✓ Found: docs/ directory${NC}"

    # Check docs contents
    if [ ! -f "$PRODUCT_DIR/docs/GUIDE.md" ]; then
        echo -e "    ${RED}✗ Missing: docs/GUIDE.md${NC}"
        MISSING_FILES+=("docs/GUIDE.md")
    else
        echo -e "    ${GREEN}✓ Found: docs/GUIDE.md${NC}"
    fi

    if [ ! -f "$PRODUCT_DIR/docs/guide.html" ]; then
        echo -e "    ${RED}✗ Missing: docs/guide.html${NC}"
        MISSING_FILES+=("docs/guide.html")
    else
        echo -e "    ${GREEN}✓ Found: docs/guide.html${NC}"
    fi
fi

# Check LICENSE (MIT)
if [ ! -f "$PRODUCT_DIR/LICENSE" ]; then
    echo -e "  ${RED}✗ Missing: LICENSE${NC}"
    MISSING_FILES+=("LICENSE")
else
    echo -e "  ${GREEN}✓ Found: LICENSE${NC}"
fi

# Check dependencies file
if [ -f "$PRODUCT_DIR/package.json" ]; then
    echo -e "  ${GREEN}✓ Found: package.json${NC}"
elif [ -f "$PRODUCT_DIR/requirements.txt" ]; then
    echo -e "  ${GREEN}✓ Found: requirements.txt${NC}"
else
    echo -e "  ${YELLOW}⚠ Warning: Neither package.json nor requirements.txt found${NC}"
fi

# Check for Dockerfile (optional but recommended)
if [ -f "$PRODUCT_DIR/Dockerfile" ]; then
    echo -e "  ${GREEN}✓ Found: Dockerfile${NC}"
else
    echo -e "  ${YELLOW}⚠ Note: No Dockerfile found (optional)${NC}"
fi

# Check for docker-compose.yml (optional)
if [ -f "$PRODUCT_DIR/docker-compose.yml" ]; then
    echo -e "  ${GREEN}✓ Found: docker-compose.yml${NC}"
else
    echo -e "  ${YELLOW}⚠ Note: No docker-compose.yml found (optional)${NC}"
fi

echo ""

# Report results
if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}VALIDATION FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${RED}Missing files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo -e "  - $file"
    done
    echo ""
    echo "Please add the missing files and try again."
    exit 1
else
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}VALIDATION PASSED${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
fi

# Create package
echo -e "${YELLOW}Creating package...${NC}"

ZIP_FILE="/home/Memo1981/n8n-automations/zips/${PRODUCT_NAME}_${TIMESTAMP}.tar.gz"

# Create tarball (exclude .git, __pycache__, venv, node_modules)
tar -czf "$ZIP_FILE" \
    -C "$(dirname "$PRODUCT_DIR")" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='dist' \
    --exclude='build' \
    "$(basename "$PRODUCT_DIR")"

echo -e "${GREEN}✓ Package created: $ZIP_FILE${NC}"
echo ""

# Get file size
FILE_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "Package size: $FILE_SIZE"

# Update PACKAGING_LOG
LOG_FILE="/home/Memo1981/n8n-automations/PACKAGING_LOG.md"
if [ -f "$LOG_FILE" ]; then
    echo "" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"
    echo "**[$TIMESTAMP]** Packaged $PRODUCT_NAME → ${ZIP_FILE##*/} ($FILE_SIZE)" >> "$LOG_FILE"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PACKAGING COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Package: $ZIP_FILE"
echo "Size: $FILE_SIZE"
echo ""
echo "To extract:"
echo "  tar -xzf $ZIP_FILE"
echo ""
