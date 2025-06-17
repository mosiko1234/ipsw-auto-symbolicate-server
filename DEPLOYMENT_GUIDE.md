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

### Prerequisites
- Docker (no internet access required after setup)
- Pre-built Docker images from regular environment
- External S3 storage

### Step 1: Prepare Images (in regular environment)
```bash
# 1. Configure airgap settings
cp config/env.airgap .env
# Edit registry and S3 settings

# 2. Build and push images
./build-images-for-airgap.sh
```

### Step 2: Transfer to Airgap Environment
```bash
# Option A: Registry transfer (if registry accessible)
# Images are already pushed to AIRGAP_REGISTRY

# Option B: Offline transfer
# 1. Copy ipsw-images-{version}.tar to airgap environment
# 2. Load images: docker load -i ipsw-images-{version}.tar
```

### Step 3: Deploy in Airgap
```bash
# 1. Configure airgap environment
cp config/env.airgap .env
# Update S3 and registry settings

# 2. Deploy
./deploy-airgap.sh
```

### Configuration (env.airgap)
```bash
# Airgap Registry
AIRGAP_REGISTRY=your-registry.local:5000
VERSION=latest

# External S3 Configuration
AIRGAP_S3_ENDPOINT=http://s3.internal.local:9000
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET=ipsw
```

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