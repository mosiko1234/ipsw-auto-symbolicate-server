#!/bin/bash
# IPSW Symbol Server v3.1.0 - Complete Deployment Script

set -e

echo "🚀 IPSW Symbol Server v3.1.0 - Professional Deployment"
echo "========================================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Load Docker images
echo ""
echo "📦 Loading Docker images..."
./scripts/load-images.sh

# Install CLI tools
echo ""
echo "🛠️ Installing enhanced CLI tools..."
cd cli-tools
./install-dev-tools.sh
cd ..

# Set permissions
echo ""
echo "🔧 Setting up permissions..."
chmod +x *.sh
chmod +x cli-tools/*.py
chmod +x cli-tools/ipsw-dev-cli

# Start the system
echo ""
echo "🚀 Starting IPSW Symbol Server..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
echo ""
echo "❤️ Checking system health..."
if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    echo "✅ System is healthy and ready!"
    echo ""
    echo "🌐 Access Points:"
    echo "   Main Interface:   http://localhost:8082/"
    echo "   Upload Interface: http://localhost:8082/upload"
    echo "   Health Check:     http://localhost:8082/health"
    echo "   Direct API:       http://localhost:3993/"
    echo ""
    echo "🛠️ CLI Tools Available:"
    echo "   ipsw-dev-cli status"
    echo "   ipsw-symbolicate crash.ips"
    echo "   ipsw-add iPhone_IPSW.ipsw"
    echo ""
    echo "🎉 Deployment Complete! Ready for professional iOS development!"
else
    echo "⚠️ System is starting up, may take a few more moments..."
    echo "💡 Check status: docker-compose ps"
fi
