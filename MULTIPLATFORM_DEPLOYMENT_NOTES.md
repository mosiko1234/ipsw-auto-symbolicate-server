# IPSW Symbol Server v2.0.1 - Multi-Platform Deployment Package

## 🚀 What's New

This package includes the **multi-platform Docker image** that automatically works on:
- **AMD64** (Intel/AMD x86_64 servers)
- **ARM64** (Apple Silicon/ARM servers)

## 📦 Package Details

- **File**: `ipsw-symbol-server-v2.0.1-multiplatform-deployment.tar.gz`
- **Size**: 487MB (increased from 330MB due to multi-platform support)
- **SHA256**: `3230196d452ef99cfe397885dce69089691705a25cb5cdab47eefcd3fb7b41ba`

## 🔧 Key Improvements

1. **Automatic Architecture Detection**: The Docker image automatically downloads the correct `ipsw` CLI binary for your server's architecture
2. **Universal Compatibility**: Same package works on any Linux server (Intel, AMD, or ARM)
3. **Future-Proof**: Ready for ARM-based cloud servers (AWS Graviton, etc.)

## 📋 Deployment Instructions

1. **Extract the package:**
   ```bash
   tar -xzf ipsw-symbol-server-v2.0.1-multiplatform-deployment.tar.gz
   cd deployment-package/
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

3. **Verify it's working:**
   ```bash
   curl http://localhost/health | jq
   ```

## 🔍 Architecture Verification

Once deployed, you can verify the architecture:
```bash
# Check container architecture
docker exec symbol-server uname -m

# Check ipsw binary is working
docker exec symbol-server ipsw version
```

## 📚 Full Documentation

See `DEPLOYMENT_README.md` inside the package for complete deployment instructions and troubleshooting.

---

**This package replaces the previous v2.0.0 deployment with enhanced multi-platform support.** 