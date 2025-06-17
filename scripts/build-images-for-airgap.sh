#!/bin/bash

# Build Docker Images for Airgap Deployment
# Builds all required images and pushes them to airgap registry

set -e

# Load configuration
if [ ! -f config/env.airgap ]; then
    echo "❌ Error: config/env.airgap file not found"
    echo "Please configure config/env.airgap first"
    exit 1
fi

source config/env.airgap

echo "🏗️  Building Docker Images for Airgap Deployment"
echo "📦 Target Registry: $AIRGAP_REGISTRY"
echo "🏷️  Version: $VERSION"

# Validate configuration
if [ -z "$AIRGAP_REGISTRY" ]; then
    echo "❌ Error: AIRGAP_REGISTRY not set in env.airgap"
    exit 1
fi

if [ -z "$VERSION" ]; then
    echo "❌ Error: VERSION not set in env.airgap"
    exit 1
fi

# Define images to build
declare -A images
images[symbol-server]="docker/Dockerfile.symbol-server"
images[api-server]="docker/Dockerfile.api"
images[web-ui]="docker/Dockerfile.webui"
images[nginx]="docker/Dockerfile.nginx"

echo "🔨 Building images..."

for service in "${!images[@]}"; do
    dockerfile="${images[$service]}"
    local_tag="ipsw-${service}:${VERSION}"
    registry_tag="${AIRGAP_REGISTRY}/ipsw-${service}:${VERSION}"
    
    echo ""
    echo "🔨 Building $service..."
    echo "   Dockerfile: $dockerfile"
    echo "   Local tag: $local_tag"
    echo "   Registry tag: $registry_tag"
    
    # Build image
    if docker build -f "$dockerfile" -t "$local_tag" .; then
        echo "   ✅ Build successful"
    else
        echo "   ❌ Build failed for $service"
        exit 1
    fi
    
    # Tag for registry
    docker tag "$local_tag" "$registry_tag"
    echo "   ✅ Tagged for registry"
done

echo ""
echo "📤 Pushing images to registry..."

for service in "${!images[@]}"; do
    registry_tag="${AIRGAP_REGISTRY}/ipsw-${service}:${VERSION}"
    
    echo ""
    echo "📤 Pushing $service..."
    if docker push "$registry_tag"; then
        echo "   ✅ Push successful: $registry_tag"
    else
        echo "   ❌ Push failed for $service"
        echo "   Please check your registry connection and credentials"
        exit 1
    fi
done

echo ""
echo "🗜️  Creating image archive for offline transfer..."
archive_file="ipsw-images-${VERSION}.tar"

# Export all images to tar file
image_list=""
for service in "${!images[@]}"; do
    image_list="$image_list ${AIRGAP_REGISTRY}/ipsw-${service}:${VERSION}"
done

if docker save -o "$archive_file" $image_list; then
    echo "✅ Images exported to: $archive_file"
    echo "   File size: $(du -h "$archive_file" | cut -f1)"
else
    echo "❌ Failed to create image archive"
    exit 1
fi

echo ""
echo "📋 Summary:"
echo "   • Registry: $AIRGAP_REGISTRY"
echo "   • Version: $VERSION"
echo "   • Images built: ${#images[@]}"
echo "   • Archive: $archive_file"
echo ""
echo "📝 For offline deployment:"
echo "   1. Transfer $archive_file to airgap environment"
echo "   2. Load images: docker load -i $archive_file"
echo "   3. Run: ./deploy-airgap.sh"
echo ""
echo "✅ All images built and pushed successfully!" 