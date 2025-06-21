# IPSW Auto-Symbolicate Server

Enterprise-ready iOS crash symbolication system with **unified deployment** supporting both regular and **airgap environments**.

## 🎯 Key Features

✅ **Fully Automated Workflow** - True end-to-end automation from IPSW upload to symbolication (v1.2.4)  
✅ **Real-Time S3 Detection** - Symbol Server automatically detects new files without manual restarts  
✅ **Unified Deployment** - Single Docker Compose file for all environments  
✅ **Complete Airgap Support** - Pre-built images with all dependencies for secure offline deployments  
✅ **Auto-Symbolication** - Intelligent IPSW detection, download, and symbol extraction  
✅ **Device Mapping** - Automatic translation between marketing names (iPhone 14 Pro) and identifiers (iPhone15,2)  
✅ **AppleDB Integration** - Complete device database for offline device identification  
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

> **✨ NEW in v1.2.4**: Upload IPSW files to S3 and the system automatically detects, processes, and generates symbols within 5 minutes. No manual intervention required!

### Airgap/Offline Deployment (no internet required)
> **IMPORTANT: In airgap/offline mode, all dependencies (AppleDB, symbolicator, CLI, IPSW, etc.) are pre-included. No internet access required during operation.**

1. Extract the provided package (includes pre-built Docker images and offline data)
2. Start services:
```bash
docker-compose --profile airgap up -d
```
3. The system includes:
   - Complete AppleDB database for device mapping
   - IPSW CLI tool pre-installed
   - All required dependencies bundled
4. Upload IPSW files to MinIO and the system will automatically:
   - Map device names (iPhone 14 Pro → iPhone15,2)
   - Extract and cache symbols
   - Enable full crash symbolication

## 📋 Deployment Options

| Type | Use Case | Features | Command |
|------|----------|----------|---------|
| **Regular** | Development teams | Builds images, internal MinIO, auto-downloads | `./deploy-regular.sh` |
| **Airgap** | Secure environments | Pre-built images, offline device mapping, manual IPSW upload | `./deploy-airgap.sh` |

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
                  │
          [AppleDB Device Mapping]
     (Offline device identification)
