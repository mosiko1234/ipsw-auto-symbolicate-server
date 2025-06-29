#!/bin/bash

# IPSW Symbol Server v3.0.0 - Deployment Package Verification Script

echo "🔍 IPSW Symbol Server v3.0.0 - Package Verification"
echo "=================================================="

PACKAGE_FILE="ipsw-symbol-server-v3.0.0-deployment.tar.gz"
CHECKSUM_FILE="ipsw-symbol-server-v3.0.0-deployment.tar.gz.sha256"

# Check if package exists
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Package file $PACKAGE_FILE not found"
    exit 1
fi

# Check if checksum file exists
if [ ! -f "$CHECKSUM_FILE" ]; then
    echo "❌ Checksum file $CHECKSUM_FILE not found"
    exit 1
fi

echo "📦 Package found: $PACKAGE_FILE"
echo "📋 Checksum file found: $CHECKSUM_FILE"

# Verify package integrity
echo ""
echo "🔐 Verifying package integrity..."
if sha256sum -c "$CHECKSUM_FILE"; then
    echo "✅ Package integrity verified successfully!"
else
    echo "❌ Package integrity verification failed!"
    exit 1
fi

# Show package info
echo ""
echo "📊 Package Information:"
echo "   File: $PACKAGE_FILE"
echo "   Size: $(ls -lh $PACKAGE_FILE | awk '{print $5}')"
echo "   Date: $(stat -c %y $PACKAGE_FILE 2>/dev/null || stat -f %Sm $PACKAGE_FILE)"

echo ""
echo "📦 Package Contents Preview:"
tar -tzf "$PACKAGE_FILE" | head -20

if [ $(tar -tzf "$PACKAGE_FILE" | wc -l) -gt 20 ]; then
    echo "   ... and $(expr $(tar -tzf "$PACKAGE_FILE" | wc -l) - 20) more files"
fi

echo ""
echo "🚀 To deploy this package:"
echo "   1. Extract: tar -xzf $PACKAGE_FILE"
echo "   2. Deploy: cd ipsw-symbol-server-v3.0.0-deployment && ./deploy.sh"
echo ""
echo "✅ Package verification complete!" 