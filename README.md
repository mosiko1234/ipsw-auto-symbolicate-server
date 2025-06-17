# 🍎 IPSW Symbol Server - Complete Production System

**Enterprise-grade iOS crash log symbolication system with auto-scanning, intelligent storage management, and comprehensive Web UI.**

## 🚀 Quick Start

```bash
# Start all services
./start-server.sh

# Access the system
open http://localhost
```

**Main Entry Point**: http://localhost

---

## 📋 Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Quick Deployment](#quick-deployment)
3. [System Components](#system-components)
4. [API Documentation](#api-documentation)
5. [Web Interface](#web-interface)
6. [Auto-Symbolication Features](#auto-symbolication-features)
7. [Storage Management](#storage-management)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)
11. [Development & Integration](#development--integration)

---

## 🎯 Overview & Architecture

### System Architecture

```
                    🌐 Nginx Reverse Proxy (Port 80)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    🌍 Web UI            📡 API Server        🔧 Symbol Server
    (Port 5001)          (Port 8000)         (Port 3993)
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    💾 PostgreSQL + S3 + Auto-Cleanup
```

### Core Features

- ✅ **Auto-Symbolication**: Automatically downloads and processes IPSW files
- ✅ **25,000+ Kernel Symbols**: Pre-configured with blacktop/symbolicator signatures
- ✅ **Intelligent Storage**: Auto-cleanup saves 99% disk space (18.8GB+ saved)
- ✅ **Production Ready**: Nginx load balancer, health monitoring, comprehensive logging
- ✅ **Multi-Device Support**: iPhone15,2, iPhone15,4, iPhone17,3 and more
- ✅ **Enterprise Features**: PostgreSQL storage, S3 integration, security headers

---

## 🚀 Quick Deployment

### Prerequisites

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| RAM | 4GB | 8GB | 16GB+ |
| Storage | 50GB | 200GB | 500GB+ |
| CPU | 2 cores | 4 cores | 8+ cores |
| Docker | 20.10+ | Latest | Latest |

### One-Command Deployment

```bash
# Start complete system
chmod +x start-server.sh
./start-server.sh

# Stop system
./stop-server.sh
```

### Manual Deployment Options

```bash
# Option 1: Local Development
./quick-deploy.sh  # Select option 1
# - Fast setup (~2 minutes)
# - Symbol Server + Web UI
# - Local file storage

# Option 2: Production with S3
./quick-deploy.sh  # Select option 2
# - Full system with PostgreSQL
# - S3 storage integration
# - Smart caching

# Option 3: Custom Enterprise
./deploy-full-system.sh
# - Complete customization
# - SSL/TLS support
# - Load balancing
```

---

## 🏗️ System Components

### 1. **Nginx Reverse Proxy**
- **Single entry point**: http://localhost
- **Load balancing**: Distributes requests across services
- **Security**: XSS protection, content validation, frame options
- **Compression**: Gzip for improved performance
- **Timeouts**: Optimized for large IPSW file processing

### 2. **Symbol Server (Custom)**
- **Auto-scanning**: Detects missing symbols and downloads IPSW files
- **Kernel symbolication**: 25,212+ symbols per device/version
- **Cache management**: Automatic cleanup of 9GB+ IPSW files
- **Signature support**: blacktop/symbolicator integration
- **Health monitoring**: Real-time status and metrics

### 3. **API Server**
- **Crash log processing**: Supports .ips, .crash, .txt, .json formats
- **S3 integration**: Direct access to IPSW storage
- **Database storage**: PostgreSQL for metadata and symbols
- **Concurrent processing**: Multiple crash logs simultaneously

### 4. **Web Interface**
- **Modern UI**: Drag & drop file upload
- **Real-time feedback**: Live symbolication progress
- **Results visualization**: Performance metrics, device info
- **Download capability**: Full JSON results export

### 5. **Storage Layer**
- **PostgreSQL**: Symbol metadata and cache
- **S3 Storage**: IPSW files (MinIO/AWS compatible)
- **Local cache**: Intelligent caching with auto-cleanup
- **Backup support**: Automated backup capabilities

---

## 📡 API Documentation

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Redirects to Web UI |
| `/docs` | GET | Interactive API documentation |
| `/status` | GET | System status overview |
| `/health` | GET | Health check |

### Symbolication API

```bash
# Upload and symbolicate crash log
curl -X POST "http://localhost/api/symbolicate" \
  -F "file=@crash.ips" \
  -H "Accept: application/json"

# Response
{
  "success": true,
  "crash_info": {
    "device_model": "iPhone15,2",
    "os_version": "18.5",
    "build_number": "22F76",
    "process_name": "stackshot via sysdiagnose"
  },
  "symbolication_time": 0.165,
  "total_time": 0.292
}
```

### Management API

```bash
# Check API health
curl "http://localhost/api/health"

# List available IPSW files
curl "http://localhost/api/s3/list" | jq

# View system statistics
curl "http://localhost/api/stats" | jq
```

### Symbol Server API

```bash
# Symbol server health
curl "http://localhost/symbol-server/health"

# Disk usage and cleanup stats
curl "http://localhost/symbol-server/v1/disk-usage" | jq

# Manual cleanup of IPSW files
curl -X POST "http://localhost/symbol-server/v1/cleanup"

# Trigger auto-scan for specific device
curl -X POST "http://localhost/symbol-server/v1/auto-scan?device_model=iPhone15,2&ios_version=18.5"

# View symbol server statistics
curl "http://localhost/symbol-server/stats" | jq
```

---

## 🌐 Web Interface

### Features

- **File Upload**: Drag & drop or click to select
- **Supported Formats**: .ips, .crash, .txt, .json (up to 10GB)
- **Real-time Processing**: Live progress updates
- **Results Dashboard**: Comprehensive analysis display
- **Export Options**: Download full JSON results

### Interface Sections

#### 📊 Performance Metrics
```
Total Processing Time: 0.292s
Symbolication Time: 0.123s
Analysis Time: 2025-06-17 19:45:23
```

#### 📱 Device Information
```
OS Version: iPhone OS 18.5 (22F76)
Device Model: iPhone15,2
Process: stackshot via sysdiagnose
```

#### 🎯 Kernel Analysis
```
4 Kernel Addresses Found:
0xfffffff407ed0398 → _vm_map_lookup_entry+0x398
0xfffffff407f3a3b0 → _vm_fault+0x3b0
0xfffffff407f38404 → _vm_page_lookup+0x404
0xfffffff407f349b0 → _vm_object_reference+0x9b0
```

#### 🔧 Symbolication Summary
```
✅ Successfully symbolicated: 4 addresses
❌ Unknown addresses: 0
📊 Output size: 1,522,271 characters
⏱️ Cache hit ratio: 95%
```

### Access URLs

- **Main Interface**: http://localhost/ui/
- **Documentation**: http://localhost/docs
- **Service Status**: http://localhost/status

---

## 🔧 Auto-Symbolication Features

### Intelligent Symbol Detection

The system automatically:
1. **Detects missing symbols** for crash log device/version
2. **Searches S3 storage** for matching IPSW files
3. **Downloads IPSW** (9GB+) to temporary storage
4. **Extracts kernelcache** and generates symbols
5. **Caches symbols** in PostgreSQL for future use
6. **Auto-deletes IPSW** to save disk space

### Supported Devices & Versions

| Device Model | iOS Versions | Status |
|--------------|--------------|--------|
| iPhone15,2 | 18.5 (22F76, 22F74, 22F75) | ✅ Full Support |
| iPhone15,4 | 18.5 (22F76, 22F74, 22F75) | ✅ Full Support |
| iPhone17,3 | 18.5 (22F76, 22F74, 22F75) | ✅ Full Support |
| Others | iOS 18.x | 🔄 Auto-detected |

### Kernel Signatures

- **blacktop/symbolicator**: 4,549 iOS 18.5 kernel signatures
- **Darwin Versions**: 20.x - 25.x support
- **Automatic Updates**: New signatures downloaded as available
- **Fallback Support**: Manual signature addition capability

---

## 💾 Storage Management

### Intelligent Auto-Cleanup

The system implements sophisticated storage management:

#### **Auto-Cleanup Process**
1. **IPSW Download**: 9GB+ file downloaded for symbolication
2. **Symbol Extraction**: 25,212+ symbols extracted and cached
3. **Immediate Cleanup**: IPSW file deleted after successful processing
4. **Kernelcache Cleanup**: Binary files removed, only symbols.json retained
5. **Space Tracking**: 18.8GB+ already saved through auto-cleanup

#### **Storage Statistics**
```bash
curl "http://localhost/symbol-server/v1/disk-usage" | jq
```

Response:
```json
{
  "success": true,
  "disk_usage": {
    "downloads": {
      "size_mb": 0.0,
      "file_count": 0,
      "ipsw_count": 0
    },
    "cache": {
      "size_mb": 246.7,
      "file_count": 6
    },
    "overall": {
      "total_gb": 58.37,
      "used_gb": 9.11,
      "free_gb": 46.26,
      "usage_percent": 15.6
    },
    "cleanup_stats": {
      "total_space_saved_mb": 18830.9,
      "auto_cleanup_enabled": true
    }
  }
}
```

### Manual Storage Management

```bash
# Manual cleanup of all IPSW files
curl -X POST "http://localhost/symbol-server/v1/cleanup"

# View current disk usage
curl "http://localhost/symbol-server/v1/disk-usage"

# Check system statistics
curl "http://localhost/symbol-server/stats"
```

### S3 Integration

#### Supported S3 Providers
- **AWS S3**: Native support
- **MinIO**: Local/private cloud
- **Ceph RadosGW**: Open-source storage
- **Dell ECS**: Enterprise storage
- **Custom S3 APIs**: Any S3-compatible storage

#### S3 Configuration
```bash
# Environment variables
S3_ENDPOINT=http://host.docker.internal:9000
S3_BUCKET=ipsw
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_USE_SSL=false
```

---

## 📊 Monitoring & Maintenance

### Health Monitoring

#### System Status Dashboard
```bash
curl "http://localhost/status" | jq
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "api": "http://localhost/api/health",
    "symbol_server": "http://localhost/symbol-server/health",
    "ui": "http://localhost/ui",
    "s3": "http://localhost/s3/minio/health/live"
  },
  "timestamp": "2025-06-17T21:26:34+00:00"
}
```

#### Individual Service Health Checks
```bash
# API Server health
curl "http://localhost/api/health" | jq

# Symbol Server health  
curl "http://localhost/symbol-server/health" | jq

# Nginx health
curl "http://localhost/health"
```

### Performance Metrics

#### Key Performance Indicators
- **Symbolication Speed**: 0.1-0.3 seconds per crash log
- **Auto-Scan Time**: 2-4 minutes for new device/version (one-time)
- **Storage Efficiency**: 99% space savings through auto-cleanup
- **Cache Hit Ratio**: 85%+ for optimal performance
- **Concurrent Users**: Nginx handles multiple simultaneous requests

#### Performance Monitoring
```bash
# Symbol server statistics
curl "http://localhost/symbol-server/stats" | jq

# Cache performance (S3 optimized deployments)
curl "http://localhost/api/cache-stats" | jq

# Disk usage trends
curl "http://localhost/symbol-server/v1/disk-usage" | jq
```

### Log Management

```bash
# View all service logs
docker logs ipsw-nginx
docker logs ipsw-api-server
docker logs ipsw-web-ui
docker logs custom-symbol-server

# Follow logs in real-time
docker logs -f custom-symbol-server

# View Symbol Server logs for debugging
docker-compose -f docker-compose.symbol-server.yml logs -f
```

### Backup & Recovery

```bash
# PostgreSQL backup
docker exec symbols-postgres pg_dump -U symbols_user symbols > backup_$(date +%Y%m%d).sql

# Configuration backup
cp .env .env.backup.$(date +%Y%m%d)
cp -r signatures/ signatures.backup.$(date +%Y%m%d)/

# Restore database
docker exec -i symbols-postgres psql -U symbols_user symbols < backup_YYYYMMDD.sql
```

---

## 🏭 Production Deployment

### Environment Configuration

```bash
# Production .env configuration
NGINX_PORT=80
API_PORT=8000
SYMBOL_PORT=3993
WEB_UI_PORT=5001

# S3 Storage
S3_ENDPOINT=https://s3.company.com
S3_BUCKET=ipsw-production
S3_ACCESS_KEY=production_access_key
S3_SECRET_KEY=production_secret_key
S3_USE_SSL=true

# PostgreSQL
POSTGRES_DB=symbols
POSTGRES_USER=symbols_user
POSTGRES_PASSWORD=SecureProductionPassword123!

# Performance tuning
CACHE_SIZE_GB=200
CLEANUP_AFTER_HOURS=12
MAX_CONCURRENT_DOWNLOADS=5
```

### Security Considerations

#### Network Security
- **Nginx reverse proxy**: Single entry point with security headers
- **Internal communication**: Services communicate through Docker networks
- **SSL/TLS**: Configurable SSL for S3 and external connections
- **Authentication**: Configurable access controls for production

#### Container Security
- **Non-root execution**: All containers run as non-root users
- **Read-only configurations**: Critical config files mounted read-only
- **Resource limits**: Memory and CPU limits prevent resource exhaustion
- **Network isolation**: Services isolated in Docker networks

#### Data Security
- **Encrypted connections**: PostgreSQL and S3 connections can use SSL
- **Credential management**: Environment-based credential configuration
- **Input validation**: File type and size validation for uploads
- **Access logging**: Comprehensive request and access logging

### Scaling Strategies

#### Horizontal Scaling
```yaml
# docker-compose.production.yml
services:
  api-server:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

#### Load Balancing
```nginx
# nginx.conf - upstream configuration
upstream api_backend {
    server ipsw-api-server-1:8000;
    server ipsw-api-server-2:8000;
    server ipsw-api-server-3:8000;
}
```

#### Performance Optimization

```bash
# For high-volume environments
export CACHE_SIZE_GB="500"
export MAX_CONCURRENT_DOWNLOADS="10"
export CLEANUP_AFTER_HOURS="6"

# Database tuning
export POSTGRES_SHARED_BUFFERS="2GB"
export POSTGRES_EFFECTIVE_CACHE_SIZE="6GB"
```

---

## 🚨 Troubleshooting

### Common Issues

#### Service Startup Problems
```bash
# Check service status
curl "http://localhost/status"

# View service logs
docker logs custom-symbol-server --tail 50

# Restart specific service
docker-compose -f docker-compose.symbol-server.yml restart custom-symbol-server

# Complete system restart
./stop-server.sh && ./start-server.sh
```

#### Storage Issues
```bash
# Check disk space
df -h

# View current storage usage
curl "http://localhost/symbol-server/v1/disk-usage" | jq

# Manual cleanup
curl -X POST "http://localhost/symbol-server/v1/cleanup"

# Docker cleanup
docker system prune -f
```

#### Network Connectivity Issues
```bash
# Test Nginx health
curl "http://localhost/health"

# Test individual services
curl "http://localhost:8000/health"  # API
curl "http://localhost:3993/health"  # Symbol Server
curl "http://localhost:5001/"        # Web UI

# Check container networking
docker network ls
docker network inspect ipsw-symbol-server_default
```

#### S3 Connection Problems
```bash
# Test S3 endpoint
curl -I "$S3_ENDPOINT/$S3_BUCKET/"

# Check S3 configuration
docker exec custom-symbol-server env | grep S3_

# View S3 logs
docker logs custom-symbol-server | grep -i s3
```

#### Database Issues
```bash
# Check PostgreSQL connection
docker exec symbols-postgres pg_isready -U symbols_user -d symbols

# Connect to database
docker exec -it symbols-postgres psql -U symbols_user -d symbols

# View database logs
docker logs symbols-postgres --tail 50
```

### Performance Issues

#### Slow Symbolication
```bash
# Check symbol cache status
curl "http://localhost/symbol-server/stats" | jq .total_symbols_extracted

# View current processing
docker logs custom-symbol-server | tail -20

# Check disk I/O
docker exec custom-symbol-server iostat -x 1 5
```

#### Memory Issues
```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Restart memory-intensive services
docker-compose -f docker-compose.symbol-server.yml restart
```

### Diagnostic Scripts

#### Health Check Script
```bash
#!/bin/bash
# health-check.sh

echo "🏥 IPSW Symbol Server Health Check"
echo "================================="

# Service health
curl -s http://localhost/health && echo "✅ Nginx: OK" || echo "❌ Nginx: FAIL"
curl -s http://localhost/api/health && echo "✅ API: OK" || echo "❌ API: FAIL"
curl -s http://localhost/symbol-server/health && echo "✅ Symbol Server: OK" || echo "❌ Symbol Server: FAIL"
curl -s http://localhost:5001/ >/dev/null && echo "✅ Web UI: OK" || echo "❌ Web UI: FAIL"

# Storage check
echo ""
echo "💾 Storage Status:"
curl -s "http://localhost/symbol-server/v1/disk-usage" | jq -r '.disk_usage.overall | "Free: \(.free_gb)GB / \(.total_gb)GB (\(.usage_percent)% used)"'

echo ""
echo "🧹 Cleanup Stats:"
curl -s "http://localhost/symbol-server/v1/disk-usage" | jq -r '.disk_usage.cleanup_stats | "Space saved: \(.total_space_saved_mb)MB, Auto-cleanup: \(.auto_cleanup_enabled)"'
```

---

## 👨‍💻 Development & Integration

### For iOS Developers

#### Basic Symbolication
```bash
# Command line usage
curl -X POST "http://localhost/api/symbolicate" \
  -F "file=@crash.ips" \
  -H "Accept: application/json" \
  -o symbolicated_result.json
```

#### Batch Processing
```bash
#!/bin/bash
# batch_symbolicate.sh

for crash_file in *.ips; do
    echo "Processing $crash_file..."
    curl -X POST "http://localhost/api/symbolicate" \
      -F "file=@$crash_file" \
      -o "symbolicated_${crash_file%.ips}.json"
done
```

### For QA Teams

#### Web Interface Usage
1. Open http://localhost/ui/
2. Drag & drop crash files or click to select
3. View real-time symbolication progress
4. Download full JSON results
5. Compare symbolicated addresses with source code

#### Supported File Formats
- **.ips**: iOS crash logs from Xcode/Console.app
- **.crash**: Legacy crash log format
- **.txt**: Plain text crash logs
- **.json**: JSON-formatted crash data

### For DevOps Teams

#### Monitoring Integration
```bash
# Prometheus metrics endpoint (if configured)
curl "http://localhost/metrics"

# Custom monitoring script
#!/bin/bash
DISK_USAGE=$(curl -s "http://localhost/symbol-server/v1/disk-usage" | jq -r '.disk_usage.overall.usage_percent')
if (( $(echo "$DISK_USAGE > 80" | bc -l) )); then
    echo "ALERT: Disk usage is ${DISK_USAGE}%"
    # Send to monitoring system
fi
```

#### CI/CD Integration
```yaml
# .github/workflows/symbolicate.yml
name: Symbolicate Crash Logs
on: [push]

jobs:
  symbolicate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Symbolicate crash logs
        run: |
          for file in crash_logs/*.ips; do
            curl -X POST "http://symbol-server.company.com/api/symbolicate" \
              -F "file=@$file" \
              -o "results/$(basename $file .ips).json"
          done
```

### API Response Format

```json
{
  "success": true,
  "crash_info": {
    "device_model": "iPhone15,2",
    "os_version": "18.5",
    "build_number": "22F76",
    "process_name": "MyApp",
    "exception_type": "EXC_BAD_ACCESS"
  },
  "symbolication_time": 0.165,
  "total_time": 0.292,
  "kernel_analysis": {
    "addresses_found": 4,
    "addresses_symbolicated": 4,
    "sample_symbols": [
      "0xfffffff407ed0398 → _vm_map_lookup_entry+0x398",
      "0xfffffff407f3a3b0 → _vm_fault+0x3b0"
    ]
  },
  "cache_info": {
    "cache_hit": true,
    "symbols_loaded": 25212,
    "cache_key": "iPhone15,2_22F76_unknown"
  },
  "symbolicated_content": "... full symbolicated crash log ..."
}
```

---

## 📞 Support & Documentation

### Quick Reference

| Resource | URL |
|----------|-----|
| **Main Interface** | http://localhost |
| **API Documentation** | http://localhost/docs |
| **System Status** | http://localhost/status |
| **Health Check** | http://localhost/health |

### Management Commands

```bash
# Start system
./start-server.sh

# Stop system
./stop-server.sh

# Quick deployment options
./quick-deploy.sh

# Health diagnostics
curl "http://localhost/status" | jq
```

### Log Locations

```bash
# Service logs
docker logs ipsw-nginx            # Nginx access/error logs
docker logs ipsw-api-server       # API server logs
docker logs ipsw-web-ui           # Web UI logs  
docker logs custom-symbol-server  # Symbol server logs
docker logs symbols-postgres      # Database logs
```

### Configuration Files

- **`.env`**: Main environment configuration
- **`nginx.conf`**: Nginx reverse proxy configuration
- **`docker-compose.yml`**: Main service orchestration
- **`docker-compose.symbol-server.yml`**: Symbol server configuration

---

## 🎉 Success Metrics

After successful deployment, your system provides:

✅ **Fast Symbolication**: 0.1-0.3 seconds per crash log
✅ **Auto-Discovery**: Automatic IPSW detection and processing  
✅ **Storage Efficiency**: 99% space savings through intelligent cleanup
✅ **Multi-Device Support**: iPhone 15 series and expanding device coverage
✅ **Production Ready**: Nginx load balancing, health monitoring, comprehensive logging
✅ **Developer Friendly**: Web UI, REST API, batch processing capabilities
✅ **Enterprise Features**: PostgreSQL storage, S3 integration, security headers

**The system is now ready for production use by development teams!** 🚀

---

*Built with ❤️ for iOS development teams worldwide* 