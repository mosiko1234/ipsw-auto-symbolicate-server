# 📚 IPSW Symbol Server - Documentation

**Complete documentation suite for iOS crash symbolication platform**

---

## 🎯 Quick Navigation

| Need | Document | Time |
|------|----------|------|
| **Get started fast** | [Quick Start Guide](#-quick-start-guide) | 5 min |
| **Team deployment** | [Development Teams Guide](#-development-teams-guide) | 15 min |
| **Technical details** | [Developer Documentation](#-developer-documentation) | 30 min |
| **API integration** | [API Reference](#-api-reference) | 20 min |
| **CLI mastery** | [CLI Usage Guide](#-cli-usage-guide) | 10 min |

---

## 📖 Core Documentation

### 🚀 Quick Start Guide
**File**: [`QUICK_START_DEVELOPERS.md`](QUICK_START_DEVELOPERS.md)  
**Perfect for**: First-time users, rapid deployment

Get up and running with iOS crash symbolication in 5 minutes. Covers:
- Personal setup (single developer)
- Team server deployment  
- Basic usage examples
- Common workflows

**Start here** if you want to try the system immediately.

---

### 🏢 Development Teams Guide
**File**: [`README_DEVELOPMENT_TEAMS.md`](README_DEVELOPMENT_TEAMS.md)  
**Perfect for**: Team leads, project managers

Complete guide for development teams. Covers:
- All deployment scenarios (individual → enterprise)
- Access methods: CLI, Web UI, S3 Console, REST API
- System architecture and configuration
- Network setup and security
- Monitoring and troubleshooting

**Start here** if you're setting up for a team.

---

### 🔧 Developer Documentation  
**File**: [`DEVELOPER_DOCUMENTATION.md`](DEVELOPER_DOCUMENTATION.md)  
**Perfect for**: DevOps engineers, system administrators

Complete technical deployment and operations guide. Covers:
- Detailed system architecture
- All deployment options (Docker, Airgap, Development)
- Network configuration and security
- Advanced features and optimization
- Production deployment best practices

**Start here** for production deployments.

---

### 🔌 API Reference
**File**: [`API_REFERENCE.md`](API_REFERENCE.md)  
**Perfect for**: Developers building integrations

Complete REST API documentation. Covers:
- All endpoints with detailed examples
- Request/response formats
- Code examples (Python, JavaScript, Shell)
- Error handling and rate limiting
- OpenAPI specification

**Start here** for custom integrations.

---

### 💻 CLI Usage Guide
**File**: [`CLI_UNIFIED_USAGE.md`](CLI_UNIFIED_USAGE.md)  
**Perfect for**: Command-line users

Complete unified CLI documentation. Covers:
- Smart auto-detection features
- Local vs. network usage
- Advanced options and workflows
- Migration from separate CLIs

**Start here** if you prefer command-line tools.

---

## 🛠️ Deployment & Operations

### 📋 Deployment Guide
**File**: [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)  
Comprehensive deployment instructions. Covers:
- Step-by-step installation for all environments
- Configuration options and customization
- Troubleshooting and performance optimization
- Security considerations

### ⚡ Quick Deployment
**File**: [`DEPLOYMENT_QUICK_START.md`](DEPLOYMENT_QUICK_START.md)  
Fast deployment guide. Covers:
- Rapid deployment commands
- Essential configuration
- Basic testing and validation

### 🔒 Airgap Deployment
**File**: [`AIRGAP_DEPLOYMENT.md`](AIRGAP_DEPLOYMENT.md)  
Secure offline deployment guide. Covers:
- Airgap environment setup
- Pre-built images and dependencies
- Offline device mapping and symbolication
- Security features and considerations

### 💻 Legacy CLI Usage
**File**: [`CLI_USAGE.md`](CLI_USAGE.md)  
Original CLI documentation (before unified CLI). Covers:
- Traditional CLI features
- Historical usage patterns
- Migration guidance to unified CLI

---

## 🌐 Network & Team Collaboration

### 📡 Network Usage Guide
**File**: [`NETWORK_USAGE.md`](NETWORK_USAGE.md)  
Comprehensive network deployment guide (Hebrew). Covers:
- Remote server access
- Client installation for network usage
- Firewall and network configuration
- Team collaboration setup

### 🌍 Network Quick Setup
**File**: [`QUICK_NETWORK_SETUP.md`](QUICK_NETWORK_SETUP.md)  
Fast network setup instructions (Hebrew). Covers:
- Quick network client setup
- Essential URLs and commands
- Basic troubleshooting

### 📋 Network README
**File**: [`README_NETWORK.md`](README_NETWORK.md)  
Network access overview (Hebrew). Covers:
- Network accessibility confirmation
- Client distribution
- Usage examples

---

## 🎯 Advanced Features

### 🔍 Kernel Symbolication
**File**: [`KERNEL_SYMBOLICATION.md`](KERNEL_SYMBOLICATION.md)  
Advanced kernel crash analysis. Covers:
- Kernel-specific symbolication features
- Advanced crash analysis techniques
- Kernel symbol extraction and usage

### 🤖 Auto-Detection Features
**File**: [`README_AUTO_DETECTION.md`](README_AUTO_DETECTION.md)  
Intelligent auto-detection capabilities. Covers:
- Automatic device mapping
- Smart IPSW detection
- Intelligent symbol extraction
- Auto-scan features

---

## 📋 Reference & Overview

### 📚 Documentation Index
**File**: [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md)  
Complete navigation guide for all documentation. Covers:
- Which document for which use case
- Documentation flow and cross-references
- Package information

### 🎉 Unified Solution Overview
**File**: [`README_UNIFIED_SOLUTION.md`](README_UNIFIED_SOLUTION.md)  
Overview of the unified CLI approach. Covers:
- What changed and why
- Before vs. after comparison
- New features and benefits
- Migration guidance

---

## 🎯 Documentation by Role

### 👨‍💻 Individual Developer
1. [Quick Start Guide](#-quick-start-guide) - Get started in 5 minutes
2. [CLI Usage Guide](#-cli-usage-guide) - Master the unified command line
3. [API Reference](#-api-reference) - For custom scripts and automation

### 👥 Team Lead / Project Manager
1. [Development Teams Guide](#-development-teams-guide) - Complete team overview
2. [Quick Start Guide](#-quick-start-guide) - Understand the basics
3. [Deployment Guide](#-deployment--operations) - Planning deployment

### 🔧 DevOps / System Admin
1. [Developer Documentation](#-developer-documentation) - Full deployment guide
2. [Deployment Guide](#-deployment--operations) - Step-by-step instructions
3. [Airgap Deployment](#-deployment--operations) - Secure environments
4. [Network Usage Guide](#-network--team-collaboration) - Network setup

### 🔌 Integration Developer
1. [API Reference](#-api-reference) - Complete API documentation
2. [Developer Documentation](#-developer-documentation) - System architecture
3. [CLI Usage Guide](#-cli-usage-guide) - CLI automation and scripting

### 🏢 Enterprise / Security Teams
1. [Airgap Deployment](#-deployment--operations) - Secure offline deployment
2. [Developer Documentation](#-developer-documentation) - Security features
3. [Deployment Guide](#-deployment--operations) - Production considerations

---

## 📦 Available Packages

| Package | Size | Contents | Best For |
|---------|------|----------|----------|
| **ipsw-unified-cli-complete-v1.2.5.tar.gz** | 7.5KB | CLI + installer + docs | Individual developers |
| **ipsw-symbol-server-v1.2.5.tar.gz** | 271MB | Complete Docker deployment | Server deployment |
| **ipsw-symbol-server-ultimate-v1.2.5.tar.gz** | 29KB | All documentation + CLI | Complete solution |

---

## 🚀 Quick Start Summary

### Option 1: Personal Use
```bash
# Download and install CLI
curl -L <download-url> | tar -xz && ./install-unified-cli.sh

# Start using
ipsw-cli crash.ips
```

### Option 2: Team Server
```bash
# Deploy server
docker-compose --profile regular up -d

# Team members use
ipsw-cli --server http://TEAM_IP:8000 crash.ips
```

### Option 3: Just Browse
```bash
# Access web interface
open http://localhost        # Local
open http://TEAM_IP          # Team server
```

---

## 🔗 External Links

| Resource | URL | Description |
|----------|-----|-------------|
| **Web UI** | `http://localhost` or `http://SERVER_IP` | Visual interface |
| **S3 Console** | `http://localhost:9001` or `http://SERVER_IP:9001` | Large file uploads |
| **API Base** | `http://localhost:8000` or `http://SERVER_IP:8000` | REST API |
| **Health Check** | `http://SERVER_IP:8000/health` | Server status |

---

## 📞 Support & Resources

### Getting Help
- **New users**: Start with [Quick Start Guide](#-quick-start-guide)
- **Team deployment**: See [Development Teams Guide](#-development-teams-guide)  
- **Technical issues**: Check [Developer Documentation](#-developer-documentation)
- **API questions**: Refer to [API Reference](#-api-reference)
- **Deployment problems**: Use [Deployment Guide](#-deployment--operations)

### Additional Resources
- **Docker deployment**: See deployment guides in documentation
- **CLI installation**: Multiple installation methods covered
- **Network configuration**: Comprehensive network guides available
- **Troubleshooting**: Each guide includes troubleshooting sections
- **Advanced features**: Kernel symbolication and auto-detection guides

---

## 🏗️ System Overview

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

---

**🎯 Choose your starting point above and get iOS crash symbolication working today!** 