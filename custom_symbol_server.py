#!/usr/bin/env python3
"""
Enhanced Custom Symbol Server for IPSW Auto-Symbolication
Replaces broken IPSWD with full functionality including:
- Database integration for symbol storage
- Improved address parsing for crash logs
- Real symbolication using IPSW binary
"""

import os
import re
import json
import uuid
import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import psycopg2
import asyncpg
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('custom_symbol_server')

# Configuration
SIGNATURES_DIR = os.getenv('SIGNATURES_DIR', '/app/data/signatures')
DOWNLOADS_DIR = os.getenv('DOWNLOADS_DIR', '/app/data/downloads')
CACHE_DIR = os.getenv('CACHE_DIR', '/app/data/cache')
SYMBOLS_DIR = os.getenv('SYMBOLS_DIR', '/app/data/symbols')
IPSW_BINARY = os.getenv('IPSW_BINARY', 'ipsw')

# Database configuration
DATABASE_URL = "postgresql://symbols_user:symbols_pass@symbols-postgres:5432/symbols"

# Global stats
stats = {
    'total_ipsws_scanned': 0,
    'total_symbols_extracted': 0,
    'cache_size_mb': 0.0,
    'uptime_seconds': 0,
    'start_time': datetime.now()
}

# Pydantic models
class IPSWScanRequest(BaseModel):
    ipsw_path: str
    extract_kernelcache: bool = True
    extract_dyld: bool = False

class SymbolicateRequest(BaseModel):
    crash_content: str
    ios_version: str
    device_model: str
    build_number: Optional[str] = None

class SymbolicateResponse(BaseModel):
    success: bool
    message: str
    symbols: Optional[Dict[str, str]] = None
    symbolicated_crash: Optional[str] = None

