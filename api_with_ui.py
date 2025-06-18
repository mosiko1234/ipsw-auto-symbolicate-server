#!/usr/bin/env python3
"""
IPSW Auto-Symbolication API with Integrated Web UI
"""

import os
import re
import json
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Import the S3 manager
from internal_s3_manager import InternalS3Manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IPSW Auto-Symbolication API with Web UI",
    description="Complete iOS crash symbolication solution",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Configuration
SYMBOL_SERVER_URL = os.getenv("SYMBOL_SERVER_URL", "http://localhost:3993")
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
TEMP_DIR = DATA_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# S3 Configuration
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_BUCKET = os.getenv("S3_BUCKET", "ipsw")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")

# Initialize S3 manager
downloads_dir = DATA_DIR / "downloads"
downloads_dir.mkdir(parents=True, exist_ok=True)

try:
    s3_manager = InternalS3Manager(
        s3_endpoint=S3_ENDPOINT,
        bucket_name=S3_BUCKET,
        downloads_dir=downloads_dir,
        use_ssl=False
    )
    logger.info(f"S3 manager initialized successfully: {S3_ENDPOINT}/{S3_BUCKET}")
except Exception as e:
    logger.error(f"Failed to initialize S3 manager: {e}")
    s3_manager = None

class SymbolicationResult(BaseModel):
    success: bool
    message: str
    symbolicated_output: Optional[str] = None
    analysis_id: Optional[str] = None
    file_info: Optional[Dict] = None
    total_time: Optional[float] = None

class AutoScanRequest(BaseModel):
    device_model: str
    ios_version: str
    build_number: Optional[str] = None

class AutoScanResult(BaseModel):
    success: bool
    message: str
    found_files: List[Dict] = []
    download_started: bool = False
    download_id: Optional[str] = None

