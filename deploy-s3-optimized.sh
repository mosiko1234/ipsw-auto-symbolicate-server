#!/bin/bash

echo "🚀 Deploying S3-Optimized IPSW Symbol Server..."
echo "=================================================="

# Configuration
S3_ENDPOINT=${S3_ENDPOINT:-"http://host.docker.internal:9000"}
S3_ACCESS_KEY=${S3_ACCESS_KEY:-"minioadmin"}
S3_SECRET_KEY=${S3_SECRET_KEY:-"minioadmin"}
S3_BUCKET=${S3_BUCKET:-"ipsw"}
CACHE_SIZE_GB=${CACHE_SIZE_GB:-"100"}

echo "📋 Configuration:"
echo "   S3 Endpoint: $S3_ENDPOINT"
echo "   S3 Bucket: $S3_BUCKET"
echo "   Cache Size: ${CACHE_SIZE_GB}GB"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker stop symbol-server-s3-optimized s3-mount-service 2>/dev/null || true
docker rm symbol-server-s3-optimized s3-mount-service 2>/dev/null || true

# Check if s3fs image exists, if not build it
echo "🔍 Checking S3FS image..."
if ! docker images | grep -q "s3fs/s3fs"; then
    echo "📦 Building S3FS image..."
    cat > Dockerfile.s3fs << 'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    s3fs \
    fuse \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /mnt/s3
WORKDIR /mnt

CMD ["s3fs"]
EOF
    docker build -t s3fs/s3fs -f Dockerfile.s3fs .
    rm Dockerfile.s3fs
fi

# Update docker-compose environment
cat > .env.s3-optimized << EOF
S3_ENDPOINT=$S3_ENDPOINT
S3_ACCESS_KEY=$S3_ACCESS_KEY
S3_SECRET_KEY=$S3_SECRET_KEY
S3_BUCKET=$S3_BUCKET
CACHE_SIZE_GB=$CACHE_SIZE_GB
CLEANUP_AFTER_HOURS=24
MAX_CONCURRENT_DOWNLOADS=3
CLEANUP_OLD_FILES=true
EOF

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.s3-optimized.yml --env-file .env.s3-optimized up -d --build

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.s3-optimized.yml ps

# Test S3 mount
echo ""
echo "🔍 Testing S3 mount..."
docker exec symbol-server-s3-optimized ls -la /app/data/s3-ipsw/ 2>/dev/null || echo "⚠️  S3 mount not yet ready"

# Show logs
echo ""
echo "📋 Recent logs:"
docker logs symbol-server-s3-optimized --tail 20

echo ""
echo "✅ Deployment completed!"
echo "🌐 Symbol Server API: http://localhost:8000"
echo "📊 Cache Stats: http://localhost:8000/cache-stats"
echo ""
echo "🛠️  Management commands:"
echo "   View logs: docker logs symbol-server-s3-optimized -f"
echo "   View S3 mount: docker exec symbol-server-s3-optimized ls -lh /app/data/s3-ipsw/"
echo "   View cache: docker exec symbol-server-s3-optimized ls -lh /app/data/cache/"
echo "   Stop: docker-compose -f docker-compose.s3-optimized.yml down" 