# IPSW Auto-Symbolicate Server - Deployment Guide

## 🚀 Overview

This system provides enterprise-ready iOS crash symbolication with support for both **regular** and **airgap** deployments using a single unified Docker Compose configuration.

## 📋 Deployment Types

### 1. Regular Deployment
- **Use case**: Development teams with internet access
- **Features**: Builds Docker images, includes internal MinIO S3
- **Command**: `./deploy-regular.sh`

### 2. Airgap Deployment  
- **Use case**: Secure environments without internet access
- **Features**: Uses pre-built images, connects to external S3
- **Command**: `./deploy-airgap.sh`

## 🛠️ Regular Deployment

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM
- 50GB+ disk space

### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/mosiko1234/ipsw-auto-symbolicate-server.git
cd ipsw-auto-symbolicate-server

# 2. Configure environment (optional - has defaults)
cp config/env.regular .env
# Edit .env if needed

# 3. Deploy
./deploy-regular.sh
```

### Services Available
- **Web UI**: http://localhost:5001
- **API**: http://localhost:8000  
- **Symbol Server**: http://localhost:3993
- **MinIO Console**: http://localhost:9001
- **Main Portal**: http://localhost (Nginx)

### Configuration (env.regular)
```bash
# Service Ports
WEB_UI_PORT=5001
API_PORT=8000
SYMBOL_PORT=3993
NGINX_PORT=80

# Internal MinIO S3
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=ipsw

# Performance
CACHE_SIZE_GB=100
CLEANUP_AFTER_HOURS=24
MAX_CONCURRENT_DOWNLOADS=3
```

## 🔒 Airgap Deployment

> **IMPORTANT: In airgap/offline mode, all dependencies (AppleDB, symbolicator, CLI, IPSW, etc.) are pre-included in Docker images. No internet access required during operation.**

### Complete Offline Features
- **AppleDB Integration**: Complete device mapping database (2000+ devices) bundled in images
- **Device Intelligence**: Automatic translation (iPhone 14 Pro → iPhone15,2) without external API calls
- **IPSW CLI Bundled**: Pre-installed ipsw binary for symbol extraction
- **Zero External Dependencies**: No git clone, curl, wget, or API calls during runtime
- **Smart Auto-Scan**: Automatic IPSW detection and symbol extraction based on device mapping

### Airgap Deployment Steps

1. **Prepare Environment** (one-time setup in connected environment):
```bash
# Clone repository and build images with all dependencies
git clone https://github.com/mosiko1234/ipsw-auto-symbolicate-server.git
cd ipsw-auto-symbolicate-server

# Download all required dependencies (AppleDB, symbolicator, IPSW CLI)
./scripts/prepare-airgap.sh

# Build images with bundled dependencies
docker-compose --profile airgap build
```

2. **Create Airgap Package**:
```bash
# Export Docker images for transfer
docker save -o ipsw-symbol-server-v1.2.0.tar \
  $(docker-compose --profile airgap config | grep 'image:' | awk '{print $2}')

# Package everything for transfer
tar -czf ipsw-airgap-v1.2.0.tar.gz \
  ipsw-symbol-server-v1.2.0.tar \
  docker-compose.yml \
  data/ \
  README.md \
  DEPLOYMENT_GUIDE.md
```

3. **Deploy in Airgap Environment**:
```bash
# Transfer and extract package
tar -xzf ipsw-airgap-v1.2.0.tar.gz
cd ipsw-auto-symbolicate-server

# Load Docker images
docker load -i ipsw-symbol-server-v1.2.0.tar

# Start airgap deployment
docker-compose --profile airgap up -d
```

4. **Verify Deployment**:
```bash
# Check all services are running
docker-compose --profile airgap ps

# Test device mapping capability
curl "http://localhost:3993/v1/ipsws"

# Test system health
curl "http://localhost:8000/health"
```

### Device Mapping in Airgap Mode

The system includes complete AppleDB database with support for:
- **All iPhone models**: iPhone 3G through iPhone 15 series
- **All iPad models**: Original iPad through iPad Pro M2
- **Apple Watch**: All generations and sizes
- **Apple TV**: All generations including 4K models
- **iPod**: All iPod touch generations

Example device mappings included:
```
iPhone 14 Pro → iPhone15,2
iPhone 14 Pro Max → iPhone15,3
iPad Pro 12.9-inch (6th generation) → iPad14,5
Apple Watch Series 9 → Watch6,18
Apple TV 4K (3rd generation) → AppleTV11,1
```

### Upload IPSW Files

1. **Access MinIO Console**: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`

2. **Create/Access ipsw bucket** (auto-created on startup)

3. **Upload IPSW files** with proper naming:
```
iPhone15,2_18.5_22F76_Restore.ipsw
iPad14,3_18.5_22F76_Restore.ipsw
```

4. **Test Auto-Scan**:
```bash
# System will automatically map device names and find matching IPSW
curl -X POST "http://localhost:3993/v1/auto-scan?device_model=iPhone%2014%20Pro&ios_version=18.5&build_number=22F76"
```

