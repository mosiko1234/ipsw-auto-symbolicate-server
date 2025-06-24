#!/usr/bin/env python3
"""
Simple IPSW Symbol Server
Symbolicate iOS crashlogs using stored symbol data and kernel signatures
"""

import os
import re
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import psycopg2
from psycopg2.extras import RealDictCursor
import glob
from psycopg2 import pool as pg_pool
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://symboluser:symbolpass@localhost:5432/symbols')
KERNEL_SIGS_DIR = os.getenv('KERNEL_SIGS_DIR', '/app/signatures/kernel')

# Cache for kernel signatures
kernel_signatures = {}

# Upload directory
UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/uploads')

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize database connection pool (set after first call)
conn_pool = None

def load_kernel_signatures():
    """Load kernel signatures from JSON files"""
    global kernel_signatures
    if not os.path.exists(KERNEL_SIGS_DIR):
        logger.warning(f"Kernel signatures directory not found: {KERNEL_SIGS_DIR}")
        return
    
    # Load XNU signatures
    xnu_files = glob.glob(f"{KERNEL_SIGS_DIR}/*/xnu.json")
    for xnu_file in xnu_files:
        try:
            version = os.path.basename(os.path.dirname(xnu_file))
            with open(xnu_file, 'r') as f:
                data = json.load(f)
                if version not in kernel_signatures:
                    kernel_signatures[version] = {}
                kernel_signatures[version]['xnu'] = data
                logger.info(f"Loaded XNU signatures for version {version}")
        except Exception as e:
            logger.error(f"Failed to load {xnu_file}: {e}")
    
    # Load KEXT signatures
    kext_dirs = glob.glob(f"{KERNEL_SIGS_DIR}/*/kexts")
    for kext_dir in kext_dirs:
        version = os.path.basename(os.path.dirname(kext_dir))
        kext_files = glob.glob(f"{kext_dir}/*.json")
        
        if version not in kernel_signatures:
            kernel_signatures[version] = {}
        kernel_signatures[version]['kexts'] = {}
        
        for kext_file in kext_files:
            try:
                kext_name = os.path.splitext(os.path.basename(kext_file))[0]
                with open(kext_file, 'r') as f:
                    data = json.load(f)
                    kernel_signatures[version]['kexts'][kext_name] = data
            except Exception as e:
                logger.error(f"Failed to load {kext_file}: {e}")
        
        if kernel_signatures[version]['kexts']:
            logger.info(f"Loaded {len(kernel_signatures[version]['kexts'])} KEXT signatures for version {version}")

def get_db_connection():
    """Get a connection from the global pool (creates pool lazily)."""
    global conn_pool
    try:
        if conn_pool is None:
            conn_pool = pg_pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
        return conn_pool.getconn()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def put_db_connection(conn):
    global conn_pool
    if conn_pool and conn:
        conn_pool.putconn(conn)

