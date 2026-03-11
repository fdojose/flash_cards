# FlashLearn Production Deployment Guide

## Overview
This is a complete FlashLearn application ready for production deployment. The application consists of:
- **Frontend**: React application with Nginx (Production build)
- **Backend**: FastAPI application with Python
- **Database**: PostgreSQL 15

## Architecture
- **Single Port Access**: Only port 3000 is exposed to the outside world
- **Internal Network**: All services communicate through a Docker internal network
- **API Proxy**: Nginx proxies API requests to the backend internally
- **Database**: PostgreSQL accessible only within the Docker network

## Quick Start

**Choose your deployment method:**

### Option A: Source Code Deployment (Simple)
1. **Prerequisites**
   - Docker and Docker Compose installed
   - At least 2GB RAM available

2. **Deploy the Application**
   ```bash
   # Clone or extract the application files
   # Navigate to the project directory
   cd flash_cards

   # Start all services (builds images locally)
   docker-compose -f docker-compose.production.yml up -d

   # Check status
   docker-compose -f docker-compose.production.yml ps
   ```

### Option B: Docker Registry Deployment (Recommended for Production)
```bash
# Use pre-built images for faster deployment
docker-compose -f docker-compose.images.yml up -d
```
*See `DOCKER_REGISTRY_DEPLOYMENT.md` for complete instructions*

3. **Access the Application**
   - Open your browser and go to: `http://localhost:3000`
   - The application will be available immediately

4. **Initialize Database with Sample Data**
   ```bash
   # Populate database with admin user and system configurations
   ./repopulate_db.sh
   
   # This creates:
   # - Admin user: admin@flashcards.com / admin123
   # - 20 system configuration variables
   # - Database tables and migrations
   ```

## Configuration

### Environment Variables
The application is configured with these production settings:
- `ENVIRONMENT=production`
- `VITE_API_BASE_URL=/api` (API calls routed through Nginx proxy)
- Database connection via internal Docker network

### Ports
- **External**: 3000 (Frontend + API proxy)
- **Internal**: 8000 (Backend), 5432 (Database)

## Data Persistence
- Database data is stored in Docker volume: `postgres_data`
- Data persists across container restarts

## Administration
The application includes:
- Dynamic learning rules configuration
- Admin interface for system management
- **Learning variables**: initial_set_size, mastery_threshold, stage_increment, max_set_size, mid_tier_threshold, chunk_size_progression, reinforcement_percentage
- **Spaced Repetition variables**: initial_ease, minimum_ease, maximum_ease, ease_bonus, ease_penalty, initial_interval, graduation_interval, maximum_interval, learning_steps, relearning_steps  
- **Ranking variables**: accuracy_min_cards, speed_min_cards, cards_answered_min_threshold

## Security Features
- No direct database access from outside
- API endpoints protected through Nginx proxy
- CORS properly configured
- Security headers in Nginx configuration

## Monitoring
Check application health:
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check container status
docker-compose -f docker-compose.production.yml ps

# Test API endpoint
curl http://localhost:3000/api/v1/admin/config/learning/public
```

## Stopping the Application
```bash
docker-compose -f docker-compose.production.yml down
```

## Backup
To backup the database:
```bash
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U flashcard_user flashcard_db > backup.sql
```

## Support
The application is fully functional with:
- ✅ Dynamic rules explanation system
- ✅ User authentication and management  
- ✅ Learning session management
- ✅ Progress tracking and analytics
- ✅ Admin configuration system
- ✅ Production-optimized build
- ✅ Single-port deployment (3000 only)

## Production Ready Features
- Optimized Docker images
- Nginx reverse proxy
- Production database settings
- Compressed static assets
- Security headers
- Health checks
- Data persistence
