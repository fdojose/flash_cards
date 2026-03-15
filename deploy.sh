#!/bin/bash
# =============================================================================
# Local deploy script — pushes to GitHub then triggers server deployment
# Usage: ./deploy.sh
# =============================================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

KEY="/Users/maccasa/Downloads/mysql1 2.key"
SERVER="root@134.209.249.242"
BRANCH="dev"

echo -e "${YELLOW}[1/2] Pushing $BRANCH to GitHub...${NC}"
git push origin "$BRANCH"

echo -e "${YELLOW}[2/2] Triggering server deployment...${NC}"
ssh -i "$KEY" "$SERVER" "/root/flashcard/deploy.sh"
