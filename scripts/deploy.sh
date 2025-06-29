#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying IPSW Symbol Server...${NC}"

# Load environment variables
if [ -f ".env" ]; then
    source .env
else
    echo -e "${RED}❌ .env file not found. Run ./scripts/setup.sh first.${NC}"
    exit 1
fi

# Validate required variables
if [[ "$DOCKER_IMAGE" == *"your-dockerhub-username"* ]]; then
    echo -e "${RED}❌ Please update DOCKER_IMAGE in .env file with your actual DockerHub username${NC}"
    exit 1
fi

# Pull the latest image
echo -e "${YELLOW}📥 Pulling latest Docker image...${NC}"
docker pull $DOCKER_IMAGE

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down

# Start services
echo -e "${YELLOW}🏃 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 15

# Health check
echo -e "${YELLOW}🏥 Performing health check...${NC}"
max_attempts=12
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:$IPSW_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for service...${NC}"
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo -e "${RED}❌ Health check failed after $max_attempts attempts${NC}"
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker-compose logs --tail=20 ipsw
    exit 1
fi

# Show status
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 Service URLs:"
echo "  - API: http://localhost:$IPSW_PORT"
echo "  - Health: http://localhost:$IPSW_PORT/health"
echo ""
echo "📋 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
