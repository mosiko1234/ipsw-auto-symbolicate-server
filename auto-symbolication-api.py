#!/usr/bin/env python3
"""
Auto-Symbolication API for iOS Crash Logs with S3 IPSW Downloads
Automatically downloads required IPSW from S3 and returns symbolicated output
"""

import os
import re
import json
import tempfile
import subprocess
import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging

# Import our internal S3 manager and symbol server
from internal_s3_manager import InternalS3Manager
from symbol_server_manager import SymbolServerManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IPSW Auto-Symbolication API (S3 Edition)",
    description="Automatically symbolicate iOS crash logs using IPSW files from S3",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for internal network
IPSWD_URL = os.getenv("IPSWD_URL", "http://ipswd-symbol-server:3993")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://your-internal-s3.company.local")
S3_BUCKET = os.getenv("S3_BUCKET", "ipsw-files")
S3_USE_SSL = os.getenv("S3_USE_SSL", "false").lower() == "true"
DATA_DIR = Path("/data")
DOWNLOADS_DIR = DATA_DIR / "downloads"
CACHE_DIR = DATA_DIR / "cache"
SYMBOLS_DIR = DATA_DIR / "symbols"

# Ensure directories exist
for dir_path in [DOWNLOADS_DIR, CACHE_DIR, SYMBOLS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Initialize internal S3 manager
s3_manager = InternalS3Manager(
    s3_endpoint=S3_ENDPOINT,
    bucket_name=S3_BUCKET,
    downloads_dir=DOWNLOADS_DIR,
    use_ssl=S3_USE_SSL
)

# Initialize Symbol Server Manager
IPSWD_URL = os.getenv("IPSWD_URL", "http://ipswd-symbol-server:3993")
SYMBOL_DB_URL = os.getenv("SYMBOL_DB_URL", "postgresql://symbols_admin:symbols_pass@symbols-postgres:5432/symbols")
SIGNATURES_DIR = os.getenv("SIGNATURES_DIR", "/data/signatures")

# Initialize Symbol Server Manager (with fallback)
try:
    symbol_server = SymbolServerManager(
        ipswd_url=IPSWD_URL,
        database_url=SYMBOL_DB_URL,
        s3_manager=s3_manager,
        signatures_dir=SIGNATURES_DIR
    )
    logger.info("✅ Symbol Server Manager initialized")
except Exception as e:
    logger.warning(f"⚠️ Symbol Server not available: {e}")
    symbol_server = None

class CrashInfo(BaseModel):
    device_model: str
    os_version: str
    build_number: str
    process_name: Optional[str] = None
    exception_type: Optional[str] = None

class SymbolicationResult(BaseModel):
    success: bool
    message: str
    crash_info: Optional[CrashInfo] = None
    symbolicated_output: Optional[str] = None
    download_time: Optional[float] = None
    symbolication_time: Optional[float] = None
    total_time: Optional[float] = None
    s3_info: Optional[Dict] = None

def extract_crash_info(crash_content: str) -> Optional[CrashInfo]:
    """Extract device info from crash log - supports both text and JSON formats"""
    try:
        logger.info(f"🔍 Starting crash info extraction. Content length: {len(crash_content)} chars")
        logger.info(f"🔍 First 100 chars: {crash_content[:100]}")
        logger.info(f"🔍 Content starts with curly brace: {crash_content.strip().startswith('{')}")
        # Try JSON format first (stackshot .ips files)
        if crash_content.strip().startswith('{'):
            try:
                # Handle multi-line JSON (first line might be metadata, second line main data)
                lines = crash_content.strip().split('\n')
                crash_data = None
                metadata = None
                
                # Try to parse first line as metadata
                try:
                    first_line = lines[0].strip()
                    logger.info(f"First line: {first_line[:100]}...")
                    if first_line.startswith('{') and first_line.endswith('}'):
                        metadata = json.loads(first_line)
                        logger.info(f"✅ Found metadata: {metadata}")
                    else:
                        logger.info("First line is not a complete JSON object")
                except Exception as e:
                    logger.info(f"Failed to parse first line as metadata: {e}")
                    pass
                
                # Try to parse the main JSON object (might be on line 2 or entire content)
                try:
                    if len(lines) > 1:
                        # Multi-line case - try from line 2 onwards
                        main_json = '\n'.join(lines[1:])
                        logger.info(f"Trying to parse main JSON from line 2, length: {len(main_json)} chars")
                        crash_data = json.loads(main_json)
                        logger.info("✅ Successfully parsed main JSON from line 2")
                    else:
                        # Single JSON object
                        logger.info("Single line JSON, parsing entire content")
                        crash_data = json.loads(crash_content)
                        logger.info("✅ Successfully parsed single JSON")
                except json.JSONDecodeError as je:
                    logger.info(f"Multi-line parsing failed: {je}, trying entire content")
                    # Try the entire content as one JSON
                    crash_data = json.loads(crash_content)
                
                # Extract from JSON format
                extracted = {}
                
                # Check metadata first for quick info
                if metadata:
                    if 'os_version' in metadata:
                        os_version_info = metadata['os_version']
                        version_match = re.search(r'iPhone OS ([0-9.]+)', os_version_info)
                        if version_match:
                            extracted['os_version'] = version_match.group(1)
                        
                        build_match = re.search(r'\(([^)]+)\)', os_version_info)
                        if build_match:
                            extracted['build_number'] = build_match.group(1)
                
                # Extract from main crash data
                if crash_data:
                    # Device model from "product" field
                    if 'product' in crash_data:
                        extracted['device_model'] = crash_data['product']
                    
                    # OS version from "build" field (if not already found in metadata)
                    if 'build' in crash_data and 'os_version' not in extracted:
                        build_info = crash_data['build']
                        # Parse "iPhone OS 18.5 (22F76)" format
                        version_match = re.search(r'iPhone OS ([0-9.]+)', build_info)
                        if version_match:
                            extracted['os_version'] = version_match.group(1)
                        
                        # Build number from parentheses
                        build_match = re.search(r'\(([^)]+)\)', build_info)
                        if build_match:
                            extracted['build_number'] = build_match.group(1)
                    
                    # Alternative: check os_version field in main data
                    if 'os_version' in crash_data and 'os_version' not in extracted:
                        os_version_info = crash_data['os_version']
                        version_match = re.search(r'iPhone OS ([0-9.]+)', os_version_info)
                        if version_match:
                            extracted['os_version'] = version_match.group(1)
                        
                        build_match = re.search(r'\(([^)]+)\)', os_version_info)
                        if build_match:
                            extracted['build_number'] = build_match.group(1)
                    
                    # Process name from bug_type or reason
                    if 'reason' in crash_data:
                        extracted['process_name'] = crash_data['reason']
                    elif 'bug_type' in crash_data:
                        extracted['process_name'] = f"bug_type_{crash_data['bug_type']}"
                    
                    # Exception type from exception field
                    if 'exception' in crash_data:
                        extracted['exception_type'] = str(crash_data['exception'])
                
                logger.info(f"Extracted fields: {extracted}")
                
                if 'device_model' in extracted and 'os_version' in extracted:
                    if 'build_number' not in extracted:
                        extracted['build_number'] = 'unknown'
                    
                    logger.info(f"✅ Successfully extracted JSON crash info: {extracted}")
                    return CrashInfo(**extracted)
                else:
                    logger.warning(f"❌ Missing required fields. Have: {list(extracted.keys())}, Need: device_model, os_version")
                    
            except json.JSONDecodeError as e:
                logger.info(f"JSON parsing failed: {e}, trying text format...")
                pass
            except Exception as e:
                logger.warning(f"JSON processing failed: {e}, trying text format...")
                pass
        
        # Try traditional text format
        patterns = {
            'device_model': r'Hardware Model:\s*([^\s\n]+)',
            'os_version': r'OS Version:\s*iPhone OS\s+([0-9.]+)',
            'build_number': r'OS Version:.*\(([^)]+)\)',
            'process_name': r'Process:\s*([^\s\[\n]+)',
            'exception_type': r'Exception Type:\s*([^\s\n]+)'
        }
        
        extracted = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, crash_content, re.IGNORECASE)
            if match:
                extracted[key] = match.group(1).strip()
        
        if 'device_model' in extracted and 'os_version' in extracted:
            if 'build_number' not in extracted:
                build_match = re.search(r'BuildID:\s*([^\s\n]+)', crash_content, re.IGNORECASE)
                if build_match:
                    extracted['build_number'] = build_match.group(1).strip()
            
            logger.info(f"Extracted text crash info: {extracted}")
            return CrashInfo(**extracted)
        
        logger.warning("Could not extract minimum required crash info from either JSON or text format")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting crash info: {e}")
        return None

