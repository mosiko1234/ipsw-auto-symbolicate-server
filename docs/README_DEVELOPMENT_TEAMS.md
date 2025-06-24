# 🚀 IPSW Symbol Server - Complete Guide for Development Teams

**Professional iOS Crash Symbolication Platform**  
*Everything you need to deploy, use, and integrate iOS crash symbolication*

---

## 📋 What This Platform Provides

### ✅ Core Capabilities
- **Automated iOS crash symbolication** - Turn crash dumps into readable stack traces
- **Kernel crash analysis** - Deep system-level debugging for advanced issues
- **Large IPSW support** - Handle 10GB+ firmware files with streaming uploads
- **Team collaboration** - Shared server for multiple developers
- **Multiple interfaces** - CLI, Web UI, REST API, and S3 console

### ✅ Deployment Options
- **Individual developer** - Personal local server with auto-start
- **Team server** - Shared network server for collaboration
- **Enterprise deployment** - Production-ready with monitoring and security
- **Airgap installation** - For environments without internet access

---

## 🎯 Quick Access Summary

| Access Method | URL/Command | Best For |
|---------------|-------------|----------|
| **CLI Tool** | `ipsw-cli crash.ips` | Daily development, automation |
| **Web Interface** | `http://SERVER_IP` | Visual interface, file management |
| **S3 Console** | `http://SERVER_IP:9001` | Large IPSW uploads (>1GB) |
| **REST API** | `http://SERVER_IP:8000` | Integration, custom workflows |

---

## 🚀 Getting Started (Choose Your Path)

### Path 1: Individual Developer (5 minutes)
```bash
# Install unified CLI
curl -L https://releases/ipsw-unified-cli-complete-v1.2.5.tar.gz | tar -xz
./install-unified-cli.sh

# Start using immediately
ipsw-cli crash.ips                                    # Basic symbolication
ipsw-cli --local-ipsw firmware.ipsw crash.ips        # With specific IPSW
ipsw-cli --check                                      # Check status
```

### Path 2: Team Server (10 minutes)
```bash
# On server machine
git clone <repository>
cd ipsw-symbol-server
docker-compose --profile regular up -d

# Get server IP for team
ifconfig | grep "inet " | grep -v 127.0.0.1
# Share: http://192.168.1.100 with team
```

### Path 3: Enterprise Deployment (30 minutes)
```bash
# Production deployment with SSL/monitoring
docker-compose --profile production up -d
# Configure SSL, monitoring, backups
# Set up user management and access control
```

---

## 🛠️ Access Methods Detailed

### 1. 💻 CLI Tool (Unified Local & Network)

#### Installation
```bash
# Download complete package
wget ipsw-unified-cli-complete-v1.2.5.tar.gz
tar -xzf ipsw-unified-cli-complete-v1.2.5.tar.gz
./install-unified-cli.sh
```

#### Usage Examples
```bash
# Local mode (auto-detects and starts local server)
ipsw-cli crash.ips
ipsw-cli --local-ipsw firmware.ipsw crash.ips

# Network mode (connect to team server)
ipsw-cli --server http://192.168.1.100:8000 crash.ips
ipsw-cli --server http://team-server:8000 --local-ipsw firmware.ipsw crash.ips

# Status and health checks
ipsw-cli --check                                      # Local server
ipsw-cli --server http://192.168.1.100:8000 --check   # Remote server

# Advanced options
ipsw-cli --full --save results.json crash.ips        # Complete output + save
ipsw-cli --quiet --no-banner crash.ips               # Minimal output
```

#### CLI Features
- **Smart auto-detection** - Automatically detects local vs. remote mode
- **Auto-start capability** - Starts Docker services when needed
- **Large file support** - Automatic streaming for files >1GB
- **Beautiful output** - Color-coded, formatted results
- **Cross-platform** - Works on macOS, Linux, Windows

---

### 2. 🌐 Web Interface

#### Access URLs
```
Local:    http://localhost
Team:     http://SERVER_IP
Secure:   https://symbolication.company.com
```

