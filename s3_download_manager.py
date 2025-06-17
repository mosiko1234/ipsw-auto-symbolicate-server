#!/usr/bin/env python3
"""
S3 Download Manager for IPSW files in airgap environment
Downloads IPSW files from public S3 bucket without authentication
"""

import os
import re
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET

import httpx
import aiofiles
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class S3IPSWDownloader:
    def __init__(self, s3_endpoint: str, bucket_name: str, downloads_dir: Path):
        """
        Initialize S3 IPSW Downloader
        
        Args:
            s3_endpoint: S3 endpoint URL (e.g., "https://s3.example.com")
            bucket_name: S3 bucket name containing IPSW files
            downloads_dir: Local directory to download IPSW files
        """
        self.s3_endpoint = s3_endpoint.rstrip('/')
        self.bucket_name = bucket_name
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for S3 bucket listing
        self._bucket_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 3600  # 1 hour
        
    @property
    def bucket_url(self) -> str:
        """Get the base URL for the S3 bucket"""
        return f"{self.s3_endpoint}/{self.bucket_name}"
    
    async def refresh_bucket_cache(self) -> None:
        """Refresh the bucket cache by listing all IPSW files"""
        try:
            logger.info(f"Refreshing S3 bucket cache from {self.bucket_url}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # List bucket contents using S3 API
                response = await client.get(f"{self.bucket_url}/")
                
                if response.status_code == 200:
                    await self._parse_bucket_listing(response.text)
                    self._cache_timestamp = datetime.now()
                    logger.info(f"Cached {len(self._bucket_cache)} IPSW files")
                else:
                    logger.error(f"Failed to list S3 bucket: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error refreshing bucket cache: {e}")
    
    async def _parse_bucket_listing(self, xml_content: str) -> None:
        """Parse S3 bucket XML listing and extract IPSW file information"""
        try:
            # Parse XML response
            root = ET.fromstring(xml_content)
            
            # Handle different XML namespaces
            namespace = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
            if not root.findall('.//s3:Contents', namespace):
                # Try without namespace
                namespace = {}
            
            self._bucket_cache = {}
            
            # Extract file information
            for content in root.findall('.//Contents' if not namespace else './/s3:Contents', namespace):
                key_elem = content.find('Key' if not namespace else 's3:Key', namespace)
                size_elem = content.find('Size' if not namespace else 's3:Size', namespace)
                modified_elem = content.find('LastModified' if not namespace else 's3:LastModified', namespace)
                
                if key_elem is not None and key_elem.text.endswith('.ipsw'):
                    file_key = key_elem.text
                    file_info = self._parse_ipsw_filename(file_key)
                    
                    if file_info:
                        cache_key = f"{file_info['device']}_{file_info['version']}"
                        if file_info['build']:
                            cache_key += f"_{file_info['build']}"
                        
                        self._bucket_cache[cache_key] = {
                            'key': file_key,
                            'size': int(size_elem.text) if size_elem is not None else 0,
                            'modified': modified_elem.text if modified_elem is not None else None,
                            'device': file_info['device'],
                            'version': file_info['version'],
                            'build': file_info['build'],
                            'url': f"{self.bucket_url}/{quote(file_key)}"
                        }
                        
        except Exception as e:
            logger.error(f"Error parsing bucket listing: {e}")
    
    def _parse_ipsw_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Parse IPSW filename to extract device, version, and build info"""
        try:
            # Common IPSW filename patterns:
            # iPhone15,2_17.4_21E219_Restore.ipsw
            # iPad_Pro_HFR_17.4_21E219_Restore.ipsw
            # iPhone_15_Pro_17.4_21E219.ipsw
            
            patterns = [
                # Pattern 1: iPhone15,2_17.4_21E219_Restore.ipsw
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+)_.*\.ipsw',
                # Pattern 2: iPhone_15_Pro_17.4_21E219_Restore.ipsw
                r'([^/]+)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+).*\.ipsw',
                # Pattern 3: iPhone15,2_17.4_Restore.ipsw (no build)
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_.*\.ipsw',
                # Pattern 4: Simple format
                r'([^/]+?)[-_](\d+\.\d+(?:\.\d+)?).*\.ipsw'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    return {
                        'device': groups[0],
                        'version': groups[1],
                        'build': groups[2] if len(groups) > 2 else None
                    }
            
            logger.warning(f"Could not parse IPSW filename: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing filename {filename}: {e}")
            return None
    
    async def _ensure_cache_fresh(self) -> None:
        """Ensure the bucket cache is fresh"""
        if (self._cache_timestamp is None or 
            (datetime.now() - self._cache_timestamp).seconds > self._cache_ttl):
            await self.refresh_bucket_cache()
    
    async def find_ipsw(self, device_model: str, os_version: str, build_number: Optional[str] = None) -> Optional[Dict]:
        """Find IPSW file in S3 bucket"""
        await self._ensure_cache_fresh()
        
        # Try exact match first
        cache_keys = [
            f"{device_model}_{os_version}_{build_number}" if build_number else None,
            f"{device_model}_{os_version}",
        ]
        
        for cache_key in cache_keys:
            if cache_key and cache_key in self._bucket_cache:
                return self._bucket_cache[cache_key]
        
        # Try fuzzy matching
        for key, file_info in self._bucket_cache.items():
            if (self._device_matches(file_info['device'], device_model) and 
                file_info['version'] == os_version):
                if build_number is None or file_info['build'] == build_number:
                    return file_info
        
        logger.warning(f"IPSW not found in S3: {device_model} {os_version} {build_number}")
        return None
    
    def _device_matches(self, s3_device: str, target_device: str) -> bool:
        """Check if device names match (handle different naming conventions)"""
        # Normalize device names
        s3_norm = s3_device.lower().replace('_', '').replace('-', '').replace(' ', '')
        target_norm = target_device.lower().replace('_', '').replace('-', '').replace(' ', '')
        
        # Direct match
        if s3_norm == target_norm:
            return True
        
        # Handle iPhone naming variations
        if 'iphone' in s3_norm and 'iphone' in target_norm:
            # Extract numbers
            s3_nums = re.findall(r'\d+', s3_device)
            target_nums = re.findall(r'\d+', target_device)
            if s3_nums and target_nums:
                return s3_nums == target_nums
        
        return False
    
    async def download_ipsw(self, device_model: str, os_version: str, build_number: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Download IPSW file from S3"""
        try:
            # Check if already downloaded
            local_pattern = f"*{device_model}*{os_version}*.ipsw"
            existing_files = list(self.downloads_dir.glob(local_pattern))
            
            if existing_files:
                logger.info(f"IPSW already exists: {existing_files[0]}")
                return True, f"Already available: {existing_files[0].name}", str(existing_files[0])
            
            # Find IPSW in S3
            file_info = await self.find_ipsw(device_model, os_version, build_number)
            
            if not file_info:
                return False, f"IPSW not found in S3 for {device_model} {os_version} {build_number}", None
            
            # Download the file
            download_url = file_info['url']
            local_filename = f"{device_model}_{os_version}_{file_info['build'] or 'unknown'}.ipsw"
            local_path = self.downloads_dir / local_filename
            
            logger.info(f"Downloading IPSW from S3: {download_url}")
            start_time = datetime.now()
            
            async with httpx.AsyncClient(timeout=3600.0) as client:  # 1 hour timeout
                async with client.stream('GET', download_url) as response:
                    if response.status_code == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.aiter_bytes(chunk_size=1024*1024):  # 1MB chunks
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Log progress every 100MB
                                if downloaded % (100 * 1024 * 1024) == 0:
                                    progress = (downloaded / total_size * 100) if total_size > 0 else 0
                                    logger.info(f"Download progress: {progress:.1f}% ({downloaded // (1024*1024)}MB/{total_size // (1024*1024)}MB)")
                        
                        download_time = (datetime.now() - start_time).total_seconds()
                        logger.info(f"IPSW downloaded successfully in {download_time:.2f}s: {local_path}")
                        
                        return True, f"Downloaded from S3 in {download_time:.2f}s", str(local_path)
                    
                    else:
                        return False, f"S3 download failed with status {response.status_code}", None
            
        except Exception as e:
            logger.error(f"Error downloading IPSW from S3: {e}")
            return False, f"S3 download error: {str(e)}", None
    
    async def list_available_ipsw(self, device_filter: Optional[str] = None) -> List[Dict]:
        """List all available IPSW files in S3"""
        await self._ensure_cache_fresh()
        
        results = []
        for file_info in self._bucket_cache.values():
            if device_filter is None or device_filter.lower() in file_info['device'].lower():
                results.append({
                    'device': file_info['device'],
                    'version': file_info['version'],
                    'build': file_info['build'],
                    'size_mb': file_info['size'] // (1024 * 1024),
                    'modified': file_info['modified'],
                    'key': file_info['key']
                })
        
        return sorted(results, key=lambda x: (x['device'], x['version']))
    
    async def get_bucket_stats(self) -> Dict:
        """Get statistics about the S3 bucket"""
        await self._ensure_cache_fresh()
        
        devices = set()
        versions = set()
        total_size = 0
        
        for file_info in self._bucket_cache.values():
            devices.add(file_info['device'])
            versions.add(file_info['version'])
            total_size += file_info['size']
        
        return {
            'total_files': len(self._bucket_cache),
            'unique_devices': len(devices),
            'unique_versions': len(versions),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'devices': sorted(list(devices)),
            'versions': sorted(list(versions), key=lambda x: [int(i) for i in x.split('.')])
        }