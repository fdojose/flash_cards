#!/bin/bash
# Quick server restart script
cd /Users/maccasa/Dropbox/TDCLA/Combos/NotebooksPython/course_creator/flash_cards

echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "🗄️  Checking database (port 5433)..."
if ! pg_isready -h localhost -p 5433 > /dev/null 2>&1; then
    echo "⚠️  Postgres not reachable — starting Docker containers..."
    docker compose up -d
    echo "⏳ Waiting for Postgres to be ready..."
    for i in {1..15}; do
        pg_isready -h localhost -p 5433 > /dev/null 2>&1 && break
        sleep 1
    done
    if ! pg_isready -h localhost -p 5433 > /dev/null 2>&1; then
        echo "❌ Postgres still not ready. Check Docker logs: docker compose logs"
        exit 1
    fi
fi
echo "✅ Database is ready"

echo "🛑 Stopping all services..."
pkill -f "uvicorn.*main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true

echo "⏳ Waiting for services to stop..."
sleep 3

echo "🚀 Starting backend..."
nohup bash -c "source venv/bin/activate && cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000" > backend.log 2>&1 &

echo "⏳ Waiting for backend to start..."
sleep 5

echo "⚛️  Starting frontend..."
cd frontend
nohup npx vite --port 3000 --host 0.0.0.0 > ../frontend.log 2>&1 &

echo "⏳ Waiting for frontend to start..."
sleep 5

echo "✅ Services restarted!"
echo "🌐 Frontend: http://localhost:3000"
echo "📊 Backend: http://localhost:8000"
echo "📋 API Docs: http://localhost:8000/docs"