def allowed_file(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    allowed_extensions = {'ips', 'crash', 'txt', 'json', 'log', 'panic'}
    return filename.rsplit('.', 1)[1].lower() in allowed_extensions

def parse_ips_file(content: str) -> Dict[str, any]:
    """Parse IPS file to extract crash information"""
    info = {
        "bug_type": None,
        "device_model": None,
        "ios_version": None,
        "build_version": None,
        "incident_id": None,
        "process_name": None,
        "crash_content": content,
        "is_ips_format": False
    }
    
    try:
        # Try to parse as JSON first (for .ips files)
        data = json.loads(content)
        info["is_ips_format"] = True
        
        # Extract metadata
        info["bug_type"] = data.get("bug_type", "unknown")
        info["incident_id"] = data.get("incident_id")
        info["process_name"] = data.get("procName") or data.get("processName")
        
        # Extract device information
        device_info = data.get("device", {}) or data.get("modelCode", {})
        if isinstance(device_info, dict):
            info["device_model"] = device_info.get("model") or device_info.get("marketingName")
        elif isinstance(device_info, str):
            info["device_model"] = device_info
            
        # Extract OS version
        os_version = data.get("osVersion", {}) or data.get("systemVersion", {})
        if isinstance(os_version, dict):
            info["ios_version"] = os_version.get("major", "unknown")
            info["build_version"] = os_version.get("build")
        elif isinstance(os_version, str):
            info["ios_version"] = os_version
            
        # Try alternative paths for version info
        if not info["ios_version"]:
            version_str = data.get("version") or data.get("osVersion")
            if version_str:
                # Extract version from string like "iOS 18.5 (22F76)"
                version_match = re.search(r'iOS\s+([\d.]+)', str(version_str))
                if version_match:
                    info["ios_version"] = version_match.group(1)
                    
                build_match = re.search(r'\(([\w\d]+)\)', str(version_str))
                if build_match:
                    info["build_version"] = build_match.group(1)
        
        logger.info(f"Parsed IPS file: {info}")
        
    except json.JSONDecodeError:
        # Not a JSON file, try to parse as text crash log
        info["is_ips_format"] = False
        
        # Look for crash information in text format
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Device model patterns
            if 'Hardware Model:' in line or 'Model:' in line:
                info["device_model"] = line.split(':')[-1].strip()
            elif 'Identifier:' in line and 'iPhone' in line:
                info["device_model"] = line.split(':')[-1].strip()
                
            # iOS version patterns  
            elif 'OS Version:' in line or 'Version:' in line:
                version_part = line.split(':')[-1].strip()
                version_match = re.search(r'([\d.]+)', version_part)
                if version_match:
                    info["ios_version"] = version_match.group(1)
                    
                build_match = re.search(r'\(([\w\d]+)\)', version_part)
                if build_match:
                    info["build_version"] = build_match.group(1)
                    
            # Process name
            elif 'Process:' in line or 'Process Name:' in line:
                info["process_name"] = line.split(':')[-1].strip()
                
    return info

async def symbolicate_via_api(crash_content: str) -> SymbolicationResult:
    analysis_id = str(uuid.uuid4())[:8]
    
    try:
        # Parse IPS file to extract metadata
        file_info = parse_ips_file(crash_content)
        
        # Extract device and version information
        device_model = file_info.get("device_model", "unknown")
        ios_version = file_info.get("ios_version", "unknown")
        build_version = file_info.get("build_version", "unknown")
        
        logger.info(f"Extracted from crash file - Device: {device_model}, iOS: {ios_version}, Build: {build_version}")
        
        # Improve device model extraction from content if not found in metadata
        if device_model == "unknown" or not device_model:
            # Look for device patterns in the crash content
            device_patterns = [
                r'Hardware Model:\s*(\S+)',
                r'Model:\s*(\S+)',
                r'Identifier:\s*(iPhone\d+,\d+)',
                r'"modelCode":\s*"([^"]+)"',
                r'"model":\s*"([^"]+)"'
            ]
            
            for pattern in device_patterns:
                match = re.search(pattern, crash_content, re.IGNORECASE)
                if match:
                    device_model = match.group(1)
                    logger.info(f"Found device model via pattern: {device_model}")
                    break
        
        # Improve iOS version extraction
        if ios_version == "unknown" or not ios_version:
            version_patterns = [
                r'OS Version:\s*iOS\s+([\d.]+)',
                r'Version:\s*iOS\s+([\d.]+)',
                r'"osVersion":\s*"([^"]+)"',
                r'iOS\s+([\d.]+)\s*\(',
                r'System Version:\s*([\d.]+)'
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, crash_content, re.IGNORECASE)
                if match:
                    ios_version = match.group(1)
                    logger.info(f"Found iOS version via pattern: {ios_version}")
                    break
        
        # Update file_info with potentially improved data
        file_info['device_model'] = device_model
        file_info['ios_version'] = ios_version
        
        # Make request to symbol server
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{SYMBOL_SERVER_URL}/v1/symbolicate",
                json={
                    "crash_content": crash_content,
                    "ios_version": ios_version,
                    "device_model": device_model
                }
            )
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success', False):
                    symbolicated_output = api_result.get('symbolicated_crash', crash_content)
                    
                    # Enhanced success message with file info
                    message = f"Symbolication completed successfully"
                    if file_info.get("is_ips_format"):
                        message += f" for IPS file"
                    if file_info.get("process_name"):
                        message += f" (Process: {file_info['process_name']})"
                    if device_model != "unknown":
                        message += f" on {device_model}"
                    if ios_version != "unknown":
                        message += f" iOS {ios_version}"
                    
                    return SymbolicationResult(
                        success=True,
                        message=message,
                        symbolicated_output=symbolicated_output,
                        analysis_id=analysis_id,
                        file_info=file_info,  # Add file info to result
                        total_time=api_result.get('processing_time', 0)
                    )
                else:
                    # Handle cases where server returns 200 but success=false
                    error_msg = api_result.get('message', 'Unknown error')
                    if 'No symbols found' in error_msg or 'symbols not available' in error_msg:
                        error_msg = f"אין סימבולים זמינים עבור {device_model} iOS {ios_version}. "
                        if build_version != "unknown":
                            error_msg += f"Build {build_version}. "
                        error_msg += "יש להוסיף קובץ IPSW מתאים למערכת או לבדוק שפרטי המכשיר נכונים."
                    
                    return SymbolicationResult(
                        success=False,
                        message=error_msg,
                        symbolicated_output=crash_content,
                        analysis_id=analysis_id,
                        file_info=file_info,
                        total_time=api_result.get('processing_time', 0)
                    )
            else:
                return SymbolicationResult(
                    success=False,
                    message=f"שגיאת שרת סימבולים: HTTP {response.status_code}",
                    symbolicated_output=crash_content,
                    analysis_id=analysis_id,
                    file_info=file_info
                )
                
    except Exception as e:
        logger.error(f"Symbolication error: {e}")
        return SymbolicationResult(
            success=False,
            message=f"Connection error: {str(e)}",
            symbolicated_output=crash_content,
            analysis_id=analysis_id,
            file_info=parse_ips_file(crash_content)
        )

# Web UI Routes
@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def web_ui_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ui/upload")
async def web_ui_upload(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "לא נבחר קובץ"
        })
    
    if not allowed_file(file.filename):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "סוג קובץ לא תקין"
        })
    
    try:
        content = await file.read()
        crash_content = content.decode('utf-8', errors='ignore')
        
        result = await symbolicate_via_api(crash_content)
        result_dict = result.model_dump()
        
        # Save results
        results_file = TEMP_DIR / f"{result.analysis_id}_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": result,
            "result_dict": result_dict,
            "original_filename": file.filename
        })
        
    except Exception as e:
        logger.error(f"Error processing file upload: {e}", exc_info=True)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"שגיאת עיבוד: {str(e)}"
        })

