# Deployment Scripts

This directory contains all deployment and management scripts for the IPSW Auto-Symbolicate Server.

## 🚀 Deployment Scripts

### deploy-regular.sh
- **Purpose**: Deploy in regular environment with internet access
- **Features**: Builds Docker images, creates internal MinIO
- **Usage**: `./deploy-regular.sh`

### deploy-airgap.sh
- **Purpose**: Deploy in airgap/offline environment
- **Features**: Uses pre-built images, external S3
- **Usage**: `./deploy-airgap.sh`

### build-images-for-airgap.sh
- **Purpose**: Prepare Docker images for airgap deployment
- **Features**: Builds and pushes to registry, creates offline archive
- **Usage**: `./build-images-for-airgap.sh`

## 🔧 Management Scripts

### start-server.sh
- **Purpose**: Start the unified server system
- **Features**: Health checks, service coordination
- **Usage**: `./start-server.sh`

### stop-server.sh
- **Purpose**: Stop all services gracefully
- **Features**: Proper shutdown sequence
- **Usage**: `./stop-server.sh`

## 🔄 Workflow

### Regular Deployment
```bash
./deploy-regular.sh
```

### Airgap Deployment
```bash
# Step 1: In connected environment
./build-images-for-airgap.sh

# Step 2: Transfer to airgap environment
# Copy ipsw-images-{version}.tar

# Step 3: In airgap environment
docker load -i ipsw-images-{version}.tar
./deploy-airgap.sh
```

## 📋 Requirements

All scripts require:
- ✅ Docker & Docker Compose
- ✅ Bash shell
- ✅ Proper permissions (executable)
- ✅ Environment configuration in `config/` 