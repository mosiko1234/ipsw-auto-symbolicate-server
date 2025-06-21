#!/usr/bin/env python3
"""
S3 File Watcher for automatic IPSW detection and processing
Monitors S3 bucket for new IPSW files and triggers auto-scan
"""

import asyncio
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from pathlib import Path
import httpx
import os

logger = logging.getLogger(__name__)

class S3FileWatcher:
    def __init__(self, 
                 s3_manager, 
                 symbol_server_url: str = "http://localhost:3993",
                 check_interval_seconds: Optional[int] = None):  # Use env var or default
        """
        Initialize S3 File Watcher
        
        Args:
            s3_manager: The S3 manager instance to monitor
            symbol_server_url: URL of the symbol server
            check_interval_seconds: How often to check for changes (default: 5 minutes)
        """
        self.s3_manager = s3_manager
        self.symbol_server_url = symbol_server_url.rstrip('/')
        
        # Get configuration from environment or use defaults
        if check_interval_seconds is None:
            self.check_interval = int(os.getenv("S3_CHECK_INTERVAL", "300"))  # 5 minutes default
        else:
            self.check_interval = check_interval_seconds
            
        # Get auto-scan cooldown from environment
        cooldown_minutes = int(os.getenv("AUTO_SCAN_COOLDOWN", "600")) / 60  # Convert seconds to minutes
        self.auto_scan_cooldown = timedelta(minutes=cooldown_minutes)
        
        # Track known files
        self.known_files: Set[str] = set()
        self.last_check_timestamp = None
        
        # Store last known file hashes to detect actual changes
        self.file_hashes: Dict[str, str] = {}
        
        # Rate limiting for auto-scan to prevent overload
        self.last_auto_scan: Dict[str, datetime] = {}
        
        self.running = False
        
    async def start_monitoring(self):
        """Start monitoring S3 bucket for changes"""
        self.running = True
        logger.info(f"Starting S3 file watcher (check interval: {self.check_interval}s)")
        
        # Initial scan to populate known files
        await self._initial_scan()
        
        # Start monitoring loop
        while self.running:
            try:
                await self._check_for_changes()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in file watcher loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        logger.info("S3 file watcher stopped")
    
    async def _initial_scan(self):
        """Perform initial scan to establish baseline"""
        try:
            logger.info("Performing initial S3 scan...")
            await self.s3_manager.refresh_bucket_cache()
            
            # Get all currently available files
            current_files = await self.s3_manager.list_available_ipsw()
            
            for file_info in current_files:
                file_key = f"{file_info['device']}_{file_info['version']}"
                if file_info.get('build'):
                    file_key += f"_{file_info['build']}"
                
                self.known_files.add(file_key)
                
                # Calculate hash for change detection
                file_hash = self._calculate_file_hash(file_info)
                self.file_hashes[file_key] = file_hash
            
            self.last_check_timestamp = datetime.now()
            logger.info(f"Initial scan complete: found {len(self.known_files)} existing IPSW files")
            
        except Exception as e:
            logger.error(f"Error in initial scan: {e}")
    
    async def _check_for_changes(self):
        """Check for new or changed files"""
        try:
            # Refresh S3 cache
            await self.s3_manager.refresh_bucket_cache()
            
            # Get current files
            current_files = await self.s3_manager.list_available_ipsw()
            current_file_keys = set()
            current_file_hashes = {}
            
            # Process current files
            for file_info in current_files:
                file_key = f"{file_info['device']}_{file_info['version']}"
                if file_info.get('build'):
                    file_key += f"_{file_info['build']}"
                
                current_file_keys.add(file_key)
                file_hash = self._calculate_file_hash(file_info)
                current_file_hashes[file_key] = file_hash
            
            # Detect new files
            new_files = current_file_keys - self.known_files
            
            # Detect changed files (different hash)
            changed_files = set()
            for file_key in current_file_keys:
                if (file_key in self.known_files and 
                    current_file_hashes[file_key] != self.file_hashes.get(file_key)):
                    changed_files.add(file_key)
            
            # Process new and changed files
            files_to_process = new_files | changed_files
            
            if files_to_process:
                logger.info(f"Detected {len(new_files)} new files and {len(changed_files)} changed files")
                
                # Find the actual file info for processing
                files_info = []
                for file_info in current_files:
                    file_key = f"{file_info['device']}_{file_info['version']}"
                    if file_info.get('build'):
                        file_key += f"_{file_info['build']}"
                    
                    if file_key in files_to_process:
                        files_info.append(file_info)
                
                # Process each new/changed file
                for file_info in files_info:
                    await self._process_new_file(file_info)
            
            # Update tracking
            self.known_files = current_file_keys
            self.file_hashes = current_file_hashes
            self.last_check_timestamp = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
    
    async def _process_new_file(self, file_info: Dict):
        """Process a newly detected or changed IPSW file"""
        try:
            device = file_info['device']
            version = file_info['version']
            build = file_info.get('build', 'unknown')
            filename = file_info['filename']
            
            logger.info(f"Processing new/changed IPSW: {filename}")
            
            # Check rate limiting
            rate_limit_key = f"{device}_{version}_{build}"
            now = datetime.now()
            
            if (rate_limit_key in self.last_auto_scan and 
                now - self.last_auto_scan[rate_limit_key] < self.auto_scan_cooldown):
                logger.info(f"Skipping auto-scan for {rate_limit_key} due to rate limiting")
                return
            
            # Trigger symbol server cache refresh first
            await self._trigger_symbol_server_refresh()
            
            # Wait a bit for cache to refresh
            await asyncio.sleep(5)
            
            # Trigger auto-scan for this specific device/version
            success = await self._trigger_auto_scan(device, version, build)
            
            if success:
                logger.info(f"Successfully triggered auto-scan for {device} {version} ({build})")
                self.last_auto_scan[rate_limit_key] = now
            else:
                logger.warning(f"Failed to trigger auto-scan for {device} {version} ({build})")
            
        except Exception as e:
            logger.error(f"Error processing new file {file_info.get('filename', 'unknown')}: {e}")
    
    async def _trigger_symbol_server_refresh(self):
        """Trigger symbol server cache refresh"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.symbol_server_url}/v1/refresh-cache")
                if response.status_code == 200:
                    logger.info("Successfully triggered symbol server cache refresh")
                    return True
                else:
                    logger.warning(f"Symbol server cache refresh failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error triggering symbol server refresh: {e}")
            return False
    
    async def _trigger_auto_scan(self, device: str, version: str, build: str) -> bool:
        """Trigger auto-scan for specific device/version"""
        try:
            # Map device names to identifiers if needed
            device_model = self._map_device_name(device)
            
            params = {
                "device_model": device_model,
                "ios_version": version,
                "build_number": build
            }
            
            async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minute timeout for auto-scan
                response = await client.post(
                    f"{self.symbol_server_url}/v1/auto-scan",
                    params=params
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Auto-scan completed: {result.get('message', 'Success')}")
                    return True
                else:
                    error_text = response.text[:200] if response.text else "No error details"
                    logger.warning(f"Auto-scan failed ({response.status_code}): {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error triggering auto-scan: {e}")
            return False
    
    def _map_device_name(self, device: str) -> str:
        """Map device names to proper identifiers"""
        # Handle multi-device IPSW files (like "iPhone12,3,iPhone12,5")
        if ',' in device:
            # For multi-device, take the first device
            return device.split(',')[0]
        
        return device
    
    def _calculate_file_hash(self, file_info: Dict) -> str:
        """Calculate a hash for the file to detect changes"""
        # Use filename, size, and modification time if available
        hash_input = f"{file_info['filename']}_{file_info.get('size', 0)}"
        if file_info.get('modified'):
            hash_input += f"_{file_info['modified']}"
        
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def get_status(self) -> Dict:
        """Get current watcher status"""
        return {
            "running": self.running,
            "last_check": self.last_check_timestamp.isoformat() if self.last_check_timestamp else None,
            "known_files_count": len(self.known_files),
            "check_interval_seconds": self.check_interval,
            "auto_scan_cooldown_minutes": self.auto_scan_cooldown.total_seconds() / 60,
            "recent_auto_scans": {
                key: timestamp.isoformat() 
                for key, timestamp in self.last_auto_scan.items()
                if datetime.now() - timestamp < timedelta(hours=1)
            }
        }

# Global watcher instance
_watcher_instance: Optional[S3FileWatcher] = None

async def start_file_watcher(s3_manager, symbol_server_url: str = "http://localhost:3993"):
    """Start the global file watcher"""
    global _watcher_instance
    
    if _watcher_instance and _watcher_instance.running:
        logger.warning("File watcher is already running")
        return
    
    _watcher_instance = S3FileWatcher(s3_manager, symbol_server_url)
    
    # Start monitoring in background task
    asyncio.create_task(_watcher_instance.start_monitoring())
    logger.info("File watcher started in background")

def stop_file_watcher():
    """Stop the global file watcher"""
    global _watcher_instance
    
    if _watcher_instance:
        _watcher_instance.stop_monitoring()
        _watcher_instance = None
        logger.info("File watcher stopped")

async def get_watcher_status() -> Optional[Dict]:
    """Get status of the global file watcher"""
    global _watcher_instance
    
    if _watcher_instance:
        return await _watcher_instance.get_status()
    
    return None 