#### Web UI Features
- **Drag & drop upload** - Easy file upload interface
- **Real-time progress** - Upload and processing status
- **Results viewer** - Syntax-highlighted symbolicated output
- **History management** - View past analyses
- **Device detection** - Automatic iOS version and device identification
- **Export options** - Download results as JSON, text, or PDF

#### Web UI Workflows
1. **Basic Symbolication**
   - Open web interface
   - Drag crash file to upload area
   - View symbolicated results

2. **IPSW + Crash**
   - Upload both IPSW and crash files
   - System automatically processes with specific firmware
   - Download complete analysis

3. **Batch Processing**
   - Upload multiple crash files
   - Process all with same or different IPSWs
   - Export batch results

---

### 3. 📦 S3 Console (MinIO)

#### Access URLs
```
Local:    http://localhost:9001
Team:     http://SERVER_IP:9001
```

#### Default Credentials
- **Username**: `minioadmin`
- **Password**: `minioadmin`

#### S3 Console Features
- **Large file uploads** - Upload IPSW files up to 10GB+
- **File management** - Browse, download, delete IPSW files
- **Bucket organization** - Organized storage structure
- **Direct access** - Files uploaded here are immediately available

#### S3 Workflows
1. **Large IPSW Management**
   ```bash
   # Upload via browser
   open http://SERVER_IP:9001
   # Login: minioadmin/minioadmin
   # Upload to 'ipsw' bucket
   
   # Use in CLI (auto-detects uploaded files)
   ipsw-cli crash.ips
   ```

2. **AWS CLI Integration**
   ```bash
   # Configure AWS CLI for MinIO
   aws configure set aws_access_key_id minioadmin
   aws configure set aws_secret_access_key minioadmin
   
   # Upload via CLI
   aws --endpoint-url http://localhost:9000 s3 cp firmware.ipsw s3://ipsw/
   
   # List files
   aws --endpoint-url http://localhost:9000 s3 ls s3://ipsw/
   ```

---

### 4. 🔌 REST API

#### Base URLs
```
Local:    http://localhost:8000
Team:     http://SERVER_IP:8000
```

#### Core Endpoints
| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/health` | GET | Server health check |
| `/symbolicate` | POST | Basic crash symbolication |
| `/local-ipsw-symbolicate` | POST | Symbolication with specific IPSW |
| `/local-ipsw-symbolicate-stream` | POST | Large file streaming upload |
| `/status` | GET | Detailed server status |
| `/ipsw/list` | GET | List available IPSW files |

#### API Examples
```bash
# Health check
curl http://localhost:8000/health

# Basic symbolication
curl -X POST -F "file=@crash.ips" http://localhost:8000/symbolicate

# With local IPSW
curl -X POST \
  -F "ipsw_file=@firmware.ipsw" \
  -F "ips_file=@crash.ips" \
  http://localhost:8000/local-ipsw-symbolicate

# Get server status
curl http://localhost:8000/status | jq
```

#### Integration Examples
```python
# Python integration
import requests

