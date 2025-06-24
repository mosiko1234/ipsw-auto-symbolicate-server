#!/bin/bash

# IPSW Symbol Server - Docker Images Export Script
# Version: v1.2.4 - Critical S3 Sync Fix (Clean Build)

set -e

echo "=============================================="
echo "IPSW Symbol Server - Docker Images Export"
echo "🎯 Version: v1.2.4 - Critical S3 Sync Fix"
echo "=============================================="
echo

# Create export directory
EXPORT_DIR="docker_images_v1.2.4"
echo "📁 Creating export directory: $EXPORT_DIR"
rm -rf "$EXPORT_DIR"  # Remove old version if exists
mkdir -p "$EXPORT_DIR"

# Function to export image with validation
export_image() {
    local image_name="$1"
    local tar_file="$2"
    local description="$3"
    
    echo "📦 Exporting $description..."
    echo "   Image: $image_name"
    echo "   Output: $tar_file"
    
    # Check if image exists
    if ! docker image inspect "$image_name" >/dev/null 2>&1; then
        echo "❌ ERROR: Image $image_name not found!"
        echo "   Please build the image first with:"
        echo "   docker-compose --profile regular build"
        return 1
    fi
    
    # Export the image
    if docker save "$image_name" -o "$EXPORT_DIR/$tar_file"; then
        echo "✅ $description exported successfully"
        
        # Get image size
        local size=$(du -h "$EXPORT_DIR/$tar_file" | cut -f1)
        echo "   Size: $size"
        echo
    else
        echo "❌ ERROR: Failed to export $description"
        return 1
    fi
}

echo "🚀 Starting Docker images export process..."
echo

# Check what images we have
echo "🔍 Available images:"
docker images | grep -E "(ipsw-symbol-server|minio|postgres)" | head -10
echo

echo "📋 Exporting images for IPSW Symbol Server v1.2.4:"
echo

# Export all images with fresh builds
export_image "ipsw-symbol-server-api-server" "ipsw-api-server-v1.2.4.tar" "API Server (with S3 File Watcher)"
export_image "ipsw-symbol-server-symbol-server" "ipsw-symbol-server-v1.2.4.tar" "Symbol Server (with persistent S3Manager)"
export_image "ipsw-symbol-server-nginx" "ipsw-nginx-v1.2.4.tar" "Nginx Reverse Proxy"
export_image "minio/minio:latest" "minio-v1.2.4.tar" "MinIO S3 Storage"
export_image "postgres:15" "postgres-v1.2.4.tar" "PostgreSQL Database"

echo "✅ All Docker images exported successfully!"
echo

# Create checksums
echo "🔐 Generating checksums..."
cd "$EXPORT_DIR"
sha256sum *.tar > checksums-v1.2.4.sha256
echo "✅ Checksums generated: checksums-v1.2.4.sha256"
echo

# Create load script
echo "📝 Creating load script..."
cat > load-images-v1.2.4.sh << 'EOF'
#!/bin/bash

# IPSW Symbol Server - Docker Images Loader
# Version: v1.2.4 - Critical S3 Sync Fix
# This script loads all required Docker images for the IPSW Symbol Server

set -e

echo "=============================================="
echo "IPSW Symbol Server - Loading Images v1.2.4"
echo "🐛 Critical S3 Sync Fix + Enhanced Export"
echo "=============================================="
echo

# Function to load image with validation
load_image() {
    local tar_file="$1"
    local description="$2"
    
    if [ ! -f "$tar_file" ]; then
        echo "❌ ERROR: $tar_file not found!"
        return 1
    fi
    
    echo "📦 Loading $description..."
    if docker load -i "$tar_file"; then
        echo "✅ $description loaded successfully"
        echo
    else
        echo "❌ ERROR: Failed to load $description"
        return 1
    fi
}

echo "🚀 Starting Docker image loading process..."
echo

# Load all images
load_image "ipsw-api-server-v1.2.4.tar" "API Server (with S3 File Watcher)"
load_image "ipsw-symbol-server-v1.2.4.tar" "Symbol Server (with persistent S3Manager)"
load_image "ipsw-nginx-v1.2.4.tar" "Nginx Reverse Proxy"
load_image "minio-v1.2.4.tar" "MinIO S3 Storage"
load_image "postgres-v1.2.4.tar" "PostgreSQL Database"

echo "✅ All Docker images loaded successfully!"
echo
echo "🎯 New Features in v1.2.4:"
echo "  🐛 CRITICAL FIX: Symbol Server S3 Synchronization"
echo "  🔧 Persistent S3Manager eliminates manual restarts"
echo "  ⚡ Enhanced cache refresh functionality"
echo "  🚀 True end-to-end automation"
echo "  💾 Enhanced CLI with export options"
echo
echo "🚀 Ready to deploy! Run:"
echo "   docker-compose --profile regular up -d"
echo
echo "📖 For more information, see README.md"
echo
EOF

