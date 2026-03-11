#!/bin/bash

# Flashcard Learning System - Server Control Script
# Usage: ./server_control.sh [start|stop|restart|status]

PROJECT_DIR="/Users/maccasa/Dropbox/TDCLA/Combos/NotebooksPython/course_creator/flash_cards"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_PATH="$PROJECT_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if a process is running on a port
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service_name=$2
    
    if check_port $port; then
        log "Stopping $service_name on port $port..."
        local pids=$(lsof -ti:$port)
        if [ ! -z "$pids" ]; then
            echo $pids | xargs kill -9
            sleep 2
            if check_port $port; then
                error "Failed to stop $service_name on port $port"
                return 1
            else
                success "$service_name stopped successfully"
                return 0
            fi
        fi
    else
        warning "$service_name not running on port $port"
        return 0
    fi
}

# Function to stop all services
stop_services() {
    log "🛑 Stopping Flashcard Learning System services..."
    
    # Kill specific processes
    pkill -f "uvicorn.*main" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    pkill -f "npm.*dev" 2>/dev/null || true
    
    # Kill by port
    kill_port 8000 "Backend (FastAPI)"
    kill_port 3000 "Frontend (Vite)"
    kill_port 5173 "Frontend (Vite alternate)"
    kill_port 5174 "Frontend (Vite alternate)"
    
    success "All services stopped"
}

# Function to check PostgreSQL Docker container
check_postgres() {
    log "🐘 Checking PostgreSQL Docker container..."
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "flash_cards-postgres-1.*Up"; then
        success "PostgreSQL container is running"
        return 0
    else
        warning "PostgreSQL container not running, attempting to start..."
        cd "$PROJECT_DIR"
        docker-compose up -d postgres
        sleep 5
        
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "flash_cards-postgres-1.*Up"; then
            success "PostgreSQL container started successfully"
            return 0
        else
            error "Failed to start PostgreSQL container"
            return 1
        fi
    fi
}

# Function to start backend
start_backend() {
    log "🚀 Starting Backend (FastAPI)..."
    
    if check_port 8000; then
        warning "Port 8000 already in use, stopping existing service..."
        kill_port 8000 "Backend"
    fi
    
    cd "$PROJECT_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found at $VENV_PATH"
        log "Please create virtual environment: python -m venv venv"
        return 1
    fi
    
    # Start backend in background
    nohup bash -c "
        source '$VENV_PATH/bin/activate' && 
        cd '$BACKEND_DIR' && 
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
    " > backend.log 2>&1 &
    
    # Wait for backend to start
    sleep 5
    
    if check_port 8000; then
        success "Backend started on http://localhost:8000"
        log "Backend logs: tail -f $PROJECT_DIR/backend.log"
        return 0
    else
        error "Failed to start backend"
        log "Check backend.log for details: cat $PROJECT_DIR/backend.log"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    log "⚛️  Starting Frontend (React + Vite)..."
    
    if check_port 3000; then
        warning "Port 3000 already in use, stopping existing service..."
        kill_port 3000 "Frontend"
    fi
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log "Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend in background
    nohup npx vite --port 3000 --host 0.0.0.0 > ../frontend.log 2>&1 &
    
    # Wait for frontend to start
    sleep 5
    
    if check_port 3000; then
        success "Frontend started on http://localhost:3000"
        log "Frontend logs: tail -f $PROJECT_DIR/frontend.log"
        return 0
    else
        error "Failed to start frontend"
        log "Check frontend.log for details: cat $PROJECT_DIR/frontend.log"
        return 1
    fi
}

# Function to start all services
start_services() {
    log "🚀 Starting Flashcard Learning System..."
    
    # Check PostgreSQL first
    if ! check_postgres; then
        error "Cannot start without PostgreSQL"
        return 1
    fi
    
    # Start backend
    if ! start_backend; then
        error "Failed to start backend"
        return 1
    fi
    
    # Start frontend
    if ! start_frontend; then
        error "Failed to start frontend"
        return 1
    fi
    
    success "🎉 Flashcard Learning System started successfully!"
    log "📊 Backend: http://localhost:8000"
    log "🌐 Frontend: http://localhost:3000"
    log "📋 API Docs: http://localhost:8000/docs"
}

# Function to show service status
show_status() {
    log "📊 Flashcard Learning System Status"
    echo
    
    # Check PostgreSQL
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "flash_cards-postgres-1.*Up"; then
        success "PostgreSQL: Running (Docker)"
    else
        error "PostgreSQL: Not running"
    fi
    
    # Check Backend
    if check_port 8000; then
        success "Backend: Running on port 8000"
    else
        error "Backend: Not running"
    fi
    
    # Check Frontend
    if check_port 3000; then
        success "Frontend: Running on port 3000"
    else
        error "Frontend: Not running"
    fi
    
    echo
    log "🔗 Service URLs:"
    log "   Frontend: http://localhost:3000"
    log "   Backend API: http://localhost:8000"
    log "   API Documentation: http://localhost:8000/docs"
}

# Function to restart services
restart_services() {
    log "🔄 Restarting Flashcard Learning System..."
    stop_services
    sleep 3
    start_services
}

# Function to show logs
show_logs() {
    local service=$1
    case $service in
        "backend"|"api")
            if [ -f "$PROJECT_DIR/backend.log" ]; then
                tail -f "$PROJECT_DIR/backend.log"
            else
                error "Backend log file not found"
            fi
            ;;
        "frontend"|"ui")
            if [ -f "$PROJECT_DIR/frontend.log" ]; then
                tail -f "$PROJECT_DIR/frontend.log"
            else
                error "Frontend log file not found"
            fi
            ;;
        *)
            log "Available logs: backend, frontend"
            ;;
    esac
}

# Main script logic
case "${1:-}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "${2:-}"
        ;;
    *)
        echo "Flashcard Learning System - Server Control"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  start     - Start all services (PostgreSQL, Backend, Frontend)"
        echo "  stop      - Stop all services"
        echo "  restart   - Stop and start all services"
        echo "  status    - Show status of all services"
        echo "  logs      - Show logs (backend|frontend)"
        echo
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 restart"
        echo "  $0 logs backend"
        ;;
esac
