#!/bin/bash

# =============================================================================
# Database Reset & Repopulation Script for Flashcard Learning System
# =============================================================================
# This script completely resets the database and repopulates it with fresh data
# WARNING: This will DELETE ALL existing data!
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  DATABASE RESET & REPOPULATION SCRIPT ⚠️${NC}"
echo -e "${RED}=================================================================================${NC}"
echo -e "${RED}WARNING: This will PERMANENTLY DELETE all existing database data!${NC}"
echo -e "${RED}=================================================================================${NC}"
echo ""

# Confirmation prompt
read -p "Are you sure you want to reset the database? Type 'YES' to confirm: " confirm
if [ "$confirm" != "YES" ]; then
    echo -e "${YELLOW}❌ Operation cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🔥 Starting complete database reset...${NC}"

# Step 1: Stop all services
echo -e "${YELLOW}🛑 Stopping all services...${NC}"
docker-compose down

# Step 2: Remove database data directory
echo -e "${YELLOW}🗑️  Removing database data directory...${NC}"
if [ -d "postgres_data" ]; then
    sudo rm -rf postgres_data
    echo -e "${GREEN}✅ Database data directory removed${NC}"
else
    echo -e "${BLUE}ℹ️  Database data directory does not exist${NC}"
fi

# Step 3: Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose up -d

# Step 4: Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Check if containers are running
if ! docker ps --format "table {{.Names}}" | grep -q "flashcard_postgres"; then
    echo -e "${RED}❌ PostgreSQL container failed to start${NC}"
    exit 1
fi

if ! docker ps --format "table {{.Names}}" | grep -q "flashcard_backend"; then
    echo -e "${RED}❌ Backend container failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Services are running${NC}"

# Step 5: Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
retries=30
while [ $retries -gt 0 ]; do
    if docker exec flashcard_postgres pg_isready -U flashcard_user -d flashcard_db > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database is ready${NC}"
        break
    fi
    retries=$((retries - 1))
    sleep 2
    echo -n "."
done

if [ $retries -eq 0 ]; then
    echo -e "${RED}❌ Database failed to become ready${NC}"
    exit 1
fi

# Step 6: Run the repopulation script
echo -e "${YELLOW}🔄 Running repopulation script...${NC}"
./repopulate_db.sh

echo ""
echo -e "${GREEN}🎉 Database reset and repopulation completed successfully!${NC}"
echo -e "${BLUE}=================================================================================${NC}"
echo -e "${BLUE}Your flashcard system is ready with:${NC}"
echo -e "   🌐 Frontend: http://localhost:5173"
echo -e "   🔧 Backend API: http://localhost:8000"
echo -e "   👤 Admin Panel: http://localhost:3000/admin"
echo -e "   📧 Admin Email: admin@flashcards.com"
echo -e "   🔐 Admin Password: admin123"
echo -e "   📊 17 System Configurations Available"
echo -e "${BLUE}=================================================================================${NC}"