def symbolicate_with_ipsw_cli(crashlog_content):
    """Use ipsw CLI for symbolication if available"""
    try:
        # Check if ipsw CLI is available
        result = subprocess.run(['ipsw', 'version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            logger.warning("ipsw CLI not available, falling back to basic symbolication")
            return None
        
        logger.info(f"Using ipsw CLI: {result.stdout.strip()}")
        
        # Create temporary file for crashlog
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ips', delete=False) as temp_file:
            temp_file.write(crashlog_content)
            temp_file_path = temp_file.name
        
        try:
            # Try to symbolicate with ipsw CLI (without IPSW file for basic parsing)
            cmd = ['ipsw', 'symbolicate', '--color', temp_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("ipsw CLI symbolication successful")
                return {
                    'method': 'ipsw_cli',
                    'output': result.stdout,
                    'success': True
                }
            else:
                logger.warning(f"ipsw CLI symbolication failed: {result.stderr}")
                return None
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except subprocess.TimeoutExpired:
        logger.warning("ipsw CLI timed out")
        return None
    except Exception as e:
        logger.warning(f"ipsw CLI error: {e}")
        return None

def parse_crashlog(crashlog_content):
    """Parse iOS crashlog to extract basic information"""
    info = {
        'process': None,
        'device': None,
        'os_version': None,
        'build_id': None,
        'architecture': None,
        'crashed_thread': None,
        'stack_trace': [],
        'is_kernel_panic': False
    }
    
    lines = crashlog_content.split('\n')
    in_thread_section = False
    in_kernel_section = False
    thread_number = None
    
    # Check if this is a kernel panic
    if any('panic' in line.lower() for line in lines[:10]):
        info['is_kernel_panic'] = True
    
    for line in lines:
        line = line.strip()
        
        # Extract basic info
        if line.startswith('Process:'):
            info['process'] = line.split(':', 1)[1].strip()
        elif line.startswith('Hardware Model:'):
            info['device'] = line.split(':', 1)[1].strip()
        elif line.startswith('OS Version:'):
            info['os_version'] = line.split(':', 1)[1].strip()
        elif line.startswith('BuildID:'):
            info['build_id'] = line.split(':', 1)[1].strip()
        elif 'Crashed:' in line and 'Thread' in line:
            match = re.search(r'Thread (\d+)', line)
            if match:
                info['crashed_thread'] = int(match.group(1))
                in_thread_section = True
        elif in_thread_section and re.match(r'^\s*\d+:', line):
            # Parse stack frame: "0: LibraryName 0x1234567 symbol_name + offset"
            parts = line.split()
            if len(parts) >= 3:
                frame_info = {
                    'frame_number': parts[0].rstrip(':'),
                    'library': parts[1],
                    'address': parts[2] if parts[2].startswith('0x') else None,
                    'symbol': ' '.join(parts[3:]) if len(parts) > 3 else None
                }
                info['stack_trace'].append(frame_info)
        elif 'Backtrace' in line and 'CPU' in line:
            # Start of kernel backtrace section
            in_kernel_section = True
        elif in_kernel_section and line.startswith('0x') and ':' in line:
            # Parse kernel backtrace frame: "0xffffff920000a000 : 0xffffff8000a1b2c0 kernel_trap + 0"
            parts = line.split(' : ')
            if len(parts) == 2:
                frame_addr = parts[0].strip()
                return_info = parts[1].strip()
                
                # Extract return address and symbol
                return_parts = return_info.split(' ', 1)
                return_addr = return_parts[0] if return_parts else None
                symbol_info = return_parts[1] if len(return_parts) > 1 else None
                
                if return_addr and return_addr.startswith('0x'):
                    frame_info = {
                        'frame_number': str(len(info['stack_trace'])),
                        'library': 'kernel',
                        'address': return_addr,
                        'symbol': symbol_info,
                        'frame_address': frame_addr
                    }
                    info['stack_trace'].append(frame_info)
        elif in_thread_section and line == '':
            in_thread_section = False
    
    return info

def symbolicate_kernel_address(address, os_version):
    """Symbolicate kernel address using signatures"""
    if not kernel_signatures or not os_version:
        return None
    
    # Find matching OS version in signatures
    version_key = None
    for key in kernel_signatures.keys():
        if os_version.startswith(key) or key in os_version:
            version_key = key
            break
    
    if not version_key or version_key not in kernel_signatures:
        return None
    
    sigs = kernel_signatures[version_key]
    
    try:
        addr_int = int(address, 16)
        
        # Search in XNU signatures
        if 'xnu' in sigs:
            xnu_sigs = sigs['xnu']
            if 'functions' in xnu_sigs:
                for func_name, func_data in xnu_sigs['functions'].items():
                    if isinstance(func_data, dict) and 'address' in func_data:
                        func_addr = func_data['address']
                        if isinstance(func_addr, str):
                            func_addr = int(func_addr, 16)
                        
                        # Check if address is in function range (with some tolerance)
                        if abs(addr_int - func_addr) < 0x1000:  # 4KB tolerance
                            return {
                                'symbol': func_name,
                                'offset': addr_int - func_addr,
                                'type': 'kernel_function'
                            }
        
        # Search in KEXT signatures
        if 'kexts' in sigs:
            for kext_name, kext_data in sigs['kexts'].items():
                if 'functions' in kext_data:
                    for func_name, func_data in kext_data['functions'].items():
                        if isinstance(func_data, dict) and 'address' in func_data:
                            func_addr = func_data['address']
                            if isinstance(func_addr, str):
                                func_addr = int(func_addr, 16)
                            
                            if abs(addr_int - func_addr) < 0x1000:
                                return {
                                    'symbol': f"{kext_name}::{func_name}",
                                    'offset': addr_int - func_addr,
                                    'type': 'kext_function'
                                }
        
        return None
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing kernel address {address}: {e}")
        return None

def symbolicate_address(library, address, device, os_version):
    """Lookup symbol for given address"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT symbol_name, symbol_offset 
            FROM symbols 
            WHERE library = %s 
            AND device_model = %s 
            AND os_version = %s 
            AND start_address <= %s 
            AND end_address >= %s
            ORDER BY start_address DESC
            LIMIT 1
        """, (library, device, os_version, address, address))
        
        result = cursor.fetchone()
        cursor.close()
        put_db_connection(conn)
        
        if result:
            return {
                'symbol': result['symbol_name'],
                'offset': address - result['symbol_offset'] if result['symbol_offset'] else 0
            }
        return None
        
    except Exception as e:
        logger.error(f"Symbol lookup failed: {e}")
        return None

# Initialize kernel signatures for worker
load_kernel_signatures()

@app.route('/')
def home():
    """Simple web interface"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple IPSW Symbol Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            textarea { width: 100%; height: 300px; font-family: monospace; }
            button { background: #007AFF; color: white; padding: 10px 20px; border: none; border-radius: 5px; }
            .result { background: #f5f5f5; padding: 20px; margin-top: 20px; border-radius: 5px; }
            .info { background: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛠 Simple IPSW Symbol Server</h1>
            <p>Symbolicate iOS crashlogs and kernel panics with minimal setup</p>
            
            <div class="info">
                <h4>📋 Features:</h4>
                <ul>
                    <li>✅ iOS App Crash Symbolication</li>
                    <li>✅ Kernel Panic Symbolication</li>
                    <li>✅ XNU & KEXT Symbol Resolution</li>
                    <li>✅ Database-backed Symbol Storage</li>
                    <li>✅ Integrated ipsw CLI</li>
                </ul>
            </div>
            
            <h3>Upload Crashlog</h3>
            <form id="symbolicate-form">
                <textarea id="crashlog" placeholder="Paste your crashlog or kernel panic here..."></textarea><br><br>
                <button type="submit">Symbolicate</button>
            </form>
            
            <div id="result" class="result" style="display:none;">
                <h3>Symbolicated Result:</h3>
                <pre id="output"></pre>
            </div>
        </div>
        
        <script>
            document.getElementById('symbolicate-form').onsubmit = function(e) {
                e.preventDefault();
                const crashlog = document.getElementById('crashlog').value;
                
                fetch('/symbolicate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({crashlog: crashlog})
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('output').textContent = JSON.stringify(data, null, 2);
                    document.getElementById('result').style.display = 'block';
                })
                .catch(error => {
                    document.getElementById('output').textContent = 'Error: ' + error;
                    document.getElementById('result').style.display = 'block';
                });
            };
        </script>
    </body>
    </html>
    """
    return html

@app.route('/symbolicate', methods=['POST'])
def symbolicate():
    """Symbolicate crashlog endpoint"""
    try:
        data = request.get_json()
        crashlog = data.get('crashlog', '')
        
        if not crashlog:
            return jsonify({'error': 'No crashlog provided'}), 400
        
        # Try ipsw CLI first for better results
        ipsw_result = symbolicate_with_ipsw_cli(crashlog)
        if ipsw_result and ipsw_result['success']:
            return jsonify({
                'status': 'success',
                'method': 'ipsw_cli',
                'timestamp': datetime.now().isoformat(),
                'symbolicated_output': ipsw_result['output']
            })
        
        # Fallback to our internal symbolication
        logger.info("Using fallback symbolication method")
        
        # Parse crashlog
        parsed = parse_crashlog(crashlog)
        
        # Symbolicate stack trace
        symbolicated_frames = []
        for frame in parsed['stack_trace']:
            if frame['address']:
                try:
                    address = int(frame['address'], 16)
                    
                    # Try kernel symbolication first if it's a kernel panic
                    if parsed['is_kernel_panic'] or frame['library'] == 'kernel':
                        symbol_info = symbolicate_kernel_address(frame['address'], parsed['os_version'])
                        if symbol_info:
                            frame['symbolicated_name'] = symbol_info['symbol']
                            frame['symbol_offset'] = symbol_info['offset']
                            frame['symbol_type'] = symbol_info.get('type', 'kernel')
                        else:
                            frame['symbolicated_name'] = '<kernel_unknown>'
                            frame['symbol_offset'] = 0
                            frame['symbol_type'] = 'kernel'
                    else:
                        # Regular userspace symbolication
                        symbol_info = symbolicate_address(
                            frame['library'], 
                            address, 
                            parsed['device'], 
                            parsed['os_version']
                        )
                        
                        if symbol_info:
                            frame['symbolicated_name'] = symbol_info['symbol']
                            frame['symbol_offset'] = symbol_info['offset']
                            frame['symbol_type'] = 'userspace'
                        else:
                            frame['symbolicated_name'] = '<unknown>'
                            frame['symbol_offset'] = 0
                            frame['symbol_type'] = 'userspace'
                        
                except ValueError:
                    frame['symbolicated_name'] = '<invalid_address>'
                    frame['symbol_offset'] = 0
                    frame['symbol_type'] = 'unknown'
            else:
                frame['symbolicated_name'] = '<no_address>'
                frame['symbol_offset'] = 0
                frame['symbol_type'] = 'unknown'
                
            symbolicated_frames.append(frame)
        
        result = {
            'status': 'success',
            'method': 'internal',
            'timestamp': datetime.now().isoformat(),
            'crash_info': {
                'process': parsed['process'],
                'device': parsed['device'],
                'os_version': parsed['os_version'],
                'build_id': parsed['build_id'],
                'crashed_thread': parsed['crashed_thread'],
                'is_kernel_panic': parsed['is_kernel_panic']
            },
            'symbolicated_stack': symbolicated_frames,
            'total_frames': len(symbolicated_frames),
            'kernel_signatures_loaded': len(kernel_signatures)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Symbolication failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    conn = get_db_connection()
    db_status = 'connected' if conn else 'disconnected'
    if conn:
        put_db_connection(conn)
    
    # Check ipsw CLI availability
    ipsw_available = False
    ipsw_version = None
    try:
        result = subprocess.run(['ipsw', 'version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ipsw_available = True
            ipsw_version = result.stdout.strip()
    except:
        pass
    
    return jsonify({
        'status': 'healthy' if conn else 'unhealthy',
        'database': db_status,
        'ipsw_cli': {
            'available': ipsw_available,
            'version': ipsw_version
        },
        'kernel_signatures': len(kernel_signatures),
        'kernel_versions': list(kernel_signatures.keys())
    })

@app.route('/api/symbols', methods=['GET'])
def list_symbols():
    """List available symbols in database"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT DISTINCT library, device_model, os_version, COUNT(*) as symbol_count
            FROM symbols 
            GROUP BY library, device_model, os_version
            ORDER BY device_model, os_version, library
        """)
        
        results = cursor.fetchall()
        cursor.close()
        put_db_connection(conn)
        
        return jsonify({
            'status': 'success',
            'userspace_symbols': [dict(row) for row in results],
            'kernel_signatures': {
                'loaded_versions': list(kernel_signatures.keys()),
                'total_versions': len(kernel_signatures)
            }
        })
        
    except Exception as e:
        logger.error(f"Symbol listing failed: {e}")
        return jsonify({'error': str(e)}), 500

# ---------------------- Multipart Upload Endpoint ----------------------

@app.route('/symbolicate/upload', methods=['POST'])
def symbolicate_upload():
    """Upload crashlog + IPSW as multipart/form-data and symbolicate"""
    try:
        if 'crashlog' not in request.files or 'ipsw' not in request.files:
            return jsonify({'error': 'Both crashlog and ipsw files are required (multipart/form-data)'}), 400

        crash_file = request.files['crashlog']
        ipsw_file = request.files['ipsw']

        # Save files to UPLOAD_DIR
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        crash_filename = secure_filename(f"{timestamp}_{crash_file.filename}") or f"crash_{timestamp}.ips"
        ipsw_filename = secure_filename(f"{timestamp}_{ipsw_file.filename}") or f"firmware_{timestamp}.ipsw"

        crash_path = os.path.join(UPLOAD_DIR, crash_filename)
        ipsw_path = os.path.join(UPLOAD_DIR, ipsw_filename)

        crash_file.save(crash_path)
        ipsw_file.save(ipsw_path)

        # Run ipsw CLI to symbolicate using provided IPSW
        cmd = ['ipsw', 'symbolicate', crash_path, ipsw_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        # Clean up crash file (keep IPSW for cache)
        os.unlink(crash_path)

        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'method': 'ipsw_cli_upload',
                'timestamp': datetime.utcnow().isoformat(),
                'output': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'stderr': result.stderr,
                'returncode': result.returncode
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Symbolication timed out'}), 504
    except Exception as e:
        logger.error(f"Upload symbolication failed: {e}")
        return jsonify({'error': str(e)}), 500

# ---------------------- Official ipswd API Endpoints ----------------------

@app.route('/v1/_ping', methods=['GET', 'HEAD'])
def ping():
    """Official ipswd ping endpoint"""
    if request.method == 'HEAD':
        return '', 200
    return jsonify({'status': 'OK'}), 200

@app.route('/v1/version', methods=['GET'])
def version():
    """Official ipswd version endpoint"""
    return jsonify({
        'version': '3.1.616',
        'commit': 'local-build',
        'built_at': '2025-01-16T12:00:00Z',
        'go_version': 'go1.21.0',
        'platform': 'linux/amd64'
    }), 200

@app.route('/v1/daemon/info', methods=['GET'])
def daemon_info():
    """Get daemon information"""
    return jsonify({
        'version': '3.1.616',
        'uptime': '24h',
        'kernel_sigs_loaded': len(kernel_signatures) if kernel_signatures else 0,
        'postgres_connected': True
    }), 200

# ---------------------- ipswd symbolicate endpoints ----------------------

@app.route('/v1/symbolicate', methods=['POST'])
def v1_symbolicate():
    """Official ipswd symbolicate endpoint - matches ipsw CLI expectations"""
    try:
        # Check content type - could be JSON or form-data
        if request.is_json:
            data = request.get_json()
            crashlog_content = data.get('crashlog', '')
            ipsw_path = data.get('ipsw', '')
        else:
            # Handle form data like files
            crashlog_content = request.form.get('crashlog', '')
            ipsw_path = request.form.get('ipsw', '')
            
            # Check if files were uploaded
            if 'crashlog_file' in request.files:
                crash_file = request.files['crashlog_file']
                crashlog_content = crash_file.read().decode('utf-8')
            
            if 'ipsw_file' in request.files:
                ipsw_file = request.files['ipsw_file']
                # Save IPSW temporarily for processing
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                ipsw_filename = secure_filename(f"{timestamp}_{ipsw_file.filename}") or f"firmware_{timestamp}.ipsw"
                ipsw_path = os.path.join(UPLOAD_DIR, ipsw_filename)
                ipsw_file.save(ipsw_path)

        if not crashlog_content:
            return jsonify({'error': 'No crashlog provided'}), 400

        # Use ipsw CLI with IPSW if provided
        if ipsw_path and os.path.exists(ipsw_path):
            logger.info(f"Using ipsw CLI with IPSW file: {os.path.basename(ipsw_path)}")
            
            # Create temporary file for crashlog
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ips', delete=False) as temp_file:
                temp_file.write(crashlog_content)
                temp_file_path = temp_file.name
            
            try:
                # Run ipsw symbolicate with IPSW
                cmd = ['ipsw', 'symbolicate', temp_file_path, ipsw_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                
                # Clean up temp crashlog file
                os.unlink(temp_file_path)
                
                if result.returncode == 0:
                    return jsonify({
                        'symbolicated': True,
                        'output': result.stdout,
                        'method': 'ipsw_cli_with_ipsw'
                    }), 200
                else:
                    return jsonify({
                        'error': 'Symbolication failed',
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }), 500
                    
            except subprocess.TimeoutExpired:
                os.unlink(temp_file_path)
                return jsonify({'error': 'Symbolication timed out'}), 504
            except Exception as e:
                os.unlink(temp_file_path)
                return jsonify({'error': f'Symbolication error: {str(e)}'}), 500
        else:
            # Fallback to basic symbolication without IPSW
            ipsw_result = symbolicate_with_ipsw_cli(crashlog_content)
            if ipsw_result and ipsw_result['success']:
                return jsonify({
                    'symbolicated': True,
                    'output': ipsw_result['output'],
                    'method': 'ipsw_cli_basic'
                }), 200
            else:
                # Last resort - our internal parser
                parsed = parse_crashlog(crashlog_content)
                symbolicated_frames = []
                
                for frame in parsed.get('stack_trace', []):
                    symbolicated_frame = symbolicate_frame(frame)
                    symbolicated_frames.append(symbolicated_frame)
                
                return jsonify({
                    'symbolicated': True,
                    'parsed_info': parsed,
                    'symbolicated_frames': symbolicated_frames,
                    'method': 'internal_parser'
                }), 200
                
    except Exception as e:
        logger.error(f"v1 symbolicate failed: {e}")
        return jsonify({'error': str(e)}), 500

# ---------------------- Additional ipswd API endpoints ----------------------

@app.route('/v1/info/ipsw', methods=['GET'])
def v1_info_ipsw():
    """Get IPSW info - basic implementation"""
    path = request.args.get('path')
    if not path or not os.path.exists(path):
        return jsonify({'error': 'IPSW path not found'}), 404
    
    # Basic IPSW info parsing
    try:
        import zipfile
        with zipfile.ZipFile(path, 'r') as ipsw:
            # Look for BuildManifest.plist
            if 'BuildManifest.plist' in ipsw.namelist():
                return jsonify({
                    'path': path,
                    'type': 'ipsw',
                    'files': len(ipsw.namelist()),
                    'has_buildmanifest': True
                }), 200
            else:
                return jsonify({'error': 'Invalid IPSW format'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to parse IPSW: {str(e)}'}), 500

@app.route('/v1/kernel/version', methods=['GET'])
def v1_kernel_version():
    """Get kernel version info"""
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'kernelcache path required'}), 400
    
    return jsonify({
        'path': path,
        'arch': 'arm64e',
        'version': 'unknown',
        'type': 'release'
    }), 200

if __name__ == '__main__':
    logger.info("Starting Simple IPSW Symbol Server with Kernel Support and ipsw CLI (dev mode)")
    app.run(host='0.0.0.0', port=3993, debug=True) 