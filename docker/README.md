# Docker Images

This directory contains all Dockerfile definitions for the IPSW Auto-Symbolicate Server.

## 🐳 Available Images

### Dockerfile.symbol-server
- **Purpose**: Core symbolication engine with S3 support
- **Base**: Ubuntu 22.04
- **Features**: IPSW tool, S3FS, symbol processing
- **Port**: 3993

### Dockerfile.api
- **Purpose**: REST API server with auto-symbolication
- **Base**: Python 3.11
- **Features**: FastAPI, PostgreSQL integration, auto-scanning
- **Port**: 8000

### Dockerfile.webui
- **Purpose**: Web interface for crash file upload
- **Base**: Python 3.11
- **Features**: Flask, drag-and-drop UI, result display
- **Port**: 5001

### Dockerfile.nginx
- **Purpose**: Reverse proxy and documentation server
- **Base**: Nginx Alpine
- **Features**: Load balancing, health monitoring, docs
- **Port**: 80

## 🏗️ Build Process

All images are built automatically by:
- `docker-compose.yml` (regular deployment)
- `scripts/build-images-for-airgap.sh` (airgap preparation)

## 📋 Dependencies

All Dockerfiles are optimized for:
- ✅ Multi-stage builds where applicable
- ✅ Minimal base images
- ✅ Security hardening
- ✅ Layer caching optimization
- ✅ Health checks included 