```

## 🛠️ System Components

### Core Services
- **Symbol Server** - Core symbolication engine with blacktop/symbolicator integration
- **API Server** - Auto-detection, download, and symbolication REST API
- **Web UI** - User-friendly interface for crash file upload and analysis
- **PostgreSQL** - Symbol database with 25,000+ cached symbols
- **Nginx** - Reverse proxy with documentation and health monitoring

### Intelligence & Mapping
- **Device Mapper** - Translates marketing names to device identifiers using AppleDB
- **AppleDB Integration** - Complete offline device database (iPhone, iPad, etc.)
- **Auto-Detection** - Intelligent IPSW scanning and download from S3
- **Auto-Scan** - Automatic symbol extraction when matching IPSW is found

### Storage & Performance
- **Auto-Cleanup** - Automatic deletion of IPSW files after symbol extraction
- **Space Optimization** - 99% storage savings (18.8GB+ saved automatically)
- **Multi-Device Support** - All iPhone, iPad, iPod, Apple Watch, and Apple TV models
- **Smart Caching** - Intelligent symbol caching with device-specific keys

## 📊 Supported Devices & iOS Versions

The system includes complete AppleDB integration supporting **all Apple devices**:

| Device Category | Examples | Support Level |
|----------------|----------|---------------|
| **iPhone** | iPhone 14 Pro → iPhone15,2 | ✅ Full mapping & symbolication |
| **iPad** | iPad Pro → iPad14,3 | ✅ Full mapping & symbolication |
| **Apple Watch** | Apple Watch Series 9 → Watch6,18 | ✅ Device mapping available |
| **Apple TV** | Apple TV 4K → AppleTV11,1 | ✅ Device mapping available |
| **iPod** | iPod touch → iPod9,1 | ✅ Device mapping available |

### Example Symbolication Results
```
Device: iPhone 14 Pro (mapped from iPhone15,2)
iOS Version: iPhone OS 18.5 (22F76)
Symbols Found: 21,206 kernel symbols
Success Rate: 100%
Processing Time: ~30 seconds
```

## 🔧 Management & Monitoring

### Health Endpoints
- **System Health**: `GET /health`
- **API Status**: `GET /v1/system-status`
- **Storage Usage**: `GET /v1/disk-usage`
- **Auto-Scan**: `POST /v1/auto-scan`
- **Available IPSWs**: `GET /v1/ipsws`
- **🆕 Cache Refresh**: `POST /refresh-cache` - Force refresh of IPSW cache for both API and Symbol servers

### Service URLs
- **Main Portal**: http://localhost (Nginx)
- **Web UI**: http://localhost:5001
- **API Documentation**: http://localhost:8000/docs
- **Symbol Server**: http://localhost:3993
- **MinIO Console**: http://localhost:9001 (regular deployment)

### Device Mapping Example
```bash
# CLI automatically maps device names
ipsw-cli crash.ips
# Input: "iPhone 14 Pro" → Auto-mapped to "iPhone15,2"
# System finds: iPhone15,2_18.5_22F76_Restore.ipsw
# Result: Full symbolication with 21,206 symbols
```

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

### Complete Offline Support
- **No Internet Required** - All dependencies pre-included in Docker images
- **AppleDB Included** - Complete device mapping database (2000+ devices)
- **IPSW CLI Bundled** - No external downloads required
- **Internal S3 Support** - Self-contained MinIO with auto-bucket creation
- **Device Intelligence** - Full device name mapping without external API calls

### Security Features
- **Network Isolation** - All services communicate internally only
- **Pre-built Images** - No external dependencies during runtime
- **Offline Transfer** - Complete package for secure environment deployment
- **Zero External Calls** - No git clone, curl, or wget operations during use

### Deployment Process
1. **Build Phase** (connected environment): Download all dependencies once
2. **Package Phase**: Create complete airgap package with images and data
3. **Transfer Phase**: Move package to secure environment
4. **Deploy Phase** (airgap): `docker-compose --profile airgap up -d`

## 🛡️ Enterprise Features

### High Availability
- Health checks for all services
- Automatic restart policies
- Graceful degradation handling
- Comprehensive logging and monitoring

### Integration Ready
- **REST API** - Full automation support with device mapping
- **Docker Compose** - Container orchestration
- **Environment Variables** - Flexible configuration
- **Volume Mounting** - Persistent data storage

### Performance Optimization
- **Intelligent Caching** - Multi-level symbol caching with device-specific keys
- **Device Mapping Cache** - Fast offline device name resolution
- **Concurrent Processing** - Configurable parallel downloads
- **Resource Management** - Memory and disk usage optimization
- **Auto-Cleanup** - Automatic space management

## 🚀 Development Team Integration

### 🎨 CLI Tool - Beautiful Terminal Interface

**Features:**
- 🎨 **Rich Terminal Output** - Beautiful tables, colors, and progress indicators
- 📊 **Detailed Statistics** - Symbol counts, success rates, quality indicators
- 🔍 **Syntax Highlighting** - Code output with line numbers
- 📱 **Smart Device Detection** - Automatic device mapping (iPhone 14 Pro → iPhone15,2)
- 💾 **Export Options** - Save results to JSON files
- ⚡ **Cross-Platform** - Works on macOS, Linux, and Windows

**Usage Examples:**
```bash
# Basic symbolication with auto device mapping
ipsw-cli crash.ips
# → Automatically maps device names and finds matching IPSW

# Custom server
ipsw-cli crash.ips --server http://your-server:8000

# Full output with rich formatting
ipsw-cli crash.ips --full

# Save results to JSON
ipsw-cli crash.ips --save results.json
```

📖 **[→ CLI Documentation](CLI_USAGE.md) ←**

### For iOS Developers
```bash
# Method 1: Beautiful CLI (Recommended)
ipsw-cli crash.ips
# → Auto-detects "iPhone 14 Pro", maps to "iPhone15,2"
# → Finds matching IPSW, extracts 21,206 symbols
# → Returns fully symbolicated crash report

# Method 2: Direct API
curl -X POST http://localhost:8000/v1/symbolicate \
  -F "crash_file=@crash.ips"
```

### For QA Teams
1. **Web UI**: http://localhost:5001 - Upload files via drag-and-drop
2. **CLI Tool**: `ipsw-cli crash.ips` - Professional terminal interface with device mapping
3. View symbolicated results instantly with device information

### For DevOps Teams
```bash
# Monitor system health
curl http://localhost:8000/v1/system-status

# Check available IPSWs and device mapping
curl http://localhost:3993/v1/ipsws

# 🆕 Force cache refresh after uploading new IPSW files
curl -X POST "http://localhost:8000/refresh-cache"

# Trigger auto-scan for specific device
curl -X POST "http://localhost:3993/v1/auto-scan?device_model=iPhone%2014%20Pro&ios_version=18.5"

