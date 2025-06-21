#!/bin/bash

# IPSW Symbol Server - Docker Images Loader
# Version: v1.2.3 - Multi-Device IPSW Support + Cache Refresh
# This script loads all required Docker images for the IPSW Symbol Server

set -e

echo "=============================================="
echo "IPSW Symbol Server - Loading Images v1.2.3"
echo "✨ Multi-Device IPSW Support + Cache Refresh"
echo "=============================================="
echo

# Function to load image with validation
load_image() {
    local tar_file="$1"
    local description="$2"
    
    if [ ! -f "$tar_file" ]; then
        echo "❌ ERROR: $tar_file not found!"
        return 1
    fi
    
    echo "📦 Loading $description..."
    if docker load -i "$tar_file"; then
        echo "✅ $description loaded successfully"
        echo
    else
        echo "❌ ERROR: Failed to load $description"
        return 1
    fi
}

echo "🚀 Starting Docker image loading process..."
echo

# Load all images
load_image "ipsw-api-server-v1.2.3.tar" "API Server (with cache refresh endpoint)"
load_image "ipsw-symbol-server-v1.2.3.tar" "Symbol Server (with multi-device IPSW support)"
load_image "ipsw-nginx-v1.2.3.tar" "Nginx Reverse Proxy"
load_image "minio-v1.2.3.tar" "MinIO S3 Storage"
load_image "postgres-v1.2.3.tar" "PostgreSQL Database"

echo "✅ All Docker images loaded successfully!"
echo
echo "🎯 New Features in v1.2.3:"
echo "  🆕 Multi-Device IPSW Support"
echo "  🆕 Manual Cache Refresh: POST /refresh-cache"
echo "  🆕 Real-time IPSW Detection"
echo "  🔧 Enhanced Device Matching"
echo "  ⚡ Performance Optimizations"
echo
echo "🚀 Ready to deploy! Run:"
echo "   docker-compose --profile regular up -d"
echo
echo "📖 For cache refresh after uploading new IPSW files:"
echo "   curl -X POST 'http://localhost:8000/refresh-cache'"
echo
