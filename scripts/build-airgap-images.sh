#!/bin/bash

# Build Docker Images for Airgap Deployment
# This script builds all required images and tags them for airgap registry

set -e

echo "🔧 Building IPSW Symbol Server Docker Images for Airgap Deployment"

# Configuration
REGISTRY=${AIRGAP_REGISTRY:-localhost:5000}
VERSION=${VERSION:-latest}
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "📊 Build Configuration:"
echo "   Registry: $REGISTRY"
echo "   Version: $VERSION"
echo "   Build Date: $BUILD_DATE"
echo "   Git Commit: $GIT_COMMIT"
echo ""

# Build Symbol Server
echo "🔨 Building Symbol Server..."
docker build \
  --file docker/Dockerfile.symbol-server \
  --tag "${REGISTRY}/ipsw-symbol-server:${VERSION}" \
  --tag "${REGISTRY}/ipsw-symbol-server:latest" \
  --label "build.date=${BUILD_DATE}" \
  --label "build.version=${VERSION}" \
  --label "build.commit=${GIT_COMMIT}" \
  .

# Build API Server
echo "🔨 Building API Server..."
docker build \
  --file docker/Dockerfile.api \
  --tag "${REGISTRY}/ipsw-api-server:${VERSION}" \
  --tag "${REGISTRY}/ipsw-api-server:latest" \
  --label "build.date=${BUILD_DATE}" \
  --label "build.version=${VERSION}" \
  --label "build.commit=${GIT_COMMIT}" \
  .

# Build Nginx
echo "🔨 Building Nginx..."
docker build \
  --file docker/Dockerfile.nginx \
  --tag "${REGISTRY}/ipsw-nginx:${VERSION}" \
  --tag "${REGISTRY}/ipsw-nginx:latest" \
  --label "build.date=${BUILD_DATE}" \
  --label "build.version=${VERSION}" \
  --label "build.commit=${GIT_COMMIT}" \
  .

echo ""
echo "✅ All images built successfully!"
echo ""
echo "📦 Built Images:"
docker images | grep "${REGISTRY}/ipsw-" | head -n 10

echo ""
echo "💾 To save images for airgap transfer:"
echo "   docker save ${REGISTRY}/ipsw-symbol-server:${VERSION} ${REGISTRY}/ipsw-api-server:${VERSION} ${REGISTRY}/ipsw-nginx:${VERSION} | gzip > ipsw-images-${VERSION}.tar.gz"
echo ""
echo "📤 To push to registry (if available):"
echo "   docker push ${REGISTRY}/ipsw-symbol-server:${VERSION}"
echo "   docker push ${REGISTRY}/ipsw-api-server:${VERSION}"
echo "   docker push ${REGISTRY}/ipsw-nginx:${VERSION}"
echo ""
echo "🚀 To deploy in airgap environment:"
echo "   docker-compose --profile airgap up -d" 