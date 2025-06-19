# 🔒 IPSW Symbol Server - Airgap Deployment Guide

Comprehensive deployment guide for air-gapped networks

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Building Images](#building-images)
- [Transfer to Airgap Network](#transfer-to-airgap-network)
- [Airgap Network Deployment](#airgap-network-deployment)
- [External S3 Configuration](#external-s3-configuration)
- [Troubleshooting](#troubleshooting)

## 🎯 Prerequisites

### On Source System (with Internet):
- Docker & Docker Compose
- Git access to repository
- 10GB free space for image building

### On Airgap Network:
- Docker & Docker Compose  
- PostgreSQL-compatible database (or Docker embedded)
- S3-compatible storage (MinIO/Ceph/AWS S3/etc.)
- 50GB+ free space for cache and IPSW files

## 🔨 Building Images

### Step 1: Prepare Code
```bash
# On system with internet access
git clone <repository-url>
cd ipsw-symbol-server

# Ensure system works
docker-compose --profile full up -d
# Test functionality
```

### Step 2: Build Airgap Images
```bash
# Build all required Docker images
./scripts/build-airgap-images.sh

# This will create:
# - localhost:5000/ipsw-symbol-server:latest
# - localhost:5000/ipsw-api-server:latest  
# - localhost:5000/ipsw-nginx:latest
```

### Step 3: Export Images
```bash
# Export all images to tar files
docker save localhost:5000/ipsw-symbol-server:latest > ipsw-symbol-server.tar
docker save localhost:5000/ipsw-api-server:latest > ipsw-api-server.tar
docker save localhost:5000/ipsw-nginx:latest > ipsw-nginx.tar
docker save postgres:15 > postgres.tar
docker save minio/minio:latest > minio.tar

# Create transfer package
tar czf ipsw-airgap-package.tar.gz \
  *.tar \
  docker-compose.yml \
  scripts/deploy-airgap.sh \
  config/env.airgap \
  postgres/init-symbols-db.sql \
  AIRGAP_DEPLOYMENT.md
```

## 📦 Transfer to Airgap Network

### Transfer Methods:
1. **Physical Media**: USB drive, external HDD
2. **One-way Transfer**: Secure file transfer tools
3. **Approved Network Transfer**: If permitted by policy

### Transfer Package Contents:
```
ipsw-airgap-package.tar.gz
├── ipsw-symbol-server.tar      # Main symbolication service
├── ipsw-api-server.tar         # API and web interface
├── ipsw-nginx.tar              # Reverse proxy
├── postgres.tar                # Database
├── minio.tar                   # S3-compatible storage
├── docker-compose.yml          # Deployment configuration
├── scripts/deploy-airgap.sh    # Deployment script
├── config/env.airgap           # Environment template
├── postgres/init-symbols-db.sql # Database schema
└── AIRGAP_DEPLOYMENT.md        # This guide
```

## 🚀 Airgap Network Deployment

> **IMPORTANT: In airgap/offline mode, all dependencies (AppleDB, symbolicator, CLI, IPSW, etc.) must be provided locally. Do not run any internet download commands.**

### Step 1: Extract and Load Images
```bash
# On airgap system
tar xzf ipsw-airgap-package.tar.gz
cd ipsw-airgap-package

# Load Docker images
docker load < ipsw-symbol-server.tar
docker load < ipsw-api-server.tar
docker load < ipsw-nginx.tar
docker load < postgres.tar
docker load < minio.tar
```

### Step 2: Configure Environment
```bash
# Copy environment template
cp config/env.airgap .env

# Edit configuration for your environment
nano .env
```

### Step 3: Deploy Services
```bash
# Run deployment script
chmod +x scripts/deploy-airgap.sh
./scripts/deploy-airgap.sh

# Or deploy manually
docker-compose --profile airgap up -d
```

### Step 4: Verify Deployment
```bash
# Check all services are running
docker-compose --profile airgap ps

# Test web interface
curl http://localhost:80/health

# Test API
curl http://localhost:8000/api/status
```

## 🗄️ External S3 Configuration

### Option 1: Use Embedded MinIO (Default)
```bash
# Uses internal MinIO container
S3_ENDPOINT=http://minio:9000
```

### Option 2: External S3 Service
```bash
# Edit .env file
AIRGAP_S3_ENDPOINT=https://s3.internal.company.com
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=ipsw-symbols
S3_USE_SSL=true
```

### Upload IPSW Files to S3:
```bash
# Upload IPSW files to S3 bucket
aws s3 cp iPhone15,2_18.5_22F76_Restore.ipsw s3://ipsw-symbols/
```

## 🔧 Troubleshooting

### Common Issues:

#### 1. Services Not Starting
```bash
# Check logs
docker-compose --profile airgap logs symbol-server
docker-compose --profile airgap logs api-server

# Check system resources
docker system df
```

#### 2. Database Connection Issues
```bash
# Restart PostgreSQL
docker-compose --profile airgap restart postgres

# Check database
docker exec ipsw-postgres psql -U symbols_user -d symbols -c "\dt"
```

#### 3. S3 Connection Issues
```bash
# Test S3 connectivity
docker exec ipsw-api-server curl -f http://minio:9000/minio/health/live

# Check MinIO logs
docker-compose --profile airgap logs minio
```

#### 4. Symbol Server Issues
```bash
# Test symbol server health
curl http://localhost:3993/health

# Check symbol server logs
docker-compose --profile airgap logs symbol-server
```

### Performance Tuning:
```bash
# Increase cache size (in .env)
CACHE_SIZE_GB=200

# Increase concurrent downloads
MAX_CONCURRENT_DOWNLOADS=5

# Adjust cleanup interval
CLEANUP_AFTER_HOURS=48
```

## 📊 Monitoring

### Health Checks:
```bash
# Web Interface
curl http://localhost:80/health

# API Server
curl http://localhost:8000/api/status

# Symbol Server
curl http://localhost:3993/health

# Database
docker exec ipsw-postgres pg_isready -U symbols_user -d symbols

# MinIO
curl http://localhost:9000/minio/health/live
```

### Log Monitoring:
```bash
# Follow all logs
docker-compose --profile airgap logs -f

# Follow specific service
docker-compose --profile airgap logs -f symbol-server
```

## 🔐 Security Considerations

1. **Network Isolation**: Ensure no internet connectivity
2. **Access Control**: Restrict access to web interface
3. **Data Encryption**: Use HTTPS in production
4. **Regular Updates**: Plan for security update process
5. **Backup Strategy**: Regular database and configuration backups

## 📋 Maintenance

### Regular Tasks:
- Clean old cache files
- Monitor disk space
- Backup database
- Update IPSW files as needed

### Updating Images:
1. Build new images on connected system
2. Export and transfer new images
3. Load and redeploy on airgap system

---

For additional support or questions, refer to the main project documentation or contact your system administrator. 