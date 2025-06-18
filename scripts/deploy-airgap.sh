#!/bin/bash

# IPSW Symbol Server - Airgap Deployment
# Uses pre-built Docker images from registry

set -e

echo "🔒 Starting IPSW Symbol Server - Airgap Deployment"

# Copy airgap environment file
if [ ! -f .env ]; then
    echo "📝 Copying airgap environment configuration..."
    cp config/env.airgap .env
    echo "⚠️  Please edit .env file to configure your airgap environment:"
    echo "   - AIRGAP_REGISTRY: Your internal Docker registry"
    echo "   - AIRGAP_S3_ENDPOINT: Your internal S3 endpoint"
    echo "   - S3_ACCESS_KEY/S3_SECRET_KEY: Your S3 credentials"
else
    echo "📁 Using existing .env file"
fi

# Load environment variables
source .env

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/{cache,symbols,downloads,temp,processing}
mkdir -p postgres

# Create PostgreSQL init script if not exists
if [ ! -f postgres/init-symbols-db.sql ]; then
    echo "🗃️  PostgreSQL init script not found, creating default..."
    cat > postgres/init-symbols-db.sql << 'EOF'
-- Initialize Symbol Server database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Symbols table for storing symbol metadata
CREATE TABLE IF NOT EXISTS symbols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_identifier VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_version VARCHAR(20) NOT NULL,
    kernel_path TEXT NOT NULL,
    symbols_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_identifier, ios_version, build_version)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_symbols_device_version 
ON symbols(device_identifier, ios_version, build_version);

-- Symbol cache table
CREATE TABLE IF NOT EXISTS symbol_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    symbol_data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for cache lookups
CREATE INDEX IF NOT EXISTS idx_symbol_cache_key ON symbol_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_symbol_cache_expires ON symbol_cache(expires_at);
EOF
else
    echo "✅ PostgreSQL init script found"
fi

# Validate airgap configuration
echo "🔍 Validating airgap configuration..."
if [ -z "$AIRGAP_REGISTRY" ] || [ "$AIRGAP_REGISTRY" = "your-registry.local:5000" ]; then
    echo "⚠️  Warning: AIRGAP_REGISTRY not configured properly"
    echo "Please update AIRGAP_REGISTRY in .env file"
fi

if [ -z "$AIRGAP_S3_ENDPOINT" ] || [ "$AIRGAP_S3_ENDPOINT" = "http://s3.internal.local:9000" ]; then
    echo "⚠️  Warning: AIRGAP_S3_ENDPOINT not configured properly"
    echo "Please update AIRGAP_S3_ENDPOINT in .env file"
fi

# Check if images are available
echo "🐳 Checking Docker images..."
REGISTRY=${AIRGAP_REGISTRY:-localhost:5000}
VERSION=${VERSION:-latest}

for image in "ipsw-symbol-server" "ipsw-api-server" "ipsw-nginx"; do
    if ! docker image inspect "${REGISTRY}/${image}:${VERSION}" >/dev/null 2>&1; then
        echo "❌ Image ${REGISTRY}/${image}:${VERSION} not found"
        echo "Please build images first: ./scripts/build-airgap-images.sh"
        echo "Or load from file: docker load < ipsw-images.tar.gz"
        exit 1
    else
        echo "✅ Found ${REGISTRY}/${image}:${VERSION}"
    fi
done

# Create signatures directory structure
echo "📂 Creating signatures directory..."
mkdir -p signatures/symbolicator/kernel

# Deploy using airgap profile
echo "🚀 Deploying IPSW Symbol Server (Airgap Mode)..."
docker-compose --profile airgap up -d

echo ""
echo "✅ Airgap deployment completed!"
echo ""
echo "🌐 Services will be available at:"
echo "   Web UI: http://localhost:${NGINX_PORT:-80}"
echo "   API: http://localhost:${API_PORT:-8000}"
echo "   Symbol Server: http://localhost:${SYMBOL_PORT:-3993}"
echo "   PostgreSQL: localhost:5432"
echo ""
echo "📊 To check status:"
echo "   docker-compose --profile airgap ps"
echo ""
echo "📋 To view logs:"
echo "   docker-compose --profile airgap logs -f" 