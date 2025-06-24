# IPSW Symbol Server - Quick Deployment Guide

## Prerequisites
- Docker & Docker Compose
- 50GB+ free disk space
- 8GB+ RAM

## Quick Start (5 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ipsw-symbol-server.git
cd ipsw-symbol-server
```

### 2. Create IPSW Config (One-time setup)
```bash
mkdir -p ~/.config/ipsw
cat > ~/.config/ipsw/config.yml << 'EOF'
# IPSW Symbol Server Configuration
database:
  driver: postgres
  name: symbols
  host: localhost
  port: 5432
  user: symbols_user
  password: symbols_password

daemon:
  # Path to kernel signatures from blacktop/symbolicator  
  sigs-dir: ./data/symbolicator/kernel
  port: 3993
  host: localhost
  
  s3:
    endpoint: http://localhost:9000
    access_key: minioadmin
    secret_key: minioadmin
    bucket: ipsw
    use_ssl: false

symbolication:
  enabled: true
  cache_size: 100
  cleanup_after_hours: 24

api:
  port: 8000
  host: localhost
  symbol_server_url: http://localhost:3993

cache:
  directory: ./data/cache
  max_size_gb: 100
  cleanup_interval_hours: 24
EOF
```

### 3. Download Kernel Signatures
```bash
git clone https://github.com/blacktop/symbolicator.git data/symbolicator
```

### 4. Start All Services
```bash
docker-compose --profile regular up -d --build
```

### 5. Verify Installation
```bash
# Check all services are healthy
docker ps

# Test configuration
python3 check_kernel_setup.py

# Test Web UI
curl http://localhost/
```

## Access Points

- **Web UI:** http://localhost/
- **API Docs:** http://localhost/docs  
- **Service Status:** http://localhost/status
- **S3 Console:** http://localhost/s3-console/

## CLI Tool
```bash
# Install CLI
./install_cli.sh

# Test with crash file
ipsw-cli your-crash-file.ips
```

## Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

### Database Issues
```bash
# Reset database
docker-compose down
docker volume rm $(docker volume ls -q | grep postgres)
docker-compose up -d postgres
```

### Disk Space
```bash
# Clean Docker cache
docker system prune -f

# Check disk usage
docker exec ipsw-symbol-server df -h
```

## Production Notes

1. **Security:** Change default passwords in production
2. **SSL:** Add SSL certificates for HTTPS
3. **Backups:** Backup PostgreSQL database regularly
4. **Monitoring:** Monitor disk space and memory usage
5. **Updates:** Keep Docker images updated

## File Structure
```
ipsw-symbol-server/
├── docker-compose.yml     # Main services
├── nginx.conf            # Reverse proxy config
├── data/
│   ├── symbolicator/     # Kernel signatures (1.9k files)
│   ├── cache/           # Symbol cache
│   └── temp/            # Processing temp files
├── ipsw_cli.py          # CLI tool
└── check_kernel_setup.py # Setup verification
```

## Quick Start (Airgap/Offline)

> **IMPORTANT: In airgap/offline mode, all dependencies (AppleDB, symbolicator, CLI, IPSW, etc.) must be provided locally. Do not run any internet download commands.**

1. Extract the provided package (including ./data/appledb, ./data/symbolicator, ./data/ipsw, etc.)
2. Start services:
```bash
docker-compose --profile airgap up -d
```
3. To install the CLI, copy ipsw_cli.py from the package to your PATH and run:
```bash
chmod +x ipsw_cli.py
mv ipsw_cli.py ~/.local/bin/ipsw-cli
```
4. All symbolication and device mapping will work fully offline, as long as all required data is present in ./data/. 