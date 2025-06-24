# 🔌 IPSW Symbol Server - API Reference

**Complete REST API documentation for developers and integrations**

---

## 📚 Table of Contents

1. [Base Configuration](#base-configuration)
2. [Authentication](#authentication)
3. [Response Formats](#response-formats)
4. [Core Endpoints](#core-endpoints)
5. [File Management](#file-management)
6. [Administrative Endpoints](#administrative-endpoints)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Code Examples](#code-examples)
10. [OpenAPI Specification](#openapi-specification)

---

## ⚙️ Base Configuration

### Base URLs

| Environment | Base URL |
|-------------|----------|
| **Local Development** | `http://localhost:8000` |
| **Team Server** | `http://TEAM_IP:8000` |
| **Production** | `https://symbolication.company.com` |

### Content Types

| Operation | Content-Type |
|-----------|--------------|
| **File Upload** | `multipart/form-data` |
| **JSON Data** | `application/json` |
| **Health Checks** | `application/json` |

### Common Headers

```http
Accept: application/json
User-Agent: YourApp/1.0
```

---

## 🔐 Authentication

### Current Implementation
**No authentication required** for local/team deployments.

### Production Recommendations
```http
# API Key (recommended)
Authorization: Bearer your-api-key-here

# Basic Auth (fallback)
Authorization: Basic base64(username:password)
```

---

## 📄 Response Formats

### Success Response Format
```json
{
  "success": true,
  "analysis_id": "abc123",
  "message": "Operation completed successfully",
  "data": { ... },
  "timestamp": "2025-06-22T15:47:01.578751Z"
}
```

### Error Response Format  
```json
{
  "success": false,
  "error": "InvalidFileFormat",
  "message": "The uploaded file is not a valid crash report",
  "details": "Expected .ips or .crash file format",
  "timestamp": "2025-06-22T15:47:01.578751Z"
}
```

### File Information Format
```json
{
  "device_model": "iPhone17,3",
  "ios_version": "iPhone OS 18.5 (22F76)",
  "build_version": "22F76", 
  "process_name": "MyApp",
  "bug_type": "288",
  "is_ips_format": true,
  "file_size": 1845857,
  "upload_timestamp": "2025-06-22T15:47:01.578751Z"
}
```

---

## 🔧 Core Endpoints

### 1. Health Check

**Check server health and status**

```http
GET /health
```

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-06-22T15:47:01.578751Z",
  "version": "1.2.5",
  "uptime": "2 hours, 34 minutes",
  "services": {
    "symbol_server": "healthy",
    "database": "healthy", 
    "storage": "healthy",
    "cache": "healthy"
  },
  "performance": {
    "active_analyses": 3,
    "total_analyses": 1247,
    "avg_processing_time": 2.34
  }
}
```

#### Example
```bash
curl http://localhost:8000/health
```

---

### 2. Basic Symbolication

**Symbolicate a crash file using available IPSWs**

```http
POST /symbolicate
Content-Type: multipart/form-data

file: <crash-file>
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Crash report file (.ips, .crash, .txt) |

#### Response
```json
{
  "success": true,
  "analysis_id": "a1b2c3d4",
  "message": "Symbolication completed successfully",
  "file_info": {
    "device_model": "iPhone17,3",
    "ios_version": "iPhone OS 18.5 (22F76)",
    "build_version": "22F76",
    "process_name": "MyApp",
    "bug_type": "288",
    "is_ips_format": true
  },
  "symbolicated_output": "Incident Identifier: 12345...\n0  MyApp  0x0000000104567890 main + 123 (MyApp.c:45)\n1  libdyld.dylib  0x000000018456789a start + 1\n...",
  "statistics": {
    "symbols_found": 45,
    "symbols_unknown": 3,
    "success_rate": 93.75
  },
  "processing_time": 2.34,
  "timestamp": "2025-06-22T15:47:01.578751Z"
}
```

#### Examples
```bash
# Basic upload
curl -X POST \
  -F "file=@crash.ips" \
  http://localhost:8000/symbolicate

# With custom filename
curl -X POST \
  -F "file=@crash.ips;filename=myapp_crash.ips" \
  http://localhost:8000/symbolicate
```

#### Error Responses
```json
// No matching IPSW found
{
  "success": false,
  "error": "NoSymbolsFound", 
  "message": "No symbols found for iPhone17,3 iOS iPhone OS 18.5 (22F76)",
  "details": "Please download the appropriate IPSW and ensure device details are correct",
  "file_info": { ... }
}

// Invalid file format
{
  "success": false,
  "error": "InvalidFileFormat",
  "message": "The uploaded file is not a valid crash report",
  "details": "Expected .ips, .crash, or .txt file format"
}
```

---

### 3. Local IPSW Symbolication

**Symbolicate using a specific IPSW file**

```http
POST /local-ipsw-symbolicate
Content-Type: multipart/form-data

ipsw_file: <ipsw-file>
ips_file: <crash-file>
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ipsw_file` | File | Yes | IPSW firmware file (.ipsw) |
| `ips_file` | File | Yes | Crash report file (.ips, .crash, .txt) |

#### Response
Same format as basic symbolication, with additional IPSW information:

```json
{
  "success": true,
  "analysis_id": "x1y2z3w4",
  "message": "Local IPSW symbolication completed successfully",
  "ipsw_info": {
    "filename": "iPhone17,3_18.5_22F76_Restore.ipsw",
    "size": 9876543210,
    "device_compatibility": ["iPhone17,3"],
    "ios_version": "18.5",
    "build_number": "22F76",
    "processing_method": "direct_upload"
  },
  "file_info": { ... },
  "symbolicated_output": "...",
  "processing_time": 45.67
}
```

#### Examples
```bash
# Standard upload
curl -X POST \
  -F "ipsw_file=@iPhone_18.5.ipsw" \
  -F "ips_file=@crash.ips" \
  http://localhost:8000/local-ipsw-symbolicate

# With progress monitoring (JavaScript)
const formData = new FormData();
formData.append('ipsw_file', ipswFile);
formData.append('ips_file', crashFile);

const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
  const percent = (e.loaded / e.total) * 100;
  console.log(`Upload progress: ${percent}%`);
});
xhr.open('POST', 'http://localhost:8000/local-ipsw-symbolicate');
xhr.send(formData);
```

---

### 4. Streaming Upload (Large Files)

**For IPSW files larger than 1GB**

```http
POST /local-ipsw-symbolicate-stream
Content-Type: multipart/form-data

ipsw_file: <large-ipsw-file>
ips_file: <crash-file>
```

#### Parameters
Same as local IPSW symbolication, but optimized for large files.

#### Features
- **Chunked upload** in 8MB segments
- **Extended timeout** (60 minutes)
- **Memory efficient** processing
- **Progress tracking** support

#### Response
Same format as local IPSW symbolication, with additional streaming metadata:

```json
{
  "success": true,
  "analysis_id": "stream123",
  "message": "Streaming IPSW symbolication completed successfully",
  "ipsw_info": {
    "filename": "iPhone17,3_18.5_22F76_Restore.ipsw",
    "size": 10737418240,
    "processing_method": "streaming_upload",
    "chunks_processed": 1280,
    "streaming_time": 1234.56
  },
  "processing_time": 1789.34
}
```

#### Notes
- Automatically selected by CLI for files >1GB
- Requires stable network connection
- May take 30-60 minutes for 10GB+ files

---

### 5. Analysis Status

**Check status of ongoing or completed analysis**

```http
GET /analysis/{analysis_id}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_id` | String | Yes | Unique analysis identifier |

#### Response
```json
{
  "analysis_id": "abc123",
  "status": "completed",
  "progress": 100,
  "file_info": { ... },
  "symbolicated_output": "...",
  "created_at": "2025-06-22T15:47:01.578751Z",
  "completed_at": "2025-06-22T15:47:03.890123Z",
  "processing_time": 2.34,
  "error": null
}
```

#### Status Values
| Status | Description |
|--------|-------------|
| `pending` | Analysis queued |
| `processing` | Currently processing |
| `completed` | Successfully completed |
| `failed` | Processing failed |
| `timeout` | Processing timed out |

#### Examples
```bash
# Check analysis status
curl http://localhost:8000/analysis/abc123

# Poll for completion
while true; do
  STATUS=$(curl -s http://localhost:8000/analysis/abc123 | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then break; fi
  sleep 5
done
```

---

### 6. Server Status

**Detailed server information and statistics**

```http
GET /status
```

#### Response
```json
{
  "server": "IPSW Symbol Server",
  "version": "1.2.5",
  "build": "20250622-1534",
  "environment": "production",
  "uptime": "2 hours, 34 minutes",
  "started_at": "2025-06-22T13:13:01.578751Z",
  "statistics": {
    "total_analyses": 1247,
    "successful_analyses": 1180,
    "failed_analyses": 67,
    "active_analyses": 3,
    "avg_processing_time": 2.34,
    "success_rate": 94.6
  },
  "storage": {
    "ipsw_files": 45,
    "total_ipsw_size": "456.7 GB",
    "cache_size": "89.2 GB",
    "free_space": "156.8 GB",
    "cache_hit_rate": 87.3
  },
  "performance": {
    "cpu_usage": 23.4,
    "memory_usage": 67.8,
    "disk_io": "moderate",
    "network_io": "low"
  },
  "services": {
    "symbol_server": {
      "status": "healthy",
      "port": 3993,
      "version": "1.2.5"
    },
    "database": {
      "status": "healthy",
      "port": 5432,
      "connections": 12
    },
    "storage": {
      "status": "healthy",
      "port": 9000,
      "buckets": 1
    }
  }
}
```

---

## 📁 File Management

### 7. List IPSW Files

**List available IPSW files in storage**

```http
GET /ipsw/list
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | Integer | 50 | Maximum number of results |
| `offset` | Integer | 0 | Results offset for pagination |
| `device` | String | - | Filter by device model |
| `ios_version` | String | - | Filter by iOS version |

#### Response
```json
{
  "success": true,
  "total": 45,
  "limit": 50,
  "offset": 0,
  "ipsw_files": [
    {
      "filename": "iPhone17,3_18.5_22F76_Restore.ipsw",
      "size": 9876543210,
      "device_model": "iPhone17,3",
      "ios_version": "18.5",
      "build_number": "22F76",
      "uploaded_at": "2025-06-22T10:30:00.000Z",
      "last_used": "2025-06-22T15:45:00.000Z",
      "usage_count": 23,
      "status": "ready"
    },
    {
      "filename": "iPhone16,2_18.4_22F74_Restore.ipsw", 
      "size": 8765432109,
      "device_model": "iPhone16,2",
      "ios_version": "18.4",
      "build_number": "22F74",
      "uploaded_at": "2025-06-20T14:20:00.000Z",
      "last_used": "2025-06-21T09:15:00.000Z",
      "usage_count": 7,
      "status": "ready"
    }
  ]
}
```

#### Examples
```bash
# List all IPSW files
curl http://localhost:8000/ipsw/list

# Filter by device
curl "http://localhost:8000/ipsw/list?device=iPhone17,3"

# Pagination
curl "http://localhost:8000/ipsw/list?limit=10&offset=20"
```

---

### 8. IPSW File Information

**Get detailed information about specific IPSW file**

```http
GET /ipsw/{filename}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filename` | String | Yes | IPSW filename |

#### Response
```json
{
  "success": true,
  "ipsw_info": {
    "filename": "iPhone17,3_18.5_22F76_Restore.ipsw",
    "size": 9876543210,
    "size_formatted": "9.2 GB",
    "device_model": "iPhone17,3",
    "device_name": "iPhone 16 Pro",
    "ios_version": "18.5",
    "build_number": "22F76",
    "release_date": "2025-05-13",
    "uploaded_at": "2025-06-22T10:30:00.000Z",
    "processed_at": "2025-06-22T10:45:00.000Z",
    "last_used": "2025-06-22T15:45:00.000Z",
    "usage_count": 23,
    "status": "ready",
    "checksum": "sha256:a1b2c3d4e5f6...",
    "components": {
      "kernel": "present",
      "frameworks": 145,
      "applications": 67,
      "drivers": 234
    },
    "compatibility": [
      "iPhone17,3"
    ]
  }
}
```

---

### 9. Upload IPSW File

**Upload new IPSW file to server storage**

```http
POST /ipsw/upload
Content-Type: multipart/form-data

file: <ipsw-file>
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | IPSW file (.ipsw) |
| `overwrite` | Boolean | No | Allow overwriting existing files |

#### Response
```json
{
  "success": true,
  "message": "IPSW file uploaded and processed successfully",
  "ipsw_info": {
    "filename": "iPhone17,3_18.5_22F76_Restore.ipsw",
    "size": 9876543210,
    "device_model": "iPhone17,3",
    "ios_version": "18.5",
    "build_number": "22F76",
    "upload_time": 234.56,
    "processing_time": 567.89,
    "status": "ready"
  },
  "analysis_capabilities": {
    "user_space": true,
    "kernel_space": true,
    "frameworks": 145,
    "system_libraries": 234
  }
}
```

---

### 10. Delete IPSW File

**Remove IPSW file from server storage**

```http
DELETE /ipsw/{filename}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filename` | String | Yes | IPSW filename to delete |
| `force` | Boolean | No | Force deletion even if in use |

#### Response
```json
{
  "success": true,
  "message": "IPSW file deleted successfully",
  "deleted_file": "iPhone17,3_18.5_22F76_Restore.ipsw",
  "freed_space": "9.2 GB"
}
```

---

## ⚙️ Administrative Endpoints

### 11. Cache Management

**Manage symbol cache and temporary files**

```http
POST /admin/cache/clean
```

#### Request Body
```json
{
  "max_age_hours": 24,
  "force": false,
  "categories": ["symbols", "temp", "uploads"]
}
```

#### Response
```json
{
  "success": true,
  "message": "Cache cleaned successfully",
  "cleaned": {
    "symbols": "2.3 GB",
    "temp_files": "567 MB", 
    "old_uploads": "1.2 GB",
    "total_freed": "4.1 GB"
  },
  "remaining": {
    "symbols": "15.7 GB",
    "free_space": "160.9 GB"
  }
}
```

---

### 12. System Metrics

**Get detailed system performance metrics**

```http
GET /admin/metrics
```

#### Response
```json
{
  "success": true,
  "timestamp": "2025-06-22T15:47:01.578751Z",
  "system": {
    "cpu": {
      "usage_percent": 23.4,
      "load_average": [1.2, 1.4, 1.1],
      "cores": 8
    },
    "memory": {
      "total": "16 GB",
      "used": "10.8 GB",
      "free": "5.2 GB",
      "usage_percent": 67.5
    },
    "disk": {
      "total": "500 GB",
      "used": "343.2 GB", 
      "free": "156.8 GB",
      "usage_percent": 68.6
    }
  },
  "application": {
    "analyses": {
      "active": 3,
      "queued": 0,
      "completed_today": 89,
      "avg_processing_time": 2.34
    },
    "storage": {
      "ipsw_files": 45,
      "total_ipsw_size": "456.7 GB",
      "cache_size": "89.2 GB",
      "cache_hit_rate": 87.3
    },
    "performance": {
      "requests_per_minute": 12.3,
      "success_rate": 94.6,
      "error_rate": 5.4
    }
  }
}
```

---

### 13. Service Control

**Control individual services**

```http
POST /admin/service/{service_name}/{action}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `service_name` | String | Yes | Service: `symbol-server`, `database`, `storage` |
| `action` | String | Yes | Action: `start`, `stop`, `restart`, `status` |

#### Response
```json
{
  "success": true,
  "service": "symbol-server",
  "action": "restart",
  "message": "Service restarted successfully",
  "status": "running",
  "uptime": "00:00:15"
}
```

---

## ❌ Error Handling

### Error Codes

| Code | Error Type | Description |
|------|------------|-------------|
| 400 | `BadRequest` | Invalid request format or parameters |
| 404 | `NotFound` | Requested resource not found |
| 409 | `Conflict` | Resource already exists |
| 413 | `PayloadTooLarge` | File too large (>10GB) |
| 415 | `UnsupportedMediaType` | Invalid file format |
| 422 | `UnprocessableEntity` | Valid format but processing failed |
| 429 | `TooManyRequests` | Rate limit exceeded |
| 500 | `InternalServerError` | Server error |
| 503 | `ServiceUnavailable` | Service temporarily unavailable |

### Error Response Examples

```json
// File too large
{
  "success": false,
  "error": "PayloadTooLarge",
  "message": "File size exceeds maximum limit of 10GB",
  "details": "Current file size: 12.3 GB",
  "max_size": "10 GB"
}

// Invalid file format
{
  "success": false,
  "error": "UnsupportedMediaType", 
  "message": "File type not supported",
  "details": "Expected: .ips, .crash, .txt, .ipsw",
  "received": ".zip"
}

// Processing failed
{
  "success": false,
  "error": "ProcessingFailed",
  "message": "Failed to symbolicate crash report",
  "details": "No matching symbols found in available IPSWs",
  "suggestions": [
    "Upload the correct IPSW file for this device/iOS version",
    "Verify the crash report format is valid",
    "Check if device model is supported"
  ]
}

// Rate limited
{
  "success": false,
  "error": "TooManyRequests",
  "message": "Rate limit exceeded",
  "details": "Maximum 10 requests per minute allowed",
  "retry_after": 45
}
```

---

## 🚦 Rate Limiting

### Current Limits
| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `/symbolicate` | 10 requests | per minute |
| `/local-ipsw-symbolicate` | 5 requests | per minute |
| `/health` | 60 requests | per minute |
| `/status` | 30 requests | per minute |
| `/ipsw/upload` | 2 requests | per minute |

### Rate Limit Headers
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1640995200
```

---

## 💻 Code Examples

### Python Integration
```python
import requests
import json
import time

class IPSWSymbolicator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def health_check(self):
        """Check server health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def symbolicate_crash(self, crash_file_path):
        """Symbolicate crash file"""
        with open(crash_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.base_url}/symbolicate", files=files)
        return response.json()
    
    def symbolicate_with_ipsw(self, ipsw_path, crash_path):
        """Symbolicate with specific IPSW"""
        with open(ipsw_path, 'rb') as ipsw_f, open(crash_path, 'rb') as crash_f:
            files = {
                'ipsw_file': ipsw_f,
                'ips_file': crash_f
            }
            response = requests.post(f"{self.base_url}/local-ipsw-symbolicate", files=files)
        return response.json()
    
    def wait_for_analysis(self, analysis_id, timeout=300):
        """Wait for analysis to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(f"{self.base_url}/analysis/{analysis_id}")
            result = response.json()
            
            if result['status'] == 'completed':
                return result
            elif result['status'] == 'failed':
                raise Exception(f"Analysis failed: {result.get('error')}")
            
            time.sleep(5)
        
        raise TimeoutError("Analysis timed out")

# Usage
symbolizer = IPSWSymbolicator("http://team-server:8000")

# Check health
health = symbolizer.health_check()
print(f"Server status: {health['status']}")

# Symbolicate crash
result = symbolizer.symbolicate_crash("crash.ips")
print(f"Analysis ID: {result['analysis_id']}")
print(f"Device: {result['file_info']['device_model']}")
```

### JavaScript/Node.js Integration
```javascript
const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');

class IPSWSymbolicator {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }
    
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`);
        return response.data;
    }
    
    async symbolicateCrash(crashFilePath) {
        const form = new FormData();
        form.append('file', fs.createReadStream(crashFilePath));
        
        const response = await axios.post(`${this.baseUrl}/symbolicate`, form, {
            headers: form.getHeaders(),
            timeout: 300000 // 5 minutes
        });
        
        return response.data;
    }
    
    async symbolicateWithIPSW(ipswPath, crashPath) {
        const form = new FormData();
        form.append('ipsw_file', fs.createReadStream(ipswPath));
        form.append('ips_file', fs.createReadStream(crashPath));
        
        const response = await axios.post(`${this.baseUrl}/local-ipsw-symbolicate`, form, {
            headers: form.getHeaders(),
            timeout: 1800000 // 30 minutes
        });
        
        return response.data;
    }
    
    async getAnalysisStatus(analysisId) {
        const response = await axios.get(`${this.baseUrl}/analysis/${analysisId}`);
        return response.data;
    }
}

// Usage
const symbolizer = new IPSWSymbolicator('http://team-server:8000');

async function main() {
    try {
        // Check health
        const health = await symbolizer.healthCheck();
        console.log(`Server status: ${health.status}`);
        
        // Symbolicate crash
        const result = await symbolizer.symbolicateCrash('crash.ips');
        console.log(`Analysis ID: ${result.analysis_id}`);
        console.log(`Device: ${result.file_info.device_model}`);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

### Shell Script Integration
```bash
#!/bin/bash

# IPSW Symbol Server API client
BASE_URL="http://localhost:8000"
TIMEOUT=300

# Function: Check server health
check_health() {
    curl -s "$BASE_URL/health" | jq -r '.status'
}

# Function: Symbolicate crash file
symbolicate_crash() {
    local crash_file="$1"
    local result
    
    if [ ! -f "$crash_file" ]; then
        echo "Error: Crash file not found: $crash_file" >&2
        return 1
    fi
    
    echo "Uploading and symbolicating: $crash_file"
    result=$(curl -s -X POST \
        -F "file=@$crash_file" \
        --max-time $TIMEOUT \
        "$BASE_URL/symbolicate")
    
    if [ $? -eq 0 ]; then
        echo "$result" | jq '.'
    else
        echo "Error: Upload failed" >&2
        return 1
    fi
}

# Function: Symbolicate with local IPSW
symbolicate_with_ipsw() {
    local ipsw_file="$1"
    local crash_file="$2"
    local result
    
    if [ ! -f "$ipsw_file" ] || [ ! -f "$crash_file" ]; then
        echo "Error: Files not found" >&2
        return 1
    fi
    
    echo "Uploading IPSW and crash file..."
    result=$(curl -s -X POST \
        -F "ipsw_file=@$ipsw_file" \
        -F "ips_file=@$crash_file" \
        --max-time 1800 \
        "$BASE_URL/local-ipsw-symbolicate")
    
    if [ $? -eq 0 ]; then
        echo "$result" | jq '.'
    else
        echo "Error: Upload failed" >&2
        return 1
    fi
}

# Function: Get analysis status
get_analysis_status() {
    local analysis_id="$1"
    curl -s "$BASE_URL/analysis/$analysis_id" | jq '.'
}

# Main script
case "$1" in
    health)
        echo "Server health: $(check_health)"
        ;;
    symbolicate)
        symbolicate_crash "$2"
        ;;
    symbolicate-ipsw)
        symbolicate_with_ipsw "$2" "$3"
        ;;
    status)
        get_analysis_status "$2"
        ;;
    *)
        echo "Usage: $0 {health|symbolicate <crash_file>|symbolicate-ipsw <ipsw_file> <crash_file>|status <analysis_id>}"
        exit 1
        ;;
esac
```

---

## 📋 OpenAPI Specification

### Download OpenAPI Spec
```bash
# Get OpenAPI 3.0 specification
curl http://localhost:8000/openapi.json > ipsw-symbol-server-api.json

# Get Swagger UI
open http://localhost:8000/docs
```

### Generate Client SDKs
```bash
# Generate Python client
openapi-generator generate -i ipsw-symbol-server-api.json -g python -o python-client/

# Generate JavaScript client  
openapi-generator generate -i ipsw-symbol-server-api.json -g javascript -o js-client/

# Generate Go client
openapi-generator generate -i ipsw-symbol-server-api.json -g go -o go-client/
```

---

## 🔗 Related Documentation

- **[Developer Documentation](DEVELOPER_DOCUMENTATION.md)** - Complete deployment guide
- **[Quick Start Guide](QUICK_START_DEVELOPERS.md)** - Get started in 5 minutes  
- **[CLI Usage Guide](CLI_UNIFIED_USAGE.md)** - Command-line interface
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

---

**🚀 Ready to integrate IPSW Symbol Server into your development workflow!**

*For additional API support or feature requests, please contact the development team.* 