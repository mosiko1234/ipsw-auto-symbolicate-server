#!/bin/bash

echo "🍎 Starting IPSW Symbol Server..."

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "✅ Environment loaded"
else
    echo "❌ .env file not found!"
    exit 1
fi

# Check if MinIO is running
echo "🔍 Checking MinIO..."
if ! curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "❌ MinIO is not running! Please start it first."
    echo "   Run: docker run -d -p 9000:9000 -p 9001:9001 --name minio ..."
    exit 1
fi
echo "✅ MinIO is running"

# Start PostgreSQL (symbols database)
echo "🗄️  Starting PostgreSQL..."
docker-compose -f docker-compose.symbol-server.yml up -d symbols-postgres
sleep 5

# Start Symbol Server
echo "🔧 Starting Symbol Server..."
docker-compose -f docker-compose.symbol-server.yml up -d custom-symbol-server
sleep 10

# Start API Server
echo "🌐 Starting API Server..."
docker run -d --name ipsw-api-server \
  -p ${API_PORT}:8000 \
  -e SYMBOL_SERVER_URL=http://host.docker.internal:3993 \
  -e S3_ENDPOINT=${S3_ENDPOINT} \
  -e S3_ACCESS_KEY=${S3_ACCESS_KEY} \
  -e S3_SECRET_KEY=${S3_SECRET_KEY} \
  -e S3_BUCKET=${S3_BUCKET} \
  -v $(pwd)/data:/app/data \
  --add-host host.docker.internal:host-gateway \
  $(docker build -q -f auto-symbolication-api.py .) 2>/dev/null || \
  echo "ℹ️  API Server already running or failed to start"

sleep 5

# Start Web UI
echo "🖥️  Starting Web UI..."
docker run -d --name ipsw-web-ui \
  -p ${WEB_UI_PORT}:5001 \
  -e API_SERVER_URL=http://host.docker.internal:8000 \
  -v $(pwd)/templates:/app/templates \
  -v $(pwd)/static:/app/static \
  --add-host host.docker.internal:host-gateway \
  $(docker build -q -f Dockerfile.webui .) 2>/dev/null || \
  echo "ℹ️  Web UI already running or failed to start"

sleep 3

# Start Nginx (main entry point)
echo "🌐 Starting Nginx..."
docker rm -f ipsw-nginx 2>/dev/null || true
docker run -d --name ipsw-nginx \
  -p ${NGINX_PORT:-80}:80 \
  --add-host host.docker.internal:host-gateway \
  $(docker build -q -f Dockerfile.nginx .)

sleep 3

# Health checks
echo ""
echo "🔍 Performing health checks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Nginx
if curl -s http://localhost/health > /dev/null; then
    echo "✅ Nginx: http://localhost (Port ${NGINX_PORT:-80})"
else
    echo "❌ Nginx: Failed"
fi

# API
if curl -s http://localhost/api/health > /dev/null; then
    echo "✅ API Server: http://localhost/api"
else
    echo "❌ API Server: Failed"
fi

# Symbol Server
if curl -s http://localhost/symbol-server/health > /dev/null; then
    echo "✅ Symbol Server: http://localhost/symbol-server"
else
    echo "❌ Symbol Server: Failed"
fi

# Web UI (direct check)
if curl -s http://localhost:${WEB_UI_PORT} > /dev/null; then
    echo "✅ Web UI: http://localhost/ui"
else
    echo "❌ Web UI: Failed"
fi

echo ""
echo "🎉 IPSW Symbol Server is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Main URL: http://localhost"
echo "📋 API Documentation: http://localhost/docs"
echo "🔍 Service Status: http://localhost/status"
echo "💻 Web Interface: http://localhost/ui"
echo ""
echo "🚀 Quick test:"
echo "curl -X POST \"http://localhost/api/symbolicate\" -F \"file=@your-crash.ips\"" 