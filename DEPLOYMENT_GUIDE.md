# 🚀 IPSW Symbol Server v3.1.0 - Deployment Guide

## 📦 Complete Professional Deployment Package

### Package Contents: `ipsw-symbol-server-v3.1.0-deployment.tar.gz` (361MB)

- **🐳 Docker Images**: Complete containerized application
- **🛠️ CLI Tools**: Professional developer tools
- **📚 Documentation**: Comprehensive guides
- **⚙️ Configuration**: Ready-to-use setup files
- **🚀 Scripts**: One-click deployment automation

---

## 🌟 Key Features v3.1.0

### ⚡ Database-First Symbolication
- **10-20x faster** than previous versions
- **99% storage reduction** with symbol extraction
- **PostgreSQL backend** for enterprise reliability

### 🎨 Professional Developer Experience
- **Beautiful CLI tools** with rich terminal UI
- **One-click installation** for development teams
- **Remote server support** for distributed teams
- **Comprehensive error handling** with helpful suggestions

### 🔧 Enhanced Management
- **Background symbol extraction** with real-time progress
- **Automatic IPSW detection** and cataloging
- **Health monitoring** and statistics
- **Professional deployment** with verification

---

## 📋 Quick Deployment Steps

### 1. Transfer Package
```bash
# Upload to target server
scp ipsw-symbol-server-v3.1.0-deployment.tar.gz user@server:/opt/
```

### 2. Extract and Verify
```bash
# Extract package
cd /opt
tar -xzf ipsw-symbol-server-v3.1.0-deployment.tar.gz
cd ipsw-symbol-server-v3.1.0-deployment

# Verify package integrity
./verify-deployment.sh
```

### 3. Deploy System
```bash
# One-click deployment
./deploy.sh
```

### 4. Install Developer Tools
```bash
# Install CLI tools for local team
cd cli-tools
./install-dev-tools.sh
```

---

## 🔗 Access Points

After successful deployment:

- **🌐 Main Interface**: http://server:8082/
- **📤 Upload Interface**: http://server:8082/upload  
- **🔌 API Endpoint**: http://server:3993/
- **❤️ Health Check**: http://server:8082/health

---

## 🛠️ CLI Tools Usage

### System Status
```bash
ipsw-dev-cli --server http://server:8082 status
```

### Symbolicate Crashes
```bash
# Local symbolication
ipsw-symbolicate crash.ips

# Remote server
ipsw-dev-cli --server http://server:8082 symbolicate crash.ips
```

### Manage IPSW Files
```bash
# Add IPSW with symbol extraction
ipsw-dev-cli --server http://server:8082 add-ipsw iPhone_IPSW.ipsw

# Quick local alias
ipsw-add iPhone_IPSW.ipsw
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                IPSW Symbol Server v3.1.0                   │
├─────────────────────────────────────────────────────────────┤
│  🌐 Nginx (Port 8082)                                      │
│  ├── Reverse Proxy + Load Balancer                         │
│  └── Static File Serving                                   │
├─────────────────────────────────────────────────────────────┤
│  🐍 Flask Application (Port 3993)                          │
│  ├── RESTful API Endpoints                                 │
│  ├── Symbol Extraction Engine                              │
│  ├── Database-First Symbolication                          │
│  └── IPSW Management System                                │
├─────────────────────────────────────────────────────────────┤
│  🗄️ PostgreSQL Database (Port 5432)                        │
│  ├── Symbol Storage (99% space savings)                    │
│  ├── IPSW Metadata Catalog                                │
│  ├── Scan Status Tracking                                  │
│  └── Performance Analytics                                 │
└─────────────────────────────────────────────────────────────┘

External CLI Tools:
├── ipsw-dev-cli (Unified interface)
├── ipsw-symbolicate (Direct symbolication)
├── ipsw-add (IPSW management)
└── Remote server support
```

---

## 🔧 Configuration Options

