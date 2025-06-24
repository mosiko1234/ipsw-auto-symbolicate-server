# IPSW Symbol Server

A production-ready iOS crashlog symbolication system that requires **both** crashlog (.ips) and IPSW firmware files for accurate symbolication.

## 🚀 Quick Start

```bash
# Start the system
docker-compose up -d

# Symbolicate with both files
curl -F "crashlog=@crash.ips" -F "ipsw=@iPhone15,2_18.5_22F76_Restore.ipsw" \
     http://localhost/symbolicate/upload | jq '.output'
```

## 🏗 Architecture

The system consists of 3 containers in production:

1. **symbol-nginx** - Nginx reverse proxy (Port 80)
   - Handles large file uploads (up to 15GB IPSW files)
   - Proxies requests to symbol-server

2. **symbol-server** - Python Flask API with integrated ipsw CLI (Port 3993)
   - Multipart file upload processing
   - Runs ipsw CLI with provided IPSW for accurate symbolication
   - Gunicorn with 4 workers for production load

3. **symbol-db** - PostgreSQL database (Port 5432)
   - Stores symbol metadata
   - Connection pooling for performance

## 🛠️  Production Deployment Guide (DevOps)

### Prerequisites
1. Linux host with Docker 20.10+ and Docker Compose v2
2. At least **8 GB RAM** and **50 GB free disk** (large IPSW files)
3. Public DNS record (e.g. `symbol.example.com`)

### One-Shot Installation
```bash
# Clone repository
git clone https://github.com/your-org/ipsw-symbol-server.git
cd ipsw-symbol-server

# Build & start all services
docker-compose up -d --build

# Verify health
curl http://symbol.example.com/health | jq
```

### Components That Come Up
| Container          | Port | Description                              |
|--------------------|------|------------------------------------------|
| `symbol-nginx`     | 80   | Reverse-proxy, allows uploads ≤ 15 GB    |
| `symbol-server`    | 3993 | Gunicorn (Flask) API + `ipsw` CLI inside |
| `symbol-db`        | 5432 | PostgreSQL 13 with `symbols` database    |

### Data Persistence
```
./uploads/           # Uploaded IPSW files (cached for reuse)
./signatures/        # Kernel signatures (mounted read-only)
postgres_data/       # Database volume
```

### Backups
```bash
# Database backup
docker-compose exec symbol-db pg_dump -U symboluser symbols > backup.sql

# Restore
docker-compose exec -T symbol-db psql -U symboluser symbols < backup.sql
```

### Scaling Tips
* Increase workers: Set `GUNICORN_WORKERS` environment variable
* Add TLS termination with Traefik/Let's Encrypt in front of nginx
* Monitor disk usage in `./uploads/` - old IPSW files can be deleted

---

## 👩‍💻  Developer Usage Guide

**IMPORTANT**: This service requires **both** a crashlog file (.ips) and the matching IPSW firmware file for symbolication to work.

### Health Check
```bash
curl http://symbol.example.com/health | jq
```

### Symbolication (Required: Crashlog + IPSW)
```bash
# Upload both files for symbolication
curl -F "crashlog=@stacks-2025-06-16-134742.ips" \
     -F "ipsw=@iPhone17,3_18.5_22F76_Restore.ipsw" \
     http://symbol.example.com/symbolicate/upload | jq '.output'
```

**Response Example:**
```json
{
  "status": "success",
  "method": "ipsw_cli_upload", 
  "timestamp": "2025-06-23T19:05:41.689Z",
  "output": "[16Jun2025 13:47:42] - Stackshot - iPhone15,2 iPhone OS 18.5 (22F76)\n\n<symbolicated output>"
}
```

### Helper Script for Command Line
Save as `symbolicate-remote`:
```bash
#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: $0 <crashlog.ips> <firmware.ipsw>"
    exit 1
fi

SERVER="${SYMBOL_SERVER:-http://symbol.example.com}"
curl -s -F "crashlog=@$1" -F "ipsw=@$2" "$SERVER/symbolicate/upload" | jq -r '.output'
```

Make executable and use:
```bash
chmod +x symbolicate-remote
./symbolicate-remote crash.ips iPhone15,2_18.5_22F76_Restore.ipsw
```

### File Requirements
- **Crashlog**: .ips files (traditional crashes, kernel panics, JSON stackshots)
- **IPSW**: Matching firmware file for the device/OS version in the crashlog
- **File sizes**: Crashlogs typically < 1MB, IPSW files 8-15GB
- **Upload time**: Large IPSW files may take 5-30 minutes depending on connection

### Error Handling
```bash
# Check for errors in response
curl -F "crashlog=@crash.ips" -F "ipsw=@firmware.ipsw" \
     http://symbol.example.com/symbolicate/upload | jq '.status'

# If status is "error", check .stderr field for details
```

## 📁 Project Structure

```
ipsw-symbol-server/
├── docker-compose.yml      # Main orchestration  
├── nginx.conf              # Reverse proxy config (15GB upload limit)
├── app.py                  # Flask API + ipsw CLI integration
├── Dockerfile              # Symbol server image
├── init.sql                # Database schema
├── requirements.txt        # Python dependencies
├── signatures/             # Kernel signatures (blacktop/symbolicator)
├── uploads/                # IPSW cache directory
└── README.md               # This documentation
```

## 🔧 Development & Maintenance

### Updating the Service
```bash
# Pull new code
git pull origin main

# Rebuild and restart
docker-compose build symbol-server
docker-compose up -d symbol-server
```

### Monitoring
```bash
# Check container health
docker-compose ps

# View logs
docker-compose logs symbol-server

# Monitor disk usage (IPSW files are large)
du -sh uploads/
```

### Troubleshooting

**Upload fails with large files:**
```bash
# Check nginx config allows large uploads
docker-compose exec symbol-nginx cat /etc/nginx/nginx.conf | grep client_max_body_size

# Should show: client_max_body_size 15G;
```

**Symbolication returns errors:**
```bash
# Check ipsw CLI is working in container
docker-compose exec symbol-server ipsw version

# Test with sample files
curl -F "crashlog=@crashlogs/sample_crash.ips" \
     -F "ipsw=@iPhone15,2_18.5_22F76_Restore.ipsw" \
     http://localhost/symbolicate/upload
```

**Database issues:**
```bash
# Check database connectivity
docker-compose exec symbol-db pg_isready -U symboluser

# Connect to database
docker-compose exec symbol-db psql -U symboluser -d symbols
```

## 📊 Supported Formats

✅ **Supported Crashlogs:**
- iOS App Crashes (.ips)
- Kernel Panics  
- JSON Stackshots
- Traditional crash reports

✅ **Supported IPSW:**
- iOS 14.0+
- All device types (iPhone, iPad)
- Beta and release firmwares

❌ **NOT Supported:**
- Crashlog-only symbolication (IPSW required)
- macOS crashes (limited support)
- Pre-iOS 14 firmware

---

**🎯 Production-ready iOS crash symbolication requiring both crashlog and IPSW files.**

> **Need help?** Check logs with `docker-compose logs` or contact DevOps team. 