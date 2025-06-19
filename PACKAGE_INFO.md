# IPSW Symbol Server - Complete Project Package

## Package Information
- **File**: `ipsw-symbol-server-project.zip`
- **Size**: 468MB
- **Version**: v1.1.0
- **Date**: June 19, 2025

## What's Included

### ✅ **Complete Source Code**
- All Python scripts and modules
- Web UI templates and static files
- Docker configuration files
- Database initialization scripts
- Configuration files

### ✅ **Device Database**
- Complete AppleDB repository (240+ devices)
- Device mapping manager with offline support
- Cached device information (484KB)

### ✅ **Kernel Signatures**
- 104,214 lines of kernel symbols
- iOS versions 18.5 through 25.0
- Multiple device support

### ✅ **CLI Tool**
- Beautiful terminal interface
- Rich formatting and colors
- Export capabilities
- Cross-platform support

### ✅ **Documentation**
- Installation guides
- Usage examples
- CLI documentation
- API endpoints

## What's NOT Included

### ❌ **Large Files Excluded**
- `.ipsw` files (can be GBs in size)
- Virtual environments (`venv`, `venv-webui`)
- Python cache files (`__pycache__`)
- Git history (`.git`)
- Node modules
- Downloaded IPSW cache files

### ❌ **Runtime Generated**
- Docker containers (will be built on deployment)
- Database data (will be created on first run)
- User uploads (created during usage)

## Quick Deployment

1. **Extract the zip file**
2. **Navigate to directory**: `cd ipsw-symbol-server/`
3. **Run deployment**: `docker-compose --profile regular up -d`

## Features

- **Web UI**: Modern interface with animations and responsive design
- **API Server**: RESTful API for IPS file processing
- **Symbol Server**: Advanced symbol resolution
- **PostgreSQL**: Persistent data storage
- **MinIO**: S3-compatible object storage
- **Nginx**: Reverse proxy and load balancing
- **CLI Tool**: Terminal-based file processing

## Services Included

1. **ipsw-nginx** - Web server and reverse proxy
2. **ipsw-api-server** - Main API service
3. **ipsw-symbol-server** - Symbol processing service
4. **ipsw-postgres** - Database server
5. **ipsw-minio** - Object storage server

## System Requirements

- Docker & Docker Compose
- 4GB+ RAM recommended
- 10GB+ disk space for operation
- Network access for initial setup

## Support

- Complete English interface (Hebrew removed)
- Offline device mapping support
- Cross-platform compatibility
- Professional UI/UX design

---

**Note**: This package contains the complete, working IPSW Symbol Server project ready for deployment in any environment. 