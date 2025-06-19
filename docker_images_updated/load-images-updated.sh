#!/bin/bash

echo "🐳 Loading updated IPSW Symbol Server Docker images..."
echo "================================================="

images=(
    "ipsw-api-server-updated.tar.gz"
    "ipsw-symbol-server-updated.tar.gz" 
    "ipsw-nginx-updated.tar.gz"
    "postgres-15-updated.tar.gz"
    "minio-latest-updated.tar.gz"
    "buildkit-updated.tar.gz"
)

total_images=${#images[@]}
loaded_count=0
failed_count=0

for image in "${images[@]}"; do
    if [ -f "$image" ]; then
        echo ""
        echo "Loading $image..."
        docker load < "$image"
        if [ $? -eq 0 ]; then
            echo "✅ Successfully loaded $image"
            loaded_count=$((loaded_count + 1))
        else
            echo "❌ Failed to load $image"
            failed_count=$((failed_count + 1))
        fi
    else
        echo "⚠️  File not found: $image"
        failed_count=$((failed_count + 1))
    fi
done

echo ""
echo "================================================="
echo "📊 Loading Summary:"
echo "   Total images: $total_images"
echo "   Successfully loaded: $loaded_count"
echo "   Failed: $failed_count"

if [ $failed_count -eq 0 ]; then
    echo ""
    echo "🎉 All images loaded successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start the system: docker-compose --profile regular up -d"
    echo "2. Test device mapping: curl -X POST http://localhost:8000/auto-scan -H 'Content-Type: application/json' -d '{\"device_model\": \"iPhone 14 Pro\", \"ios_version\": \"18.5\"}'"
    echo "3. Open web UI: http://localhost:8000/ui"
else
    echo ""
    echo "⚠️  Some images failed to load. Please check the errors above."
    exit 1
fi 