### Environment Variables
```bash
# Database connection
DATABASE_URL=postgresql://symboluser:symbolpass@symbol-db:5432/symbols

# Application settings
KERNEL_SIGS_DIR=/app/symbolicator/kernel
UPLOAD_DIR=/app/uploads

# Performance tuning
MAX_WORKERS=4
TIMEOUT=300
```

### Port Configuration
```yaml
# docker-compose.yml
ports:
  - "8082:80"    # Nginx (main interface)
  - "3993:3993"  # Flask API
  - "5432:5432"  # PostgreSQL (optional external access)
```

---

## 🐛 Troubleshooting

### Common Deployment Issues

#### Docker Not Available
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose
```

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :8082
sudo netstat -tulpn | grep :3993

# Stop conflicting services
sudo systemctl stop nginx  # if using system nginx
```

#### Permission Issues
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix file permissions
sudo chown -R $USER:$USER ipsw-symbol-server-v3.1.0-deployment/
```

### Service Health Checks

#### Check Container Status
```bash
docker-compose ps
docker-compose logs symbol-server
docker-compose logs symbol-db
```

#### Verify API Endpoints
```bash
# Health check
curl http://localhost:8082/health

# API status
curl http://localhost:3993/v1/_ping

# Symbol statistics
curl http://localhost:8082/v1/syms/stats
```

#### Database Connection
```bash
# Test database
docker-compose exec symbol-db psql -U symboluser -d symbols -c "SELECT COUNT(*) FROM symbols;"
```

---

## 📈 Performance Optimization

### Database Tuning
```sql
-- Monitor symbol extraction progress
SELECT scan_id, status, symbols_extracted, created_at 
FROM scanned_ipsw 
ORDER BY created_at DESC;

-- Check database size
SELECT pg_size_pretty(pg_database_size('symbols')) as database_size;
```

### System Monitoring
```bash
# Resource usage
docker stats

# Disk usage
du -sh ipsw_files/
du -sh symbols/

# Log monitoring
tail -f logs/symbol-server.log
```

---

## 🔐 Security Considerations

### Network Security
- Configure firewall rules for ports 8082, 3993
- Use HTTPS in production with SSL certificates
- Implement authentication for sensitive environments

### Data Protection
- Regular database backups
- Secure IPSW file storage
- Access logging and monitoring

### Container Security
- Regular image updates
- Security scanning
- Resource limits

---

## 🎯 Production Deployment Checklist

- [ ] **System Requirements**: Docker, Docker Compose installed
- [ ] **Package Verification**: SHA256 checksum validated
- [ ] **Network Configuration**: Ports 8082, 3993 available
- [ ] **Storage**: Sufficient disk space (recommend 50GB+)
- [ ] **Memory**: Minimum 4GB RAM, recommend 8GB+
- [ ] **Deployment**: `./deploy.sh` completed successfully
- [ ] **Health Check**: All endpoints responding
- [ ] **CLI Tools**: Developer tools installed and tested
- [ ] **Documentation**: Team onboarded with guides
- [ ] **Monitoring**: Health checks configured
- [ ] **Backups**: Database backup strategy implemented

---

## 🎉 Success Metrics

After deployment, you should see:

- **⚡ Fast Symbolication**: 2-5 seconds vs 30-60 seconds
- **💾 Storage Efficiency**: 99% reduction after symbol extraction  
- **🎨 Developer Experience**: Beautiful CLI tools working
- **📊 System Health**: All services green in status checks
- **🚀 Team Productivity**: Streamlined crash analysis workflow

---

## 📞 Support Resources

- **📚 Complete Documentation**: `/docs/` directory
- **🛠️ CLI Guide**: `docs/DEVELOPER_TOOLS.md`
- **📖 API Reference**: `docs/API_USAGE.md`
- **🔧 IPSW Management**: `docs/IPSW_SCANNING_GUIDE.md`

---

**🚀 Ready for professional iOS development with IPSW Symbol Server v3.1.0!**

*Complete deployment package with Docker images, CLI tools, and comprehensive documentation.*
