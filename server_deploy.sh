#!/bin/bash
# =============================================================================
# SERVER-SIDE deploy script — runs ON the server via SSH
# Do not run this locally. Use ./deploy.sh instead.
# =============================================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /root/flashcard

echo -e "${YELLOW}[1/4] Pulling latest code from GitHub (dev)...${NC}"
git fetch origin dev
git reset --hard origin/dev

echo -e "${YELLOW}[2/4] Running database migrations...${NC}"
docker exec flashcard_backend alembic upgrade heads

echo -e "${YELLOW}[3/4] Restarting backend...${NC}"
docker restart flashcard_backend

echo -e "${YELLOW}[4/4] Restarting frontend...${NC}"
docker restart flashcard_frontend

echo ""
echo -e "${GREEN}✅ Deployment complete! https://flashcards.tdcla.com${NC}"