chmod +x load-images-v1.2.4.sh
echo "✅ Load script created: load-images-v1.2.4.sh"
echo

# Create verification script
echo "🔍 Creating verification script..."
cat > verify-checksums-v1.2.4.sh << 'EOF'
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
EOF

chmod +x verify-checksums-v1.2.4.sh
echo "✅ Verification script created: verify-checksums-v1.2.4.sh"
echo

# Create README
echo "📖 Creating README..."
cat > README-v1.2.4.md << 'EOF'
# IPSW Symbol Server - Docker Images v1.2.4

## 🐛 Critical S3 Sync Fix + Enhanced Export (Clean Build)

This package contains all Docker images for IPSW Symbol Server v1.2.4 with the critical S3 synchronization fix.

### 🎯 What's Fixed in v1.2.4

- **🐛 CRITICAL FIX**: Symbol Server now automatically detects new IPSW files from S3
- **🔧 Persistent S3Manager**: Eliminates manual container restart requirements
- **⚡ Enhanced Cache Refresh**: Fixed refresh-cache endpoint functionality
- **🚀 True End-to-End Automation**: System works as originally intended
- **💾 Enhanced CLI**: New export options for symbolication results

### 📦 Included Images (Clean Build)

- `ipsw-api-server-v1.2.4.tar` - API Server with S3 File Watcher
- `ipsw-symbol-server-v1.2.4.tar` - Symbol Server with persistent S3Manager
- `ipsw-nginx-v1.2.4.tar` - Nginx Reverse Proxy
- `minio-v1.2.4.tar` - MinIO S3 Storage
- `postgres-v1.2.4.tar` - PostgreSQL Database

### 🚀 Quick Start

1. **Verify integrity**:
   ```bash
   ./verify-checksums-v1.2.4.sh
   ```

2. **Load images**:
   ```bash
   ./load-images-v1.2.4.sh
   ```

3. **Deploy**:
   ```bash
   docker-compose --profile regular up -d
   ```

### 📈 Workflow Now Fully Automated

```bash
# Before v1.2.4 (required manual intervention):
aws s3 cp newfile.ipsw s3://ipsw/                    # Upload
# Manual: docker-compose restart symbol-server       # ❌ Required
# Manual: curl -X POST ".../refresh-cache"           # ❌ Required  
# Manual: curl -X POST ".../auto-scan"               # ❌ Required

# After v1.2.4 (fully automated):
aws s3 cp newfile.ipsw s3://ipsw/                    # Upload
# Wait 5 minutes - File Watcher detects automatically
# Symbol Server auto-refreshes cache
# Auto-scan runs automatically  
# Symbols generated automatically
ipsw-cli newcrash.ips                                # ✅ Just works!
```

### 💾 Enhanced CLI Export Options

```bash
# New export features in ipsw-cli
ipsw-cli crash.ips --export                  # Auto-save to crash_symbolicated.json
ipsw-cli crash.ips --export-symbols          # Save only symbols
ipsw-cli crash.ips --export-text             # Save symbolicated text
ipsw-cli crash.ips --export-all              # Export all formats
```

### 🔒 Security

All images are signed with SHA256 checksums. Always verify before deployment:

```bash
sha256sum -c checksums-v1.2.4.sha256
```

### 📋 System Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 100GB disk space recommended

### 🆘 Support

For issues or questions:
- Check the main README.md
- Review DEPLOYMENT_GUIDE.md
- See troubleshooting in README_AUTO_DETECTION.md

---

**IPSW Symbol Server v1.2.4** - Now truly automated end-to-end! 🚀
EOF

echo "✅ README created: README-v1.2.4.md"
echo

# Go back to parent directory
cd ..

# Show summary
echo "📊 Export Summary:"
echo "=================="
echo "📁 Export directory: $EXPORT_DIR"
echo "📦 Total images: 5"
echo "🔐 Checksums: ✅"
echo "📝 Scripts: ✅"
echo "📖 Documentation: ✅"
echo

# Show directory contents
echo "📋 Package contents:"
ls -lh "$EXPORT_DIR"
echo

# Show total size
echo "💾 Total package size:"
du -sh "$EXPORT_DIR"
echo

echo "🎉 Docker images package v1.2.4 created successfully!"
echo
echo "🚀 Ready for deployment or distribution!"
echo "📁 All files are in: $EXPORT_DIR/"
echo
echo "📖 Next steps:"
echo "   1. Test: cd $EXPORT_DIR && ./verify-checksums-v1.2.4.sh"
echo "   2. Deploy: ./load-images-v1.2.4.sh"
echo "   3. Run: docker-compose --profile regular up -d"