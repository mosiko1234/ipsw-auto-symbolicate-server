# Kernel Symbolication Setup - Complete Guide

## ✅ Setup Completed Successfully!

Your IPSW Symbol Server now has **full kernel symbolication support** configured and ready to use.

## 📋 What Was Configured

### 1. **Database Setup**
- ✅ **PostgreSQL Database**: `symbols` 
- ✅ **User**: `symbols_user`
- ✅ **Tables Created**:
  - `kernel_symbols` - Stores symbolicated kernel data
  - `daemon_config` - Daemon configuration settings
  - `symbols` - Regular symbol cache
  - `symbol_cache` - Symbol metadata
  - `analysis` - Analysis results

### 2. **Kernel Signatures**
- ✅ **Repository**: `blacktop/symbolicator` (1,917 signature files)
- ✅ **Location**: `./data/symbolicator/kernel/`
- ✅ **iOS Versions**: 20, 21, 22, 23, 24.0, 24.1, 24.2
- ✅ **Mount Path**: `/app/data/symbolicator/kernel` (in containers)

### 3. **Configuration Files**
- ✅ **IPSW Config**: `~/.config/ipsw/config.yml`
- ✅ **Docker Compose**: Updated with symbolicator volumes
- ✅ **Environment**: `KERNEL_SIGS_DIR` set for containers

## 📊 Current Statistics

```
📈 Kernel Signatures: 1,917 files
🗃️ Database Tables: 5 tables
🎯 iOS Support: iOS 16-25
💾 Cache Size: 100GB configured
🔄 Cleanup: Every 24 hours
```

## 🚀 How to Use Kernel Symbolication

### 1. **Upload IPSW File**
```bash
# Via Web UI: http://localhost/
# Upload any iOS IPSW file that contains kernel cache
```

### 2. **Process IPS Files**
```bash
# Via CLI tool
ipsw-cli your-crash-file.ips

# Via Web UI
# Upload IPS file through the interface
```

### 3. **Check Results**
```bash
# Check database for symbolicated results
python3 check_kernel_setup.py

# Or query directly
docker exec ipsw-postgres psql -U symbols_user -d symbols -c "SELECT * FROM kernel_symbols LIMIT 5;"
```

## 🛠️ Configuration Details

### Database Configuration
```yaml
database:
  driver: postgres
  name: symbols
  host: localhost
  port: 5432
  user: symbols_user
  password: symbols_password
```

### Daemon Configuration
```yaml
daemon:
  sigs-dir: ./data/symbolicator/kernel
  port: 3993
  host: localhost
```

### S3 Configuration
```yaml
s3:
  endpoint: http://localhost:9000
  access_key: minioadmin
  secret_key: minioadmin
  bucket: ipsw
  use_ssl: false
```