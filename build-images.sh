#!/bin/bash

# FlashLearn - Build and Push Docker Images Script
# This script builds both frontend and backend images and pushes them to Docker Hub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-your-dockerhub-username}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BACKEND_IMAGE="${DOCKER_USERNAME}/flashlearn-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${DOCKER_USERNAME}/flashlearn-frontend:${IMAGE_TAG}"

echo "========================================================================"
echo "  FlashLearn - Docker Image Build & Push Script"
echo "========================================================================"
echo -e "${BLUE}📦 Building images for Docker Hub deployment...${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if logged into Docker Hub
if ! docker system info | grep -q "Username:"; then
    echo -e "${YELLOW}⚠️  Not logged into Docker Hub. Please run: docker login${NC}"
    echo -e "${BLUE}💡 Or set DOCKER_USERNAME environment variable${NC}"
fi

echo -e "${YELLOW}🔨 Building backend image...${NC}"
docker build -t $BACKEND_IMAGE ./backend

echo -e "${YELLOW}🔨 Building frontend image...${NC}"
docker build -t $FRONTEND_IMAGE \
    -f frontend/Dockerfile.prod \
    --build-arg VITE_API_BASE_URL=/api/v1 \
    ./frontend

echo -e "${GREEN}✅ Images built successfully!${NC}"
echo ""
echo "Images created:"
echo "  - $BACKEND_IMAGE"
echo "  - $FRONTEND_IMAGE"
echo ""

# Push images (optional - uncomment to enable)
# echo -e "${YELLOW}🚀 Pushing images to Docker Hub...${NC}"
# docker push $BACKEND_IMAGE
# docker push $FRONTEND_IMAGE
# echo -e "${GREEN}✅ Images pushed successfully!${NC}"

echo -e "${BLUE}📋 To push images to Docker Hub:${NC}"
echo "  docker push $BACKEND_IMAGE"
echo "  docker push $FRONTEND_IMAGE"
echo ""
echo -e "${BLUE}📋 To use these images on your server:${NC}"
echo "  1. Copy docker-compose.images.yml to your server"
echo "  2. Update the image names in the compose file"
echo "  3. Run: docker-compose -f docker-compose.images.yml up -d"
echo ""
echo -e "${GREEN}🎉 Build complete!${NC}"
