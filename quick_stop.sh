#!/bin/bash
# Quick server stop script
cd /Users/maccasa/Dropbox/TDCLA/Combos/NotebooksPython/course_creator/flash_cards

echo "🛑 Stopping all services..."

# Stop backend processes (uvicorn)
echo "  📊 Stopping backend (uvicorn)..."
pkill -f "uvicorn.*main" 2>/dev/null || true

# Stop frontend processes (vite/npm dev)
echo "  ⚛️  Stopping frontend (vite/npm)..."
pkill -f "vite" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true

echo "⏳ Waiting for services to stop..."
sleep 3

# Check if processes are still running
backend_running=$(pgrep -f "uvicorn.*main" | wc -l)
frontend_running=$(pgrep -f "vite\|npm.*dev" | wc -l)

if [ $backend_running -eq 0 ] && [ $frontend_running -eq 0 ]; then
    echo "✅ All services stopped successfully!"
else
    echo "⚠️  Some processes may still be running:"
    if [ $backend_running -gt 0 ]; then
        echo "  - Backend processes still running: $backend_running"
        echo "  - Try: pkill -9 -f \"uvicorn.*main\""
    fi
    if [ $frontend_running -gt 0 ]; then
        echo "  - Frontend processes still running: $frontend_running"
        echo "  - Try: pkill -9 -f \"vite\""
    fi
    echo "  - Or use: pkill -9 -f \"uvicorn\|vite\|npm.*dev\""
fi

echo "🏁 Stop script completed."
