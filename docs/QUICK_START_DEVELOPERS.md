# ⚡ IPSW Symbol Server - Developer Quick Start

**Get up and running with iOS crash symbolication in 5 minutes**

---

## 🎯 What You Get

- **Instant crash symbolication** for iOS apps
- **Kernel crash analysis** for advanced debugging  
- **Team collaboration** with shared server
- **Large IPSW support** (up to 10GB+)
- **Multiple interfaces**: CLI, Web UI, REST API

---

## 🚀 Option 1: Personal Use (Single Developer)

### Install CLI Tool
```bash
# Download and install (one command)
curl -L https://github.com/company/ipsw-symbol-server/releases/download/v1.2.5/ipsw-unified-cli-complete-v1.2.5.tar.gz | tar -xz && ./install-unified-cli.sh

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

### Use Immediately  
```bash
# Basic symbolication (server starts automatically)
ipsw-cli crash.ips

# With your own IPSW file
ipsw-cli --local-ipsw iPhone_iOS18.5.ipsw crash.ips

# Check what's happening
ipsw-cli --check
```

**That's it! The CLI automatically starts a local server and symbolicates your crashes.**

---

## 🏢 Option 2: Team Use (Shared Server)

### Server Setup (Run Once)
```bash
# On the server machine
git clone <repository>
cd ipsw-symbol-server

# Start all services
docker-compose --profile regular up -d

# Get server IP
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example output: 192.168.1.100
```

### Team Members
```bash
# Install CLI (same as above)
curl -L <download-link> | tar -xz && ./install-unified-cli.sh

# Use team server  
ipsw-cli --server http://192.168.1.100:8000 crash.ips

# Or use web interface
open http://192.168.1.100
```

---

## 🌐 Access Methods

### 1. CLI (Command Line)
```bash
# Local use
ipsw-cli crash.ips

# Team server
ipsw-cli --server http://TEAM_IP:8000 crash.ips

# Large IPSW files
ipsw-cli --local-ipsw huge-firmware.ipsw crash.ips
```

### 2. Web UI (Browser)
```
Local:  http://localhost
Team:   http://TEAM_IP
```
- Drag & drop crash files
- View symbolicated output
- Download results

### 3. S3 Console (Large Files)
```
Local:  http://localhost:9001
Team:   http://TEAM_IP:9001
```
- **Login**: `minioadmin` / `minioadmin`
- Upload large IPSW files (>1GB)
- Manage file storage

### 4. REST API (Automation)
```bash
# Basic symbolication
curl -X POST -F "file=@crash.ips" http://localhost:8000/symbolicate

# With local IPSW
curl -X POST \
  -F "ipsw_file=@firmware.ipsw" \
  -F "ips_file=@crash.ips" \
  http://localhost:8000/local-ipsw-symbolicate
```

---

## 📋 Key API Endpoints

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/health` | GET | Server status |
| `/symbolicate` | POST | Basic crash symbolication |
| `/local-ipsw-symbolicate` | POST | With local IPSW |
| `/local-ipsw-symbolicate-stream` | POST | Large files (auto-selected) |
| `/status` | GET | Detailed server info |

---

## 🔧 Common Workflows

### Workflow 1: Daily Development
```bash
# When you get a crash report
ipsw-cli crash.ips

# If you need specific IPSW
ipsw-cli --local-ipsw MyApp_iOS18.5.ipsw crash.ips
```

### Workflow 2: Team Debugging
```bash
# Everyone uses team server  
ipsw-cli --server http://team-server:8000 crash.ips

# Share results via web UI
open http://team-server/results/abc123
```

### Workflow 3: Large IPSW Files
```bash
# Option A: Upload via web console
open http://localhost:9001  # Upload to S3
ipsw-cli crash.ips          # Auto-uses uploaded IPSW

# Option B: CLI streaming (automatic for >1GB)
ipsw-cli --local-ipsw iPhone_10GB.ipsw crash.ips
```

### Workflow 4: Automation/CI
```python
import requests

# Symbolicate in CI pipeline
with open('crash.ips', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://build-server:8000/symbolicate', files=files)
    result = response.json()
    
print(f"Success: {result['success']}")
print(f"Device: {result['file_info']['device_model']}")
```

---

## 🎛️ Configuration Options

### Environment Variables
```bash
# Server configuration
CACHE_SIZE_GB=100              # Symbol cache size
CLEANUP_AFTER_HOURS=24         # Auto-cleanup interval
MAX_CONCURRENT_DOWNLOADS=3     # Parallel IPSW downloads

# S3 configuration  
S3_ENDPOINT=http://minio:9000
S3_BUCKET=ipsw
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

### CLI Options
```bash
# Show all options
ipsw-cli --help

# Key options:
--server URL        # Connect to remote server
--local-ipsw FILE   # Use local IPSW file  
--check            # Check server status
--full             # Show complete output
--save FILE        # Save results to JSON
--quiet            # Minimal output
--no-banner        # Skip banner
```

---

## 🔍 Troubleshooting

### CLI Issues
```bash
# Server won't start
docker ps --filter "name=ipsw"
docker-compose logs api-server

# Can't connect to remote server  
curl http://TEAM_IP:8000/health
ping TEAM_IP

# Large file upload fails
# → Use S3 console: http://TEAM_IP:9001
```

### Common Fixes
```bash
# Reset everything
docker-compose down && docker-compose --profile regular up -d

# Check ports
netstat -tulpn | grep :8000

# Update CLI
rm ~/.local/bin/ipsw-cli && ./install-unified-cli.sh
```

---

## 📊 Success Indicators

### ✅ Everything Working
```bash
# CLI check passes
$ ipsw-cli --check
✅ Connected to server: http://localhost:8000
Status: ✅ Online

# Docker services running
$ docker ps --filter "name=ipsw" --format "table {{.Names}}\t{{.Status}}"
ipsw-nginx         Up 10 minutes
ipsw-api-server    Up 10 minutes  
ipsw-symbol-server Up 10 minutes
ipsw-minio         Up 10 minutes
ipsw-postgres      Up 10 minutes

# Web UI accessible
$ curl -s http://localhost:8000/health | jq .status
"healthy"
```

### 🎯 Sample Successful Output
```bash
$ ipsw-cli crash.ips

🚀 IPSW Symbol Server CLI
✅ Connected to server: http://localhost:8000

📁 File Information
Filename: crash.ips
Size: 1,845,857 bytes
Status: ✅ Ready for upload

✅ File processed successfully!

📱 Device & Crash Information  
Device: iPhone17,3
iOS Version: iPhone OS 18.5 (22F76)
Process: MyApp

🔍 Symbolicated Output
[Colorized symbolicated crash output with line numbers]

📋 Summary
✅ Symbolication completed successfully
⏱️ Processing time: 2.34 seconds
📱 Device: iPhone17,3
🔧 iOS: iPhone OS 18.5 (22F76)
```

---

## 🎉 Next Steps

1. **Bookmark this**: Save the server URL for your team
2. **Share the CLI**: Distribute the installation command  
3. **Integrate**: Add to your CI/CD pipeline
4. **Explore**: Try the web UI and S3 console
5. **Scale**: Deploy additional servers for larger teams

---

**🚀 You're now ready for professional iOS crash symbolication!**

- 💻 **CLI**: `ipsw-cli crash.ips`
- 🌐 **Web**: `http://localhost` or `http://TEAM_IP`  
- 📦 **S3**: `http://localhost:9001` or `http://TEAM_IP:9001`
- 🔌 **API**: `http://localhost:8000` or `http://TEAM_IP:8000` 