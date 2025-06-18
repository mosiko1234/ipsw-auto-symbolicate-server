# IPSW Auto-Symbolicate Server

Enterprise-ready iOS crash symbolication system with **unified deployment** supporting both regular and **airgap environments**.

## 🎯 Key Features

✅ **Unified Deployment** - Single Docker Compose file for all environments  
✅ **Airgap Support** - Pre-built images for secure offline deployments  
✅ **Auto-Symbolication** - Intelligent IPSW detection and symbol extraction  
✅ **Storage Management** - Auto-cleanup with 99% space savings  
✅ **Enterprise Ready** - PostgreSQL, Nginx, monitoring, and health checks  
✅ **Development Team Integration** - Web UI, API, and comprehensive documentation  
✅ **Beautiful CLI Tool** - Professional terminal interface for developers  

## 🚀 Quick Start

### Regular Deployment (with internet access)
```bash
git clone https://github.com/mosiko1234/ipsw-auto-symbolicate-server.git
cd ipsw-auto-symbolicate-server
./deploy-regular.sh
```
**Access**: http://localhost

### Airgap Deployment (secure/offline environments)
```bash
# 1. Prepare images (in connected environment)
./build-images-for-airgap.sh

# 2. Transfer to airgap environment
# 3. Deploy
./deploy-airgap.sh  
```

## 📋 Deployment Options

| Type | Use Case | Features | Command |
|------|----------|----------|---------|
| **Regular** | Development teams | Builds images, internal MinIO | `./deploy-regular.sh` |
| **Airgap** | Secure environments | Pre-built images, external S3 | `./deploy-airgap.sh` |

## 🏗️ System Architecture

```
         [Nginx Reverse Proxy]
                  │
    ┌─────────────┼─────────────┐
    │             │             │
[Web UI]    [API Server]   [Symbol Server]
    │             │             │
    └─────────────┼─────────────┘
                  │
          [PostgreSQL Database]
                  │
              [S3 Storage]
     (Internal MinIO / External)
```

## 🛠️ System Components

### Core Services
- **Symbol Server** - Core symbolication engine with blacktop/symbolicator integration
- **API Server** - Auto-detection, download, and symbolication REST API
- **Web UI** - User-friendly interface for crash file upload and analysis
- **PostgreSQL** - Symbol database with 25,000+ cached symbols
- **Nginx** - Reverse proxy with documentation and health monitoring

### Storage & Performance
- **Auto-Detection** - Intelligent IPSW scanning and download from S3
- **Auto-Cleanup** - Automatic deletion of IPSW files after symbol extraction
- **Space Optimization** - 99% storage savings (18.8GB+ saved automatically)
- **Multi-Device Support** - iPhone 15 Pro, iPhone 15 Pro Max, and more

## 📊 Supported Devices & iOS Versions

| Device | iOS Versions | Kernel Signatures |
|--------|--------------|-------------------|
| iPhone 15 Pro (iPhone15,2) | 18.2-19.0 | ✅ 21,208 symbols |
| iPhone 15 Pro Max (iPhone15,4) | 18.2-19.0 | ✅ 25,619 symbols |
| iPhone 17,3 | 18.5+ | ✅ 25,000+ symbols |

## 🔧 Management & Monitoring

### Health Endpoints
- **System Health**: `GET /health`
- **API Status**: `GET /v1/system-status`
- **Storage Usage**: `GET /v1/disk-usage`
- **Auto-Scan**: `POST /v1/auto-scan`

### Service URLs
- **Main Portal**: http://localhost (Nginx)
- **Web UI**: http://localhost:5001
- **API Documentation**: http://localhost:8000/docs
- **Symbol Server**: http://localhost:3993
- **MinIO Console**: http://localhost:9001 (regular deployment)

## 📖 Complete Documentation

For detailed deployment instructions, configuration options, and troubleshooting:

### 📚 [→ DEPLOYMENT GUIDE](DEPLOYMENT_GUIDE.md) ←

**Covers:**
- Step-by-step deployment for both environments
- Configuration options and customization
- Troubleshooting and performance optimization
- Security considerations for airgap deployments
- Monitoring, updates, and maintenance procedures

## 🔒 Airgap Deployment Highlights

### Security Features
- **No Internet Required** - All dependencies in pre-built images
- **Internal S3 Support** - Configurable internal storage endpoints
- **Offline Transfer** - Image archives for secure environment transfer
- **Network Isolation** - All services communicate internally

### Deployment Process
1. **Build Phase** (connected environment): `./build-images-for-airgap.sh`
2. **Transfer Phase**: Copy images to airgap environment
3. **Deploy Phase** (airgap): `./deploy-airgap.sh`

## 🛡️ Enterprise Features

