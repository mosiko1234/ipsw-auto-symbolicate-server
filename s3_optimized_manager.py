#!/usr/bin/env python3
"""
S3 Optimized Manager for Production IPSW Symbol Server
Handles direct S3 access, intelligent caching, and automatic cleanup
"""

import os
import time
import shutil
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import json

class S3OptimizedManager:
    def __init__(self):
        # Configuration from environment
        self.s3_mount_path = Path("/app/data/s3-ipsw")
        self.cache_path = Path("/app/data/cache")
        self.symbols_path = Path("/app/data/symbols")
        self.temp_path = Path("/app/data/temp")
        self.processing_path = Path("/app/data/processing")
        
        # Cache settings
        self.cache_size_gb = int(os.getenv("CACHE_SIZE_GB", "50"))
        self.cleanup_after_hours = int(os.getenv("CLEANUP_AFTER_HOURS", "24"))
        self.max_concurrent_downloads = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
        
        # Ensure directories exist
        for path in [self.cache_path, self.symbols_path, self.temp_path, self.processing_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Cache tracking
        self.cache_metadata_file = self.cache_path / "cache_metadata.json"
        self.access_log = {}
        self.processing_lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load cache metadata
        self.load_cache_metadata()
        
        # Start background cleanup thread
        cleanup_thread = threading.Thread(target=self.background_cleanup, daemon=True)
        cleanup_thread.start()
    
    def load_cache_metadata(self):
        """Load cache access metadata"""
        try:
            if self.cache_metadata_file.exists():
                with open(self.cache_metadata_file, 'r') as f:
                    self.access_log = json.load(f)
            else:
                self.access_log = {}
        except Exception as e:
            self.logger.error(f"Failed to load cache metadata: {e}")
            self.access_log = {}
    
    def save_cache_metadata(self):
        """Save cache access metadata"""
        try:
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(self.access_log, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache metadata: {e}")
    
    def get_cache_key(self, device_model: str, os_version: str, build_number: str) -> str:
        """Generate cache key for IPSW file"""
        key_string = f"{device_model}_{os_version}_{build_number}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def get_ipsw_path(self, device_model: str, os_version: str, build_number: str) -> Optional[Path]:
        """
        Get IPSW file path using intelligent caching strategy:
        1. Check local cache first
        2. Check S3 mount
        3. Download to cache if needed
        """
        cache_key = self.get_cache_key(device_model, os_version, build_number)
        
        # Update access log
        self.access_log[cache_key] = {
            "device_model": device_model,
            "os_version": os_version,
            "build_number": build_number,
            "last_access": datetime.now().isoformat(),
            "access_count": self.access_log.get(cache_key, {}).get("access_count", 0) + 1
        }
        
        # 1. Check local cache
        cached_ipsw = self.get_cached_ipsw(cache_key, device_model, os_version, build_number)
        if cached_ipsw and cached_ipsw.exists():
            self.logger.info(f"Using cached IPSW: {cached_ipsw}")
            return cached_ipsw
        
        # 2. Check S3 mount (direct access)
        s3_ipsw = self.find_s3_ipsw(device_model, os_version, build_number)
        if s3_ipsw and s3_ipsw.exists():
            self.logger.info(f"Using S3 IPSW: {s3_ipsw}")
            
            # Optionally cache frequently accessed files
            if self.should_cache_file(cache_key):
                self.cache_ipsw_async(s3_ipsw, cache_key, device_model, os_version, build_number)
            
            return s3_ipsw
        
        # 3. File not found
        self.logger.warning(f"IPSW not found for {device_model} {os_version} {build_number}")
        return None
    
    def find_s3_ipsw(self, device_model: str, os_version: str, build_number: str) -> Optional[Path]:
        """Find IPSW file in S3 mount"""
        try:
            if not self.s3_mount_path.exists():
                self.logger.warning("S3 mount path not available")
                return None
            
            # Common naming patterns
            patterns = [
                f"{device_model}_{os_version}_{build_number}_Restore.ipsw",
                f"{device_model}_{os_version}_{build_number}_Restore-2.ipsw",
                f"{device_model}_{build_number}_Restore.ipsw",
                f"{device_model}*{os_version}*.ipsw",
                f"{device_model}*{build_number}*.ipsw"
            ]
            
            for pattern in patterns:
                matches = list(self.s3_mount_path.glob(pattern))
                if matches:
                    return matches[0]  # Return first match
            
            return None
        except Exception as e:
            self.logger.error(f"Error searching S3 mount: {e}")
            return None
    
    def get_cached_ipsw(self, cache_key: str, device_model: str, os_version: str, build_number: str) -> Optional[Path]:
        """Get IPSW from local cache"""
        cache_dir = self.cache_path / cache_key
        if not cache_dir.exists():
            return None
        
        # Find IPSW file in cache directory
        ipsw_files = list(cache_dir.glob("*.ipsw"))
        if ipsw_files:
            return ipsw_files[0]
        
        return None
    
    def should_cache_file(self, cache_key: str) -> bool:
        """Determine if file should be cached based on access patterns"""
        access_info = self.access_log.get(cache_key, {})
        access_count = access_info.get("access_count", 0)
        
        # Cache files that are accessed more than once
        return access_count > 1
    
    def cache_ipsw_async(self, source_path: Path, cache_key: str, device_model: str, os_version: str, build_number: str):
        """Cache IPSW file asynchronously"""
        def cache_worker():
            try:
                cache_dir = self.cache_path / cache_key
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = cache_dir / source_path.name
                
                if not target_path.exists():
                    self.logger.info(f"Caching IPSW: {source_path} -> {target_path}")
                    
                    # Check available space before caching
                    if self.has_enough_space(source_path.stat().st_size):
                        shutil.copy2(source_path, target_path)
                        self.logger.info(f"Successfully cached IPSW: {target_path}")
                    else:
                        self.logger.warning("Not enough space to cache IPSW")
                        
            except Exception as e:
                self.logger.error(f"Failed to cache IPSW: {e}")
        
        # Run in background thread
        cache_thread = threading.Thread(target=cache_worker, daemon=True)
        cache_thread.start()
    
    def has_enough_space(self, required_bytes: int) -> bool:
        """Check if there's enough space for caching"""
        try:
            # Get cache directory usage
            cache_usage = sum(f.stat().st_size for f in self.cache_path.rglob('*') if f.is_file())
            cache_usage_gb = cache_usage / (1024**3)
            
            required_gb = required_bytes / (1024**3)
            
            # Check if adding this file would exceed cache limit
            if cache_usage_gb + required_gb > self.cache_size_gb:
                # Try to free up space
                self.cleanup_cache(required_gb)
                
                # Recheck after cleanup
                cache_usage = sum(f.stat().st_size for f in self.cache_path.rglob('*') if f.is_file())
                cache_usage_gb = cache_usage / (1024**3)
                
                return cache_usage_gb + required_gb <= self.cache_size_gb
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            return False
    
    def cleanup_cache(self, required_gb: float = 0):
        """Clean up cache to free space"""
        try:
            self.logger.info(f"Starting cache cleanup (need {required_gb:.1f}GB)")
            
            # Get all cached items with their access info
            cached_items = []
            for cache_dir in self.cache_path.iterdir():
                if cache_dir.is_dir() and cache_dir.name in self.access_log:
                    access_info = self.access_log[cache_dir.name]
                    last_access = datetime.fromisoformat(access_info.get("last_access", "1970-01-01"))
                    
                    # Calculate size
                    size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    size_gb = size / (1024**3)
                    
                    cached_items.append({
                        "path": cache_dir,
                        "cache_key": cache_dir.name,
                        "last_access": last_access,
                        "size_gb": size_gb,
                        "access_count": access_info.get("access_count", 0)
                    })
            
            # Sort by last access time (oldest first) and low access count
            cached_items.sort(key=lambda x: (x["access_count"], x["last_access"]))
            
            freed_gb = 0
            for item in cached_items:
                if required_gb > 0 and freed_gb >= required_gb:
                    break
                
                # Remove old or infrequently accessed items
                age_hours = (datetime.now() - item["last_access"]).total_seconds() / 3600
                
                if age_hours > self.cleanup_after_hours or item["access_count"] == 1:
                    self.logger.info(f"Removing cached item: {item['path']} ({item['size_gb']:.1f}GB)")
                    shutil.rmtree(item["path"], ignore_errors=True)
                    
                    # Remove from access log
                    if item["cache_key"] in self.access_log:
                        del self.access_log[item["cache_key"]]
                    
                    freed_gb += item["size_gb"]
            
            self.logger.info(f"Cache cleanup completed, freed {freed_gb:.1f}GB")
            self.save_cache_metadata()
            
        except Exception as e:
            self.logger.error(f"Cache cleanup failed: {e}")
    
    def background_cleanup(self):
        """Background thread for periodic cleanup"""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                self.cleanup_cache()
            except Exception as e:
                self.logger.error(f"Background cleanup error: {e}")
    
    def get_symbols_path(self, device_model: str, os_version: str, build_number: str) -> Path:
        """Get symbols directory path"""
        cache_key = self.get_cache_key(device_model, os_version, build_number)
        symbols_dir = self.symbols_path / cache_key
        symbols_dir.mkdir(parents=True, exist_ok=True)
        return symbols_dir
    
    def get_processing_path(self) -> Path:
        """Get temporary processing path"""
        processing_file = self.processing_path / f"processing_{int(time.time())}_{threading.get_ident()}"
        return processing_file
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            cache_usage = sum(f.stat().st_size for f in self.cache_path.rglob('*') if f.is_file())
            cache_usage_gb = cache_usage / (1024**3)
            
            cached_items = len([d for d in self.cache_path.iterdir() if d.is_dir()])
            
            return {
                "cache_usage_gb": round(cache_usage_gb, 2),
                "cache_limit_gb": self.cache_size_gb,
                "cache_utilization_percent": round((cache_usage_gb / self.cache_size_gb) * 100, 1),
                "cached_items": cached_items,
                "total_accesses": sum(item.get("access_count", 0) for item in self.access_log.values())
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}


# Global instance
s3_manager = S3OptimizedManager() 