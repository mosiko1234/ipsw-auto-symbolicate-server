#!/bin/bash

# IPSW Symbol Server - Checksum Verification
# Version: v1.2.4

set -e

echo "🔐 Verifying Docker image checksums for v1.2.4..."
echo

if [ ! -f "checksums-v1.2.4.sha256" ]; then
    echo "❌ ERROR: checksums-v1.2.4.sha256 not found!"
    exit 1
fi

if sha256sum -c checksums-v1.2.4.sha256; then
    echo
    echo "✅ All checksums verified successfully!"
    echo "🎯 Docker images are ready for deployment"
else
    echo
    echo "❌ ERROR: Checksum verification failed!"
    echo "🚨 Some files may be corrupted or tampered with"
    exit 1
fi
