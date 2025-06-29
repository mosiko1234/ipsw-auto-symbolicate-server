#!/bin/bash
# 🧪 IPSW Symbol Server v3.1.0 - Deployment Package Test
# Quick verification script for the deployment package

set -e

PACKAGE_FILE="ipsw-symbol-server-v3.1.0-deployment.tar.gz"
CHECKSUM_FILE="ipsw-symbol-server-v3.1.0-deployment.tar.gz.sha256"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function log_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

function log_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

function log_info() {
    echo -e "${BLUE}ℹ️ ${1}${NC}"
}

function log_warning() {
    echo -e "${YELLOW}⚠️ ${1}${NC}"
}

echo "🧪 IPSW Symbol Server v3.1.0 - Package Verification"
echo "=================================================="

# Check if package exists
if [ ! -f "$PACKAGE_FILE" ]; then
    log_error "Package file $PACKAGE_FILE not found"
    exit 1
fi

if [ ! -f "$CHECKSUM_FILE" ]; then
    log_error "Checksum file $CHECKSUM_FILE not found"
    exit 1
fi

log_success "Package files found"

# Verify checksum
echo ""
log_info "Verifying package integrity..."
if sha256sum -c "$CHECKSUM_FILE" >/dev/null 2>&1; then
    log_success "Package integrity verified"
else
    log_error "Package integrity verification failed!"
    exit 1
fi

# Show package info
echo ""
log_info "Package Information:"
echo "   File: $PACKAGE_FILE"
echo "   Size: $(ls -lah $PACKAGE_FILE | awk '{print $5}')"
echo "   Date: $(stat -c %y $PACKAGE_FILE 2>/dev/null || stat -f %Sm $PACKAGE_FILE)"

# Check package contents (without extracting)
echo ""
log_info "Package Contents Preview:"
tar -tzf "$PACKAGE_FILE" | head -20
echo "   ... and $(expr $(tar -tzf "$PACKAGE_FILE" | wc -l) - 20) more files"

# Check for key components
echo ""
log_info "Verifying key components..."

if tar -tzf "$PACKAGE_FILE" | grep -q "deploy.sh"; then
    log_success "Deployment script included"
else
    log_error "Deployment script missing"
fi

if tar -tzf "$PACKAGE_FILE" | grep -q "cli-tools/ipsw-dev-cli"; then
    log_success "CLI tools included"
else
    log_error "CLI tools missing"
fi

if tar -tzf "$PACKAGE_FILE" | grep -q "docker-images/.*\.tar\.gz"; then
    log_success "Docker images included"
else
    log_error "Docker images missing"
fi

if tar -tzf "$PACKAGE_FILE" | grep -q "docs/.*\.md"; then
    log_success "Documentation included"
else
    log_error "Documentation missing"
fi

if tar -tzf "$PACKAGE_FILE" | grep -q "simple_app.py"; then
    log_success "Main application included"
else
    log_error "Main application missing"
fi

echo ""
log_info "Docker Images Check:"
echo "$(tar -tzf "$PACKAGE_FILE" | grep "docker-images/" | while read line; do
    size=$(tar -tzf "$PACKAGE_FILE" --list --verbose | grep "$line" | awk '{print $3}' 2>/dev/null || echo "unknown")
    echo "   $(basename "$line"): $size bytes"
done)"

echo ""
log_info "CLI Tools Check:"
echo "$(tar -tzf "$PACKAGE_FILE" | grep "cli-tools/" | grep -E "\.(py|sh)$|ipsw-dev-cli$" | while read line; do
    echo "   $(basename "$line")"
done)"

echo ""
log_success "Package verification complete!"
echo ""
log_info "Deployment Instructions:"
echo "   1. Transfer: scp $PACKAGE_FILE user@server:/path/"
echo "   2. Extract: tar -xzf $PACKAGE_FILE"
echo "   3. Deploy: cd ipsw-symbol-server-v3.1.0-deployment && ./deploy.sh"
echo ""
log_info "Quick Test (local):"
echo "   tar -xzf $PACKAGE_FILE"
echo "   cd ipsw-symbol-server-v3.1.0-deployment"
echo "   ./verify-deployment.sh"
