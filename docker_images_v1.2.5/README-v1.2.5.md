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
