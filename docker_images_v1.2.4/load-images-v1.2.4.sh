#!/bin/bash

# IPSW Symbol Server - Docker Images Loader
# Version: v1.2.4 - Critical S3 Sync Fix
# This script loads all required Docker images for the IPSW Symbol Server

set -e

echo "=============================================="
echo "IPSW Symbol Server - Loading Images v1.2.4"
echo "🐛 Critical S3 Sync Fix + Enhanced Export"
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
load_image "ipsw-api-server-v1.2.4.tar" "API Server (with S3 File Watcher)"
load_image "ipsw-symbol-server-v1.2.4.tar" "Symbol Server (with persistent S3Manager)"
load_image "ipsw-nginx-v1.2.4.tar" "Nginx Reverse Proxy"
load_image "minio-v1.2.4.tar" "MinIO S3 Storage"
load_image "postgres-v1.2.4.tar" "PostgreSQL Database"

echo "✅ All Docker images loaded successfully!"
echo
echo "🎯 New Features in v1.2.4:"
echo "  🐛 CRITICAL FIX: Symbol Server S3 Synchronization"
echo "  🔧 Persistent S3Manager eliminates manual restarts"
echo "  ⚡ Enhanced cache refresh functionality"
echo "  🚀 True end-to-end automation"
echo "  💾 Enhanced CLI with export options"
echo
echo "🚀 Ready to deploy! Run:"
echo "   docker-compose --profile regular up -d"
echo
echo "📖 For more information, see README.md"
echo
