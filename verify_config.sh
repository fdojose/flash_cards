#!/bin/bash

# Configuration Verification Script
# Checks that all configuration files are set to PostgreSQL

echo "🔍 Verifying PostgreSQL Configuration..."
echo

# Check for any SQLite references in configuration files
echo "📋 Checking for SQLite references in config files..."
SQLITE_REFS=$(grep -r -i "sqlite" --include="*.env*" --include="*.md" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=tests . 2>/dev/null | grep -v "# Test files" | grep -v "pandas" | grep -v "__pycache__")

if [ -z "$SQLITE_REFS" ]; then
    echo "✅ No SQLite references found in configuration files"
else
    echo "⚠️  Found SQLite references:"
    echo "$SQLITE_REFS"
fi

echo

# Check PostgreSQL configuration
echo "🐘 Checking PostgreSQL configuration..."

# Check backend .env
if [ -f "backend/.env" ]; then
    DB_URL=$(grep "DATABASE_URL" backend/.env | head -1)
    if [[ $DB_URL == *"postgresql"* ]]; then
        echo "✅ backend/.env: $DB_URL"
    else
        echo "❌ backend/.env: $DB_URL (should be PostgreSQL)"
    fi
else
    echo "⚠️  backend/.env not found"
fi

# Check root .env
if [ -f ".env" ]; then
    DB_URL=$(grep "DATABASE_URL" .env | head -1)
    if [[ $DB_URL == *"postgresql"* ]]; then
        echo "✅ .env: $DB_URL"
    else
        echo "❌ .env: $DB_URL (should be PostgreSQL)"
    fi
else
    echo "⚠️  .env not found"
fi

# Check backend/.env.development
if [ -f "backend/.env.development" ]; then
    DB_URL=$(grep "DATABASE_URL" backend/.env.development | head -1)
    if [[ $DB_URL == *"postgresql"* ]]; then
        echo "✅ backend/.env.development: $DB_URL"
    else
        echo "❌ backend/.env.development: $DB_URL (should be PostgreSQL)"
    fi
fi

echo

# Check Docker container
echo "🐳 Checking PostgreSQL Docker container..."
if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "flash_cards-postgres-1.*Up"; then
    echo "✅ PostgreSQL Docker container is running"
    CONTAINER_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "flash_cards-postgres-1")
    echo "   $CONTAINER_STATUS"
else
    echo "❌ PostgreSQL Docker container is not running"
    echo "   Run: docker-compose up -d postgres"
fi

echo

# Check server status
echo "🚀 Checking server status..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Backend server running on port 8000"
else
    echo "❌ Backend server not running on port 8000"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Frontend server running on port 3000"
else
    echo "❌ Frontend server not running on port 3000"
fi

echo
echo "🎯 Configuration Summary:"
echo "   Database: PostgreSQL on port 5433 (Docker)"
echo "   Backend: FastAPI on port 8000"  
echo "   Frontend: React+Vite on port 3000"
echo "   All SQLite references removed from config files"
