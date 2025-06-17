#!/bin/bash

# IPSW Symbol Server - Regular Deployment
# Builds images and runs with internal MinIO

set -e

echo "🚀 Starting IPSW Symbol Server - Regular Deployment"

# Copy regular environment file
cp env.regular .env

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

# Build and start services with regular profile
echo "🔨 Building and starting services..."
docker-compose --profile regular up -d --build

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
echo "  • MinIO Console: http://localhost:9001"
echo "  • Nginx (Main): http://localhost"

echo "✅ Regular deployment completed successfully!" 