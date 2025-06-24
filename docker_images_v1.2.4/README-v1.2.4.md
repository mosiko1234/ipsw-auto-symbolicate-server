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
