#!/bin/bash

# IPSW Symbol Server v1.2.5 - Docker Images Export
# Includes large file support and streaming upload improvements

VERSION="v1.2.5"
PACKAGE_NAME="docker_images_${VERSION}"
EXPORT_DIR="${PACKAGE_NAME}"

echo "🚀 IPSW Symbol Server - Docker Images Export ${VERSION}"
echo "======================================================"

# Create export directory
echo "📁 Creating export directory..."
rm -rf "${EXPORT_DIR}"
mkdir -p "${EXPORT_DIR}"

# Export Docker images
echo "💾 Exporting Docker images..."

# Get the actual running container images
SYMBOL_SERVER_IMAGE=$(docker ps --format "table {{.Image}}" | grep symbol-server | head -1)
API_SERVER_IMAGE=$(docker ps --format "table {{.Image}}" | grep api-server | head -1)
NGINX_IMAGE=$(docker ps --format "table {{.Image}}" | grep nginx | head -1)

if [ -z "$SYMBOL_SERVER_IMAGE" ]; then
    SYMBOL_SERVER_IMAGE="ipsw-symbol-server-symbol-server:latest"
fi

if [ -z "$API_SERVER_IMAGE" ]; then
    API_SERVER_IMAGE="ipsw-symbol-server-api-server:latest"  
fi

if [ -z "$NGINX_IMAGE" ]; then
    NGINX_IMAGE="ipsw-symbol-server-nginx:latest"
fi

echo "  • Symbol Server: ${SYMBOL_SERVER_IMAGE}"
echo "  • API Server: ${API_SERVER_IMAGE}"  
echo "  • Nginx: ${NGINX_IMAGE}"
echo "  • PostgreSQL: postgres:15"
echo "  • MinIO: minio/minio:latest"

# Export all images to tar files
docker save -o "${EXPORT_DIR}/ipsw-symbol-server-${VERSION}.tar" \
    "${SYMBOL_SERVER_IMAGE}" \
    "${API_SERVER_IMAGE}" \
    "${NGINX_IMAGE}" \
    postgres:15 \
    minio/minio:latest

if [ $? -eq 0 ]; then
    echo "✅ Docker images exported successfully"
else
    echo "❌ Failed to export Docker images"
    exit 1
fi

# Create loading script
echo "📝 Creating load script..."
cat > "${EXPORT_DIR}/load-images-${VERSION}.sh" << 'EOF'
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
EOF

chmod +x "${EXPORT_DIR}/load-images-${VERSION}.sh"

# Create verification script
echo "🔐 Creating verification script..."
cat > "${EXPORT_DIR}/verify-checksums-${VERSION}.sh" << 'EOF'
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
EOF

chmod +x "${EXPORT_DIR}/verify-checksums-${VERSION}.sh"

# Generate checksums
echo "🔐 Generating checksums..."
cd "${EXPORT_DIR}"

# Check if there are any tar files
if ls *.tar 1> /dev/null 2>&1; then
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum *.tar *.sh > "checksums-${VERSION}.sha256"
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 *.tar *.sh > "checksums-${VERSION}.sha256"
    else
        echo "⚠️  Warning: No SHA256 tool found, skipping checksum generation"
    fi
else
    echo "⚠️  Warning: No tar files found, skipping checksum generation"
fi

cd ..

# Create README
echo "📖 Creating README..."
cat > "${EXPORT_DIR}/README-${VERSION}.md" << 'EOFREADME'
# IPSW Symbol Server v1.2.5 - Docker Images Package

## 🆕 What's New in v1.2.5

### Large File Support
- **Streaming Upload**: Support for IPSW files up to 15GB
- **Automatic Detection**: CLI automatically chooses best upload method
- **Smart Endpoints**: Files >500MB use streaming, smaller files use direct upload
- **Enhanced Performance**: 8MB chunk streaming with progress tracking

### Improved CLI
- **Size-based routing**: Automatically selects /local-ipsw-symbolicate-stream for large files
- **Better error messages**: Clear guidance for large file handling
- **Extended timeouts**: Up to 60 minutes for large file processing
- **Progress indicators**: Real-time upload progress for large files

### MinIO Integration  
- **Web Console**: Easy upload via http://localhost:9001
- **Bucket Management**: Automatic ipsw bucket creation
- **File Detection**: Auto-discovery of uploaded IPSW files
- **Cache Management**: Improved refresh and cleanup

## 📦 Package Contents

