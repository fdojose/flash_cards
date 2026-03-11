# Phase 8.3: Development and Local Deployment
# ============================================
# Quick deployment script for local development and testing

#!/bin/bash

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🏠 Flashcard Learning System - Local Development Setup${NC}"
echo "====================================================="

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create development environment file
log_info "Creating development environment file..."
cat > backend/.env.development << 'EOF'
# Development Environment Configuration
DATABASE_URL=postgresql://flashcard_user:dev_password@postgres:5432/flashcard_dev
SECRET_KEY=dev-secret-key-not-for-production-use-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
REDIS_PASSWORD=dev_redis_password
REDIS_URL=redis://:dev_redis_password@redis:6379/0
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development
MAX_UPLOAD_SIZE=10485760
UPLOAD_PATH=/app/uploads
SESSION_TIMEOUT=86400
RATE_LIMIT_PER_MINUTE=100
AUTH_RATE_LIMIT_PER_MINUTE=10
WORKERS=2
MAX_CONNECTIONS=100
KEEPALIVE_TIMEOUT=30
SECURITY_HEADERS_ENABLED=false
FORCE_HTTPS=false
HSTS_MAX_AGE=0
POSTGRES_DB=flashcard_dev
POSTGRES_USER=flashcard_user
POSTGRES_PASSWORD=dev_password
EOF
log_success "Development environment file created"

# Create development Docker Compose override
log_info "Creating development Docker Compose configuration..."
cat > docker-compose.dev.yml << 'EOF'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: flashcard_dev
      POSTGRES_USER: flashcard_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5433:5432"  # Changed to avoid port conflict

  redis:
    image: redis:7-alpine
    environment:
      - REDIS_PASSWORD=dev_redis_password
    ports:
      - "6379:6379"  # Expose for external tools

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.new
      target: development
    env_file:
      - ./backend/.env.development
    volumes:
      - ./backend:/app
      - backend_uploads:/app/uploads
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
      - REACT_APP_ENVIRONMENT=development
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.dev.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3001:3000"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"

volumes:
  backend_uploads:
EOF
log_success "Development Docker Compose configuration created"

# Create development nginx configuration
log_info "Creating development nginx configuration..."
cat > nginx.dev.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name localhost;

        # API routes
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for React hot reload
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
log_success "Development nginx configuration created"

# Stop any existing containers
log_info "Stopping any existing containers..."
docker-compose -f docker-compose.dev.yml down --remove-orphans || true
log_success "Existing containers stopped"

# Build and start development environment
log_info "Building and starting development environment..."
docker-compose -f docker-compose.dev.yml up -d --build

# Wait for services to be ready
log_info "Waiting for services to be ready..."
sleep 15

# Check if services are running
log_info "Checking service health..."
if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    log_success "Development environment is running!"
else
    log_error "Some services failed to start. Check logs with: docker-compose -f docker-compose.dev.yml logs"
    exit 1
fi

# Run database migrations
log_info "Running database migrations..."
sleep 5  # Give database a moment to fully start
docker-compose -f docker-compose.dev.yml exec backend python -m alembic upgrade head || {
    log_warning "Migration failed, trying again in 5 seconds..."
    sleep 5
    docker-compose -f docker-compose.dev.yml exec backend python -m alembic upgrade head
}
log_success "Database migrations completed"

# Create test data (optional)
read -p "$(echo -e ${YELLOW}Would you like to create test data? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Creating test data..."
    docker-compose -f docker-compose.dev.yml exec backend python -c "
import asyncio
from app.auth.utils import get_password_hash
from app.database import get_db
from app.auth.models import User
from app.datasets.models import Dataset, Flashcard
from sqlalchemy.orm import Session
import uuid

async def create_test_data():
    db = next(get_db())
    
    # Create test admin user
    admin_user = User(
        id=str(uuid.uuid4()),
        username='admin',
        email='admin@test.com',
        hashed_password=get_password_hash('admin123'),
        is_admin=True
    )
    db.add(admin_user)
    
    # Create test regular user
    user = User(
        id=str(uuid.uuid4()),
        username='testuser',
        email='user@test.com',
        hashed_password=get_password_hash('user123'),
        is_admin=False
    )
    db.add(user)
    
    # Create test dataset
    dataset = Dataset(
        id=str(uuid.uuid4()),
        name='Sample Math Dataset',
        description='Basic math questions for testing',
        created_by=admin_user.id,
        metadata_={'subject': 'mathematics', 'difficulty': 'beginner'}
    )
    db.add(dataset)
    db.commit()
    
    # Create test flashcards
    flashcards = [
        {'question': 'What is 2 + 2?', 'answer': '4'},
        {'question': 'What is 5 * 3?', 'answer': '15'},
        {'question': 'What is 10 / 2?', 'answer': '5'},
        {'question': 'What is 7 - 3?', 'answer': '4'},
        {'question': 'What is 8 + 6?', 'answer': '14'}
    ]
    
    for card_data in flashcards:
        flashcard = Flashcard(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            question=card_data['question'],
            answer=card_data['answer']
        )
        db.add(flashcard)
    
    db.commit()
    print('Test data created successfully!')
    print('Admin user: admin / admin123')
    print('Regular user: testuser / user123')

asyncio.run(create_test_data())
"
    log_success "Test data created"
fi

# Show service URLs
echo ""
echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo "============================================"
log_info "Service URLs:"
echo "🌐 Frontend: http://localhost:3000"
echo "🌐 Nginx Proxy: http://localhost:8080"
echo "🔧 Backend API: http://localhost:8000"
echo "🔧 API Docs: http://localhost:8000/docs"
echo "📊 Grafana: http://localhost:3001 (admin/admin)"
echo "📈 Prometheus: http://localhost:9090"
echo "🗄️  PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
log_info "Useful commands:"
echo "- View logs: docker-compose -f docker-compose.dev.yml logs"
echo "- Restart services: docker-compose -f docker-compose.dev.yml restart"
echo "- Stop services: docker-compose -f docker-compose.dev.yml down"
echo "- Backend shell: docker-compose -f docker-compose.dev.yml exec backend bash"
echo "- Run tests: docker-compose -f docker-compose.dev.yml exec backend pytest"
echo ""
log_success "Happy coding! 🚀"
