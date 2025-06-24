#!/usr/bin/env python3
"""
Symbol Server Manager for Internal Network IPSW Auto-Symbolication
Manages ipswd symbol server, automatic IPSW scanning, and symbolication
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import tempfile

import httpx
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from internal_s3_manager import InternalS3Manager

logger = logging.getLogger(__name__)

class SymbolServerManager:
    def __init__(
        self,
        ipswd_url: str = "http://ipswd-symbol-server:3993",
        database_url: str = "postgresql://symbols_user:symbols_password@postgres:5432/symbols",
        s3_manager: Optional[InternalS3Manager] = None,
        signatures_dir: Optional[Path] = None
    ):
        """
        Initialize Symbol Server Manager
        
        Args:
            ipswd_url: URL to ipswd symbol server
            database_url: PostgreSQL connection string for symbols
            s3_manager: Internal S3 manager for IPSW files
            signatures_dir: Directory containing symbolicator signatures
        """
        self.ipswd_url = ipswd_url.rstrip('/')
        self.database_url = database_url
        self.s3_manager = s3_manager
        self.signatures_dir = Path(signatures_dir) if signatures_dir else Path("/data/signatures")
        
        # HTTP client configuration for internal network
        self.timeout = httpx.Timeout(connect=30.0, read=300.0, write=300.0, pool=300.0)
        
        # Cache for server status
        self._server_status = None
        self._last_status_check = None
        self._status_check_interval = 60  # seconds
        
        # Create signatures directory
        self.signatures_dir.mkdir(parents=True, exist_ok=True)
    
    async def check_server_health(self) -> Tuple[bool, str]:
        """Check if ipswd symbol server is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(f"{self.ipswd_url}/v1/_ping")
                
                if response.status_code == 200:
                    # IPSWD ping returns "OK" as text, not JSON
                    return True, f"Symbol server healthy: {response.text}"
                else:
                    return False, f"Symbol server unhealthy: HTTP {response.status_code}"
                    
        except Exception as e:
            return False, f"Cannot connect to symbol server: {str(e)}"
    
    async def get_server_stats(self) -> Dict:
        """Get symbol server statistics"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                # Try to get version info as a basic stat
                response = await client.get(f"{self.ipswd_url}/v1/version")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get server stats: HTTP {response.status_code}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {}
    
    async def list_scanned_ipsws(self) -> List[Dict]:
        """List all IPSW files that have been scanned into the symbol server"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                # Use the correct endpoint for listing IPSW symbols
                response = await client.get(f"{self.ipswd_url}/v1/syms/ipsw")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to list scanned IPSWs: HTTP {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing scanned IPSWs: {e}")
            return []
    
    async def scan_ipsw_to_server(self, ipsw_path: str) -> Tuple[bool, str, Dict]:
        """
        Scan an IPSW file and add its symbols to the symbol server
        
        Args:
            ipsw_path: Path to IPSW file
            
        Returns:
            Tuple of (success, message, scan_results)
        """
        try:
            logger.info(f"Scanning IPSW to symbol server: {ipsw_path}")
            
            scan_data = {
                "path": ipsw_path,
                "extract_dyld": True,
                "extract_kernelcache": True,
                "include_signatures": True
            }
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30.0, read=1800.0, write=1800.0, pool=1800.0),  # 30 min timeout
                verify=False
            ) as client:
                response = await client.post(
                    f"{self.ipswd_url}/v1/syms/scan",
                    json=scan_data
                )
                
                if response.status_code == 200:
                    scan_results = response.json()
                    logger.info(f"Successfully scanned IPSW: {scan_results.get('message', 'Success')}")
                    return True, "IPSW scanned successfully", scan_results
                else:
                    error_msg = f"Failed to scan IPSW: HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', 'Unknown error')}"
                    except:
                        pass
                    return False, error_msg, {}
                    
        except Exception as e:
            error_msg = f"Error scanning IPSW: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    async def symbolicate_via_server(
        self, 
        crash_content: str, 
        device_model: Optional[str] = None,
        os_version: Optional[str] = None,
        build_number: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Symbolicate crash log using the symbol server
        
        Args:
            crash_content: Raw crash log content
            device_model: Device model (optional, will be detected)
            os_version: OS version (optional, will be detected)
            build_number: Build number (optional, will be detected)
            
        Returns:
            Tuple of (success, message, symbolicated_content)
        """
        try:
            logger.info("Symbolicating crash via symbol server")
            logger.info(f"Sending request to: {self.ipswd_url}/v1/symbolicate")
            logger.info(f"Request data: device_model={device_model}, os_version={os_version}")
            
            # Create request data matching Symbol Server API
            symbolicate_data = {
                "crash_content": crash_content,
                "device_model": device_model or "unknown",
                "ios_version": os_version or "unknown"
            }
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30.0, read=300.0, write=300.0, pool=300.0),
                verify=False
            ) as client:
                response = await client.post(
                    f"{self.ipswd_url}/v1/symbolicate",
                    json=symbolicate_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Symbol Server response: {result}")
                    
                    if result.get("success", False):
                        symbolicated_content = result.get("symbolicated_crash", "")
                        symbols = result.get("symbols", {})
                        
                        # If we have symbols, the symbolication was successful
                        if symbols:
                            logger.info(f"Successfully symbolicated crash via server: {len(symbols)} symbols found")
                            # Generate a readable symbolicated output from symbols
                            if symbolicated_content:
                                return True, f"Symbolication successful - {len(symbols)} symbols found", symbolicated_content
                            else:
                                # Create a summary of found symbols
                                symbol_summary = "\n".join([f"  {addr}: {symbol}" for addr, symbol in list(symbols.items())[:10]])
                                if len(symbols) > 10:
                                    symbol_summary += f"\n  ... and {len(symbols) - 10} more symbols"
                                return True, f"Symbolication successful - {len(symbols)} symbols found", symbol_summary
                        else:
                            return False, "No symbols found in crash log", None
                    else:
                        logger.info(f"Symbol Server returned success=false: {result.get('message', 'Unknown error')}")
                        return False, result.get("message", "Unknown error"), None
                        
                elif response.status_code == 404:
                    return False, "Symbols not found in server - IPSW may need to be scanned first", None
                    
                else:
                    error_msg = f"Symbolication failed: HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', 'Unknown error')}"
                    except:
                        pass
                    return False, error_msg, None
                    
        except Exception as e:
            error_msg = f"Error during symbolication: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False, error_msg, None
    
    async def auto_scan_s3_ipsws(self) -> Dict[str, any]:
        """
        Automatically scan all IPSW files from internal S3 to symbol server
        
        Returns:
            Dictionary with scan results
        """
        if not self.s3_manager:
            return {"error": "S3 manager not configured"}
        
        try:
            logger.info("Starting automatic S3 IPSW scanning...")
            
            # Get list of available IPSWs from S3
            available_ipsws = await self.s3_manager.list_available_ipsw()
            
            # Get list of already scanned IPSWs
            scanned_ipsws = await self.list_scanned_ipsws()
            scanned_files = {item.get('filename', '') for item in scanned_ipsws}
            
            scan_results = {
                "total_available": len(available_ipsws),
                "already_scanned": len(scanned_files),
                "newly_scanned": 0,
                "failed_scans": 0,
                "scan_details": []
            }
            
            # Scan new IPSWs
            for ipsw_info in available_ipsws:
                filename = ipsw_info.get('filename', '')
                
                if filename in scanned_files:
                    logger.info(f"IPSW already scanned: {filename}")
                    continue
                
                # Download IPSW if needed
                success, message, ipsw_path = await self.s3_manager.download_ipsw(
                    device_model=ipsw_info['device'],
                    os_version=ipsw_info['version'],
                    build_number=ipsw_info.get('build')
                )
                
                if not success:
                    scan_results["failed_scans"] += 1
                    scan_results["scan_details"].append({
                        "filename": filename,
                        "status": "download_failed",
                        "error": message
                    })
                    continue
                
                # Scan to symbol server
                scan_success, scan_message, scan_data = await self.scan_ipsw_to_server(ipsw_path)
                
                if scan_success:
                    scan_results["newly_scanned"] += 1
                    scan_results["scan_details"].append({
                        "filename": filename,
                        "status": "scanned_successfully",
                        "symbols_added": scan_data.get("symbols_count", 0)
                    })
                    logger.info(f"Successfully scanned: {filename}")
                else:
                    scan_results["failed_scans"] += 1
                    scan_results["scan_details"].append({
                        "filename": filename,
                        "status": "scan_failed",
                        "error": scan_message
                    })
                    logger.error(f"Failed to scan {filename}: {scan_message}")
            
            logger.info(f"Auto-scan completed: {scan_results['newly_scanned']} new, {scan_results['failed_scans']} failed")
            return scan_results
            
        except Exception as e:
            error_msg = f"Error during auto-scan: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def download_signatures(self, ios_version: str = "latest") -> bool:
        # AIRGAP: Only use local symbolicator signatures. Never clone or update from internet.
            signatures_repo_dir = self.signatures_dir / "symbolicator"
            if not signatures_repo_dir.exists():
            logger.error("[AIRGAP] Symbolicator signatures not found locally. Airgap mode requires local copy.")
            return False
        logger.info("[AIRGAP] Using local symbolicator signatures only.")
        return True
    
    async def get_signature_path(self, ios_version: str) -> Optional[str]:
        """Get path to signatures for specific iOS version"""
        try:
            # Download signatures if needed
            await self.download_signatures()
            
            signatures_repo = self.signatures_dir / "symbolicator" / "kernel"
            
            if not signatures_repo.exists():
                return None
            
            # Find best matching version
            version_dirs = [d for d in signatures_repo.iterdir() if d.is_dir()]
            
            # Try exact match first
            ios_major = ios_version.split('.')[0]
            for version_dir in version_dirs:
                if version_dir.name == ios_major:
                    return str(version_dir)
            
            # Use latest available
            if version_dirs:
                latest_version = max(version_dirs, key=lambda x: x.name)
                logger.info(f"Using signatures for iOS {latest_version.name} (requested: {ios_version})")
                return str(latest_version)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting signature path: {e}")
            return None
    
    async def ensure_ipsw_scanned(
        self, 
        device_model: str, 
        os_version: str, 
        build_number: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Ensure specific IPSW is scanned into symbol server
        Downloads from S3 and scans if needed
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.s3_manager:
                return False, "S3 manager not configured"
            
            # Download IPSW
            success, message, ipsw_path = await self.s3_manager.download_ipsw(
                device_model=device_model,
                os_version=os_version,
                build_number=build_number
            )
            
            if not success:
                return False, f"Failed to download IPSW: {message}"
            
            # Scan to symbol server
            scan_success, scan_message, scan_data = await self.scan_ipsw_to_server(ipsw_path)
            
            if scan_success:
                return True, f"IPSW scanned successfully: {scan_data.get('symbols_count', 0)} symbols added"
            else:
                return False, f"Failed to scan IPSW: {scan_message}"
                
        except Exception as e:
            return False, f"Error ensuring IPSW scanned: {str(e)}"
    
    async def cleanup_old_downloads(self, keep_days: int = 7) -> int:
        """
        Clean up old downloaded IPSW files to save space
        Keep recently downloaded files
        
        Args:
            keep_days: Number of days to keep files
            
        Returns:
            Number of files cleaned up
        """
        try:
            if not self.s3_manager:
                return 0
            
            downloads_dir = self.s3_manager.downloads_dir
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            cleaned_count = 0
            for ipsw_file in downloads_dir.glob("*.ipsw"):
                if ipsw_file.stat().st_mtime < cutoff_time:
                    ipsw_file.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned up old IPSW: {ipsw_file.name}")
            
            logger.info(f"Cleaned up {cleaned_count} old IPSW files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0 