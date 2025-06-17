#!/usr/bin/env python3
"""
S3 HTML Index Download Manager for IPSW files
Downloads IPSW files from S3 static website with HTML index
Enhanced with better error handling and flexibility
"""

import os
import re
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, quote, urlparse
from bs4 import BeautifulSoup

import httpx
import aiofiles

logger = logging.getLogger(__name__)

class S3HTMLIPSWDownloader:
    def __init__(self, s3_endpoint: str, bucket_name: str, downloads_dir: Path, verify_ssl: bool = True):
        """
        Initialize S3 HTML IPSW Downloader for static websites
        
        Args:
            s3_endpoint: S3 website URL (e.g., "https://s3-prod.moshe.network")
            bucket_name: Path to IPSW files (e.g., "ipsw")  
            downloads_dir: Local directory to download IPSW files
            verify_ssl: Whether to verify SSL certificates (set False for internal networks)
        """
        self.s3_endpoint = s3_endpoint.rstrip('/')
        self.bucket_name = bucket_name.strip('/')
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.verify_ssl = verify_ssl
        
        # Cache for S3 bucket listing
        self._bucket_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 3600  # 1 hour
        
        # Connection settings
        self._timeout = 60.0
        self._max_retries = 3
        
        # Log SSL verification setting
        if not self.verify_ssl:
            import logging
            logging.getLogger(__name__).warning("SSL certificate verification is DISABLED - use only in trusted internal networks")
        
    @property
    def bucket_url(self) -> str:
        """Get the base URL for the S3 bucket"""
        return f"{self.s3_endpoint}/{self.bucket_name}"
    
    async def refresh_bucket_cache(self) -> None:
        """Refresh the bucket cache by parsing HTML index"""
        try:
            logger.info(f"Refreshing S3 bucket cache from {self.bucket_url}")
            
            # Enhanced URL list with more variations
            urls_to_try = [
                f"{self.bucket_url}/",
                f"{self.bucket_url}/index.html",
                f"{self.bucket_url}",
                f"{self.bucket_url}/index.htm",
                # Try HTTP if HTTPS fails
                f"{self.bucket_url.replace('https://', 'http://')}/",
                f"{self.bucket_url.replace('https://', 'http://')}/index.html",
            ]
            
            # Remove duplicates while preserving order
            urls_to_try = list(dict.fromkeys(urls_to_try))
            
            html_content = None
            working_url = None
            
            # Enhanced HTTP client with better error handling
            client_config = {
                'timeout': self._timeout,
                'follow_redirects': True,
                'verify': self.verify_ssl,  # Use configurable SSL verification
            }
            
            async with httpx.AsyncClient(**client_config) as client:
                for url in urls_to_try:
                    try:
                        logger.info(f"Trying URL: {url}")
                        response = await client.get(url)
                        
                        logger.info(f"Response: {response.status_code} from {url}")
                        
                        if response.status_code == 200:
                            html_content = response.text
                            working_url = url
                            logger.info(f"Successfully fetched from: {url}")
                            break
                        elif response.status_code in [301, 302, 303, 307, 308]:
                            logger.info(f"Redirect from {url} to {response.headers.get('location', 'unknown')}")
                            continue
                        else:
                            logger.warning(f"HTTP {response.status_code} from {url}")
                            
                    except httpx.ConnectTimeout:
                        logger.warning(f"Connection timeout for {url}")
                        continue
                    except httpx.ReadTimeout:
                        logger.warning(f"Read timeout for {url}")
                        continue
                    except httpx.ConnectError as e:
                        logger.warning(f"Connection error for {url}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Unexpected error for {url}: {e}")
                        continue
                
                if html_content and working_url:
                    await self._parse_html_listing(html_content, working_url)
                    self._cache_timestamp = datetime.now()
                    logger.info(f"Cached {len(self._bucket_cache)} IPSW files from HTML")
                else:
                    logger.error("Failed to fetch HTML listing from any URL")
                    logger.error("Tried URLs:")
                    for url in urls_to_try:
                        logger.error(f"  - {url}")
                    
        except Exception as e:
            logger.error(f"Error refreshing bucket cache: {e}")
    
    async def _parse_html_listing(self, html_content: str, base_url: str) -> None:
        """Parse HTML index and extract IPSW file information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            self._bucket_cache = {}
            
            # Look for IPSW links in the HTML
            ipsw_links = []
            
            # Method 1: Find all links ending with .ipsw
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.ipsw'):
                    ipsw_links.append(href)
            
            # Method 2: Find text containing .ipsw (in case links are broken)
            if not ipsw_links:
                text_content = soup.get_text()
                ipsw_matches = re.findall(r'[^\s<>"\']+\.ipsw', text_content)
                ipsw_links.extend(ipsw_matches)
            
            # Method 3: Look for common patterns in table rows or list items
            if not ipsw_links:
                for element in soup.find_all(['tr', 'li', 'div', 'span']):
                    text = element.get_text()
                    if '.ipsw' in text:
                        # Extract filename from text
                        ipsw_match = re.search(r'([^\s<>"\']*\.ipsw)', text)
                        if ipsw_match:
                            ipsw_links.append(ipsw_match.group(1))
            
            # Method 4: Look in script tags or data attributes
            if not ipsw_links:
                for script in soup.find_all('script'):
                    if script.string:
                        ipsw_matches = re.findall(r'[^\s<>"\']+\.ipsw', script.string)
                        ipsw_links.extend(ipsw_matches)
            
            logger.info(f"Found {len(ipsw_links)} IPSW links in HTML")
            
            # Process each IPSW file
            for ipsw_file in ipsw_links:
                # Clean up the filename (remove any URL encoding)
                filename = ipsw_file.split('/')[-1]  # Get just the filename
                
                file_info = self._parse_ipsw_filename(filename)
                if file_info:
                    cache_key = f"{file_info['device']}_{file_info['version']}"
                    if file_info['build']:
                        cache_key += f"_{file_info['build']}"
                    
                    # Build the download URL with better logic
                    download_url = self._build_download_url(ipsw_file, base_url)
                    
                    self._bucket_cache[cache_key] = {
                        'key': filename,
                        'size': 0,  # Size unknown from HTML
                        'modified': None,  # Modification time unknown
                        'device': file_info['device'],
                        'version': file_info['version'],
                        'build': file_info['build'],
                        'url': download_url
                    }
                    
                    logger.debug(f"Cached IPSW: {cache_key} -> {download_url}")
                        
        except Exception as e:
            logger.error(f"Error parsing HTML listing: {e}")
    
    def _build_download_url(self, ipsw_file: str, base_url: str) -> str:
        """Build proper download URL for IPSW file"""
        try:
            # If it's already a full URL, use it
            if ipsw_file.startswith('http'):
                return ipsw_file
            
            # If it starts with /, it's relative to domain
            if ipsw_file.startswith('/'):
                parsed_base = urlparse(base_url)
                return f"{parsed_base.scheme}://{parsed_base.netloc}{ipsw_file}"
            
            # Otherwise, it's relative to current path
            return urljoin(base_url, ipsw_file)
            
        except Exception as e:
            logger.warning(f"Error building download URL for {ipsw_file}: {e}")
            # Fallback to simple concatenation
            return f"{self.bucket_url}/{ipsw_file}"
    
    def _parse_ipsw_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Parse IPSW filename to extract device, version, and build info"""
        try:
            # Enhanced patterns for better matching
            patterns = [
                # Pattern 1: iPhone15,2_17.4_21E219_Restore.ipsw
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+)_.*\.ipsw',
                # Pattern 2: iPhone_15_Pro_17.4_21E219_Restore.ipsw  
                r'([^/]+)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+).*\.ipsw',
                # Pattern 3: iPhone15,2_17.4_Restore.ipsw (no build)
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_.*\.ipsw',
                # Pattern 4: Simple format
                r'([^/]+?)[-_](\d+\.\d+(?:\.\d+)?).*\.ipsw',
                # Pattern 5: Even simpler - just device and version
                r'([^/\s]+).*?(\d+\.\d+(?:\.\d+)?).*\.ipsw'
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
            
            # Enhanced download with better error handling
            client_config = {
                'timeout': 3600.0,  # 1 hour timeout for large files
                'follow_redirects': True,
                'verify': self.verify_ssl,  # Use configurable SSL verification
            }
            
            async with httpx.AsyncClient(**client_config) as client:
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
            logger.error(f"Error downloading IPSW: {e}")
            return False, f"Download error: {str(e)}", None
    
    async def list_available_ipsw(self, device_filter: Optional[str] = None) -> List[Dict]:
        """List all available IPSW files, optionally filtered by device"""
        await self._ensure_cache_fresh()
        
        files = []
        for key, file_info in self._bucket_cache.items():
            if device_filter is None or device_filter.lower() in file_info['device'].lower():
                files.append({
                    'filename': file_info['key'],
                    'device': file_info['device'],
                    'version': file_info['version'],
                    'build': file_info['build'],
                    'size': file_info['size'],
                    'url': file_info['url']
                })
        
        return sorted(files, key=lambda x: (x['device'], x['version']))
    
    async def get_bucket_stats(self) -> Dict:
        """Get statistics about the S3 bucket"""
        await self._ensure_cache_fresh()
        
        total_files = len(self._bucket_cache)
        devices = set(info['device'] for info in self._bucket_cache.values())
        versions = set(info['version'] for info in self._bucket_cache.values())
        
        return {
            'total_files': total_files,
            'unique_devices': len(devices),
            'unique_versions': len(versions),
            'devices': sorted(list(devices)),
            'versions': sorted(list(versions)),
            'cache_timestamp': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        } 