async def check_symbols_available(crash_info: CrashInfo) -> bool:
    """Check if symbols are already available locally"""
    try:
        # Check if we have local symbol cache for this device/version
        cache_path = SYMBOLS_DIR / f"{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}"
        return cache_path.exists() and len(list(cache_path.glob("*.ipsw"))) > 0
    except Exception as e:
        logger.error(f"Error checking available symbols: {e}")
        return False

async def download_ipsw_from_s3(crash_info: CrashInfo) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
    """Download required IPSW file from S3"""
    start_time = datetime.now()
    
    try:
        logger.info(f"Downloading IPSW from S3: {crash_info.device_model} {crash_info.os_version} {crash_info.build_number}")
        
        success, message, ipsw_path = await s3_manager.download_ipsw(
            device_model=crash_info.device_model,
            os_version=crash_info.os_version,
            build_number=crash_info.build_number
        )
        
        download_time = (datetime.now() - start_time).total_seconds()
        
        s3_info = {
            "endpoint": S3_ENDPOINT,
            "bucket": S3_BUCKET,
            "download_source": "s3"
        }
        
        if success and ipsw_path:
            file_size = os.path.getsize(ipsw_path) if os.path.exists(ipsw_path) else 0
            s3_info.update({
                "file_path": ipsw_path,
                "file_size_mb": file_size // (1024 * 1024),
                "download_time_seconds": download_time
            })
        
        return success, message, ipsw_path, s3_info
        
    except Exception as e:
        logger.error(f"Error downloading IPSW from S3: {e}")
        return False, f"S3 download error: {str(e)}", None, None

