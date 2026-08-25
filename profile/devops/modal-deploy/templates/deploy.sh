#!/usr/bin/env bash
# Smart deployment script with optional GPU availability pre-check
# Usage: ./deploy.sh [--check] [--skip-check]
#
# The pre-check (check_gpu.py) requests a minimal container with the
# configured GPU and confirms allocation within a time budget. It is
# skipped by default because high-availability GPUs (T4, A10) usually
# allocate within 1-3 minutes anyway; use --check for scarce GPUs
# (H100, B200) before committing to a full deploy.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration — use relative paths for portability
VENV_BIN=".venv/bin"
DEPLOY_CMD="$VENV_BIN/modal deploy modal_app.py"
CHECK_SCRIPT="$VENV_BIN/python check_gpu.py"

# Parse arguments
SKIP_CHECK=true  # Default: skip check
for arg in "$@"; do
    case $arg in
        --skip-check)
            SKIP_CHECK=true
            ;;
        --check)
            SKIP_CHECK=false
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: $0 [--check] [--skip-check]"
            echo "  --check       Run GPU availability pre-check before deploying"
            echo "  --skip-check  Skip GPU availability check (default)"
            exit 1
            ;;
    esac
done

# Read a value from config.py, stripping inline comments, quotes, and whitespace
config_value() {
    grep "^$1[[:space:]]*=" config.py | cut -d'=' -f2- | sed -E 's/[[:space:]]*#.*$//' | tr -d '"' | tr -d "'" | xargs
}

echo "============================================================"
echo "🚀 Smart Deployment"
echo "============================================================"
echo ""

# Step 1: Check configuration
echo "📋 Step 1: Checking configuration..."
if [ ! -f "config.py" ]; then
    echo -e "${RED}❌ config.py file not found${NC}"
    exit 1
fi

GPU_MODEL=$(config_value GPU_MODEL)
CPU=$(config_value CPU)
MEMORY=$(config_value MEMORY)

echo "   GPU Model: ${GPU_MODEL:-none}"
echo "   CPU: ${CPU:-default} cores"
echo "   Memory: ${MEMORY:-default} MB"
echo ""

# Step 2: GPU pre-check (optional)
if [ "$SKIP_CHECK" = true ]; then
    echo -e "${YELLOW}⏭  Skipping GPU availability check (default; use --check to enable)${NC}"
    echo "   If GPU allocation stalls after deploy, check:"
    echo "     .venv/bin/modal app list"
    echo "     .venv/bin/modal app logs <app-name>"
    echo ""
else
    echo "🔍 Step 2: Checking GPU availability..."
    echo ""

    if $CHECK_SCRIPT; then
        echo ""
        echo -e "${GREEN}✅ GPU available${NC}"
    else
        echo ""
        echo -e "${RED}❌ GPU pre-check failed — see alternatives above${NC}"
        echo "   Update MODAL_GPU_MODEL in .env, or deploy anyway with:"
        echo "     ./deploy.sh --skip-check"
        exit 1
    fi
    echo ""
fi

# Step 3: Deploy
echo "📦 Step 3: Deploying to Modal..."
echo ""

if $DEPLOY_CMD; then
    echo ""
    echo "============================================================"
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Check status: .venv/bin/modal app list"
    echo "  2. View logs: .venv/bin/modal app logs <app-name>"
    echo "  3. Access the app at the URL provided above"
else
    echo ""
    echo "============================================================"
    echo -e "${RED}❌ Deployment failed${NC}"
    echo "============================================================"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: .venv/bin/modal app logs <app-name>"
    echo "  2. Verify config.py configuration"
    echo "  3. Try a different GPU model"
    exit 1
fi
