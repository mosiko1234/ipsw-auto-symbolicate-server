# 🛠 IPSW Symbol Server

A production-ready iOS crash symbolication system using the official [ipsw CLI](https://github.com/blacktop/ipsw) tool.

## 🎯 Overview

This system provides a complete solution for iOS crash symbolication with two main workflows:

### 🔧 For DevOps Teams
- **Scan IPSW files** and store metadata in PostgreSQL database
- **Manage symbol repositories** with automatic tracking
- **Monitor system status** and scan history

### 👨‍💻 For Developers
- **Upload crashlogs** via web interface or API
- **Get symbolicated results** instantly
- **Download processed files** with full symbol information

## ⚡ Quick Start

### 1. Start the System
```bash
git clone <repository-url>
cd ipsw-symbol-server
docker-compose up -d
```

### 2. Add IPSW Files (DevOps)
```bash
# Copy IPSW file to shared directory
cp ~/Downloads/iPhone15,2_17.5_21F79_Restore.ipsw ipsw_files/

# Scan using helper script
./add_ipsw.sh ipsw_files/iPhone15,2_17.5_21F79_Restore.ipsw
```

### 3. Symbolicate Crashes (Developers)
```bash
# Option 1: Web Interface
open http://localhost:8082/upload

# Option 2: Command Line
./symbolicate.sh crash.ips

# Option 3: Direct API
curl -F "crashlog=@crash.ips" http://localhost:3993/v1/symbolicate
```

## 🌐 Web Interfaces

### Main Interface
- **Direct**: http://localhost:3993/
- **Via Nginx**: http://localhost:8082/

### Upload Interface
- **Crash Symbolication**: http://localhost:8082/upload
- Drag & drop .ips files
- Instant results with download option
- Shows available IPSW versions

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/_ping` | GET | Health check |
| `/v1/ipsw/list` | GET | List available IPSW files |
| `/v1/syms/scan` | POST | Scan IPSW file |
| `/v1/symbolicate` | POST | Symbolicate crashlog |
| `/v1/syms/scans` | GET | List scan history |
| `/health` | GET | Detailed system status |
| `/upload` | GET | Web upload interface |

## 📁 Project Structure

```
ipsw-symbol-server/
├── ipsw_files/           # 📥 Place IPSW files here
├── crashlogs/            # 📂 Optional crashlog storage
├── uploads/              # 📤 API uploaded files
├── symbols/              # 🔍 Extracted symbols
├── add_ipsw.sh          # 🔧 IPSW addition helper
├── symbolicate.sh       # 🔧 Symbolication helper
├── simple_app.py        # 🐍 Python Flask server
├── docker-compose.yml   # 🐳 Container orchestration
├── nginx.conf           # 🌐 Reverse proxy config
├── QUICK_START.md       # 🚀 Quick reference
└── API_USAGE.md         # 📖 Detailed documentation
```

## 🛠 Helper Scripts

### add_ipsw.sh
Automates IPSW file addition:
```bash
./add_ipsw.sh path/to/file.ipsw
```
- Copies file to shared directory
- Verifies detection
- Performs scan
- Shows results

### symbolicate.sh
Automates crash symbolication:
```bash
./symbolicate.sh crash.ips [output.txt]
```
- Checks system status
- Processes crashlog
- Saves results
- Shows preview

## 🔍 System Components

### Core Services
- **Python Flask Server** - Main API and web interface
- **PostgreSQL Database** - IPSW metadata and scan tracking
- **Nginx Proxy** - Load balancing and static file serving
- **ipsw CLI** - Official symbolication engine

### Key Features
- **Multi-format Support** - JSON, form-data, file uploads
- **Automatic IPSW Detection** - Smart matching based on crash metadata
- **Large File Handling** - 15GB file upload limit via nginx
- **Production Ready** - Health checks, logging, error handling
- **Flexible Architecture** - Shared directory for easy file management

## 📊 Usage Examples

### DevOps: Bulk IPSW Processing
```bash
for ipsw in ~/Downloads/*.ipsw; do
    ./add_ipsw.sh "$ipsw"
done
```

### Developer: Batch Symbolication
```bash
for crash in *.ips; do
    ./symbolicate.sh "$crash"
done
```

### API Integration
```bash
# Check available IPSW files
curl http://localhost:3993/v1/ipsw/list | jq '.ipsw_files[].device_model'

# Symbolicate with specific IPSW
curl -X POST http://localhost:3993/v1/symbolicate \
  -H "Content-Type: application/json" \
  -d '{"crashlog": "...", "ipsw": "/app/ipsw_files/specific.ipsw"}'
```

## 🔒 System Requirements

- **Docker & Docker Compose**
- **15GB+ disk space** (for IPSW files)
- **4GB+ RAM** (for large file processing)
- **jq** (for JSON processing in scripts)

## 🎯 Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/symbols
KERNEL_SIGS_DIR=/app/symbolicator/kernel
UPLOAD_DIR=/app/uploads
```

### Port Configuration
- **3993** - Python server (direct access)
- **8082** - Nginx proxy (recommended)
- **5432** - PostgreSQL (database access)

### Volume Mounts
- `./ipsw_files` - Shared IPSW storage
- `./uploads` - API uploaded files
- `./symbolicator/kernel` - Kernel signatures
- `postgres_data` - Database persistence

## 🐛 Troubleshooting

### Server Issues
```bash
# Check logs
docker-compose logs symbol-server

# Restart system
docker-compose restart

# Full rebuild
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

### Symbolication Issues
```bash
# Verify IPSW files
curl http://localhost:3993/v1/ipsw/list

# Test ipsw CLI
docker exec symbol-server ipsw version

# Check system health
curl http://localhost:3993/health
```

## 📝 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Fast setup and common tasks
- **[API_USAGE.md](./API_USAGE.md)** - Comprehensive API documentation

## 🚀 System Status

✅ **Production Ready** - Full symbolication pipeline  
✅ **Web Interface** - Upload and process files via browser  
✅ **API Complete** - REST endpoints for automation  
✅ **Docker Orchestrated** - Easy deployment and scaling  
✅ **Fully Documented** - Comprehensive guides and examples  

---

**Ready for production deployment! 🎉** 