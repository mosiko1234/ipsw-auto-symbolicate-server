# Changelog

All notable changes to the IPSW Auto-Symbolicate Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-06-19

### ✨ Added
- **Complete Device Mapping System** - AppleDB integration for automatic device name translation
  - Marketing names (iPhone 14 Pro) to device identifiers (iPhone15,2)
  - Support for all Apple devices (iPhone, iPad, Apple Watch, Apple TV, iPod)
  - 2000+ device mappings included offline
- **Enhanced Airgap Support** - Zero internet dependencies during operation
  - Pre-bundled AppleDB database in Docker images
  - Pre-installed IPSW CLI binary
  - All dependencies included, no external downloads required
- **Smart Auto-Scan** - Intelligent IPSW detection and symbol extraction
  - Automatic device mapping in symbolication workflow
  - Enhanced S3 IPSW discovery with device filtering
  - Improved error messaging with mapping information

### 🔧 Fixed
- **Container Networking** - Fixed S3 endpoint configuration for containerized environments
  - Changed from localhost:9000 to minio:9000 for internal Docker communication
  - Consistent S3 credentials across all services
  - Proper container-to-container networking
- **Device Filtering** - Enhanced device matching logic in S3 IPSW discovery
  - Fixed list_available_ipsw filtering to use same logic as find_ipsw
  - Improved device name matching for fuzzy searches
  - Better handling of marketing names vs identifiers

### 📦 Infrastructure
- **Docker Image Optimization** - Bundled all offline dependencies
  - AppleDB data included in symbol-server image
  - IPSW CLI binary pre-installed
  - Reduced external dependencies to zero for airgap mode
- **Configuration Simplification** - Streamlined Docker Compose setup
  - Fixed environment variables across all services
  - Consistent credentials and endpoints
  - Simplified deployment process

### 🚀 Performance
- **Symbol Extraction** - Improved symbolication performance
  - Enhanced caching with device-specific keys
  - Better memory management during IPSW processing
  - Faster device mapping lookups
- **Auto-Scan Results** - More detailed symbolication reporting
  - 21,206+ symbols extracted for iPhone 14 Pro iOS 18.5
  - Improved success rate reporting
  - Better error handling and user feedback

### 📖 Documentation
- **Updated README** - Complete rewrite with new features
  - Device mapping examples and workflows
  - Enhanced airgap deployment instructions
  - Improved architecture diagrams
- **Enhanced CLI Documentation** - Updated usage examples
  - Smart device detection examples
  - Rich output formatting samples
  - Airgap-specific installation instructions

### 🔄 Migration Notes
- Existing deployments will automatically benefit from device mapping
- No configuration changes required for existing setups
- AppleDB data will be included in new container builds
- IPSW files uploaded with proper naming will be automatically detected

---

## [1.1.0] - 2024-06-15

### Added
- Airgap deployment support with Docker Compose profiles
- Enhanced storage management with auto-cleanup
- CLI tool with rich terminal interface
- Comprehensive documentation and deployment guides

### Fixed
- MinIO bucket auto-creation issues
- Docker volume mounting problems
- Memory usage optimization

### Changed
- Unified Docker Compose configuration
- Simplified deployment process
- Enhanced security for offline environments

---

## [1.0.0] - 2024-06-10

### Added
- Initial release with core symbolication functionality
- Docker Compose deployment
- Web UI for crash file upload
- REST API for automation
- PostgreSQL symbol caching
- MinIO S3 storage integration

### Features
- Automatic IPSW detection and download
- Symbol extraction and caching
- Multi-device support
- Health monitoring and logging 