# FastAPI app
app = FastAPI(title="Enhanced Custom Symbol Server", version="2.0.0")

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.pool = None
    
    async def init_pool(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_pool(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def save_symbols_metadata(self, device_identifier: str, ios_version: str, 
                                  build_version: str, kernel_path: str, symbols_path: str):
        """Save symbols metadata to database"""
        try:
            async with self.pool.acquire() as conn:
                # Insert or update symbols metadata
                await conn.execute("""
                    INSERT INTO symbols (device_identifier, ios_version, build_version, kernel_path, symbols_path)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (device_identifier, ios_version, build_version)
                    DO UPDATE SET 
                        kernel_path = EXCLUDED.kernel_path,
                        symbols_path = EXCLUDED.symbols_path,
                        updated_at = CURRENT_TIMESTAMP
                """, device_identifier, ios_version, build_version, kernel_path, symbols_path)
                
                logger.info(f"Saved symbols metadata for {device_identifier} {ios_version}")
        except Exception as e:
            logger.error(f"Failed to save symbols metadata: {e}")
    
    async def cache_symbols(self, cache_key: str, symbol_data: Dict[str, str], expires_hours: int = 24):
        """Cache symbols data in database"""
        try:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO symbol_cache (cache_key, symbol_data, expires_at)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (cache_key)
                    DO UPDATE SET 
                        symbol_data = EXCLUDED.symbol_data,
                        expires_at = EXCLUDED.expires_at,
                        created_at = CURRENT_TIMESTAMP
                """, cache_key, json.dumps(symbol_data), expires_at)
                
                logger.info(f"Cached symbols with key: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to cache symbols: {e}")
    
    async def get_cached_symbols(self, cache_key: str) -> Optional[Dict[str, str]]:
        """Get cached symbols from database"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT symbol_data FROM symbol_cache 
                    WHERE cache_key = $1 AND expires_at > CURRENT_TIMESTAMP
                """, cache_key)
                
                if row:
                    return json.loads(row['symbol_data'])
                return None
        except Exception as e:
            logger.error(f"Failed to get cached symbols: {e}")
            return None

# Global database manager
db_manager = DatabaseManager()

class AddressParser:
    """Enhanced address parser for crash logs"""
    
    # Multiple address patterns for different crash log formats
    ADDRESS_PATTERNS = [
        # Standard hex addresses
        r'0x[0-9a-fA-F]{8,16}',
        # Decimal addresses (large numbers)
        r'\b\d{15,20}\b',
        # Kernel addresses in brackets
        r'\[0x[0-9a-fA-F]{8,16}\]',
        # Stack trace addresses
        r'^\s*\d+\s+\w+\s+(0x[0-9a-fA-F]+)',
        # JSON kernel frames
        r'"kernelFrames"\s*:\s*\[\s*\[\s*\d+,\s*(\d+)\s*\]',
        # Thread continuation addresses
        r'"continuation"\s*:\s*\[\s*\d+,\s*(\d+)\s*\]',
        # Wait event addresses
        r'"waitEvent"\s*:\s*\[\s*\d+,\s*(\d+)\s*\]'
    ]
    
    @classmethod
    def extract_addresses(cls, crash_content: str) -> List[int]:
        """Extract all addresses from crash log content"""
        addresses = set()
        
        # Debug: Log the crash content to see what we're working with
        logger.info(f"Processing crash content (size: {len(crash_content)} chars, first 500 chars): {crash_content[:500]}")
        
        try:
            # Extract kernel addresses from kernelFrames directly
            # Look for kernelFrames patterns in the text
            import re
            
            # For large crash files, we need to search through the entire content
            # Use regex to find all kernelFrames entries directly
            # Pattern to match: "kernelFrames":[[1,628560],[1,622884],...] 
            # We need to handle nested arrays properly
            kernel_frame_pattern = r'"kernelFrames"\s*:\s*\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]'
            matches = re.findall(kernel_frame_pattern, crash_content, re.DOTALL)
            
            logger.info(f"Found {len(matches)} kernelFrames patterns in crash log")
            
            # Also try a simpler approach: find all [digit,digit] patterns in the content
            # directly after kernelFrames mentions
            simple_pattern = r'"kernelFrames"[^{]*?\[\s*\d+\s*,\s*(\d+)\s*\]'
            simple_matches = re.findall(simple_pattern, crash_content, re.DOTALL)
            
            logger.info(f"Found {len(simple_matches)} simple kernel addresses")
            
            # Process simple matches first
            for addr_str in simple_matches:
                try:
                    kernel_addr = int(addr_str)
                    if kernel_addr > 0x1000:  # Minimum reasonable relative address
                        addresses.add(kernel_addr)
                        if len(addresses) <= 10:  # Log first 10 addresses
                            logger.info(f"Added kernel address (simple): 0x{kernel_addr:x}")
                except ValueError:
                    continue
            
            # Process complex matches
            for i, match in enumerate(matches):
                if i < 3:  # Log first few matches for debugging
                    logger.info(f"KernelFrames match {i+1}: {match[:100]}...")
                
                # Look for arrays like [1,628560] - the second number is the kernel address
                frame_pattern = r'\[\s*\d+\s*,\s*(\d+)\s*\]'
                frame_matches = re.findall(frame_pattern, match)
                
                logger.info(f"Found {len(frame_matches)} frame addresses in match {i+1}")
                
                for addr_str in frame_matches:
                    try:
                        kernel_addr = int(addr_str)
                        # These are relative kernel addresses from crash logs
                        # Use them as-is for symbolication
                        if kernel_addr > 0x1000:  # Minimum reasonable relative address
                            addresses.add(kernel_addr)
                            if len(addresses) <= 10:  # Log first 10 addresses
                                logger.info(f"Added kernel address: 0x{kernel_addr:x}")
                    except ValueError:
                        logger.debug(f"Failed to parse address: {addr_str}")
                        continue
            
            logger.info(f"Extracted {len(addresses)} kernel addresses from kernelFrames")
            
            # If we found addresses from kernelFrames, return them
            if addresses:
                return list(addresses)
            
        except Exception as e:
            logger.info(f"kernelFrames parsing failed, using regex fallback: {e}")
            # Fallback to regex patterns for text format
            for pattern in cls.ADDRESS_PATTERNS:
                matches = re.findall(pattern, crash_content, re.MULTILINE)
                for match in matches:
                    try:
                        # Handle tuple matches (from groups)
                        if isinstance(match, tuple):
                            addr_str = match[0] if match[0] else match[1] if len(match) > 1 else None
                        else:
                            addr_str = match
                        
                        if addr_str:
                            # Convert to integer
                            if addr_str.startswith('0x'):
                                addr = int(addr_str, 16)
                            else:
                                addr = int(addr_str)
                            
                            # Filter reasonable kernel addresses
                            if addr > 0x1000:  # Minimum reasonable address
                                addresses.add(addr)
                                
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse address {match}: {e}")
                        continue
        
        logger.info(f"Extracted {len(addresses)} unique addresses from crash log")
        return list(addresses)

class SymbolManager:
    """Manages symbol extraction and symbolication"""
    
    def __init__(self):
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        for dir_path in [DOWNLOADS_DIR, CACHE_DIR, SYMBOLS_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def run_command(self, cmd: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Run shell command and return success status and output"""
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=cwd,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Command completed successfully")
                return True, result.stdout
            else:
                logger.error(f"Command failed with code {result.returncode}: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False, str(e)
    
    def extract_ipsw_info(self, ipsw_path: str) -> Optional[Dict[str, str]]:
        """Extract basic info from IPSW"""
        success, output = self.run_command([IPSW_BINARY, 'info', ipsw_path])
        if not success:
            return None
        
        info = {}
        for line in output.split('\n'):
            if 'Version' in line and '=' in line:
                info['ios_version'] = line.split('=')[1].strip()
            elif 'BuildVersion' in line and '=' in line:
                info['build_version'] = line.split('=')[1].strip()
        
        return info
    
    def extract_kernelcache(self, ipsw_path: str) -> Optional[str]:
        """Extract kernelcache from IPSW"""
        ipsw_name = Path(ipsw_path).stem
        output_dir = Path(CACHE_DIR) / ipsw_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success, output = self.run_command([
            IPSW_BINARY, 'extract', '--kernel', '--output', str(output_dir), ipsw_path
        ])
        
        if not success:
            logger.error(f"Failed to extract kernelcache: {output}")
            return None
        
        logger.info(f"Extracted kernelcache: {output}")
        
        # Find the extracted kernelcache (binary file, not symbols)
        for kernel_file in output_dir.rglob('kernelcache.*'):
            if (kernel_file.is_file() and 
                'kernelcache.release' in kernel_file.name and 
                not kernel_file.name.endswith('.symbols.json')):
                logger.info(f"Found kernelcache: {kernel_file}")
                return str(kernel_file)
        
        return None
    
    def symbolicate_kernelcache(self, kernelcache_path: str) -> Optional[str]:
        """Symbolicate kernelcache using IPSW binary"""
        symbols_path = f"{kernelcache_path}.symbols.json"
        
        # Check if symbols file already exists and is valid
        if Path(symbols_path).exists():
            try:
                with open(symbols_path, 'r') as f:
                    symbols_data = json.load(f)
                if symbols_data and isinstance(symbols_data, dict):
                    logger.info(f"Using existing symbols file: {symbols_path} ({len(symbols_data)} symbols)")
                    return symbols_path
            except Exception as e:
                logger.warning(f"Existing symbols file is invalid, regenerating: {e}")
        
        # Run the symbolicate command - this generates the symbols file
        # Use both our signatures and blacktop signatures
        signatures_paths = [
            SIGNATURES_DIR,
            f"{SIGNATURES_DIR}/symbolicator/kernel"
        ]
        
        success, output = self.run_command([
            IPSW_BINARY, 'kernel', 'symbolicate',
            '--signatures', f"{SIGNATURES_DIR}/symbolicator/kernel",
            '--json',
            kernelcache_path
        ])
        
        # Log the output for debugging
        logger.info(f"Symbolication command output: {output}")
        
        if success and Path(symbols_path).exists():
            # Verify the symbols file was created and has content
            try:
                with open(symbols_path, 'r') as f:
                    symbols_data = json.load(f)
                
                if symbols_data and isinstance(symbols_data, dict):
                    symbol_count = len(symbols_data)
                    logger.info(f"Successfully generated symbols file: {symbols_path} ({symbol_count} symbols)")
                    return symbols_path
                else:
                    logger.error(f"Generated symbols file is empty or invalid format")
                    return None
                    
            except Exception as e:
                logger.error(f"Failed to validate generated symbols file: {e}")
                return None
        else:
            logger.error(f"Symbolication failed or symbols file not created: {output}")
            return None
    
    def load_symbols(self, symbols_path: str) -> Dict[str, str]:
        """Load symbols from JSON file"""
        try:
            with open(symbols_path, 'r') as f:
                symbols_data = json.load(f)
            
            # Convert to address -> symbol mapping
            if isinstance(symbols_data, dict):
                # Already in correct format
                return symbols_data
            elif isinstance(symbols_data, list):
                # Convert list format to dict
                return {item.get('address', ''): item.get('symbol', '') for item in symbols_data if 'address' in item}
            else:
                logger.error(f"Unknown symbols format in {symbols_path}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to load symbols from {symbols_path}: {e}")
            return {}
    
    def symbolicate_addresses(self, addresses: List[int], symbols: Dict[str, str]) -> Dict[str, str]:
        """Symbolicate list of addresses using symbols dictionary"""
        symbolicated = {}
        
        # Convert symbols dict to have integer keys for faster lookup
        symbols_by_int = {}
        for addr_str, symbol in symbols.items():
            try:
                if addr_str.startswith('0x'):
                    addr_int = int(addr_str, 16)
                else:
                    addr_int = int(addr_str)
                symbols_by_int[addr_int] = symbol
            except ValueError:
                continue
        
        logger.info(f"Converted {len(symbols_by_int)} symbols for lookup")
        if len(symbols_by_int) > 0:
            sample_addrs = list(symbols_by_int.keys())[:3]
            logger.info(f"Sample symbol addresses: {[hex(addr) for addr in sample_addrs]}")
            sample_crash_addrs = addresses[:3] if len(addresses) > 0 else []
            logger.info(f"Sample crash addresses: {[hex(addr) for addr in sample_crash_addrs]}")
        
        # Sort symbol addresses for efficient nearest lookup
        sorted_symbol_addrs = sorted(symbols_by_int.keys())
        
        for addr in addresses:
            hex_addr = f"0x{addr:x}"
            symbol = None
            
            # Try exact match first
            if addr in symbols_by_int:
                symbol = symbols_by_int[addr]
            else:
                # Find nearest symbol using binary search
                import bisect
                idx = bisect.bisect_right(sorted_symbol_addrs, addr) - 1
                
                if idx >= 0:
                    nearest_addr = sorted_symbol_addrs[idx]
                    offset = addr - nearest_addr
                    
                    # Only use if offset is reasonable (within 64KB)
                    if offset < 0x10000:
                        symbol = f"{symbols_by_int[nearest_addr]}+0x{offset:x}"
            
            if symbol:
                symbolicated[hex_addr] = symbol
            else:
                symbolicated[hex_addr] = f"<unknown>+0x{addr:x}"
        
        return symbolicated

# Global symbol manager
symbol_manager = SymbolManager()

# S3 Manager for auto-downloading IPSWs
try:
    from internal_s3_manager import InternalS3Manager
    # Initialize S3 manager with environment variables
    S3_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
    S3_BUCKET = os.getenv('S3_BUCKET', 'ipsw')
    S3_USE_SSL = os.getenv('S3_USE_SSL', 'false').lower() == 'true'
    
    s3_manager = InternalS3Manager(
        s3_endpoint=S3_ENDPOINT,
        bucket_name=S3_BUCKET,
        downloads_dir=Path(DOWNLOADS_DIR),
        use_ssl=S3_USE_SSL
    )
    logger.info(f"S3 manager initialized successfully: {S3_ENDPOINT}/{S3_BUCKET}")
except ImportError as e:
    s3_manager = None
    logger.warning(f"S3 manager not available: {e}")
except Exception as e:
    s3_manager = None
    logger.error(f"Failed to initialize S3 manager: {e}")

async def auto_ensure_symbols_available(device_model: str, ios_version: str, build_number: Optional[str] = None) -> Tuple[bool, str]:
    """
    Automatically ensure symbols are available for device/version.
    If not found, attempts to download and scan IPSW from S3.
    
    Args:
        device_model: Device model (e.g., iPhone15,2)
        ios_version: iOS version (e.g., 18.5)
        build_number: Build number (optional, e.g., 22F76)
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # First check if symbols already exist
        cache_key = f"{device_model}_{ios_version}"
        symbols = await db_manager.get_cached_symbols(cache_key)
        
        if symbols:
            logger.info(f"Symbols found for {cache_key} ({len(symbols)} symbols)")
            return True, f"Symbols already available for {device_model} {ios_version}"
        
        # Try with build number patterns
        if build_number:
            build_patterns = [build_number, f"{device_model}_{ios_version}_{build_number}", f"{device_model}_{build_number}_unknown"]
        else:
            build_patterns = ['22F76', '22F74', '22F75']  # Common iOS 18.5 builds
            build_patterns = [f"{device_model}_{ios_version}_{build}" for build in build_patterns]
            build_patterns.extend([f"{device_model}_{build}_unknown" for build in ['22F76', '22F74', '22F75']])
        
        for pattern in build_patterns:
            if build_number and pattern == build_number:
                # Handle direct build number check
                cache_key_with_build = f"{device_model}_{ios_version}_{build_number}"
            elif pattern.startswith(device_model):
                cache_key_with_build = pattern
            else:
                cache_key_with_build = f"{device_model}_{ios_version}_{pattern}"
                
            symbols = await db_manager.get_cached_symbols(cache_key_with_build)
            if symbols:
                logger.info(f"Found symbols with pattern: {cache_key_with_build} ({len(symbols)} symbols)")
                return True, f"Symbols found with pattern {cache_key_with_build}"
        
        logger.info(f"No symbols found for {device_model} {ios_version}, attempting auto-scan...")
        
        # Check if S3 manager is available
        if not s3_manager:
            return False, "S3 manager not available for auto-scanning"
        
        # Search for matching IPSW in S3
        try:
            available_ipsws = await s3_manager.list_available_ipsw(device_filter=device_model)
            
            matching_ipsw = None
            for ipsw in available_ipsws:
                if (ipsw.get('device') == device_model and 
                    ipsw.get('version') == ios_version):
                    if build_number and ipsw.get('build') == build_number:
                        matching_ipsw = ipsw
                        break
                    elif not build_number:
                        matching_ipsw = ipsw
                        break
            
            if not matching_ipsw and build_number:
                # Try without exact build match
                for ipsw in available_ipsws:
                    if (ipsw.get('device') == device_model and 
                        ipsw.get('version') == ios_version):
                        matching_ipsw = ipsw
                        break
            
            if not matching_ipsw:
                return False, f"No matching IPSW found in S3 for {device_model} {ios_version}"
            
            logger.info(f"Found matching IPSW: {matching_ipsw.get('filename')}")
            
            # Download IPSW
            download_success, download_msg, ipsw_path = await s3_manager.download_ipsw(
                device_model=device_model,
                os_version=ios_version,
                build_number=build_number or matching_ipsw.get('build')
            )
            
            if not download_success:
                return False, f"Failed to download IPSW: {download_msg}"
            
            logger.info(f"Downloaded IPSW: {ipsw_path}")
            
            # Extract IPSW info
            info = symbol_manager.extract_ipsw_info(ipsw_path)
            if not info:
                return False, "Failed to extract IPSW info"
            
            extracted_ios_version = info.get('ios_version', ios_version)
            extracted_build_version = info.get('build_version', 'unknown')
            
            # Check cache again with extracted info
            cache_key_extracted = f"{device_model}_{extracted_build_version}_unknown"
            symbols = await db_manager.get_cached_symbols(cache_key_extracted)
            
            if symbols:
                logger.info(f"Symbols found after extraction check: {cache_key_extracted} ({len(symbols)} symbols)")
                return True, f"Symbols found with extracted info: {cache_key_extracted}"
            
            # Extract kernelcache
            kernelcache_path = symbol_manager.extract_kernelcache(ipsw_path)
            if not kernelcache_path:
                return False, "Failed to extract kernelcache"
            
            logger.info(f"Extracted kernelcache: {kernelcache_path}")
            
            # Symbolicate kernelcache
            symbols_path = symbol_manager.symbolicate_kernelcache(kernelcache_path)
            if not symbols_path:
                return False, "Failed to symbolicate kernelcache"
            
            logger.info(f"Generated symbols: {symbols_path}")
            
            # Load symbols
            symbols = symbol_manager.load_symbols(symbols_path)
            symbols_count = len(symbols) if symbols else 0
            
            if not symbols:
                return False, f"No symbols loaded from {symbols_path}"
            
            logger.info(f"Loaded {symbols_count} symbols from {symbols_path}")
            
            # Save symbols to cache with multiple keys for better lookup
            cache_keys = [
                f"{device_model}_{ios_version}",
                f"{device_model}_{ios_version}_{extracted_build_version}",
                f"{device_model}_{extracted_build_version}_unknown"
            ]
            
            if build_number and build_number != extracted_build_version:
                cache_keys.append(f"{device_model}_{ios_version}_{build_number}")
                cache_keys.append(f"{device_model}_{build_number}_unknown")
            
            # Cache with all possible keys
            for cache_key in cache_keys:
                await db_manager.cache_symbols(cache_key, symbols, 24)
                logger.info(f"Cached symbols with key: {cache_key}")
            
            # Save metadata
            await db_manager.save_symbols_metadata(
                device_model, extracted_ios_version, extracted_build_version, 
                kernelcache_path, symbols_path
            )
            
            # Update stats
            stats['total_ipsws_scanned'] += 1
            stats['total_symbols_extracted'] += symbols_count
            
            logger.info(f"Successfully auto-scanned IPSW: {symbols_count} symbols extracted and cached")
            
            # Auto-cleanup: Delete the IPSW file after successful symbol extraction
            try:
                if Path(ipsw_path).exists():
                    ipsw_size_mb = Path(ipsw_path).stat().st_size / (1024 * 1024)
                    Path(ipsw_path).unlink()
                    logger.info(f"Auto-cleanup: Deleted IPSW file {Path(ipsw_path).name} ({ipsw_size_mb:.1f} MB) to save space")
                    stats['total_space_saved_mb'] = stats.get('total_space_saved_mb', 0) + ipsw_size_mb
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete IPSW file {ipsw_path}: {cleanup_error}")
            
            # Also cleanup extracted kernelcache files (keep only the symbols.json)
            try:
                kernelcache_dir = Path(kernelcache_path).parent
                for file_path in kernelcache_dir.rglob("*"):
                    # Keep only .symbols.json files, delete kernelcache binaries
                    if file_path.is_file() and not file_path.name.endswith('.symbols.json'):
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        if file_size_mb > 1:  # Only log deletion of larger files
                            logger.info(f"Auto-cleanup: Deleted extracted file {file_path.name} ({file_size_mb:.1f} MB)")
                        file_path.unlink()
                        stats['total_space_saved_mb'] = stats.get('total_space_saved_mb', 0) + file_size_mb
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup extracted files: {cleanup_error}")
            
            return True, f"Successfully auto-scanned and cached {symbols_count} symbols for {device_model} {ios_version}"
            
        except Exception as e:
            logger.error(f"Error during auto-scan: {e}")
            return False, f"Auto-scan failed: {str(e)}"
            
    except Exception as e:
        logger.error(f"Error in auto_ensure_symbols_available: {e}")
        return False, f"Auto-scan error: {str(e)}"

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await db_manager.init_pool()
    stats['start_time'] = datetime.now()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await db_manager.close_pool()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "custom-symbol-server", "version": "2.0.0", "timestamp": datetime.now().isoformat()}

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    # Update cache size
    try:
        cache_size = sum(f.stat().st_size for f in Path(CACHE_DIR).rglob('*') if f.is_file())
        stats['cache_size_mb'] = cache_size / (1024 * 1024)
    except:
        pass
    
    # Update downloads size (current IPSW files)
    try:
        downloads_size = sum(f.stat().st_size for f in Path(DOWNLOADS_DIR).rglob('*.ipsw') if f.is_file())
        stats['current_ipsw_size_mb'] = downloads_size / (1024 * 1024)
        stats['current_ipsw_count'] = len(list(Path(DOWNLOADS_DIR).rglob('*.ipsw')))
    except:
        stats['current_ipsw_size_mb'] = 0
        stats['current_ipsw_count'] = 0
    
    # Update uptime
    stats['uptime_seconds'] = (datetime.now() - stats['start_time']).total_seconds()
    
    return stats

@app.get("/cache-stats")
async def get_cache_stats():
    """Get cache statistics and storage info"""
    try:
        cache_stats = {}
        
        # Try to get S3 optimized manager stats
        try:
            from s3_optimized_manager import s3_manager
            cache_stats = s3_manager.get_cache_stats()
        except ImportError:
            # Fallback to basic stats
            logger.info("S3 optimized manager not available, using basic stats")
            cache_stats = {"status": "basic_mode"}
        
        # Add basic storage info
        import shutil
        storage_info = {}
        try:
            # Check main data directory
            total, used, free = shutil.disk_usage("/app/data")
            storage_info = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 1)
            }
        except Exception as e:
            storage_info = {"error": str(e)}
        
        return {
            "cache": cache_stats,
            "storage": storage_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {'error': str(e)}

@app.get("/v1/ipsws")
async def list_ipsws():
    """List available IPSW files"""
    try:
        ipsw_files = []
        downloads_path = Path(DOWNLOADS_DIR)
        
        for ipsw_file in downloads_path.glob('*.ipsw'):
            if ipsw_file.is_file():
                info = symbol_manager.extract_ipsw_info(str(ipsw_file))
                ipsw_files.append({
                    'filename': ipsw_file.name,
                    'path': str(ipsw_file),
                    'size_mb': ipsw_file.stat().st_size / (1024 * 1024),
                    'info': info or {}
                })
        
        return {'ipsws': ipsw_files, 'count': len(ipsw_files)}
    except Exception as e:
        logger.error(f"Failed to list IPSWs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/syms/scan")
async def scan_ipsw(request: IPSWScanRequest, background_tasks: BackgroundTasks):
    """Scan IPSW and extract symbols"""
    try:
        ipsw_path = request.ipsw_path
        
        if not Path(ipsw_path).exists():
            raise HTTPException(status_code=404, detail=f"IPSW file not found: {ipsw_path}")
        
        # Extract IPSW info
        info = symbol_manager.extract_ipsw_info(ipsw_path)
        if not info:
            raise HTTPException(status_code=400, detail="Failed to extract IPSW info")
        
        ios_version = info.get('ios_version', 'unknown')
        build_version = info.get('build_version', 'unknown')
        
        # Determine device model from filename
        device_model = 'unknown'
        filename = Path(ipsw_path).name
        if 'iPhone15,2' in filename:
            device_model = 'iPhone15,2'
        elif 'iPhone' in filename:
            # Extract device model from filename pattern
            import re
            match = re.search(r'iPhone\d+,\d+', filename)
            if match:
                device_model = match.group()
        
        # Check cache first
        cache_key = f"{device_model}_{ios_version}_{build_version}"
        cached_symbols = await db_manager.get_cached_symbols(cache_key)
        
        if cached_symbols:
            logger.info(f"Using cached symbols for {cache_key}")
            return {
                'success': True,
                'message': f'Using cached symbols for {device_model} {ios_version}',
                'symbols_count': len(cached_symbols),
                'cached': True
            }
        
        # Extract kernelcache
        if request.extract_kernelcache:
            kernelcache_path = symbol_manager.extract_kernelcache(ipsw_path)
            if not kernelcache_path:
                raise HTTPException(status_code=500, detail="Failed to extract kernelcache")
            
            # Symbolicate kernelcache
            symbols_path = symbol_manager.symbolicate_kernelcache(kernelcache_path)
            if not symbols_path:
                raise HTTPException(status_code=500, detail="Failed to symbolicate kernelcache")
            
            # Load symbols
            symbols = symbol_manager.load_symbols(symbols_path)
            symbols_count = len(symbols) if symbols else 0
            
            if not symbols:
                logger.error(f"No symbols loaded from {symbols_path}")
                raise HTTPException(status_code=500, detail=f"No symbols loaded from {symbols_path}")
            
            logger.info(f"Loaded {symbols_count} symbols from {symbols_path}")
            
            # Save to database
            background_tasks.add_task(
                db_manager.save_symbols_metadata,
                device_model, ios_version, build_version, kernelcache_path, symbols_path
            )
            
            # Cache symbols
            background_tasks.add_task(
                db_manager.cache_symbols,
                cache_key, symbols, 24
            )
            
            # Update stats
            stats['total_ipsws_scanned'] += 1
            stats['total_symbols_extracted'] += symbols_count
            
            logger.info(f"Successfully processed IPSW: {symbols_count} symbols extracted")
            
            return {
                'success': True,
                'message': f'Successfully extracted {symbols_count} symbols',
                'symbols_count': symbols_count,
                'device_model': device_model,
                'ios_version': ios_version,
                'build_version': build_version,
                'cached': False
            }
        
        return {'success': False, 'message': 'No extraction options specified'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning IPSW: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/symbolicate", response_model=SymbolicateResponse)
async def symbolicate_crash(request: SymbolicateRequest):
    """Symbolicate crash log with auto-scanning capability"""
    try:
        # Extract addresses from crash log
        addresses = AddressParser.extract_addresses(request.crash_content)
        
        if not addresses:
            return SymbolicateResponse(
                success=False,
                message="No addresses found in crash log"
            )
        
        logger.info(f"Extracted {len(addresses)} addresses from crash log")
        
        # Auto-ensure symbols are available (with auto-scanning if needed)
        symbols_available, symbols_message = await auto_ensure_symbols_available(
            device_model=request.device_model,
            ios_version=request.ios_version,
            build_number=getattr(request, 'build_number', None)
        )
        
        if not symbols_available:
            logger.warning(f"Auto-scan failed: {symbols_message}")
            # Continue with manual symbol lookup as fallback
        else:
            logger.info(f"Auto-scan result: {symbols_message}")
        
        # Get symbols from cache (should be available now after auto-scan)
        cache_key = f"{request.device_model}_{request.ios_version}"
        logger.info(f"Looking for symbols with key: {cache_key}")
        symbols = await db_manager.get_cached_symbols(cache_key)
        
        if not symbols:
            # Try to find symbols by build version pattern
            build_patterns = ['22F76', '22F74', '22F75']  # Common iOS 18.5 builds
            for build in build_patterns:
                cache_key_with_build = f"{request.device_model}_{request.ios_version}_{build}"
                logger.info(f"Trying key: {cache_key_with_build}")
                symbols = await db_manager.get_cached_symbols(cache_key_with_build)
                if symbols:
                    logger.info(f"Found symbols with key: {cache_key_with_build}")
                    break
                # Also try with build as ios_version (for cases where build was saved as ios_version)
                cache_key_alt = f"{request.device_model}_{build}_unknown"
                logger.info(f"Trying alternative key: {cache_key_alt}")
                symbols = await db_manager.get_cached_symbols(cache_key_alt)
                if symbols:
                    logger.info(f"Found symbols with alternative key: {cache_key_alt}")
                    break
        
        if not symbols:
            return SymbolicateResponse(
                success=False,
                message=f"No symbols found for {request.device_model} {request.ios_version} - Auto-scan: {symbols_message}"
            )
        
        # Symbolicate addresses
        symbolicated = symbol_manager.symbolicate_addresses(addresses, symbols)
        
        if not symbolicated:
            return SymbolicateResponse(
                success=False,
                message="Failed to symbolicate any addresses"
            )
        
        # Create symbolicated crash log
        symbolicated_crash = request.crash_content
        for addr, symbol in symbolicated.items():
            # Replace addresses with symbols in crash log
            symbolicated_crash = symbolicated_crash.replace(addr, f"{addr} ({symbol})")
        
        logger.info(f"Successfully symbolicated {len(symbolicated)} addresses")
        
        return SymbolicateResponse(
            success=True,
            message=f"Successfully symbolicated {len(symbolicated)} addresses",
            symbols=symbolicated,
            symbolicated_crash=symbolicated_crash
        )
        
    except Exception as e:
        logger.error(f"Error symbolicating crash: {e}")
        return SymbolicateResponse(
            success=False,
            message=f"Symbolication failed: {str(e)}"
        )

@app.post("/v1/auto-scan")
async def auto_scan_endpoint(device_model: str, ios_version: str, build_number: Optional[str] = None):
    """Manually trigger auto-scan for specific device/version"""
    try:
        success, message = await auto_ensure_symbols_available(device_model, ios_version, build_number)
        return {
            "success": success,
            "message": message,
            "device_model": device_model,
            "ios_version": ios_version,
            "build_number": build_number
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Auto-scan failed: {str(e)}",
            "device_model": device_model,
            "ios_version": ios_version,
            "build_number": build_number
        }

@app.post("/v1/cleanup")
async def manual_cleanup():
    """Manually clean up old IPSW files to save disk space"""
    try:
        downloads_path = Path(DOWNLOADS_DIR)
        if not downloads_path.exists():
            return {
                "success": True,
                "message": "Downloads directory does not exist",
                "files_deleted": 0,
                "space_saved_mb": 0
            }
        
        files_deleted = 0
        total_space_saved = 0
        deleted_files = []
        
        # Find and delete all IPSW files
        for ipsw_file in downloads_path.glob("*.ipsw"):
            try:
                if ipsw_file.is_file():
                    file_size = ipsw_file.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    
                    ipsw_file.unlink()
                    files_deleted += 1
                    total_space_saved += file_size_mb
                    deleted_files.append({
                        "filename": ipsw_file.name,
                        "size_mb": round(file_size_mb, 1)
                    })
                    logger.info(f"Manual cleanup: Deleted {ipsw_file.name} ({file_size_mb:.1f} MB)")
                    
            except Exception as e:
                logger.error(f"Failed to delete {ipsw_file}: {e}")
        
        # Update global stats
        stats['total_space_saved_mb'] = stats.get('total_space_saved_mb', 0) + total_space_saved
        
        return {
            "success": True,
            "message": f"Cleanup completed: {files_deleted} files deleted, {total_space_saved:.1f} MB freed",
            "files_deleted": files_deleted,
            "space_saved_mb": round(total_space_saved, 1),
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        return {
            "success": False,
            "message": f"Cleanup failed: {str(e)}",
            "files_deleted": 0,
            "space_saved_mb": 0
        }

@app.get("/v1/disk-usage")
async def get_disk_usage():
    """Get current disk usage information"""
    try:
        downloads_path = Path(DOWNLOADS_DIR)
        cache_path = Path(CACHE_DIR)
        symbols_path = Path(SYMBOLS_DIR)
        
        disk_info = {}
        
        # Calculate directory sizes
        for name, path in [("downloads", downloads_path), ("cache", cache_path), ("symbols", symbols_path)]:
            if path.exists():
                total_size = 0
                file_count = 0
                ipsw_count = 0
                
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
                        if file_path.suffix == '.ipsw':
                            ipsw_count += 1
                
                disk_info[name] = {
                    "size_mb": round(total_size / (1024 * 1024), 1),
                    "file_count": file_count,
                    "ipsw_count": ipsw_count if name == "downloads" else None
                }
            else:
                disk_info[name] = {"size_mb": 0, "file_count": 0, "ipsw_count": 0 if name == "downloads" else None}
        
        # Get overall disk usage
        import shutil
        try:
            total, used, free = shutil.disk_usage(downloads_path.parent)
            disk_info["overall"] = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 1)
            }
        except:
            disk_info["overall"] = {"error": "Could not get disk usage"}
        
        # Add cleanup stats
        disk_info["cleanup_stats"] = {
            "total_space_saved_mb": round(stats.get('total_space_saved_mb', 0), 1),
            "auto_cleanup_enabled": True  # Always enabled now
        }
        
        return {
            "success": True,
            "disk_usage": disk_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting disk usage: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Legacy endpoints for compatibility
@app.get("/v1/_ping")
async def ping():
    """Legacy ping endpoint"""
    return {"status": "ok"}

@app.get("/v1/version")
async def version():
    """Legacy version endpoint"""
    return {"version": "2.0.0", "service": "custom-symbol-server"}

if __name__ == "__main__":
    uvicorn.run(
        "custom_symbol_server:app",
        host="0.0.0.0",
        port=3993,
        log_level="info",
        access_log=True
    ) 