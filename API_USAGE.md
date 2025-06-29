# IPSW Symbol Server - API Usage Guide

## IPSW Symbol System - Usage Guide

### 🎯 System Purpose

The system is designed for two types of users:

1. **DevOps Team** - Scanning IPSW files and storing symbols in database
2. **Developers** - Sending IPS files for fast symbolication

---

## 📁 Directory Mapping

The system uses a shared directory for IPSW files:

```
ipsw-symbol-server/
├── ipsw_files/          # 📥 Shared directory for IPSW files
├── crashlogs/           # 📂 Crashlogs (optional)
├── uploads/             # 📤 Uploaded files
└── symbols/             # 🔍 Extracted symbols
```

---

## 🔧 Main Endpoints

### Health Check
```bash
curl "http://localhost:3993/v1/_ping"
curl "http://localhost:3993/health"
```

### ✅ 1. List Available IPSW Files
```bash
curl "http://localhost:3993/v1/ipsw/list"
```

**Example response:**
```json
{
  "directory": "/app/ipsw_files",
  "ipsw_files": [
    {
      "filename": "iPhone17,3_18.5_22F76_Restore.ipsw",
      "path": "/app/ipsw_files/iPhone17,3_18.5_22F76_Restore.ipsw",
      "size_mb": 9350.2,
      "device_model": "iPhone17,3",
      "os_version": "18.5",
      "build_id": "22F76",
      "modified": "2025-06-17T19:30:35.375794"
    }
  ],
  "total": 1
}
```

### ✅ 2. IPSW Scanning (for DevOps)

#### Adding New IPSW File
1. **Copy file to shared directory:**
```bash
# From local machine
cp new_ipsw_file.ipsw ipsw_files/

# Or via Docker
docker cp new_ipsw_file.ipsw symbol-server:/app/ipsw_files/
```

2. **Check available files list:**
```bash
curl "http://localhost:3993/v1/ipsw/list"
```

3. **Scan the file:**
```bash
curl -X POST "http://localhost:3993/v1/syms/scan" \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/ipsw_files/new_ipsw_file.ipsw"}'
```

**Example response:**
```json
{
  "message": "IPSW scan completed",
  "scan_id": 3,
  "device_model": "iPhone15,2",
  "os_version": "17.5",
  "build_id": "21F79",
  "status": "completed"
}
```

### ✅ 3. Symbolication (for Developers)

The system supports three sending methods:

#### Method 1: File Upload (Recommended)
```bash
curl -F "crashlog=@crash.ips" http://localhost:3993/v1/symbolicate
```

#### Method 2: JSON with crashlog content
```bash
curl -X POST "http://localhost:3993/v1/symbolicate" \
  -H "Content-Type: application/json" \
  -d '{
    "crashlog": "Incident Identifier: ABC123\nDate/Time: 2025-06-12...",
    "ipsw": "/app/ipsw_files/specific.ipsw"
  }'
```

#### Method 3: Form data
```bash
curl -X POST "http://localhost:3993/v1/symbolicate" \
  -d "crashlog=Incident Identifier: ABC123..." \
  -d "ipsw=/app/ipsw_files/specific.ipsw"
```

**Successful response:**
```json
{
  "symbolicated": true,
  "output": "Full symbolicated crashlog with function names...",
  "method": "ipsw_cli",
  "used_ipsw": "/app/ipsw_files/iPhone17,3_18.5_22F76_Restore.ipsw",
  "timestamp": "2025-06-25T16:44:57.779116"
}
```

### ✅ 4. Scan List (Tracking)
```bash
curl "http://localhost:3993/v1/syms/scans"
```

---

## 🚀 Updated Usage Scenarios

### Scenario 1: DevOps - Adding New IPSW
```bash
# 1. Copy IPSW file to shared directory
cp iPhone15,2_17.5_21F79_Restore.ipsw ipsw_files/

# 2. Check file is detected
curl "http://localhost:3993/v1/ipsw/list"

# 3. Scan the new file
curl -X POST "http://localhost:3993/v1/syms/scan" \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/ipsw_files/iPhone15,2_17.5_21F79_Restore.ipsw"}'

# 4. Verify scan
curl "http://localhost:3993/v1/syms/scans"
```

### Scenario 2: Developer - Quick Symbolication
```bash
# Server will automatically choose appropriate IPSW
curl -F "crashlog=@MyApp-2025-06-25.ips" http://localhost:3993/v1/symbolicate > symbolicated_crash.txt
```

### Scenario 3: Symbolication with Specific IPSW
```bash
# Specify specific IPSW from list
curl -X POST "http://localhost:3993/v1/symbolicate" \
  -H "Content-Type: application/json" \
  -d '{
    "crashlog": "...",
    "ipsw": "/app/ipsw_files/iPhone17,3_18.5_22F76_Restore.ipsw"
  }'
```

---

## 🛠 IPSW File Management

### Adding New IPSW File
```bash
# Direct copy
cp new_file.ipsw ipsw_files/

# Via Docker (if server runs in container)
docker cp new_file.ipsw symbol-server:/app/ipsw_files/

# Via scp to remote server
scp new_file.ipsw server:/path/to/ipsw-symbol-server/ipsw_files/
```

### Checking Available Files
```bash
# Detailed list with file information
curl "http://localhost:3993/v1/ipsw/list" | jq '.'

# Just filenames
curl "http://localhost:3993/v1/ipsw/list" | jq '.ipsw_files[].filename'
```

### Cleaning Old Files
```bash
# Delete old file
rm ipsw_files/old_file.ipsw

# Check file was removed
curl "http://localhost:3993/v1/ipsw/list"
```

---

## 🔗 URLs for Active System

- **Web Interface (Direct)**: http://localhost:3993/
- **Web Interface (Nginx)**: http://localhost:8082/
- **Upload Interface**: http://localhost:8082/upload - Upload .ips files directly
- **IPSW List**: http://localhost:3993/v1/ipsw/list
- **Health Check**: http://localhost:3993/health
- **API Ping**: http://localhost:3993/v1/_ping

---

## 🌟 Updated System Benefits

1. **Maximum Flexibility** - Shared directory for all IPSW files
2. **Easy Management** - Simple file copying to directory
3. **Automatic Tracking** - Everything recorded in database
4. **Space Efficient** - No need to map each file separately
5. **Development Friendly** - Add files without configuration changes

The system is now **completely flexible** and easy to manage! 🎉 