# 🆕 Upload multi-device IPSW and refresh cache
curl -X PUT "http://localhost:9000/ipsw/iPhone12,3,iPhone12,5_18.3.2_22D82_Restore.ipsw" \
  --data-binary @your-multi-device.ipsw
curl -X POST "http://localhost:8000/refresh-cache"
```

## 🔄 Recent Updates (v1.2.4)

### 🐛 CRITICAL FIX: Symbol Server S3 Synchronization
- **🚨 Fixed Symbol Server Auto-Detection** - Symbol Server now automatically detects new IPSW files from S3 without manual restart
- **🔧 Persistent S3Manager** - Added persistent S3Manager to Symbol Server, eliminating temporary instance issues
- **⚡ Enhanced Cache Refresh** - Fixed refresh-cache endpoint to work seamlessly with Symbol Server
- **🚀 True End-to-End Automation** - System now works as originally intended - fully automated from IPSW upload to symbolication

### 🛠️ Technical Improvements
- **Real-Time S3 Detection** - Symbol Server now maintains persistent connection to S3 storage
- **Improved File Watcher Integration** - Enhanced coordination between File Watcher and Symbol Server
- **FUSE Support Enhancement** - Better IPSW extraction capabilities with apfs-fuse integration
- **Memory Optimization** - Reduced container restart requirements with persistent managers

### 📈 Workflow Now Fully Automated
```bash
# Before v1.2.4 (required manual intervention):
aws s3 cp newfile.ipsw s3://ipsw/                    # Upload
# Manual: docker-compose restart symbol-server       # ❌ Required
# Manual: curl -X POST ".../refresh-cache"           # ❌ Required  
# Manual: curl -X POST ".../auto-scan"               # ❌ Required

# After v1.2.4 (fully automated):
aws s3 cp newfile.ipsw s3://ipsw/                    # Upload
# Wait 5 minutes - File Watcher detects automatically
# Symbol Server auto-refreshes cache
# Auto-scan runs automatically  
# Symbols generated automatically
ipsw-cli newcrash.ips                                # ✅ Just works!
```

### Previous Updates (v1.2.3)

### ✨ Major New Features
- **🆕 Multi-Device IPSW Support** - Automatically handles IPSW files containing multiple device models (e.g., `iPhone12,3,iPhone12,5_18.3.2_22D82_Restore.ipsw`)
- **🆕 Manual Cache Refresh** - New endpoint `POST /refresh-cache` to force cache updates when new IPSW files are uploaded
- **🆕 Real-time IPSW Detection** - Instant recognition of newly uploaded files without container restarts

### 🔧 Advanced Technical Improvements
- **Enhanced IPSW Parser** - Intelligent parsing of multi-device filename patterns with device model separation
- **Dual Cache Management** - Coordinated refresh of both API server and Symbol server caches
- **Smart Device Matching** - Improved logic to match individual device models within multi-device IPSW files
- **Performance Optimization** - Version/build checking before device matching for faster lookups

### 🛠️ Cache Management
- **Automatic Detection** - System now detects when IPSW files are added to S3 storage
- **Manual Refresh** - `curl -X POST "http://localhost:8000/refresh-cache"` to force immediate cache update
- **Coordinated Updates** - Both API and Symbol servers refresh simultaneously

### 📦 Multi-Device IPSW Examples
```bash
# These IPSW files are now fully supported:
iPhone12,3,iPhone12,5_18.3.2_22D82_Restore.ipsw  # iPhone 11 Pro + iPhone 11 Pro Max
iPhone13,1,iPhone13,2_18.5_22F76_Restore.ipsw    # iPhone 12 mini + iPhone 12
iPhone14,4,iPhone14,5_18.5_22F76_Restore.ipsw    # iPhone 13 mini + iPhone 13

# System automatically finds the right device:
# Search for "iPhone12,3" → Finds in "iPhone12,3,iPhone12,5_..." file ✅
# Search for "iPhone 11 Pro" → Maps to "iPhone12,3" → Finds in multi-device file ✅
```

### Previous Updates (v1.2.0)
- **Complete Device Mapping** - AppleDB integration for all Apple devices
- **Enhanced Airgap Support** - Zero internet dependencies during operation
- **Smart Auto-Scan** - Automatic device name mapping and IPSW detection
- **Improved CLI** - Better device detection and mapping feedback
- Fixed S3 endpoint configuration for containerized environments
- Enhanced device filtering logic in S3 IPSW discovery
- Bundled AppleDB database in Docker images

---

**Ready for enterprise deployment with complete offline support!** 🚀 