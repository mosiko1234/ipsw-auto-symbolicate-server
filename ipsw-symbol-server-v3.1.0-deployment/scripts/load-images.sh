#!/bin/bash
# Load Docker images from files

echo "📦 Loading Docker images..."

echo "  🐳 Loading ipsw-symbol-server..."
gunzip -c docker-images/ipsw-symbol-server-v3.1.0.tar.gz | docker load

echo "  🐳 Loading PostgreSQL..."
gunzip -c docker-images/postgres-13.tar.gz | docker load

echo "  �� Loading Nginx..."
gunzip -c docker-images/nginx-alpine.tar.gz | docker load

echo "✅ All Docker images loaded successfully!"
