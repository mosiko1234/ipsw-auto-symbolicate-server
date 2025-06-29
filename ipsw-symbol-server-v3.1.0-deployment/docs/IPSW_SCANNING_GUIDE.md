# IPSW Scanning Guide

This guide explains how to scan IPSW files for symbol extraction using the IPSW Symbol Server.

## 🚀 Quick Start

The server is available at **http://localhost:8082** (port 8082).

## 📡 Scanning Methods

### Method 1: Scan Specific File Path

Scan an IPSW file that's already on the server's filesystem:

```bash
curl -X POST http://localhost:8082/v1/syms/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/your/file.ipsw"}'
```

**Example:**
```bash
curl -X POST http://localhost:8082/v1/syms/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/iPhone17,3_18.5_22F76_Restore.ipsw"}'
```

**Response:**
```json
{
  "status": "scan_started",
  "scan_id": 1,
  "message": "Started scanning IPSW: iPhone17,3_18.5_22F76_Restore.ipsw",
  "estimated_time": "10-30 minutes depending on IPSW size"
}
```

### Method 2: Upload and Scan

Upload an IPSW file and scan it immediately:

```bash
curl -X POST http://localhost:8082/v1/syms/upload \
  -F "ipsw_file=@your_file.ipsw"
```

**Example:**
```bash
curl -X POST http://localhost:8082/v1/syms/upload \
  -F "ipsw_file=@iPhone17,3_18.5_22F76_Restore.ipsw"
```

**Response:**
```json
{
  "status": "upload_and_scan_started",
  "scan_id": 2,
  "file_path": "/app/uploads/iPhone17,3_18.5_22F76_Restore.ipsw",
  "file_name": "iPhone17,3_18.5_22F76_Restore.ipsw",
  "message": "Uploaded and started scanning IPSW: iPhone17,3_18.5_22F76_Restore.ipsw",
  "estimated_time": "10-30 minutes depending on IPSW size"
}
```

### Method 3: Scan Directory

Scan all IPSW files in a directory:

```bash
curl -X POST http://localhost:8082/v1/syms/scan/directory \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/ipsw/directory"}'
```

**Example:**
```bash
curl -X POST http://localhost:8082/v1/syms/scan/directory \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/uploads"}'
```

**Response:**
```json
{
  "status": "directory_scan_started",
  "directory": "/app/uploads",
  "ipsw_files_found": 3,
  "scans": [
    {
      "file": "iPhone17,3_18.5_22F76_Restore.ipsw",
      "scan_id": 3,
      "status": "scan_started"
    },
    {
      "file": "iPhone15,2_18.5_22F76_Restore.ipsw",
      "scan_id": 4,
      "status": "scan_started"
    },
    {
      "file": "iPhone14,2_18.5_22F76_Restore.ipsw",
      "scan_id": 5,
      "status": "scan_started"
    }
  ],
  "message": "Started scanning 3 IPSW files in directory"
}
```

## 📊 Monitoring Scans

### Check Scan Status

```bash
curl http://localhost:8082/v1/syms/scan/status/{scan_id}
```

**Example:**
```bash
curl http://localhost:8082/v1/syms/scan/status/1
```

**Response:**
```json
{
  "id": 1,
  "file_path": "/app/iPhone17,3_18.5_22F76_Restore.ipsw",
  "file_name": "iPhone17,3_18.5_22F76_Restore.ipsw",
  "device_model": "iPhone17,3",
  "os_version": "18.5",
  "build_id": "22F76",
  "file_size_bytes": 9876543210,
  "scan_status": "scanning",
  "symbols_extracted": 0,
  "dyld_caches_found": 0,
  "error_message": null,
  "created_at": "2025-06-25T11:00:00",
  "scan_started_at": "2025-06-25T11:00:05",
  "scan_completed_at": null
}
```

### List All Scans

```bash
curl http://localhost:8082/v1/syms/scans
```

**Response:**
```json
{
  "status": "success",
  "scans": [
    {
      "id": 1,
      "file_name": "iPhone17,3_18.5_22F76_Restore.ipsw",
      "device_model": "iPhone17,3",
      "os_version": "18.5",
      "build_id": "22F76",
      "scan_status": "completed",
      "symbols_extracted": 15420,
      "dyld_caches_found": 3,
      "scan_started_at": "2025-06-25T11:00:05",
      "scan_completed_at": "2025-06-25T11:25:30",
      "created_at": "2025-06-25T11:00:00"
    }
  ],
  "total_scans": 1
}
```

## 🔍 Scan Status Values

- **`pending`**: Scan is queued but not started yet
- **`scanning`**: Scan is currently in progress
- **`completed`**: Scan finished successfully
- **`failed`**: Scan failed with an error

