# FlashLearn - Docker Registry Deployment Guide

## Overview
This deployment method uses pre-built Docker images from a registry (Docker Hub, AWS ECR, etc.), which provides:
- **Faster deployment** (no build time on server)
- **Consistency** (same images across environments)  
- **Version control** (tagged releases)
- **Scalability** (easy to deploy to multiple servers)

## Prerequisites
1. Docker and Docker Compose installed on server
2. Access to Docker registry (Docker Hub account)
3. At least 2GB RAM available

## Step 1: Build and Push Images

### Local Development Machine:
```bash
# 1. Build the images locally
docker build -t your-username/flashlearn-backend:latest ./backend
docker build -t your-username/flashlearn-frontend:latest \
    -f frontend/Dockerfile.prod \
    --build-arg VITE_API_BASE_URL=/api/v1 \
    ./frontend

# 2. Push to Docker Hub (requires docker login)
docker push your-username/flashlearn-backend:latest
docker push your-username/flashlearn-frontend:latest
```

### Or use the provided script:
```bash
# Set your Docker Hub username
export DOCKER_USERNAME=your-username
./build-images.sh
```

## Step 2: Server Deployment

### Copy files to server:
```bash
# Required files for server:
- docker-compose.images.yml
- repopulate_db.sh
- init_db.sql
```

### Update docker-compose.images.yml:
```yaml
services:
  backend:
    image: your-username/flashlearn-backend:latest  # Update this
  frontend:
    image: your-username/flashlearn-frontend:latest # Update this
  # ... rest of config stays the same
```

### Deploy on server:
```bash
# 1. Start services
docker-compose -f docker-compose.images.yml up -d

# 2. Initialize database
./repopulate_db.sh

# 3. Verify deployment
curl http://localhost:3000/api/v1/admin/config/learning/public
```

## Benefits of This Approach:
- ✅ No build dependencies on server
- ✅ Consistent deployments across environments
- ✅ Version rollback capability
- ✅ Faster startup times
- ✅ Better for CI/CD pipelines

## Updating the Application:
```bash
# 1. Build new images with version tags
docker build -t your-username/flashlearn-backend:v1.1 ./backend
docker push your-username/flashlearn-backend:v1.1

# 2. Update compose file and redeploy
docker-compose -f docker-compose.images.yml pull
docker-compose -f docker-compose.images.yml up -d
```