- `ipsw-symbol-server-v1.2.5.tar` - Docker images (5 services)
- `load-images-v1.2.5.sh` - Automated loading script
- `verify-checksums-v1.2.5.sh` - Integrity verification
- `checksums-v1.2.5.sha256` - SHA256 checksums
- `README-v1.2.5.md` - This documentation

## 🚀 Quick Installation

### Step 1: Load Images
```bash
chmod +x load-images-v1.2.5.sh
./load-images-v1.2.5.sh
```

### Step 2: Deploy
```bash
# Regular deployment (with internet)
docker-compose --profile regular up -d

# Airgap deployment (offline)
docker-compose --profile airgap up -d
```

### Step 3: Verify
```bash
curl http://localhost/health
```

## 💡 Large File Usage

### Method 1: Direct CLI (files ≤500MB)
```bash
ipsw-cli --local-ipsw small_firmware.ipsw crash.ips
```

### Method 2: MinIO + CLI (files >500MB)
```bash
# 1. Open MinIO Console
open http://localhost:9001

# 2. Login: minioadmin / minioadmin

# 3. Upload IPSW to 'ipsw' bucket

# 4. Run symbolication
ipsw-cli crash.ips
```

## 🎯 Use Cases

- **Development Teams**: Local IPSW files without S3 setup
- **Large Files**: iPhone/iPad IPSW files (5-15GB)
- **Airgap Networks**: Complete offline symbolication
- **Enterprise**: Secure internal deployments

## 📊 Performance

- **Small files** (<500MB): Direct upload ~2-5 minutes
- **Large files** (5-15GB): Streaming upload ~10-30 minutes
- **Symbolication**: ~30 seconds for kernel extraction
- **Memory usage**: <2GB RAM for 15GB IPSW files

## 🔧 Technical Details

### Endpoints
- `/local-ipsw-symbolicate` - Standard upload (≤500MB)
- `/local-ipsw-symbolicate-stream` - Streaming upload (>500MB)
- `/symbolicate` - Crash file only (uses S3 IPSW)

### File Limits
- **Direct upload**: 500MB (system limit)
- **Streaming upload**: 15GB (tested)
- **MinIO upload**: Unlimited via web console

### Services
- **API Server**: FastAPI with async file handling
- **Symbol Server**: IPSW extraction and symbolication
- **MinIO**: S3-compatible storage
- **PostgreSQL**: Symbol database
- **Nginx**: Reverse proxy and load balancing

## 🛠️ Troubleshooting

### Large File Upload Fails
```bash
# Use MinIO Console instead
open http://localhost:9001
```

### CLI Connection Error
```bash
# Check server status
docker-compose ps
curl http://localhost:8000/health
```

### Memory Issues
```bash
# Monitor usage
docker stats

# Increase Docker memory if needed
```

## 📋 Version History

- **v1.2.5**: Large file support, streaming upload
- **v1.2.4**: Multi-device IPSW fixes  
- **v1.2.3**: Device mapping improvements
- **v1.2.2**: S3 optimization
- **v1.2.1**: Initial release

## 🆘 Support

For issues with large files:
1. Check file size: `ls -lh your-file.ipsw`
2. Use MinIO Console for files >500MB
3. Verify server health: `curl http://localhost/health`
4. Check Docker logs: `docker-compose logs`

---

**Built with ❤️ for iOS developers**
EOFREADME

# Calculate package size
PACKAGE_SIZE=$(du -sh "${EXPORT_DIR}" | cut -f1)

echo ""
echo "📊 Package Summary:"
echo "=================="
echo "  📁 Directory: ${EXPORT_DIR}"
echo "  📦 Package size: ${PACKAGE_SIZE}"
echo "  🐳 Docker images: 5 services"
echo "  🔐 Checksums: Generated"
echo "  📖 Documentation: Complete"
echo ""
echo "✅ Export completed successfully!"
echo ""
echo "🎯 What's new in v1.2.5:"
echo "  • Large IPSW file support (up to 15GB)"
echo "  • Streaming upload for files > 500MB"  
echo "  • Automatic endpoint selection in CLI"
echo "  • Improved error handling for large files"
echo "  • Enhanced MinIO integration"
echo ""
echo "📋 To deploy:"
echo "  cd ${EXPORT_DIR}"
echo "  ./load-images-${VERSION}.sh"
echo "  docker-compose --profile regular up -d"
echo ""
echo "💡 For network transfer:"
echo "  tar -czf ipsw-symbol-server-${VERSION}.tar.gz ${EXPORT_DIR}/"
</rewritten_file> 