### Expected Results
- **Device Mapping**: "iPhone 14 Pro" automatically mapped to "iPhone15,2"
- **IPSW Detection**: System finds `iPhone15,2_18.5_22F76_Restore.ipsw`
- **Symbol Extraction**: ~21,000+ kernel symbols extracted and cached
- **Crash Symbolication**: Full symbolication capability enabled

## 🏗️ Architecture

### Docker Compose Profiles
The system uses Docker Compose profiles to support different deployment types:

- **`regular`**: Regular deployment with image building
- **`airgap`**: Airgap deployment with pre-built images
- **`full`**: Development/testing (includes MinIO)

### Services Overview

| Service | Regular | Airgap | Description |
|---------|---------|---------|-------------|
| PostgreSQL | ✅ | ✅ | Symbol database |
| Symbol Server | 🔨 Build | 📦 Pre-built | Core symbolication |
| API Server | 🔨 Build | 📦 Pre-built | REST API |
| Web UI | 🔨 Build | 📦 Pre-built | User interface |
| Nginx | 🔨 Build | 📦 Pre-built | Reverse proxy |
| MinIO S3 | ✅ | ❌ | Internal storage |

### Network Architecture
```
Internet/Internal Network
         │
    [Nginx:80] ─────────────────┐
         │                      │
    ┌────▼────┐            ┌────▼────┐
    │ Web UI  │            │   API   │
    │  :5001  │            │  :8000  │
    └─────────┘            └────┬────┘
                                │
                         ┌──────▼──────┐
                         │Symbol Server│
                         │    :3993    │
                         └──────┬──────┘
                                │
                      ┌─────────▼─────────┐
                      │   PostgreSQL     │
                      │     :5432        │
                      └──────────────────┘
```

## 🔧 Management Commands

### Regular Deployment
```bash
# Start services
./deploy-regular.sh

# Stop services  
docker-compose --profile regular down

# View logs
docker-compose logs -f

# Update images
docker-compose --profile regular up -d --build
```

### Airgap Deployment
```bash
# Start services
./deploy-airgap.sh

# Stop services
docker-compose --profile airgap down

# Update images (requires new image archive)
# 1. Transfer new ipsw-images-{version}.tar
# 2. docker load -i ipsw-images-{version}.tar
# 3. ./deploy-airgap.sh
```

### Health Monitoring
```bash
# Check service health
docker-compose ps

# API health check
curl http://localhost:8000/health

# Symbol server health  
curl http://localhost:3993/health

# Web UI health
curl http://localhost:5001/
```

## 📊 Storage Management

### Auto-Cleanup Features
- **IPSW files**: Automatically deleted after symbol extraction
- **Cache management**: Configurable retention period
- **Space monitoring**: Built-in disk usage tracking

### Storage Endpoints
- **Disk usage**: `GET /v1/disk-usage`
- **Cleanup trigger**: `POST /v1/cleanup`
- **Auto-scan**: `POST /v1/auto-scan`

## 🔍 Troubleshooting

### Common Issues

**Services not starting**
```bash
# Check logs
docker-compose logs

# Verify environment
cat .env

# Check disk space
df -h
```

**Airgap image issues**
```bash
# Verify images exist
docker images | grep ipsw

# Check registry connectivity
docker pull ${AIRGAP_REGISTRY}/ipsw-symbol-server:latest
```

**S3 connectivity**
```bash
# Test S3 endpoint
curl ${S3_ENDPOINT}/health

# Check bucket access
curl -X HEAD ${S3_ENDPOINT}/${S3_BUCKET}
```

### Performance Optimization

**Memory settings**
- Increase `CACHE_SIZE_GB` for better performance
- Monitor with `docker stats`

**Concurrent downloads**
- Adjust `MAX_CONCURRENT_DOWNLOADS` based on bandwidth
- Monitor with `/v1/disk-usage` endpoint

## 🛡️ Security Considerations

### Airgap Environment
- No internet access required after deployment
- All dependencies included in pre-built images
- Configurable internal S3 endpoints

### Network Security  
- All services communicate internally
- Nginx provides single external entry point
- Configurable SSL/TLS termination

### Access Control
- API authentication (if configured)
- S3 access key management
- Database credential isolation

## 📈 Monitoring & Metrics

### Built-in Endpoints
- **Health**: `/health` (all services)
- **Metrics**: `/v1/stats`
- **Status**: `/v1/system-status`

### Log Aggregation
```bash
# Centralized logging
docker-compose logs -f api-server symbol-server

# Specific service logs
docker logs ipsw-api-server
docker logs ipsw-symbol-server
```

## 🔄 Updates & Maintenance

### Regular Environment
```bash
# Pull latest code
git pull origin main

# Rebuild and update
./deploy-regular.sh
```

### Airgap Environment
```bash
# 1. Build new images in regular environment
./build-images-for-airgap.sh

# 2. Transfer to airgap
# Copy ipsw-images-{version}.tar

# 3. Update airgap deployment
docker load -i ipsw-images-{version}.tar
./deploy-airgap.sh
```

## 📞 Support

For issues and support:
1. Check logs: `docker-compose logs`
2. Verify configuration: `cat .env`  
3. Review this guide for troubleshooting steps
4. Open issue in repository

---

**Enterprise-ready iOS crash symbolication with full airgap support** 🚀 