async def scan_ipsw(ipsw_path: str, crash_info: CrashInfo) -> Tuple[bool, str]:
    """Extract symbols from IPSW file using ipsw CLI"""
    try:
        logger.info(f"Extracting symbols from IPSW: {ipsw_path}")
        
        # Create symbols directory for this device/version
        symbols_path = SYMBOLS_DIR / f"{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}"
        symbols_path.mkdir(parents=True, exist_ok=True)
        
        # Copy IPSW to symbols directory for caching
        import shutil
        cached_ipsw = symbols_path / f"{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}.ipsw"
        if not cached_ipsw.exists():
            shutil.copy2(ipsw_path, cached_ipsw)
        
        logger.info(f"IPSW cached to: {cached_ipsw}")
        return True, "IPSW processed successfully"
                
    except Exception as e:
        logger.error(f"Error processing IPSW: {e}")
        return False, f"Processing error: {str(e)}"

async def symbolicate_crash(crash_content: str, crash_info: CrashInfo) -> Tuple[bool, str]:
    """Symbolicate crash log using ipsw Docker container"""
    temp_crash_path = None
    host_temp_path = None
    host_ipsw_path = None
    
    try:
        # Create unique temp file with device info
        temp_crash_path = f"/tmp/crash_{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}_{int(time.time())}.ips"
        with open(temp_crash_path, 'w') as temp_file:
            temp_file.write(crash_content)
        
        # Find the cached IPSW file
        symbols_path = SYMBOLS_DIR / f"{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}"
        cached_ipsw = symbols_path / f"{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}.ipsw"
        
        if not cached_ipsw.exists():
            return False, "IPSW file not available for symbolication"
        
        # Use Docker container for ipsw symbolication
        # We need to use host-accessible paths since we're running Docker-in-Docker
        host_temp_path = f"/tmp/crash_{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}.ips"
        host_ipsw_path = f"/tmp/ipsw_{crash_info.device_model}_{crash_info.os_version}_{crash_info.build_number}.ipsw"
        
        # Copy files to locations accessible from host
        import shutil
        if temp_crash_path != host_temp_path:
            shutil.copy2(temp_crash_path, host_temp_path)
        if str(cached_ipsw) != host_ipsw_path:
            shutil.copy2(str(cached_ipsw), host_ipsw_path)
        
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{host_temp_path}:/data/crash.ips:ro",
            "-v", f"{host_ipsw_path}:/data/firmware.ipsw:ro",
            "blacktop/ipsw",
            "symbolicate", "--color", "/data/crash.ips", "/data/firmware.ipsw"
        ]
        
        logger.info(f"Symbolicating crash: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            symbolicated_output = stdout.decode()
            logger.info("Crash symbolicated successfully")
            return True, symbolicated_output
        else:
            error_msg = stderr.decode() if stderr else "Unknown symbolication error"
            logger.error(f"Symbolication failed: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"Error symbolicating crash: {e}")
        return False, f"Symbolication error: {str(e)}"
        
    finally:
        # Clean up all temp files
        for path in [temp_crash_path, host_temp_path, host_ipsw_path]:
            if path:
                try:
                    os.unlink(path)
                except:
                    pass

@app.get("/", response_class=HTMLResponse)
async def root():
    """API Documentation page - Symbol Server Edition"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🚀 IPSW Auto-Symbolication API - Symbol Server Edition</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
            .container {{ background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 20px; padding: 3rem; }}
            .endpoint {{ background: rgba(255,255,255,0.1); padding: 20px; margin: 20px 0; border-radius: 10px; }}
            .symbol-server-info {{ background: rgba(255, 215, 0, 0.2); padding: 15px; margin: 10px 0; border-left: 4px solid #ffd700; border-radius: 5px; }}
            .s3-info {{ background: rgba(0, 191, 255, 0.2); padding: 15px; margin: 10px 0; border-left: 4px solid #00bfff; border-radius: 5px; }}
            code {{ background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 3px; color: #ffd700; }}
            pre {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 5px; overflow-x: auto; color: #ffffff; }}
            .badge {{ background: linear-gradient(45deg, #ff6b6b, #ee5a24); padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem; font-weight: bold; margin: 0 0.5rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 IPSW Auto-Symbolication API</h1>
            <span class="badge">Symbol Server Edition</span>
            <p>Lightning-fast iOS crash log symbolication with centralized Symbol Server!</p>
            
            <div class="symbol-server-info">
                <h3>🗄️ Symbol Server (IPSWD)</h3>
                <p><strong>Server:</strong> {IPSWD_URL}</p>
                <p><strong>Database:</strong> PostgreSQL with pre-cached symbols</p>
                <p><strong>Performance:</strong> Sub-second symbolication!</p>
            </div>
            
            <div class="s3-info">
                <h3>📦 S3 Configuration</h3>
                <p><strong>Endpoint:</strong> {S3_ENDPOINT}</p>
                <p><strong>Bucket:</strong> {S3_BUCKET}</p>
                <p><strong>Environment:</strong> Internal Network</p>
            </div>
            
            <div class="endpoint">
                <h2>POST /symbolicate</h2>
                <p>Upload a crash log file (.ips) - Symbol Server handles everything!</p>
                <pre>curl -X POST "http://localhost:8000/symbolicate" -F "file=@crash.ips"</pre>
            </div>
            
            <div class="endpoint">
                <h2>POST /symbolicate/text</h2>
                <p>Send crash log content as JSON - Ultra fast via Symbol Server</p>
                <pre>curl -X POST "http://localhost:8000/symbolicate/text" \\
  -H "Content-Type: application/json" \\
  -d '{{"crash_content": "Process: MyApp [1234]\\nHardware Model: iPhone15,2\\n..."}}'</pre>
            </div>
            
            <div class="endpoint">
                <h2>POST /symbol-server/scan-all</h2>
                <p>Scan all S3 IPSWs to Symbol Server for instant future symbolication</p>
                <pre>curl -X POST "http://localhost:8000/symbol-server/scan-all"</pre>
            </div>
            
            <div class="endpoint">
                <h2>POST /symbol-server/scan/{{device}}/{{version}}</h2>
                <p>Scan specific IPSW to Symbol Server</p>
                <pre>curl -X POST "http://localhost:8000/symbol-server/scan/iPhone15,2/17.4"</pre>
            </div>
            
            <div class="endpoint">
                <h2>GET /symbol-server/health</h2>
                <p>Check Symbol Server health status</p>
                <pre>curl "http://localhost:8000/symbol-server/health"</pre>
            </div>
            
            <div class="endpoint">
                <h2>GET /symbol-server/stats</h2>
                <p>Get Symbol Server statistics and cached symbols count</p>
                <pre>curl "http://localhost:8000/symbol-server/stats"</pre>
            </div>
            
            <h2>🚀 How Symbol Server Works:</h2>
            <ol>
                <li><strong>Pre-Scan:</strong> All IPSW files are scanned into PostgreSQL database</li>
                <li><strong>Instant Lookup:</strong> Symbols are cached and ready for instant retrieval</li>
                <li><strong>Fast Symbolication:</strong> Sub-second symbolication via IPSWD daemon</li>
                <li><strong>Smart Fallback:</strong> Auto-scans missing IPSW files from S3</li>
                <li><strong>Kernel Support:</strong> Full kernel panic and app crash symbolication</li>
            </ol>
            
            <h2>📊 Supported Crash Types:</h2>
            <ul>
                <li><code>BugType 210:</code> Kernel Panics (with signature support)</li>
                <li><code>BugType 309:</code> Application Crashes</li>
                <li><code>BugType 109:</code> Legacy Crashes</li>
                <li><code>dyld_shared_cache:</code> System library symbolication</li>
            </ul>
            
            <h2>🔗 Additional Endpoints:</h2>
            <p>
                <a href="/health" style="color: #ffd700; text-decoration: none; margin-right: 20px;">🔍 Health Check</a>
                <a href="/docs" style="color: #ffd700; text-decoration: none; margin-right: 20px;">📖 API Docs</a>
                <a href="/s3/stats" style="color: #ffd700; text-decoration: none;">💾 S3 Stats</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if Docker and ipsw container are available
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm", "blacktop/ipsw", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            ipsw_status = process.returncode == 0
            ipsw_version = stdout.decode().strip() if ipsw_status else "Not available"
        except Exception:
            ipsw_status = False
            ipsw_version = "Docker/ipsw container not available"
        
        # Check S3 connection
        try:
            await s3_manager.refresh_bucket_cache()
            s3_status = True
        except Exception:
            s3_status = False
        
        # Check Symbol Server connection
        if symbol_server:
            try:
                symbol_server_healthy, symbol_server_msg = await symbol_server.check_server_health()
            except Exception:
                symbol_server_healthy = False
                symbol_server_msg = "Symbol Server connection failed"
        else:
            symbol_server_healthy = False
            symbol_server_msg = "Symbol Server not initialized"
        
        return {
            "status": "healthy" if (ipsw_status and s3_status) else "degraded",
            "ipsw_available": ipsw_status,
            "ipsw_version": ipsw_version,
            "s3_connected": s3_status,
            "s3_endpoint": S3_ENDPOINT,
            "s3_bucket": S3_BUCKET,
            "symbol_server_available": symbol_server_healthy,
            "symbol_server_message": symbol_server_msg,
            "symbol_server_url": IPSWD_URL if symbol_server else "Not configured",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/s3/list")
async def list_s3_ipsw(device: Optional[str] = None):
    """List available IPSW files in S3"""
    try:
        files = await s3_manager.list_available_ipsw(device_filter=device)
        return {
            "success": True,
            "count": len(files),
            "files": files,
            "s3_endpoint": S3_ENDPOINT,
            "s3_bucket": S3_BUCKET
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "s3_endpoint": S3_ENDPOINT,
            "s3_bucket": S3_BUCKET
        }

@app.get("/s3/stats")
async def get_s3_stats():
    """Get S3 bucket statistics"""
    try:
        stats = await s3_manager.get_bucket_stats()
        stats.update({
            "s3_endpoint": S3_ENDPOINT,
            "s3_bucket": S3_BUCKET
        })
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# =============================================================================
# SYMBOL SERVER ENDPOINTS
# =============================================================================

@app.get("/symbol-server/health")
async def check_symbol_server_health():
    """Check Symbol Server health"""
    try:
        is_healthy, message = await symbol_server.check_server_health()
        return {
            "healthy": is_healthy,
            "message": message,
            "server_url": IPSWD_URL,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Error checking Symbol Server: {str(e)}",
            "server_url": IPSWD_URL,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/symbol-server/stats")
async def get_symbol_server_stats():
    """Get Symbol Server statistics"""
    try:
        stats = await symbol_server.get_server_stats()
        return {
            "success": True,
            "stats": stats,
            "server_url": IPSWD_URL
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_url": IPSWD_URL
        }

@app.post("/symbol-server/scan/{device_model}/{os_version}")
async def scan_specific_ipsw(
    device_model: str, 
    os_version: str, 
    build_number: Optional[str] = None
):
    """Scan specific IPSW to Symbol Server"""
    try:
        logger.info(f"Manual scan request: {device_model} {os_version} {build_number}")
        
        success, message = await symbol_server.ensure_ipsw_scanned(
            device_model=device_model,
            os_version=os_version,
            build_number=build_number
        )
        
        return {
            "success": success,
            "message": message,
            "device_model": device_model,
            "os_version": os_version,
            "build_number": build_number
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "device_model": device_model,
            "os_version": os_version,
            "build_number": build_number
        }

@app.post("/symbol-server/scan-all")
async def scan_all_s3_ipsws():
    """Scan all IPSW files from S3 to Symbol Server"""
    try:
        logger.info("Starting bulk scan of all S3 IPSWs to Symbol Server...")
        
        # This is a long-running operation, so we'll run it in background
        from fastapi import BackgroundTasks
        
        scan_results = await symbol_server.auto_scan_s3_ipsws()
        
        return {
            "success": True,
            "message": "Bulk scan completed",
            "results": scan_results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class DirectSymbolicationRequest(BaseModel):
    crash_content: str
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    build_number: Optional[str] = None

@app.post("/symbol-server/symbolicate")
async def symbolicate_via_symbol_server(request: DirectSymbolicationRequest):
    """Direct symbolication via Symbol Server (bypass IPSW download logic)"""
    try:
        success, message, symbolicated_output = await symbol_server.symbolicate_via_server(
            crash_content=request.crash_content,
            device_model=request.device_model,
            os_version=request.os_version,
            build_number=request.build_number
        )
        
        return {
            "success": success,
            "message": message,
            "symbolicated_output": symbolicated_output,
            "server_url": IPSWD_URL
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_url": IPSWD_URL
        }

class TextSymbolicationRequest(BaseModel):
    crash_content: str

@app.post("/symbolicate/text", response_model=SymbolicationResult)
async def symbolicate_text(request: TextSymbolicationRequest):
    """Symbolicate crash log from text content"""
    return await process_symbolication(request.crash_content)

@app.post("/symbolicate", response_model=SymbolicationResult)
async def symbolicate_file(file: UploadFile = File(...)):
    """Symbolicate uploaded crash log file"""
    if not file.filename or not file.filename.endswith('.ips'):
        raise HTTPException(status_code=400, detail="Please upload a .ips crash file")
    
    try:
        crash_content = await file.read()
        crash_text = crash_content.decode('utf-8')
        return await process_symbolication(crash_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

async def process_symbolication(crash_content: str) -> SymbolicationResult:
    """Main symbolication processing logic - Symbol Server Edition"""
    start_time = datetime.now()
    
    try:
        # Step 1: Extract crash information
        logger.info("Extracting crash information...")
        crash_info = extract_crash_info(crash_content)
        
        if not crash_info:
            return SymbolicationResult(
                success=False,
                message="Could not extract device information from crash log. Please ensure it's a valid iOS crash log.",
                crash_info=None
            )
        
        logger.info(f"Processing via Symbol Server: {crash_info.device_model} running {crash_info.os_version} ({crash_info.build_number})")
        
        # Step 2: Try symbolication via Symbol Server first (if available)
        if symbol_server:
            logger.info("Attempting symbolication via Symbol Server...")
            symbolication_start = datetime.now()
            success, message, symbolicated_output = await symbol_server.symbolicate_via_server(
                crash_content=crash_content,
                device_model=crash_info.device_model,
                os_version=crash_info.os_version,
                build_number=crash_info.build_number
            )
            symbolication_time = (datetime.now() - symbolication_start).total_seconds()
        else:
            logger.info("Symbol Server not available, using direct symbolication...")
            success = False
            message = "Symbol Server not available"
            symbolicated_output = None
            symbolication_time = 0
        
        download_time = None
        s3_info = None
        
        # Step 3: If symbolication failed or Symbol Server not available, use direct method
        if not success:
            if symbol_server and "Symbols not found" in message:
                logger.info("Symbols not found in Symbol Server, ensuring IPSW is scanned...")
                
                download_start = datetime.now()
                scan_success, scan_message = await symbol_server.ensure_ipsw_scanned(
                    device_model=crash_info.device_model,
                    os_version=crash_info.os_version,
                    build_number=crash_info.build_number
                )
                download_time = (datetime.now() - download_start).total_seconds()
                
                if not scan_success:
                    return SymbolicationResult(
                        success=False,
                        message=f"Failed to scan IPSW to Symbol Server: {scan_message}",
                        crash_info=crash_info,
                        download_time=download_time
                    )
                
                # Step 4: Try symbolication again after scanning
                logger.info("IPSW scanned successfully, retrying symbolication...")
                symbolication_retry_start = datetime.now()
                success, message, symbolicated_output = await symbol_server.symbolicate_via_server(
                    crash_content=crash_content,
                    device_model=crash_info.device_model,
                    os_version=crash_info.os_version,
                    build_number=crash_info.build_number
                )
                symbolication_time += (datetime.now() - symbolication_retry_start).total_seconds()
                
                s3_info = {
                    "source": "internal_s3_symbol_server",
                    "scanned_to_server": True,
                    "scan_message": scan_message,
                    "download_time": download_time
                }
            
            else:
                # Fallback to direct symbolication method
                logger.info("Using fallback direct symbolication method...")
                
                # Check if symbols are already available
                symbols_available = await check_symbols_available(crash_info)
                
                if not symbols_available:
                    # Download IPSW from S3
                    download_start = datetime.now()
                    download_success, download_msg, ipsw_path, s3_info = await download_ipsw_from_s3(crash_info)
                    download_time = (datetime.now() - download_start).total_seconds()
                    
                    if not download_success:
                        return SymbolicationResult(
                            success=False,
                            message=f"Failed to download IPSW from S3: {download_msg}",
                            crash_info=crash_info,
                            download_time=download_time,
                            s3_info=s3_info
                        )
                    
                    # Process IPSW
                    scan_success, scan_msg = await scan_ipsw(ipsw_path, crash_info)
                    
                    if not scan_success:
                        return SymbolicationResult(
                            success=False,
                            message=f"Failed to process IPSW: {scan_msg}",
                            crash_info=crash_info,
                            download_time=download_time,
                            s3_info=s3_info
                        )
                
                # Symbolicate crash using direct method
                symbolication_start = datetime.now()
                symbolication_success, symbolicated_output = await symbolicate_crash(crash_content, crash_info)
                symbolication_time = (datetime.now() - symbolication_start).total_seconds()
                
                success = symbolication_success
                message = "Direct symbolication completed" if success else "Direct symbolication failed"
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        if success:
            logger.info("✅ Symbolication completed successfully via Symbol Server!")
            return SymbolicationResult(
                success=True,
                message="Crash log symbolicated successfully via Symbol Server! 🚀",
                crash_info=crash_info,
                symbolicated_output=symbolicated_output,
                download_time=download_time,
                symbolication_time=symbolication_time,
                total_time=total_time,
                s3_info=s3_info
            )
        else:
            logger.error(f"❌ Symbol Server symbolication failed: {message}")
            return SymbolicationResult(
                success=False,
                message=f"Symbol Server symbolication failed: {message}",
                crash_info=crash_info,
                download_time=download_time,
                symbolication_time=symbolication_time,
                total_time=total_time,
                s3_info=s3_info
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in Symbol Server symbolication: {e}")
        return SymbolicationResult(
            success=False,
            message=f"Unexpected error: {str(e)}",
            crash_info=crash_info if 'crash_info' in locals() else None
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)