@app.get("/ui/download/{analysis_id}")
async def download_results(analysis_id: str):
    """Download results as JSON file"""
    try:
        results_file = TEMP_DIR / f"{analysis_id}_results.json"
        
        if not results_file.exists():
            raise HTTPException(status_code=404, detail="Results not found")
        
        return FileResponse(
            path=str(results_file),
            filename=f"symbolication_results_{analysis_id}.json",
            media_type='application/json'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

# API Routes
@app.post("/symbolicate", response_model=SymbolicationResult)
async def symbolicate_file(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    content = await file.read()
    crash_content = content.decode('utf-8', errors='ignore')
    
    return await symbolicate_via_api(crash_content)

@app.post("/auto-scan", response_model=AutoScanResult)
async def auto_scan(request: AutoScanRequest):
    """Auto-scan for IPSW files matching the device and iOS version"""
    if not s3_manager:
        raise HTTPException(status_code=503, detail="S3 manager not available")
    
    try:
        logger.info(f"Auto-scan request: {request.device_model} {request.ios_version} {request.build_number}")
        
        # Search for matching IPSW file
        file_info = await s3_manager.find_ipsw(
            device_model=request.device_model,
            os_version=request.ios_version,
            build_number=request.build_number
        )
        
        if file_info:
            logger.info(f"Found matching IPSW: {file_info}")
            
            # Check if we should start download
            download_id = str(uuid.uuid4())[:8]
            
            # Start download in background
            download_success, download_message, local_path = await s3_manager.download_ipsw(
                device_model=request.device_model,
                os_version=request.ios_version,
                build_number=request.build_number
            )
            
            return AutoScanResult(
                success=download_success,
                message=f"נמצא קובץ IPSW מתאים: {file_info['key']}. {download_message}",
                found_files=[{
                    "filename": file_info['key'],
                    "device": file_info['device'],
                    "version": file_info['version'],
                    "build": file_info['build'],
                    "size_mb": file_info['size'] // (1024 * 1024) if file_info['size'] > 0 else 0,
                    "url": file_info['url'],
                    "local_path": local_path if download_success else None
                }],
                download_started=download_success,
                download_id=download_id
            )
        else:
            # List available files for debugging
            available_files = await s3_manager.list_available_ipsw()
            logger.info(f"No matching IPSW found. Available files: {len(available_files)}")
            
            return AutoScanResult(
                success=False,
                message=f"לא נמצא קובץ IPSW עבור {request.device_model} iOS {request.ios_version}",
                found_files=[{
                    "filename": f['filename'],
                    "device": f['device'],
                    "version": f['version'],
                    "build": f['build'],
                    "size_mb": f['size_mb']
                } for f in available_files[:10]]  # Show first 10 available files
            )
            
    except Exception as e:
        logger.error(f"Auto-scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-scan error: {str(e)}")

@app.post("/download-ipsw")
async def download_ipsw_endpoint(request: AutoScanRequest):
    """Download IPSW file directly"""
    if not s3_manager:
        raise HTTPException(status_code=503, detail="S3 manager not available")
    
    try:
        logger.info(f"Download request: {request.device_model} {request.ios_version} {request.build_number}")
        
        download_success, download_message, local_path = await s3_manager.download_ipsw(
            device_model=request.device_model,
            os_version=request.ios_version,
            build_number=request.build_number
        )
        
        return {
            "success": download_success,
            "message": download_message,
            "local_path": local_path,
            "download_id": str(uuid.uuid4())[:8]
        }
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

@app.get("/download-status/{download_id}")
async def get_download_status(download_id: str):
    """Get download status (placeholder for future implementation)"""
    # For now, return a simple status
    return {
        "download_id": download_id,
        "status": "completed",
        "message": "Download completed successfully"
    }

@app.get("/auto-scan")
async def auto_scan_get(device_model: str, ios_version: str, build_number: Optional[str] = None):
    """GET version of auto-scan for easier testing"""
    request = AutoScanRequest(
        device_model=device_model,
        ios_version=ios_version,
        build_number=build_number
    )
    return await auto_scan(request)

@app.get("/available-ipsw")
async def list_available_ipsw():
    """List all available IPSW files in S3"""
    if not s3_manager:
        raise HTTPException(status_code=503, detail="S3 manager not available")
    
    try:
        files = await s3_manager.list_available_ipsw()
        return {
            "success": True,
            "total_files": len(files),
            "files": files
        }
    except Exception as e:
        logger.error(f"Error listing IPSW files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0"}

@app.get("/api/status")
async def api_status():
    """Check if symbolication API is available"""
    try:
        # Check if symbol server is responding
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{SYMBOL_SERVER_URL}/health")
            if response.status_code == 200:
                return {
                    "status": "online",
                    "api_url": SYMBOL_SERVER_URL,
                    "version": "3.0.0"
                }
            else:
                return {
                    "status": "error", 
                    "api_url": SYMBOL_SERVER_URL,
                    "message": f"Symbol server returned status {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "offline",
            "api_url": SYMBOL_SERVER_URL,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 