## ⏱️ Scan Duration

Scan duration depends on:
- **IPSW file size** (typically 8-15GB)
- **Server hardware** (CPU, disk I/O)
- **Number of dyld_shared_cache files** in the IPSW

**Typical times:**
- Small IPSW (8GB): 10-15 minutes
- Large IPSW (15GB): 20-30 minutes
- Multiple dyld caches: Additional time per cache

## 📊 Symbolication After Scanning

Once IPSW files are scanned, the server automatically uses the extracted symbols for symbolication:

### Symbolicate with Pre-scanned Symbols

```bash
# Symbolicate using JSON
curl -X POST http://localhost:8082/v1/symbolicate \
  -H "Content-Type: application/json" \
  -d '{"crashlog": "your crashlog content here"}'
```

### Symbolicate with File Upload

```bash
# Upload crashlog file
curl -X POST http://localhost:8082/v1/symbolicate \
  -F "crashlog=@crash.ips"
```

### Symbolicate with Both Files

```bash
# Upload both crashlog and IPSW (will use pre-scanned if available)
curl -X POST http://localhost:8082/v1/symbolicate \
  -F "crashlog=@crash.ips" \
  -F "ipsw=@device.ipsw"
```

## 🔧 Advanced Usage

### Python Example

```python
import requests

# Scan an IPSW file
response = requests.post('http://localhost:8082/v1/syms/scan', 
    json={'path': '/path/to/file.ipsw'})
scan_data = response.json()
scan_id = scan_data['scan_id']

# Check status
while True:
    status_response = requests.get(f'http://localhost:8082/v1/syms/scan/status/{scan_id}')
    status_data = status_response.json()
    
    if status_data['scan_status'] == 'completed':
        print(f"Scan completed! Extracted {status_data['symbols_extracted']} symbols")
        break
    elif status_data['scan_status'] == 'failed':
        print(f"Scan failed: {status_data['error_message']}")
        break
    
    print(f"Scan status: {status_data['scan_status']}")
    time.sleep(30)  # Wait 30 seconds before checking again
```

### Batch Scanning Script

```bash
#!/bin/bash

# Scan multiple IPSW files
IPSW_DIR="/path/to/ipsw/files"
SERVER="http://localhost:8082"

for ipsw_file in "$IPSW_DIR"/*.ipsw; do
    echo "Scanning $ipsw_file..."
    
    response=$(curl -s -X POST "$SERVER/v1/syms/scan" \
        -H "Content-Type: application/json" \
        -d "{\"path\": \"$ipsw_file\"}")
    
    scan_id=$(echo "$response" | jq -r '.scan_id')
    echo "Started scan ID: $scan_id"
done

echo "All scans started. Check status with: curl $SERVER/v1/syms/scans"
```

## 🐳 Docker Volume Mounting

To scan IPSW files from your local filesystem, mount them as volumes:

```yaml
# docker-compose.yml
services:
  symbol-server:
    volumes:
      - ./ipsw_files:/app/ipsw_files:ro  # Read-only mount
```

Then scan using the mounted path:

```bash
curl -X POST http://localhost:8082/v1/syms/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/ipsw_files/iPhone17,3_18.5_22F76_Restore.ipsw"}'
```

## 🔍 Troubleshooting

### Common Issues

**1. File not found:**
```json
{"error": "IPSW file not found: /path/to/file.ipsw"}
```
- Ensure the file path is correct
- Check file permissions
- Use absolute paths

**2. Scan already exists:**
```json
{
  "status": "already_scanned",
  "scan_id": 1,
  "symbols_extracted": 15420
}
```
- The file has already been scanned
- Use the existing scan_id for status checks

**3. Scan failed:**
```json
{
  "scan_status": "failed",
  "error_message": "Failed to extract dyld_shared_cache: ..."
}
```
- Check if the IPSW file is corrupted
- Ensure sufficient disk space
- Check server logs for details

### Checking Server Logs

```bash
# View container logs
docker-compose logs symbol-server

# Follow logs in real-time
docker-compose logs -f symbol-server
```

## 📈 Performance Tips

1. **Pre-scan IPSW files** during off-peak hours
2. **Use SSD storage** for faster I/O
3. **Monitor disk space** - scanned symbols are stored in database
4. **Batch scan** multiple files using the directory method
5. **Check scan status** periodically to avoid duplicate scans

## 🔄 Retry Failed Scans

If a scan fails, you can retry it:

```bash
# The server automatically allows retry for failed scans
curl -X POST http://localhost:8082/v1/syms/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/failed/file.ipsw"}'
```

The server will update the existing failed scan record and restart the process. 