### High Availability
- Health checks for all services
- Automatic restart policies
- Graceful degradation handling
- Comprehensive logging and monitoring

### Integration Ready
- **REST API** - Full automation support
- **Docker Compose** - Container orchestration
- **Environment Variables** - Flexible configuration
- **Volume Mounting** - Persistent data storage

### Performance Optimization
- **Intelligent Caching** - Multi-level symbol caching
- **Concurrent Processing** - Configurable parallel downloads
- **Resource Management** - Memory and disk usage optimization
- **Auto-Cleanup** - Automatic space management

## 🚀 Development Team Integration

### 🎨 CLI Tool - Beautiful Terminal Interface

**Quick Installation:**
```bash
curl -sSL https://github.com/mosiko1234/ipsw-auto-symbolicate-server/raw/main/install_cli.sh | bash
```

**Usage Examples:**
```bash
# Basic symbolication
ipsw-cli crash.ips

# Custom server
ipsw-cli crash.ips --server http://your-server:8000

# Full output with rich formatting
ipsw-cli crash.ips --full

# Save results to JSON
ipsw-cli crash.ips --save results.json
```

**Features:**
- 🎨 **Rich Terminal Output** - Beautiful tables, colors, and progress indicators
- 📊 **Detailed Statistics** - Symbol counts, success rates, quality indicators
- 🔍 **Syntax Highlighting** - Code output with line numbers
- 📱 **Device Information** - Automatic device/iOS version detection
- 💾 **Export Options** - Save results to JSON files
- ⚡ **Cross-Platform** - Works on macOS, Linux, and Windows

📖 **[→ CLI Documentation](CLI_USAGE.md) ←**

### For iOS Developers
```bash
# Method 1: Beautiful CLI (Recommended)
ipsw-cli crash.ips

# Method 2: Direct API
curl -X POST http://localhost:8000/v1/symbolicate \
  -F "crash_file=@crash.ips"
```

### For QA Teams
1. **Web UI**: http://localhost:5001 - Upload files via drag-and-drop
2. **CLI Tool**: `ipsw-cli crash.ips` - Professional terminal interface
3. View symbolicated results instantly with rich formatting

### For DevOps Teams
```bash
# Monitor system health
curl http://localhost:8000/v1/system-status

# Check storage usage
curl http://localhost:8000/v1/disk-usage

# Batch processing with CLI
find crashes/ -name "*.ips" -exec ipsw-cli {} --quiet --save {}.json \;
```

## 📈 Performance Metrics

- **Symbol Cache**: 25,000+ symbols across multiple iOS versions
- **Storage Savings**: 99% reduction (18.8GB+ saved automatically)
- **Processing Speed**: Optimized with tmpfs and concurrent downloads
- **Multi-Device**: Support for latest iPhone models and iOS versions

## 🔄 Updates & Maintenance

### Regular Environment
```bash
git pull origin main
./deploy-regular.sh
```

### Airgap Environment
```bash
# 1. Update in connected environment
./build-images-for-airgap.sh

# 2. Transfer and deploy in airgap
docker load -i ipsw-images-latest.tar
./deploy-airgap.sh
```

## 📞 Support & Contributing

- **Issues**: Open GitHub issues for bugs and feature requests
- **Documentation**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive setup
- **Security**: For security-related issues, please use private channels

## 📁 Project Structure

```
ipsw-auto-symbolicate-server/
├── docker/                     # Docker image definitions
│   ├── Dockerfile.api          # API server image
│   ├── Dockerfile.symbol-server # Symbol server image  
│   ├── Dockerfile.webui        # Web UI image
│   └── Dockerfile.nginx        # Nginx proxy image
├── scripts/                    # Deployment and management scripts
│   ├── deploy-regular.sh       # Regular deployment
│   ├── deploy-airgap.sh        # Airgap deployment
│   ├── build-images-for-airgap.sh # Image preparation
│   ├── start-server.sh         # Start services
│   └── stop-server.sh          # Stop services
├── config/                     # Environment configurations
│   ├── env.regular             # Regular environment
│   └── env.airgap              # Airgap environment
├── signatures/                 # blacktop/symbolicator signatures
├── data/                       # Runtime data (auto-created)
├── ipsw_cli.py                 # Beautiful CLI tool for developers
├── install_cli.sh              # CLI installation script
├── requirements-cli.txt        # CLI dependencies
├── CLI_USAGE.md                # CLI documentation
├── docker-compose.yml          # Unified deployment configuration
├── deploy-regular.sh           # Convenience script → scripts/
├── deploy-airgap.sh            # Convenience script → scripts/
└── DEPLOYMENT_GUIDE.md         # Detailed deployment instructions
```

---

**🎯 Enterprise-ready iOS crash symbolication with unified deployment for all environments** 

Built with ❤️ for development teams requiring both flexibility and security. 