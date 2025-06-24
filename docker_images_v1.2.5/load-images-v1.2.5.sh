#!/bin/bash

# IPSW Symbol Server v1.2.5 - Load Docker Images
# Includes large file support and streaming upload improvements

VERSION="v1.2.5"
IMAGE_FILE="ipsw-symbol-server-${VERSION}.tar"

echo "🚀 Loading IPSW Symbol Server Docker Images ${VERSION}"
echo "=================================================="

# Check if image file exists
if [ ! -f "${IMAGE_FILE}" ]; then
    echo "❌ Error: ${IMAGE_FILE} not found"
    echo "Please ensure you're in the correct directory"
    exit 1
fi

echo "📦 Loading Docker images from ${IMAGE_FILE}..."
docker load -i "${IMAGE_FILE}"

if [ $? -eq 0 ]; then
    echo "✅ Docker images loaded successfully!"
    echo ""
    echo "🎯 What's new in v1.2.5:"
    echo "  • Large IPSW file support (up to 15GB)"
    echo "  • Streaming upload for files > 500MB"
    echo "  • Automatic endpoint selection in CLI"
    echo "  • Improved error handling for large files"
    echo "  • Enhanced MinIO integration"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Regular deployment: docker-compose --profile regular up -d"
    echo "  2. Airgap deployment: docker-compose --profile airgap up -d"
    echo ""
    echo "💡 For large IPSW files (>500MB):"
    echo "  • Use MinIO Console: http://localhost:9001"
    echo "  • Upload to 'ipsw' bucket"
    echo "  • Run: ipsw-cli crash.ips"
else
    echo "❌ Failed to load Docker images"
    exit 1
fi
