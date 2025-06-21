# IPSW Symbol Server v1.2.1 - Complete Package

## Package Information
- **Version**: v1.2.1 (Device Mapping Fix)
- **Package Name**: `ipsw-symbol-server-v1.2.1-complete-with-images.zip`
- **Size**: 1.9GB
- **MD5 Checksum**: `6952a52e108f636e48bd2b3549a5934d`
- **Created**: June 19, 2025

## Contents
✅ **Complete Source Code** - Latest version with device mapping fix  
✅ **Updated Docker Images** - All 6 images with fixes applied  
✅ **AppleDB Data** - Device mapping database  
✅ **Documentation** - Setup and usage guides  
✅ **Automation Scripts** - Loading and verification tools  

## Critical Fix Included
🔧 **Device Mapping Implementation** - Resolves IPSW auto-scan failures by properly translating device names (e.g., "iPhone 14 Pro" → "iPhone15,2")

## Package Structure
```
ipsw-symbol-server/
├── api_with_ui.py           # ✅ FIXED - Device mapping implementation
├── docker_images_updated/   # ✅ All 6 updated Docker images
├── data/                    # AppleDB device mapping data
├── docker-compose.yml       # Updated compose configuration
├── README.md               # Comprehensive documentation
└── ... (all other project files)
```

## For Airgap Network Deployment
1. Transfer this ZIP file to target network
2. Extract: `unzip ipsw-symbol-server-v1.2.1-complete-with-images.zip`
3. Load images: `cd ipsw-symbol-server/docker_images_updated && ./load-images-updated.sh`
4. Deploy: `cd .. && docker-compose --profile regular up -d`

## Verification
```bash
# Verify package integrity
md5 ipsw-symbol-server-v1.2.1-complete-with-images.zip
# Should match: 6952a52e108f636e48bd2b3549a5934d

# Verify Docker images after loading
./docker_images_updated/verify-checksums-updated.sh
```

## Support
- GitHub: `mosiko1234/ipsw-auto-symbolicate-server`
- Tag: `v1.2.1`
- Issues: Device mapping problems resolved in this version 