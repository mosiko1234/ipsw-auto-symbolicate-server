# 📚 IPSW Symbol Server - Developer Documentation

**Professional iOS Crash Symbolication Platform**  
*Complete deployment and usage guide for development teams*

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Deployment Options](#deployment-options)
4. [CLI Installation & Usage](#cli-installation--usage)
5. [Web UI Access](#web-ui-access)
6. [S3 Console Management](#s3-console-management)
7. [API Reference](#api-reference)
8. [Network Configuration](#network-configuration)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)
11. [Security Considerations](#security-considerations)

---

## 📋 Overview

The IPSW Symbol Server is a comprehensive iOS crash symbolication platform that provides:

- **Automated IPSW scanning and indexing**
- **Real-time crash symbolication**
- **Support for kernel crashes and user-space crashes**
- **Local and network deployment options**
- **Web UI and CLI interfaces**
- **Large file support with streaming uploads**
- **S3-compatible storage backend**

### Key Features

✅ **Unified CLI** - Single tool for local and remote usage  
✅ **Auto-detection** - Smart server discovery and startup  
✅ **Large file support** - Up to 10GB+ IPSW files with streaming  
✅ **Multiple interfaces** - CLI, Web UI, and REST API  
✅ **Network ready** - Team and enterprise deployment  
✅ **Kernel symbolication** - Advanced kernel crash analysis  

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IPSW Symbol Server                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Web UI    │  │     CLI     │  │  REST API   │       │
│  │   (Port 80) │  │  (Unified)  │  │ (Port 8000) │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│         │               │               │                │
│  ┌──────┼───────────────┼───────────────┼──────────────┐ │
│  │      └───────────────┼───────────────┘              │ │
│  │                      │                              │ │
│  │               ┌─────────────┐                       │ │
│  │               │ API Server  │                       │ │
│  │               │(Port 8000)  │                       │ │
│  │               └─────────────┘                       │ │
│  │                      │                              │ │
│  │  ┌─────────────┐     │     ┌─────────────┐          │ │
│  │  │Symbol Server│     │     │   MinIO S3  │          │ │
│  │  │(Port 3993)  │     │     │(Port 9000/1)│          │ │
│  │  └─────────────┘     │     └─────────────┘          │ │
│  │                      │                              │ │
│  │                ┌─────────────┐                      │ │
│  │                │ PostgreSQL  │                      │ │
│  │                │(Port 5432)  │                      │ │
│  │                └─────────────┘                      │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Port | Purpose |
|-----------|------|---------|
| **Web UI** | 80 | User-friendly web interface |
| **API Server** | 8000 | Main symbolication API and CLI endpoint |
| **Symbol Server** | 3993 | Core symbolication engine |
| **MinIO S3** | 9000/9001 | IPSW file storage and management |
| **PostgreSQL** | 5432 | Metadata and cache database |
| **Nginx** | 80 | Reverse proxy and load balancing |

---

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker 20.0+ with Docker Compose
- 8GB RAM minimum (16GB recommended)
- 100GB+ free disk space
- Network access for IPSW downloads

#### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd ipsw-symbol-server

# Start all services
docker-compose --profile regular up -d

# Verify deployment
docker ps --filter "name=ipsw"
curl http://localhost:8000/health
```

#### Service Status Check
```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# ipsw-nginx         Up 5 minutes   0.0.0.0:80->80/tcp
# ipsw-api-server    Up 5 minutes   0.0.0.0:8000->8000/tcp
# ipsw-symbol-server Up 5 minutes   0.0.0.0:3993->3993/tcp
# ipsw-minio         Up 5 minutes   0.0.0.0:9000-9001->9000-9001/tcp
# ipsw-postgres      Up 5 minutes   0.0.0.0:5432->5432/tcp
```

### Option 2: Airgap Deployment

For environments without internet access:

```bash
# Load pre-built images
cd docker_images_v1.2.5/
./load-images-v1.2.5.sh

# Start airgap services
docker-compose --profile airgap up -d
```

### Option 3: Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start individual components
python3 symbol_server_manager.py
python3 api_with_ui.py
```

---

## 🛠️ CLI Installation & Usage

### Installation Methods

#### Method 1: Unified CLI (Recommended)
```bash
# Download complete package
wget ipsw-unified-cli-complete-v1.2.5.tar.gz

# Extract and install
tar -xzf ipsw-unified-cli-complete-v1.2.5.tar.gz
./install-unified-cli.sh

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### Method 2: Global Installation (Server Host)
```bash
# Install directly on server host
./install_cli.sh

# CLI will be available globally as 'ipsw-cli'
```

### CLI Usage Examples

#### Basic Operations
```bash
# Check server status
ipsw-cli --check

# Basic symbolication
ipsw-cli crash.ips

# Show complete output
ipsw-cli --full crash.ips

# Save results to file
ipsw-cli --save results.json crash.ips
```

#### Local IPSW Usage
```bash
# Small IPSW files (<500MB)
ipsw-cli --local-ipsw iPhone_12_15.0.ipsw crash.ips

# Large IPSW files (>1GB) - automatic streaming
ipsw-cli --local-ipsw iPhone17,3_18.5_22F76_Restore.ipsw crash.ips
```

#### Network Usage
```bash
# Connect to remote server
ipsw-cli --server http://192.168.1.100:8000 crash.ips

# Remote server with local IPSW
ipsw-cli --server http://team-server:8000 --local-ipsw firmware.ipsw crash.ips

# Check remote server status
ipsw-cli --server http://192.168.1.100:8000 --check
```

#### Advanced Options
```bash
# Quiet mode (minimal output)
ipsw-cli --quiet crash.ips

# No banner display
ipsw-cli --no-banner crash.ips

# Prevent auto-start of local server
ipsw-cli --no-autostart --server http://remote:8000 crash.ips
```

### CLI Auto-Detection Logic

The unified CLI automatically detects the best mode:

1. **No `--server` specified**:
   - Checks for local server on `localhost:8000`
   - If not found, attempts to start Docker services
   - Falls back to network-only mode if Docker unavailable

2. **`--server` specified**:
   - Connects directly to specified server
   - Skips local server detection and startup
   - Works with any remote IPSW Symbol Server

### CLI Help and Examples
```bash
# Complete help
ipsw-cli --help

# Usage examples from help:
ipsw-cli crash.ips
ipsw-cli --local-ipsw firmware.ipsw crash.ips
ipsw-cli --server http://192.168.1.100:8000 crash.ips
ipsw-cli --server http://team-server:8000 --local-ipsw firmware.ipsw crash.ips
ipsw-cli --check
ipsw-cli --server http://192.168.1.100:8000 --check
ipsw-cli --full crash.ips
```

---

## 🌐 Web UI Access

### Local Access
```
http://localhost
```

### Network Access
```
http://SERVER_IP
```
Replace `SERVER_IP` with your server's IP address (e.g., `http://192.168.1.100`)

### Web UI Features

#### 1. Main Dashboard
- **Upload crash files** - Drag & drop or browse
- **View recent analyses** - History of symbolication requests
- **Server status** - Real-time health monitoring
- **Quick actions** - Common operations

#### 2. File Upload Options
- **Single crash file** - Basic symbolication
- **Crash + IPSW** - Local IPSW symbolication
- **Batch processing** - Multiple files at once

#### 3. Results Viewer
- **Syntax highlighted output** - Color-coded symbolicated crashes
- **Device information** - iOS version, device model, build
- **Download options** - JSON, text, or PDF export
- **Sharing links** - Shareable result URLs

#### 4. Admin Interface
- **Service monitoring** - All component status
- **Storage management** - IPSW cache and cleanup
- **User activity** - Usage statistics and logs

### Web UI URLs by Function

| Function | URL Path | Description |
|----------|----------|-------------|
| Main Dashboard | `/` | Primary interface |
| Upload Page | `/upload` | File upload interface |
| Results View | `/results/<analysis_id>` | View specific analysis |
| Admin Panel | `/admin` | Administrative functions |
| API Status | `/health` | Server health check |
| Documentation | `/docs` | API documentation |

---

## 📦 S3 Console Management

### MinIO Console Access

#### Local Access
```
http://localhost:9001
```

#### Network Access
```
http://SERVER_IP:9001
```

#### Default Credentials
- **Username**: `minioadmin`
- **Password**: `minioadmin`

### S3 Console Features

#### 1. Browser Interface
- **Upload IPSW files** - Direct browser upload for large files
- **File management** - Browse, download, delete IPSW files
- **Bucket management** - Create and manage storage buckets
- **Access control** - User and permission management

#### 2. IPSW Management Workflow

For files larger than 1GB, use the S3 console:

1. **Access Console**: `http://SERVER_IP:9001`
2. **Login**: `minioadmin` / `minioadmin`
3. **Navigate to 'ipsw' bucket**
4. **Upload IPSW file** using the upload button
5. **Use CLI** without `--local-ipsw` (file will be auto-detected)

```bash
# After uploading IPSW to S3
ipsw-cli crash.ips  # Will use uploaded IPSW automatically
```

#### 3. Advanced S3 Operations

```bash
# Using AWS CLI with MinIO
aws --endpoint-url http://localhost:9000 s3 ls s3://ipsw/

# Upload via AWS CLI
aws --endpoint-url http://localhost:9000 s3 cp firmware.ipsw s3://ipsw/

# Download from S3
aws --endpoint-url http://localhost:9000 s3 cp s3://ipsw/firmware.ipsw ./
```

### S3 Configuration

#### Environment Variables
```bash
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=ipsw
S3_USE_SSL=false
```

#### Bucket Structure
```
ipsw/
├── iPhone17,3_18.5_22F76_Restore.ipsw
├── iPhone14,2_17.0_21A329_Restore.ipsw
└── cache/
    ├── extracted/
    └── symbols/
```

---

## 🔌 API Reference

### Base URLs

| Environment | URL |
|-------------|-----|
| Local | `http://localhost:8000` |
| Network | `http://SERVER_IP:8000` |

### Authentication

Currently no authentication required. For production deployments, consider implementing:
- API keys
- JWT tokens
- IP whitelisting

### Core Endpoints

#### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-22T15:47:01.578751",
  "version": "1.2.5",
  "services": {
    "symbol_server": "healthy",
    "database": "healthy",
    "storage": "healthy"
  }
}
```

#### 2. Basic Symbolication
```http
POST /symbolicate
Content-Type: multipart/form-data

file: <crash-file>
```

**Example with curl:**
```bash
curl -X POST \
  -F "file=@crash.ips" \
  http://localhost:8000/symbolicate
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "abc123",
  "message": "Symbolication completed successfully",
  "file_info": {
    "device_model": "iPhone17,3",
    "ios_version": "iPhone OS 18.5 (22F76)",
    "build_version": "22F76",
    "process_name": "kernel_task",
    "bug_type": "288"
  },
  "symbolicated_output": "...",
  "processing_time": 2.34,
  "timestamp": "2025-06-22T15:47:01.578751"
}
```

#### 3. Local IPSW Symbolication
```http
POST /local-ipsw-symbolicate
Content-Type: multipart/form-data

ipsw_file: <ipsw-file>
ips_file: <crash-file>
```

**Example:**
```bash
curl -X POST \
  -F "ipsw_file=@firmware.ipsw" \
  -F "ips_file=@crash.ips" \
  http://localhost:8000/local-ipsw-symbolicate
```

#### 4. Streaming Upload (Large Files)
```http
POST /local-ipsw-symbolicate-stream
Content-Type: multipart/form-data

ipsw_file: <large-ipsw-file>
ips_file: <crash-file>
```

Automatically used by CLI for files >1GB.

#### 5. Analysis Results
```http
GET /analysis/<analysis_id>
```

**Response:**
```json
{
  "analysis_id": "abc123",
  "status": "completed",
  "file_info": { ... },
  "symbolicated_output": "...",
  "created_at": "2025-06-22T15:47:01.578751",
  "processing_time": 2.34
}
```

#### 6. Server Status
```http
GET /status
```

**Response:**
```json
{
  "server": "IPSW Symbol Server",
  "version": "1.2.5",
  "uptime": "2 hours, 34 minutes",
  "active_analyses": 3,
  "total_analyses": 1247,
  "storage": {
    "ipsw_files": 45,
    "cache_size": "89.2 GB",
    "free_space": "156.8 GB"
  }
}
```

#### 7. IPSW Management
```http
GET /ipsw/list
POST /ipsw/upload
DELETE /ipsw/<filename>
GET /ipsw/<filename>/info
```

### API Usage Examples

#### Python Example
```python
import requests

# Basic symbolication
with open('crash.ips', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/symbolicate', files=files)
    result = response.json()

print(f"Analysis ID: {result['analysis_id']}")
print(f"Device: {result['file_info']['device_model']}")
```

#### JavaScript Example
```javascript
const formData = new FormData();
formData.append('file', crashFile);

fetch('http://localhost:8000/symbolicate', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(result => {
  console.log('Analysis ID:', result.analysis_id);
  console.log('Device:', result.file_info.device_model);
});
```

#### Shell Script Example
```bash
#!/bin/bash

# Symbolicate crash file
RESULT=$(curl -s -X POST \
  -F "file=@$1" \
  http://localhost:8000/symbolicate)

# Extract analysis ID
ANALYSIS_ID=$(echo "$RESULT" | jq -r '.analysis_id')

echo "Analysis completed: $ANALYSIS_ID"
echo "View results: http://localhost/results/$ANALYSIS_ID"
```

---

## 🌐 Network Configuration

### Firewall Configuration

#### Required Ports
| Port | Service | Purpose |
|------|---------|---------|
| 80 | HTTP | Web UI access |
| 8000 | HTTP | API and CLI access |
| 9001 | HTTP | MinIO console (optional) |

#### Firewall Rules

**Ubuntu/Debian:**
```bash
sudo ufw allow 80
sudo ufw allow 8000
sudo ufw allow 9001  # Optional: MinIO console
```

**CentOS/RHEL:**
```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9001/tcp
sudo firewall-cmd --reload
```

**macOS:**
```bash
# Disable firewall temporarily for testing
sudo pfctl -d
```

### Network Discovery

#### Find Server IP
```bash
# On server host
ifconfig | grep "inet " | grep -v 127.0.0.1

# Example output: 192.168.1.100
```

#### Test Network Access
```bash
# From client machine
curl http://192.168.1.100:8000/health

# Should return: {"status":"healthy",...}
```

### Load Balancing (Multiple Servers)

#### Nginx Configuration
```nginx
upstream ipsw_servers {
    server 192.168.1.100:8000;
    server 192.168.1.101:8000;
    server 192.168.1.102:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://ipsw_servers;
    }
}
```

### SSL/TLS Configuration

#### Enable HTTPS
```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt

# Update docker-compose.yml with SSL configuration
```

---

## 🚀 Advanced Features

### Kernel Symbolication

The server includes advanced kernel crash symbolication:

#### Supported Kernel Components
- **XNU kernel** - Core kernel crashes
- **Kernel extensions** - Driver crashes
- **System calls** - Syscall failures
- **Memory management** - VM and memory issues

#### Kernel Signatures Database
```
signatures/symbolicator/kernel/
├── 24.5/          # iOS 18.5
│   ├── xnu.json
│   └── kexts/
│       ├── apfs.json
│       ├── IOKit.json
│       └── ...
├── 24.4/          # iOS 18.4
└── ...
```

### Automatic IPSW Detection

The system can automatically detect and download IPSWs:

#### Configuration
```yaml
# ipsw-config.yml
auto_download: true
preferred_sources:
  - "official"
  - "beta"
device_support:
  - "iPhone17,3"  # iPhone 16 Pro
  - "iPhone16,2"  # iPhone 15 Pro
```

### Batch Processing

#### CLI Batch Mode
```bash
# Process multiple files
for crash in *.ips; do
  ipsw-cli "$crash" --save "results/$crash.json"
done
```

#### API Batch Endpoint
```http
POST /batch-symbolicate
Content-Type: multipart/form-data

files[]: <crash-file-1>
files[]: <crash-file-2>
ipsw_file: <ipsw-file>
```

### Performance Optimization

#### Caching Configuration
```bash
# Environment variables
CACHE_SIZE_GB=100
CLEANUP_AFTER_HOURS=24
MAX_CONCURRENT_DOWNLOADS=3
```

#### Database Tuning
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET work_mem = '256MB';
```

### Monitoring and Logging

#### Health Monitoring
```bash
# Check all services
curl http://localhost:8000/health | jq

# Monitor logs
docker-compose logs -f api-server
docker-compose logs -f symbol-server
```

#### Metrics Collection
```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics

# Sample metrics:
# symbolication_requests_total 1247
# symbolication_duration_seconds_avg 2.34
# active_analyses_current 3
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Server Won't Start
```bash
# Check Docker status
docker info

# Check port availability
netstat -tulpn | grep :8000

# Restart services
docker-compose down
docker-compose --profile regular up -d
```

#### 2. Connection Refused
```bash
# Verify services are running
docker ps --filter "name=ipsw"

# Check firewall
sudo ufw status
curl http://localhost:8000/health
```

#### 3. Large File Upload Fails
```bash
# Use MinIO console instead
open http://localhost:9001

# Or use CLI streaming
ipsw-cli --local-ipsw large-file.ipsw crash.ips
```

#### 4. Symbolication Fails
```bash
# Check available IPSWs
curl http://localhost:8000/ipsw/list

# Verify device/iOS version support
curl http://localhost:8000/status
```

### Debugging Mode

#### Enable Verbose Logging
```bash
# Docker environment
IPSW_DEBUG=true docker-compose up -d

# CLI debugging
ipsw-cli --verbose crash.ips
```

#### Log Locations
```bash
# Docker logs
docker-compose logs api-server
docker-compose logs symbol-server

# File logs
tail -f logs/symbolication.log
tail -f logs/api.log
```

### Performance Issues

#### Memory Usage
```bash
# Check memory usage
docker stats

# Optimize cache size
export CACHE_SIZE_GB=50
docker-compose restart
```

#### Disk Space
```bash
# Check disk usage
df -h
du -sh data/cache/

# Clean cache
curl -X POST http://localhost:8000/admin/clean-cache
```

### Network Issues

#### Connectivity Test
```bash
# Test from client
telnet SERVER_IP 8000
ping SERVER_IP

# Test DNS resolution
nslookup server.company.com
```

#### Proxy Configuration
```bash
# For corporate networks
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

---

## 🔒 Security Considerations

### Network Security

#### Recommended Practices
- **Use VPN** for remote access
- **Implement firewall rules** to restrict access
- **Enable HTTPS** for production deployments
- **Use private networks** for team deployments

#### Access Control
```bash
# IP whitelisting in nginx
location / {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://api-server;
}
```

### Data Privacy

#### Crash File Handling
- **Automatic cleanup** of uploaded files after processing
- **Configurable retention** policies
- **No persistent storage** of sensitive data

#### Storage Security
```bash
# Encrypt data at rest
STORAGE_ENCRYPTION=true

# Secure credentials
S3_ACCESS_KEY_FILE=/run/secrets/s3_access_key
S3_SECRET_KEY_FILE=/run/secrets/s3_secret_key
```

### Production Deployment

#### Security Checklist
- [ ] Change default MinIO credentials
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Implement backup strategy
- [ ] Configure log rotation
- [ ] Enable audit logging

#### Sample Production Configuration
```yaml
# docker-compose.prod.yml
services:
  api-server:
    environment:
      - ENVIRONMENT=production
      - ENABLE_CORS=false
      - MAX_UPLOAD_SIZE=10GB
      - SESSION_TIMEOUT=3600
    volumes:
      - /etc/ssl/certs:/app/certs:ro
```

---

## 📞 Support and Resources

### Documentation Links
- **API Reference**: `http://localhost:8000/docs`
- **CLI Help**: `ipsw-cli --help`
- **Configuration Guide**: `CLI_UNIFIED_USAGE.md`

### Community Resources
- **GitHub Repository**: [Link to repository]
- **Issue Tracker**: [Link to issues]
- **Documentation**: [Link to full docs]

### Support Channels
- **Email**: support@company.com
- **Slack**: #ios-symbolication
- **Wiki**: [Internal wiki link]

---

## 🎉 Quick Start Summary

### For Individual Developers
```bash
# 1. Install CLI
wget ipsw-unified-cli-complete-v1.2.5.tar.gz
tar -xzf ipsw-unified-cli-complete-v1.2.5.tar.gz && ./install-unified-cli.sh

# 2. Use immediately
ipsw-cli crash.ips
```

### For Team Deployment
```bash
# 1. Deploy server
docker-compose --profile regular up -d

# 2. Share with team
# CLI: ipsw-cli --server http://TEAM_SERVER:8000 crash.ips
# Web: http://TEAM_SERVER
# S3:  http://TEAM_SERVER:9001
```

### For Enterprise
```bash
# 1. Deploy with custom configuration
# 2. Configure SSL/TLS and security
# 3. Set up monitoring and backups
# 4. Distribute client tools to development teams
```

---

**🚀 The IPSW Symbol Server is now ready for professional iOS development workflows!**

*For additional support or questions, please refer to the support channels above.* 