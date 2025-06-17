#!/bin/bash

echo "🚀 Starting S3-Optimized IPSW Symbol Server..."
echo "=================================================="

# Wait for S3 mount to be ready
echo "⏳ Waiting for S3 mount..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if [ -d "/app/data/s3-ipsw" ] && [ "$(ls -A /app/data/s3-ipsw 2>/dev/null)" ]; then
        echo "✅ S3 mount is ready"
        break
    fi
    
    if [ $counter -eq 0 ]; then
        echo "🔍 Checking S3 mount availability..."
    fi
    
    sleep 2
    counter=$((counter + 2))
    
    if [ $((counter % 10)) -eq 0 ]; then
        echo "⏳ Still waiting for S3 mount... (${counter}s/${timeout}s)"
    fi
done

if [ $counter -ge $timeout ]; then
    echo "⚠️  S3 mount not available after ${timeout}s, continuing anyway..."
    echo "📁 Available directories:"
    ls -la /app/data/
else
    echo "📊 S3 mount contents:"
    ls -lh /app/data/s3-ipsw/ | head -10
fi

# Display configuration
echo ""
echo "📋 Configuration:"
echo "   S3 Endpoint: ${S3_ENDPOINT:-Not set}"
echo "   S3 Bucket: ${S3_BUCKET:-Not set}"
echo "   Cache Size: ${CACHE_SIZE_GB:-50}GB"
echo "   Cleanup After: ${CLEANUP_AFTER_HOURS:-24} hours"
echo "   Max Concurrent Downloads: ${MAX_CONCURRENT_DOWNLOADS:-3}"

# Create necessary directories
echo ""
echo "📁 Setting up directories..."
mkdir -p /app/data/{cache,symbols,temp,processing}
chmod 755 /app/data/{cache,symbols,temp,processing}

# Display storage info
echo ""
echo "💾 Storage Information:"
df -h /app/data | tail -n 1

# Start the Python application
echo ""
echo "🌐 Starting Symbol Server API on port 8000..."
echo "=================================================="

exec python3 -u /app/custom_symbol_server.py 