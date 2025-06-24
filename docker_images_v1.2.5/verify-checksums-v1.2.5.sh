#!/bin/bash

# IPSW Symbol Server v1.2.5 - Verify Checksums

VERSION="v1.2.5"
CHECKSUMS_FILE="checksums-${VERSION}.sha256"

echo "🔐 Verifying IPSW Symbol Server ${VERSION} checksums..."

if [ ! -f "${CHECKSUMS_FILE}" ]; then
    echo "❌ Checksums file not found: ${CHECKSUMS_FILE}"
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c "${CHECKSUMS_FILE}"
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 -c "${CHECKSUMS_FILE}"
else
    echo "❌ Neither sha256sum nor shasum found"
    echo "Please install one of these tools to verify checksums"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "✅ All checksums verified successfully!"
else
    echo "❌ Checksum verification failed!"
    echo "The files may be corrupted or tampered with"
    exit 1
fi
