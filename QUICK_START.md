# 🚀 IPSW Symbol Server - Quick Start Guide

## System Startup

```bash
# Run the server
docker-compose up -d

# Check everything works
curl http://localhost:3993/v1/_ping
```

## 🔧 DevOps Team - Adding IPSW Files

### Method 1: Automatic Script (Recommended)
```bash
./add_ipsw.sh /path/to/your/file.ipsw
```

### Method 2: Manual
```bash
# 1. Copy file
cp your_file.ipsw ipsw_files/

# 2. Scan
curl -X POST "http://localhost:3993/v1/syms/scan" \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/ipsw_files/your_file.ipsw"}'
```

### Check Available Files
```bash
curl "http://localhost:3993/v1/ipsw/list" | jq '.'
```

---

## 👨‍💻 Developers - Symbolication

### Method 1: Automatic Script (Recommended)
```bash
./symbolicate.sh crash.ips
# or with specific output filename:
./symbolicate.sh crash.ips symbolicated_output.txt
```

### Method 2: Direct with curl
```bash
curl -F "crashlog=@crash.ips" http://localhost:3993/v1/symbolicate > output.txt
```

---

## 📊 Monitoring & Control

```bash
# List IPSW files
curl "http://localhost:3993/v1/ipsw/list"

# List performed scans
curl "http://localhost:3993/v1/syms/scans"

# System status
curl "http://localhost:3993/health"

# Web interface (direct server)
open http://localhost:3993/

# Web interface (via nginx)
open http://localhost:8082/
```

---

## 🗂️ Directory Structure

```
ipsw-symbol-server/
├── ipsw_files/           # 📥 Put IPSW files here
├── crashlogs/            # 📂 Crashlogs (optional)  
├── uploads/              # 📤 Uploaded files
├── add_ipsw.sh          # 🔧 IPSW addition script
├── symbolicate.sh       # 🔧 Symbolication script
└── API_USAGE.md         # 📖 Detailed guide
```

---

## ⚡ Common Scenarios

### Add New IPSW
```bash
./add_ipsw.sh ~/Downloads/iPhone15,2_17.5_21F79_Restore.ipsw
```

### Quick Symbolication
```bash
./symbolicate.sh MyApp-crash.ips
```

### Multiple File Scanning
```bash
for ipsw in ~/Downloads/*.ipsw; do
    ./add_ipsw.sh "$ipsw"
done
```

### Batch Symbolication
```bash
for crash in *.ips; do
    ./symbolicate.sh "$crash"
done
```

---

## 🛠️ Troubleshooting

### Server Not Working
```bash
docker-compose logs symbol-server
docker-compose restart
```

### No IPSW Files
```bash
# Check directory
ls -la ipsw_files/

# Add file
./add_ipsw.sh path/to/file.ipsw
```

### Symbolication Failed
```bash
# Check server status
curl http://localhost:3993/health

# Check IPSW list
curl http://localhost:3993/v1/ipsw/list
```

---

## 🎯 System Works If...

✅ `curl http://localhost:3993/v1/_ping` returns `{"status":"OK"}`  
✅ `curl http://localhost:3993/v1/ipsw/list` shows IPSW files  
✅ `./symbolicate.sh crash.ips` creates symbolicated file  

---

**System ready for use! 🎉**

For detailed documentation: [API_USAGE.md](./API_USAGE.md) 