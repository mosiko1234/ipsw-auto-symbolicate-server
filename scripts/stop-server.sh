#!/bin/bash

echo "🛑 Stopping IPSW Symbol Server..."

echo "🌐 Stopping Nginx..."
docker stop ipsw-nginx 2>/dev/null && docker rm ipsw-nginx 2>/dev/null || echo "ℹ️  Nginx not running"

echo "🖥️  Stopping Web UI..."
docker stop ipsw-web-ui 2>/dev/null && docker rm ipsw-web-ui 2>/dev/null || echo "ℹ️  Web UI not running"

echo "🌐 Stopping API Server..."
docker stop ipsw-api-server 2>/dev/null && docker rm ipsw-api-server 2>/dev/null || echo "ℹ️  API Server not running"

echo "🔧 Stopping Symbol Server..."
docker-compose -f docker-compose.symbol-server.yml down 2>/dev/null || echo "ℹ️  Symbol Server not running"

echo ""
echo "✅ All services stopped!"
echo ""
echo "💡 Note: MinIO is still running (external service)"
echo "   To stop MinIO: docker stop minio && docker rm minio" 