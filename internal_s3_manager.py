#!/usr/bin/env python3
"""
Internal S3 Manager for IPSW files in internal network environment
Designed to work with internal S3 buckets with web interface (index.html)
Supports both API access and web scraping for file discovery
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
from urllib.parse import urljoin, quote, unquote
from bs4 import BeautifulSoup

import httpx
import aiofiles

logger = logging.getLogger(__name__)

class InternalS3Manager:
    def __init__(self, s3_endpoint: str, bucket_name: str, downloads_dir: Path, use_ssl: bool = False):
        """
        Initialize Internal S3 Manager for internal network
        
        Args:
            s3_endpoint: Internal S3 endpoint URL (e.g., "http://s3.company.local")
            bucket_name: S3 bucket name containing IPSW files
            downloads_dir: Local directory to download IPSW files
            use_ssl: Whether to use HTTPS (usually false for internal networks)
        """
        self.s3_endpoint = s3_endpoint.rstrip('/')
        self.bucket_name = bucket_name
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.use_ssl = use_ssl
        
        # Cache for S3 bucket listing
        self._bucket_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 1800  # 30 minutes for internal network
        
        # Internal network optimizations
        self.timeout = httpx.Timeout(connect=10.0, read=120.0, write=120.0, pool=120.0)
        
    @property
    def bucket_url(self) -> str:
        """Get the base URL for the S3 bucket"""
        return f"{self.s3_endpoint}/{self.bucket_name}"
    
    @property
    def web_index_url(self) -> str:
        """Get the web interface URL for the S3 bucket"""
        return f"{self.bucket_url}/"
    
    async def refresh_bucket_cache(self) -> None:
        """Refresh the bucket cache by listing all IPSW files from web interface"""
        try:
            logger.info(f"Refreshing internal S3 bucket cache from {self.web_index_url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=False,  # Skip SSL verification for internal networks
                follow_redirects=True
            ) as client:
                
                # Try API access first
                api_success = await self._try_api_listing(client)
                
                # If API fails, try web scraping
                if not api_success:
                    await self._try_web_scraping(client)
                
                self._cache_timestamp = datetime.now()
                logger.info(f"Cached {len(self._bucket_cache)} IPSW files from internal S3")
                    
        except Exception as e:
            logger.error(f"Error refreshing internal bucket cache: {e}")
    
    async def _try_api_listing(self, client: httpx.AsyncClient) -> bool:
        """Try to get bucket listing via S3 API"""
        try:
            # Try S3 API list-objects
            response = await client.get(f"{self.bucket_url}/")
            
            if response.status_code == 200 and 'xml' in response.headers.get('content-type', '').lower():
                await self._parse_s3_xml_listing(response.text)
                return True
                
        except Exception as e:
            logger.debug(f"S3 API listing failed: {e}")
        
        return False
    
    async def _try_web_scraping(self, client: httpx.AsyncClient) -> None:
        """Scrape web interface to get file listing"""
        try:
            response = await client.get(self.web_index_url)
            
            if response.status_code == 200:
                await self._parse_html_listing(response.text)
            else:
                logger.error(f"Failed to access web interface: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
    
    async def _parse_s3_xml_listing(self, xml_content: str) -> None:
        """Parse S3 API XML listing"""
        try:
            root = ET.fromstring(xml_content)
            
            # Handle different XML namespaces
            namespace = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
            if not root.findall('.//s3:Contents', namespace):
                namespace = {}
            
            self._bucket_cache = {}
            
            for content in root.findall('.//Contents' if not namespace else './/s3:Contents', namespace):
                key_elem = content.find('Key' if not namespace else 's3:Key', namespace)
                size_elem = content.find('Size' if not namespace else 's3:Size', namespace)
                modified_elem = content.find('LastModified' if not namespace else 's3:LastModified', namespace)
                
                if key_elem is not None and key_elem.text.endswith('.ipsw'):
                    await self._process_ipsw_file(
                        key_elem.text,
                        int(size_elem.text) if size_elem is not None else 0,
                        modified_elem.text if modified_elem is not None else None
                    )
                        
        except Exception as e:
            logger.error(f"Error parsing S3 XML listing: {e}")
    
    async def _parse_html_listing(self, html_content: str) -> None:
        """Parse HTML index page to extract IPSW files"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            self._bucket_cache = {}
            
            # Look for links to .ipsw files
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.ipsw'):
                    # Extract file name from href
                    filename = unquote(href.split('/')[-1])
                    
                    # Try to get file size from the text
                    size = 0
                    link_text = link.get_text() or ""
                    parent_text = link.parent.get_text() if link.parent else ""
                    
                    # Look for size patterns in the surrounding text
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB|KB)', parent_text, re.IGNORECASE)
                    if size_match:
                        size_val, unit = size_match.groups()
                        multiplier = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
                        size = int(float(size_val) * multiplier.get(unit.upper(), 1))
                    
                    await self._process_ipsw_file(filename, size, None)
                        
        except Exception as e:
            logger.error(f"Error parsing HTML listing: {e}")
    
    async def _process_ipsw_file(self, filename: str, size: int, modified: Optional[str]) -> None:
        """Process discovered IPSW file and add to cache"""
        file_info = self._parse_ipsw_filename(filename)
        
        if file_info:
            cache_key = f"{file_info['device']}_{file_info['version']}"
            if file_info['build']:
                cache_key += f"_{file_info['build']}"
            
            self._bucket_cache[cache_key] = {
                'key': filename,
                'size': size,
                'modified': modified,
                'device': file_info['device'],
                'version': file_info['version'],
                'build': file_info['build'],
                'url': f"{self.bucket_url}/{quote(filename)}"
            }
    
    def _parse_ipsw_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Parse IPSW filename to extract device, version, and build info"""
        try:
            # Extended patterns for internal S3 naming conventions
            patterns = [
                # iPhone15,2_17.4_21E219_Restore.ipsw
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+)_.*\.ipsw',
                # iPhone_15_Pro_17.4_21E219_Restore.ipsw
                r'([^/]+?)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+).*\.ipsw',
                # iPhone15,2_17.4_Restore.ipsw (no build)
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_.*\.ipsw',
                # iPhone15,2-17.4-21E219.ipsw (dash separator)
                r'([^-/]+)-(\d+\.\d+(?:\.\d+)?)-([A-Z0-9]+).*\.ipsw',
                # Simple format: iPhone_17.4.ipsw
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
        """Find IPSW file in internal S3 bucket"""
        await self._ensure_cache_fresh()
        
        # Try exact match first
        cache_keys = [
            f"{device_model}_{os_version}_{build_number}" if build_number else None,
            f"{device_model}_{os_version}",
        ]
        
        for cache_key in cache_keys:
            if cache_key and cache_key in self._bucket_cache:
                return self._bucket_cache[cache_key]
        
        # Try fuzzy matching for internal naming conventions
        for key, file_info in self._bucket_cache.items():
            if (self._device_matches(file_info['device'], device_model) and 
                file_info['version'] == os_version):
                if build_number is None or file_info['build'] == build_number:
                    return file_info
        
        logger.warning(f"IPSW not found in internal S3: {device_model} {os_version} {build_number}")
        return None
    
    def _device_matches(self, s3_device: str, target_device: str) -> bool:
        """Check if device names match (handle internal naming conventions)"""
        # Normalize device names for internal network variations
        s3_norm = s3_device.lower().replace('_', '').replace('-', '').replace(' ', '').replace(',', '')
        target_norm = target_device.lower().replace('_', '').replace('-', '').replace(' ', '').replace(',', '')
        
        # Direct match
        if s3_norm == target_norm:
            return True
        
        # Handle iPhone naming variations
        if 'iphone' in s3_norm and 'iphone' in target_norm:
            s3_nums = re.findall(r'\d+', s3_device)
            target_nums = re.findall(r'\d+', target_device)
            if s3_nums and target_nums:
                return s3_nums == target_nums
        
        # Handle iPad variations
        if 'ipad' in s3_norm and 'ipad' in target_norm:
            return True
        
        return False
    
    async def download_ipsw(self, device_model: str, os_version: str, build_number: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Download IPSW file from internal S3"""
        try:
            # Check if already downloaded locally
            local_pattern = f"*{device_model}*{os_version}*.ipsw"
            existing_files = list(self.downloads_dir.glob(local_pattern))
            
            if existing_files:
                existing_file = existing_files[0]
                logger.info(f"Using existing IPSW: {existing_file}")
                return True, f"Using cached IPSW: {existing_file.name}", str(existing_file)
            
            # Find file in S3
            file_info = await self.find_ipsw(device_model, os_version, build_number)
            if not file_info:
                return False, f"IPSW not found in internal S3: {device_model} {os_version}", None
            
            # Download file
            download_url = file_info['url']
            local_filename = f"{device_model}_{os_version}_{build_number or 'unknown'}_{file_info['key']}"
            local_path = self.downloads_dir / local_filename
            
            logger.info(f"Downloading IPSW from internal S3: {download_url}")
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30.0, read=300.0, write=300.0, pool=300.0),
                verify=False,
                follow_redirects=True
            ) as client:
                
                async with client.stream("GET", download_url) as response:
                    if response.status_code == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Log progress for large files
                                if total_size > 0 and downloaded % (50 * 1024 * 1024) == 0:  # Every 50MB
                                    progress = (downloaded / total_size) * 100
                                    logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total_size} bytes)")
                        
                        logger.info(f"Successfully downloaded IPSW: {local_path}")
                        return True, f"Downloaded from internal S3: {file_info['key']}", str(local_path)
                    else:
                        return False, f"Download failed: HTTP {response.status_code}", None
            
        except Exception as e:
            logger.error(f"Error downloading IPSW from internal S3: {e}")
            return False, f"Download error: {str(e)}", None
    
    async def list_available_ipsw(self, device_filter: Optional[str] = None) -> List[Dict]:
        """List available IPSW files in internal S3"""
        await self._ensure_cache_fresh()
        
        files = []
        for file_info in self._bucket_cache.values():
            if device_filter is None or device_filter.lower() in file_info['device'].lower():
                files.append({
                    'device': file_info['device'],
                    'version': file_info['version'],
                    'build': file_info['build'],
                    'filename': file_info['key'],
                    'size_mb': file_info['size'] // (1024 * 1024) if file_info['size'] > 0 else 0,
                    'url': file_info['url']
                })
        
        return sorted(files, key=lambda x: (x['device'], x['version']))
    
    async def get_bucket_stats(self) -> Dict:
        """Get statistics about the internal S3 bucket"""
        await self._ensure_cache_fresh()
        
        total_files = len(self._bucket_cache)
        total_size = sum(info['size'] for info in self._bucket_cache.values() if info['size'] > 0)
        
        devices = set(info['device'] for info in self._bucket_cache.values())
        versions = set(info['version'] for info in self._bucket_cache.values())
        
        return {
            'total_files': total_files,
            'total_size_gb': total_size / (1024**3),
            'unique_devices': len(devices),
            'unique_versions': len(versions),
            's3_endpoint': self.s3_endpoint,
            'bucket_name': self.bucket_name,
            'web_interface': self.web_index_url,
            'cache_age_minutes': (datetime.now() - self._cache_timestamp).seconds // 60 if self._cache_timestamp else 0
        }
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test connection to internal S3"""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0),
                verify=False,
                follow_redirects=True
            ) as client:
                
                response = await client.get(self.web_index_url)
                if response.status_code == 200:
                    return True, f"Successfully connected to internal S3: {self.s3_endpoint}"
                else:
                    return False, f"Connection failed: HTTP {response.status_code}"
                    
        except Exception as e:
            return False, f"Connection error: {str(e)}" 