with open('crash.ips', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://team-server:8000/symbolicate', files=files)
    result = response.json()

print(f"Device: {result['file_info']['device_model']}")
print(f"Analysis ID: {result['analysis_id']}")
```

---

## ⚙️ System Architecture & Components

### Docker Services
| Service | Port | Purpose |
|---------|------|---------|
| **Nginx** | 80 | Web UI and reverse proxy |
| **API Server** | 8000 | Main symbolication API |
| **Symbol Server** | 3993 | Core symbolication engine |
| **MinIO S3** | 9000/9001 | IPSW file storage |
| **PostgreSQL** | 5432 | Metadata and cache database |

### File Size Handling
| File Size | Method | Endpoint |
|-----------|--------|----------|
| **< 500MB** | Direct upload | `/local-ipsw-symbolicate` |
| **500MB - 1GB** | Standard upload | `/local-ipsw-symbolicate` |
| **> 1GB** | Streaming upload | `/local-ipsw-symbolicate-stream` |
| **> 5GB** | S3 Console + CLI | MinIO upload → CLI |

---

## 🔧 Configuration & Options

### Environment Variables
```bash
# Cache and performance
CACHE_SIZE_GB=100                    # Symbol cache size
CLEANUP_AFTER_HOURS=24               # Auto-cleanup interval
MAX_CONCURRENT_DOWNLOADS=3           # Parallel IPSW downloads

# S3 storage configuration
S3_ENDPOINT=http://minio:9000
S3_BUCKET=ipsw
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Database configuration
DATABASE_URL=postgresql://user:pass@postgres:5432/symbols
```

### CLI Configuration
```bash
# Global CLI options
ipsw-cli --help                      # Show all options

# Server specification
--server http://IP:8000             # Connect to specific server
--no-autostart                     # Don't auto-start local server

# Output control
--full                              # Show complete output
--quiet                             # Minimal output
--no-banner                         # Skip banner
--save FILE                         # Save results to JSON

# File handling
--local-ipsw FILE                   # Use specific IPSW file
```

### Docker Compose Profiles
```bash
# Regular deployment (with internet access)
docker-compose --profile regular up -d

# Airgap deployment (no internet)
docker-compose --profile airgap up -d

# Production deployment (with monitoring)
docker-compose --profile production up -d
```

---

## 🌐 Network Configuration

### Firewall Requirements
```bash
# Required ports
Port 80:   Web UI access
Port 8000: API and CLI access
Port 9001: MinIO console (optional)

# Ubuntu/Debian
sudo ufw allow 80 && sudo ufw allow 8000 && sudo ufw allow 9001

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9001/tcp
sudo firewall-cmd --reload
```

### Team Server Setup
```bash
# Get server IP
SERVER_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

# Test accessibility
curl http://$SERVER_IP:8000/health

# Share with team
echo "Team server ready at:"
echo "  Web UI: http://$SERVER_IP"
echo "  CLI:    ipsw-cli --server http://$SERVER_IP:8000 crash.ips"
echo "  S3:     http://$SERVER_IP:9001"
```

---

## 🔄 Deployment Scenarios

### Scenario 1: Single Developer
```bash
# Personal laptop/workstation
./install-unified-cli.sh             # Install CLI
ipsw-cli crash.ips                   # Use immediately
```
- **Pros**: Simple, fast, no network dependencies
- **Use case**: Individual development, personal projects

### Scenario 2: Small Team (2-10 developers)
```bash
# One team member hosts server
docker-compose --profile regular up -d

# Others connect via network
ipsw-cli --server http://TEAM_IP:8000 crash.ips
```
- **Pros**: Shared resources, consistent environment
- **Use case**: Startup teams, small dev groups

### Scenario 3: Medium Team (10-50 developers)
```bash
# Dedicated server machine
# Custom docker-compose with resource limits
# Load balancing and monitoring
```
- **Pros**: Dedicated resources, better performance
- **Use case**: Growing companies, multiple projects

### Scenario 4: Enterprise (50+ developers)
```bash
# Kubernetes deployment
# High availability, monitoring, security
# Integration with existing infrastructure
```
- **Pros**: Production-grade, scalable, secure
- **Use case**: Large enterprises, critical applications

---

## 🔒 Security & Best Practices

### Development Environment
```bash
# Local network only
# Default credentials acceptable
# No SSL required
```

### Team Environment
```bash
# Change default MinIO credentials
export MINIO_ROOT_USER=teamadmin
export MINIO_ROOT_PASSWORD=secure_password_123

# Enable basic access control
# Use private network/VPN
```

### Production Environment
```bash
# Enable HTTPS/TLS
# Implement authentication
# Set up monitoring and logging
# Configure backup strategy
# Use secrets management
```

### Security Checklist
- [ ] Change default MinIO credentials
- [ ] Enable firewall rules
- [ ] Use HTTPS in production
- [ ] Implement access logging
- [ ] Set up monitoring alerts
- [ ] Configure automated backups
- [ ] Use VPN for remote access

---

## 📊 Monitoring & Troubleshooting

### Health Monitoring
```bash
# Check all services
docker ps --filter "name=ipsw"

# Service health
curl http://localhost:8000/health | jq

# Detailed status
curl http://localhost:8000/status | jq
```

### Log Monitoring
```bash
# Docker logs
docker-compose logs -f api-server
docker-compose logs -f symbol-server

# Application logs
tail -f logs/symbolication.log
```

### Performance Monitoring
```bash
# System resources
docker stats

# Application metrics
curl http://localhost:8000/admin/metrics
```

### Common Issues & Solutions

#### 1. Server Won't Start
```bash
# Check Docker
docker info

# Check ports
netstat -tulpn | grep :8000

# Restart services
docker-compose down && docker-compose --profile regular up -d
```

#### 2. CLI Can't Connect
```bash
# Test connectivity
curl http://SERVER_IP:8000/health

# Check firewall
ping SERVER_IP
telnet SERVER_IP 8000
```

#### 3. Large File Upload Fails
```bash
# Use S3 console
open http://SERVER_IP:9001

# Or streaming CLI
ipsw-cli --local-ipsw large-file.ipsw crash.ips
```

#### 4. No Symbols Found
```bash
# Check available IPSWs
curl http://localhost:8000/ipsw/list

# Upload correct IPSW
# Via S3 console or CLI
```

---

## 📚 Documentation Links

### Complete Documentation Package
- **[Developer Documentation](DEVELOPER_DOCUMENTATION.md)** - Complete deployment and usage guide
- **[Quick Start Guide](QUICK_START_DEVELOPERS.md)** - Get started in 5 minutes
- **[API Reference](API_REFERENCE.md)** - Complete REST API documentation
- **[CLI Usage Guide](CLI_UNIFIED_USAGE.md)** - Command-line interface guide
- **[Unified Solution](README_UNIFIED_SOLUTION.md)** - Overview of the unified approach

### Package Downloads
- **`ipsw-unified-cli-complete-v1.2.5.tar.gz`** (7.5KB) - CLI tool with installer
- **`ipsw-symbol-server-v1.2.5.tar.gz`** (271MB) - Complete Docker deployment
- **`ipsw-symbol-server-complete-docs-v1.2.5.tar.gz`** (25KB) - All documentation

---

## 🎉 Summary for Development Teams

### ✅ What You Get
- **One unified tool** that works locally and over the network
- **Multiple access methods** - CLI, Web UI, S3 Console, REST API
- **Automatic file handling** - Small files direct, large files streaming
- **Team collaboration** - Shared server with multi-user support
- **Enterprise ready** - Production deployment options

### ✅ Installation Summary
```bash
# Individual developer
curl -L <download-url> | tar -xz && ./install-unified-cli.sh

# Team server  
docker-compose --profile regular up -d

# Team members
ipsw-cli --server http://TEAM_IP:8000 crash.ips
```

### ✅ Access Summary
```bash
# CLI (unified local + network)
ipsw-cli crash.ips                                    # Local
ipsw-cli --server http://TEAM_IP:8000 crash.ips       # Network

# Web interfaces
http://localhost          # Local web UI
http://TEAM_IP           # Team web UI  
http://TEAM_IP:9001      # S3 console

# API endpoints
http://localhost:8000    # Local API
http://TEAM_IP:8000      # Team API
```

### ✅ File Size Handling
- **< 1GB**: Direct CLI upload
- **> 1GB**: Automatic streaming or S3 console upload
- **Any size**: Web UI with progress tracking

### ✅ Integration Options
- **Shell scripts**: Simple curl commands
- **Python**: Full SDK with examples
- **JavaScript**: Node.js integration
- **CI/CD**: Automated pipeline integration

---

**🚀 Ready to revolutionize your iOS debugging workflow!**

*For support, questions, or feature requests, please contact the development team.* 