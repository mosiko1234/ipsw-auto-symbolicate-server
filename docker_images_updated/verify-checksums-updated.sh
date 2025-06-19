#!/bin/bash

echo "🔍 Verifying updated Docker images checksums..."
echo "=============================================="

if [ -f "checksums-updated.sha256" ]; then
    echo "Found checksums file: checksums-updated.sha256"
    echo ""
    
    # Check if sha256sum command exists
    if command -v sha256sum >/dev/null 2>&1; then
        echo "Using sha256sum to verify checksums..."
        sha256sum -c checksums-updated.sha256
        checksum_result=$?
    elif command -v shasum >/dev/null 2>&1; then
        echo "Using shasum to verify checksums..."
        shasum -a 256 -c checksums-updated.sha256
        checksum_result=$?
    else
        echo "❌ Neither sha256sum nor shasum found!"
        echo "Please install one of these tools to verify checksums."
        exit 1
    fi
    
    echo ""
    echo "=============================================="
    
    if [ $checksum_result -eq 0 ]; then
        echo "✅ All checksums verified successfully!"
        echo ""
        echo "🔒 File integrity confirmed:"
        echo "   • All Docker images are intact"
        echo "   • No corruption detected"
        echo "   • Safe to proceed with loading"
        echo ""
        echo "Next step: Run ./load-images-updated.sh"
    else
        echo "❌ Checksum verification failed!"
        echo ""
        echo "⚠️  This means:"
        echo "   • One or more files may be corrupted"
        echo "   • Files may have been modified"
        echo "   • Download may be incomplete"
        echo ""
        echo "🔧 Recommended actions:"
        echo "   1. Re-download the corrupted files"
        echo "   2. Check available disk space"
        echo "   3. Verify network connection stability"
        exit 1
    fi
else
    echo "❌ checksums-updated.sha256 file not found!"
    echo ""
    echo "⚠️  Cannot verify file integrity without checksums file."
    echo "Please ensure you have the complete package."
    exit 1
fi 