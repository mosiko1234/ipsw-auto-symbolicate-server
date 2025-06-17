#!/bin/bash

# IPSW Symbol Server - Airgap Deployment
# Uses pre-built Docker images from registry

set -e

echo "🔒 Starting IPSW Symbol Server - Airgap Deployment"

# Copy airgap environment file
cp config/env.airgap .env

# Load environment variables
source .env

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/{cache,symbols,downloads,temp,processing}
mkdir -p postgres

# Create PostgreSQL init script if not exists
if [ ! -f postgres/init.sql ]; then
    cat > postgres/init.sql << 'EOF'
-- IPSW Symbol Server Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Symbols table
CREATE TABLE IF NOT EXISTS symbols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_model VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_number VARCHAR(20) NOT NULL,
    symbol_address BIGINT NOT NULL,
    symbol_name TEXT NOT NULL,
    binary_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_model, ios_version, build_number, symbol_address)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_symbols_lookup 
ON symbols(device_model, ios_version, build_number, symbol_address);

-- IPSW files tracking
CREATE TABLE IF NOT EXISTS ipsw_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL UNIQUE,
    device_model VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_number VARCHAR(20) NOT NULL,
    file_size BIGINT,
    download_url TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    symbols_extracted INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ipsw_device_version 
ON ipsw_files(device_model, ios_version, build_number);
EOF
fi

# Validate airgap configuration
echo "🔍 Validating airgap configuration..."
if [ -z "$AIRGAP_REGISTRY" ]; then
    echo "❌ Error: AIRGAP_REGISTRY not set in env.airgap"
    echo "Please configure your internal Docker registry"
    exit 1
fi

if [ -z "$AIRGAP_S3_ENDPOINT" ]; then
    echo "❌ Error: AIRGAP_S3_ENDPOINT not set in env.airgap"
    echo "Please configure your internal S3 endpoint"
    exit 1
fi

echo "✅ Registry: $AIRGAP_REGISTRY"
echo "✅ S3 Endpoint: $AIRGAP_S3_ENDPOINT"

# Check if required images exist in registry
echo "🔍 Checking pre-built images availability..."
required_images=(
    "ipsw-symbol-server:${VERSION}"
    "ipsw-api-server:${VERSION}"
    "ipsw-web-ui:${VERSION}"
    "ipsw-nginx:${VERSION}"
)

for image in "${required_images[@]}"; do
    full_image="${AIRGAP_REGISTRY}/${image}"
    echo "  Checking: $full_image"
    if ! docker pull "$full_image" >/dev/null 2>&1; then
        echo "❌ Error: Image $full_image not found in registry"
        echo "Please ensure all images are built and pushed to the registry first"
        echo "Run: ./build-images-for-airgap.sh"
        exit 1
    fi
    echo "  ✅ Found: $full_image"
done

# Start services with airgap profile (no build)
echo "🚀 Starting services with pre-built images..."
docker-compose --profile airgap up -d

echo "⏳ Waiting for services to be healthy..."
timeout=300
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ Services are healthy!"
        break
    fi
    sleep 10
    elapsed=$((elapsed + 10))
    echo "   Waiting... ($elapsed/${timeout}s)"
done

# Show service status
echo "📊 Service Status:"
docker-compose ps

echo "🌐 Services are available at:"
echo "  • Web UI: http://localhost:5001"
echo "  • API: http://localhost:8000"
echo "  • Symbol Server: http://localhost:3993"
echo "  • Nginx (Main): http://localhost"
echo ""
echo "🔒 Airgap Configuration:"
echo "  • Registry: $AIRGAP_REGISTRY"
echo "  • S3: $AIRGAP_S3_ENDPOINT"

echo "✅ Airgap deployment completed successfully!" 