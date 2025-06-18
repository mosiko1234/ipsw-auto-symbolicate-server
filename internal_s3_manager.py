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
import hashlib
import hmac
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, quote, unquote, urlparse
from bs4 import BeautifulSoup

import httpx
import aiofiles
from minio import Minio
from minio.error import S3Error

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
        
        # MinIO credentials from environment
        self.access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin')
        
        # Cache for S3 bucket listing
        self._bucket_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 1800  # 30 minutes for internal network
        
        # Internal network optimizations
        self.timeout = httpx.Timeout(connect=10.0, read=300.0, write=300.0, pool=300.0)
        
    @property
    def bucket_url(self) -> str:
        """Get the base URL for the S3 bucket"""
        return f"{self.s3_endpoint}/{self.bucket_name}"
    
    @property
    def web_index_url(self) -> str:
        """Get the web interface URL for the S3 bucket"""
        return f"{self.bucket_url}/"
    
    def _create_s3_auth_headers(self, method: str, path: str, query_params: str = "") -> Dict[str, str]:
        """Create AWS S3 compatible authentication headers for MinIO"""
        try:
            from datetime import datetime, timezone
            import hashlib
            import hmac
            
            # Current timestamp
            now = datetime.now(timezone.utc)
            amz_date = now.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = now.strftime('%Y%m%d')
            
            # Parse endpoint
            parsed = urlparse(self.s3_endpoint)
            host = parsed.netloc
            
            # Canonical request components
            # For MinIO, the canonical URI should include the bucket and object path
            canonical_uri = f"/{self.bucket_name}{path}"
            canonical_querystring = query_params
            canonical_headers = f"host:{host}\nx-amz-date:{amz_date}\n"
            signed_headers = "host;x-amz-date"
            
            # Create payload hash (empty for GET requests)
            payload_hash = hashlib.sha256(b'').hexdigest()
            
            # Create canonical request
            canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
            
            # Debug logging
            logger.debug(f"Canonical request: {canonical_request}")
            
            # Create string to sign
            algorithm = 'AWS4-HMAC-SHA256'
            credential_scope = f"{date_stamp}/us-east-1/s3/aws4_request"
            string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
            
            # Debug logging
            logger.debug(f"String to sign: {string_to_sign}")
            
            # Calculate signature
            def sign(key, msg):
                return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
            
            def get_signature_key(key, date_stamp, region_name, service_name):
                k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
                k_region = sign(k_date, region_name)
                k_service = sign(k_region, service_name)
                k_signing = sign(k_service, 'aws4_request')
                return k_signing
            
            signing_key = get_signature_key(self.secret_key, date_stamp, 'us-east-1', 's3')
            signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
            
            # Create authorization header
            authorization_header = f"{algorithm} Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
            
            logger.debug(f"Authorization header: {authorization_header}")
            
            return {
                'Authorization': authorization_header,
                'X-Amz-Date': amz_date,
                'Host': host
            }
            
        except Exception as e:
            logger.error(f"Error creating S3 auth headers: {e}")
            # Fallback to basic auth
            return {}
    
    async def refresh_bucket_cache(self) -> None:
        """Refresh the bucket cache by listing all IPSW files from MinIO using HTTP API"""
        try:
            logger.info(f"=== STARTING refresh_bucket_cache ===")
            logger.info(f"Refreshing internal S3 bucket cache from {self.web_index_url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=False,
                follow_redirects=True
            ) as client:
                
                # Try S3 API with authentication
                success = await self._try_s3_api_listing(client)
                
                # If S3 API fails, try MinIO web interface
                if not success:
                    success = await self._try_minio_web_interface(client)
                
                # If both fail, try basic auth
                if not success:
                    await self._try_basic_auth_listing(client)
            
            self._cache_timestamp = datetime.now()
            logger.info(f"Cached {len(self._bucket_cache)} IPSW files from internal S3")
                    
        except Exception as e:
            logger.error(f"Error refreshing internal bucket cache: {e}")
    
    async def _try_s3_api_listing(self, client: httpx.AsyncClient) -> bool:
        """Try to get bucket listing via S3 API with proper authentication"""
        try:
            logger.info("Trying S3 API listing with authentication...")
            
            # Create S3 API request with authentication
            headers = self._create_s3_auth_headers('GET', '/', 'list-type=2')
            
            if not headers:
                # Fallback to basic auth
                logger.info("Using basic auth fallback")
                response = await client.get(
                    f"{self.bucket_url}/?list-type=2",
                    auth=(self.access_key, self.secret_key)
                )
            else:
                response = await client.get(
                    f"{self.bucket_url}/?list-type=2",
                    headers=headers
                )
            
            logger.info(f"S3 API response: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                logger.info(f"S3 API content type: {content_type}")
                
                if 'xml' in content_type:
                    await self._parse_s3_xml_listing(response.text)
                    return True
                else:
                    logger.info("S3 API returned non-XML content, trying to parse as HTML")
                    await self._parse_html_listing(response.text)
                    return len(self._bucket_cache) > 0
            else:
                logger.warning(f"S3 API failed with status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"S3 API listing failed: {e}")
        
        return False
    
    async def _try_minio_web_interface(self, client: httpx.AsyncClient) -> bool:
        """Try MinIO web interface with credentials"""
        try:
            logger.info("Trying MinIO web interface...")
            
            # Try MinIO web interface URL patterns
            web_urls = [
                f"{self.s3_endpoint}/minio/{self.bucket_name}/",
                f"{self.s3_endpoint}/{self.bucket_name}/",
                f"{self.s3_endpoint}/browser/{self.bucket_name}/",
            ]
            
            for web_url in web_urls:
                try:
                    logger.info(f"Trying web interface URL: {web_url}")
                    
                    # Try with basic auth
                    response = await client.get(
                        web_url,
                        auth=(self.access_key, self.secret_key)
                    )
                    
                    logger.info(f"Web interface response: {response.status_code}")
                    
                    if response.status_code == 200:
                        await self._parse_html_listing(response.text)
                        if len(self._bucket_cache) > 0:
                            return True
                            
                except Exception as e:
                    logger.debug(f"Web interface URL {web_url} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"MinIO web interface failed: {e}")
        
        return False
    
    async def _try_basic_auth_listing(self, client: httpx.AsyncClient) -> None:
        """Try basic bucket listing without authentication"""
        try:
            logger.info("Trying basic bucket listing...")
            
            response = await client.get(self.web_index_url)
            logger.info(f"Basic listing response: {response.status_code}")
            
            if response.status_code == 200:
                await self._parse_html_listing(response.text)
                
        except Exception as e:
            logger.error(f"Basic listing failed: {e}")
    
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
        logger.info(f"Processing IPSW file: {filename}")
        file_info = self._parse_ipsw_filename(filename)
        
        if file_info:
            cache_key = f"{file_info['device']}_{file_info['version']}"
            if file_info['build']:
                cache_key += f"_{file_info['build']}"
            
            logger.info(f"Parsed file info: {file_info}, cache_key: {cache_key}")
            
            self._bucket_cache[cache_key] = {
                'key': filename,
                'size': size,
                'modified': modified,
                'device': file_info['device'],
                'version': file_info['version'],
                'build': file_info['build'],
                'url': f"{self.bucket_url}/{quote(filename)}"
            }
            logger.info(f"Added to cache: {cache_key}")
        else:
            logger.warning(f"Failed to parse IPSW filename: {filename}")
    
    def _parse_ipsw_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Parse IPSW filename to extract device, version, and build info"""
        try:
            # Extended patterns for internal S3 naming conventions
            patterns = [
                # iPhone15,2_18.5_22F76_Restore-2.ipsw (with numbered suffix)
                r'([^_/]+)_(\d+\.\d+(?:\.\d+)?)_([A-Z0-9]+)_Restore-\d+\.ipsw',
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
        """Download IPSW file from internal S3 using HTTP API"""
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
            
            # Download file using HTTP API
            local_filename = f"{device_model}_{os_version}_{build_number or 'unknown'}_{file_info['key']}"
            local_path = self.downloads_dir / local_filename
            
            logger.info(f"Downloading IPSW via HTTP API: {file_info['key']}")
            
            success = await self._download_file_http(file_info['key'], local_path)
            
            if success:
                logger.info(f"Successfully downloaded IPSW: {local_path}")
                return True, f"Downloaded from MinIO: {file_info['key']}", str(local_path)
            else:
                return False, "HTTP download failed", None
            
        except Exception as e:
            logger.error(f"Error downloading IPSW from internal S3: {e}")
            return False, f"Download error: {str(e)}", None
    
    async def _download_file_http(self, s3_key: str, local_path: Path) -> bool:
        """Download file from MinIO using HTTP API with authentication"""
        try:
            # Try minio client first (more reliable)
            logger.info("Attempting download with minio client")
            success = await asyncio.get_event_loop().run_in_executor(
                None, lambda: asyncio.run(self._download_file_minio_sync(s3_key, local_path))
            )
            
            if success:
                return True
            
            # Fallback to HTTP API
            logger.info("Minio client failed, trying HTTP API")
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30.0, read=1800.0, write=1800.0, pool=1800.0),  # 30 min timeout for large files
                verify=False,
                follow_redirects=True
            ) as client:
                
                file_url = f"{self.bucket_url}/{quote(s3_key)}"
                logger.info(f"Starting download from URL: {file_url}")
                
                # Try S3 authentication first (required by MinIO)
                headers = self._create_s3_auth_headers('GET', f"/{s3_key}")
                
                if headers:
                    logger.info("Using S3 authentication for download")
                    async with client.stream('GET', file_url, headers=headers) as response:
                        return await self._handle_download_response(response, local_path, s3_key)
                else:
                    logger.info("Using basic auth for download")
                    async with client.stream('GET', file_url, auth=(self.access_key, self.secret_key)) as response:
                        return await self._handle_download_response(response, local_path, s3_key)
                    
        except Exception as e:
            logger.error(f"HTTP download error: {e}")
            return False
    
    def _download_file_minio_sync(self, s3_key: str, local_path: Path) -> bool:
        """Synchronous version of minio download for use with executor"""
        try:
            # Parse endpoint to get host and port
            parsed = urlparse(self.s3_endpoint)
            endpoint = parsed.netloc
            secure = parsed.scheme == 'https'
            
            # Create minio client
            client = Minio(
                endpoint=endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=secure
            )
            
            logger.info(f"Downloading with minio client: {s3_key}")
            
            # Get object info for progress tracking
            try:
                stat = client.stat_object(self.bucket_name, s3_key)
                total_size = stat.size
                logger.info(f"File size: {total_size / (1024**3):.2f} GB")
            except S3Error as e:
                logger.warning(f"Could not get file stats: {e}")
                total_size = 0
            
            # Use fget_object for direct file download
            temp_path = local_path.with_suffix('.tmp')
            
            # Download without progress callback to avoid threading issues
            client.fget_object(
                bucket_name=self.bucket_name,
                object_name=s3_key,
                file_path=str(temp_path)
            )
            
            # Move to final location
            temp_path.rename(local_path)
            
            # Verify download
            if local_path.exists() and local_path.stat().st_size > 0:
                final_size = local_path.stat().st_size
                logger.info(f"File downloaded successfully: {final_size / (1024**3):.2f} GB")
                return True
            else:
                logger.error("Downloaded file is empty or doesn't exist")
                return False
                
        except S3Error as e:
            logger.error(f"MinIO S3 error: {e}")
            return False
        except Exception as e:
            logger.error(f"MinIO download error: {e}")
            return False
    
    async def _handle_download_response(self, response, local_path: Path, s3_key: str) -> bool:
        """Handle the download response and save to file"""
        try:
            logger.info(f"Download response status: {response.status_code}")
            
            if response.status_code == 200:
                # Get file size from headers
                content_length = response.headers.get('content-length')
                if content_length:
                    total_size = int(content_length)
                    logger.info(f"File size: {total_size / (1024**3):.2f} GB")
                else:
                    total_size = 0
                    logger.info("File size unknown")
                
                # Stream download to file with progress tracking
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks for large files
                
                async with aiofiles.open(local_path, 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 100MB
                        if downloaded % (100 * 1024 * 1024) == 0 or (total_size > 0 and downloaded >= total_size):
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.info(f"Download progress: {downloaded / (1024**3):.2f} GB / {total_size / (1024**3):.2f} GB ({progress:.1f}%)")
                            else:
                                logger.info(f"Downloaded: {downloaded / (1024**3):.2f} GB")
                
                # Verify file was downloaded
                if local_path.exists() and local_path.stat().st_size > 0:
                    final_size = local_path.stat().st_size
                    logger.info(f"File downloaded successfully: {final_size / (1024**3):.2f} GB")
                    
                    # Verify size matches if we had content-length
                    if total_size > 0 and abs(final_size - total_size) > 1024:  # Allow 1KB difference
                        logger.warning(f"Size mismatch: expected {total_size}, got {final_size}")
                        return False
                    
                    return True
                else:
                    logger.error("Downloaded file is empty or doesn't exist")
                    return False
            else:
                # Read error response for debugging
                try:
                    error_text = ""
                    async for chunk in response.aiter_bytes():
                        error_text += chunk.decode('utf-8', errors='ignore')
                        if len(error_text) > 500:  # Limit error text length
                            break
                    logger.error(f"Download failed: HTTP {response.status_code} - {error_text[:200]}")
                except:
                    logger.error(f"Download failed: HTTP {response.status_code} - Unable to read error response")
                return False
                
        except Exception as e:
            logger.error(f"Error handling download response: {e}")
            return False
    
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
                follow_redirects=True,
                auth=(self.access_key, self.secret_key)
            ) as client:
                
                response = await client.get(self.web_index_url)
                if response.status_code == 200:
                    return True, f"Successfully connected to internal S3: {self.s3_endpoint}"
                else:
                    return False, f"Connection failed: HTTP {response.status_code}"
                    
        except Exception as e:
            return False, f"Connection error: {str(e)}" 