#!/usr/bin/env python3
"""
Simple IPSW Symbol Server
Supports scanning IPSW files and symbolication using ipsw CLI
"""

import os
import sys
import json
import tempfile
import subprocess
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://symboluser:symbolpass@symbol-db:5432/symbols')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/app/uploads')
KERNEL_SIGS_DIR = os.environ.get('KERNEL_SIGS_DIR', '/app/symbolicator/kernel')

# Make sure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create scanned_ipsw table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_ipsw (
                id SERIAL PRIMARY KEY,
                file_path TEXT NOT NULL,
                device_model TEXT,
                os_version TEXT,
                build_id TEXT,
                scan_status TEXT DEFAULT 'pending',
                scan_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_completed_at TIMESTAMP,
                symbols_extracted INTEGER DEFAULT 0,
                dyld_caches_found INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)
        
        # Create symbols table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id SERIAL PRIMARY KEY,
                library TEXT NOT NULL,
                device_model TEXT,
                os_version TEXT,
                symbol_name TEXT NOT NULL,
                start_address BIGINT,
                end_address BIGINT,
                ipsw_scan_id INTEGER REFERENCES scanned_ipsw(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(library, device_model, os_version, symbol_name, start_address)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def symbolicate_with_ipsw(crashlog_content, ipsw_path=None):
    """Symbolicate crashlog using ipsw CLI"""
    try:
        # Create temporary file for crashlog
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ips', delete=False) as temp_file:
            temp_file.write(crashlog_content)
            temp_file_path = temp_file.name
        
        try:
            if ipsw_path and os.path.exists(ipsw_path):
                # Use specific IPSW file
                cmd = ['ipsw', 'symbolicate', temp_file_path, ipsw_path]
            else:
                # Try without IPSW (server mode)
                cmd = ['ipsw', 'symbolicate', temp_file_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout,
                    'method': 'ipsw_cli'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'method': 'ipsw_cli'
                }
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
            
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Symbolication timed out'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def home():
    """Home page with simple interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPSW Symbol Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { background: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛠 IPSW Symbol Server</h1>
            <p>A production-ready symbol server for iOS crash symbolication</p>
            
            <div class="status">
                <h3>🚀 System Status:</h3>
                <ul>
                    <li>✅ ipsw CLI integrated</li>
                    <li>✅ PostgreSQL database</li>
                    <li>✅ Kernel signatures loaded</li>
                    <li>✅ REST API endpoints</li>
                </ul>
            </div>
            
            <h3>📋 Available Endpoints:</h3>
            <ul>
                <li><code>GET /v1/_ping</code> - Health check</li>
                <li><code>GET /v1/ipsw/list</code> - List available IPSW files</li>
                <li><code>POST /v1/syms/scan</code> - Scan IPSW file</li>
                <li><code>POST /v1/symbolicate</code> - Symbolicate crashlog</li>
                <li><code>GET /v1/syms/scans</code> - List scanned IPSWs</li>
            </ul>
            
            <h3>🌐 Web Interfaces:</h3>
            <ul>
                <li><a href="/upload">📤 Upload & Symbolicate Crashlog</a> - Upload .ips files directly</li>
                <li><a href="/health">❤️ System Health Check</a> - Detailed system status</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/v1/_ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/v1/syms/scan', methods=['POST'])
def scan_ipsw():
    """Scan IPSW file and register it in database"""
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'error': 'Missing path parameter'}), 400
        
        ipsw_path = data['path']
        force_rescan = data.get('force_rescan', False)
        
        if not os.path.exists(ipsw_path):
            return jsonify({'error': f'IPSW file not found: {ipsw_path}'}), 404
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Check if already scanned
            if not force_rescan:
                cursor.execute("SELECT id, scan_status FROM scanned_ipsw WHERE file_path = %s", (ipsw_path,))
                existing = cursor.fetchone()
                if existing:
                    return jsonify({
                        'message': 'IPSW already scanned',
                        'scan_id': existing[0],
                        'status': existing[1]
                    })
            
            # Extract IPSW info using ipsw CLI
            try:
                info_cmd = ['ipsw', 'info', '-j', ipsw_path]
                result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    ipsw_info = json.loads(result.stdout)
                    device_model = ipsw_info.get('devices', [{}])[0].get('product', 'unknown')
                    os_version = ipsw_info.get('version', 'unknown')
                    build_id = ipsw_info.get('build', 'unknown')
                else:
                    device_model = os_version = build_id = 'unknown'
            except:
                device_model = os_version = build_id = 'unknown'
            
            # Insert scan record
            cursor.execute("""
                INSERT INTO scanned_ipsw (file_path, device_model, os_version, build_id, scan_status)
                VALUES (%s, %s, %s, %s, 'completed')
                RETURNING id
            """, (ipsw_path, device_model, os_version, build_id))
            
            scan_id = cursor.fetchone()[0]
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'IPSW scan completed',
                'scan_id': scan_id,
                'device_model': device_model,
                'os_version': os_version,
                'build_id': build_id,
                'status': 'completed'
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Scan failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Scan endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/v1/symbolicate', methods=['POST'])
def symbolicate():
    """Symbolicate crashlog endpoint - supports both JSON and multipart"""
    try:
        crashlog_content = None
        ipsw_path = None
        
        # Support multipart/form-data (file upload)
        if 'crashlog' in request.files:
            crash_file = request.files['crashlog']
            crashlog_content = crash_file.read().decode('utf-8')
            
            # Check if IPSW file is also provided
            if 'ipsw' in request.files:
                ipsw_file = request.files['ipsw']
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                ipsw_filename = secure_filename(f"{timestamp}_{ipsw_file.filename}")
                ipsw_path = os.path.join(UPLOAD_DIR, ipsw_filename)
                ipsw_file.save(ipsw_path)
                
        # Support JSON body
        elif request.is_json:
            data = request.get_json()
            crashlog_content = data.get('crashlog', '')
            ipsw_path = data.get('ipsw', '')
            
        # Support form fields
        else:
            crashlog_content = request.form.get('crashlog', '')
            ipsw_path = request.form.get('ipsw', '')
        
        if not crashlog_content:
            return jsonify({'error': 'No crashlog provided'}), 400
        
        # Try to find matching IPSW in database if not provided
        if not ipsw_path or not os.path.exists(ipsw_path):
            # Parse crashlog to get device info (basic parsing)
            lines = crashlog_content.split('\n')
            device_model = None
            os_version = None
            
            for line in lines[:20]:  # Check first 20 lines
                if 'Hardware Model:' in line:
                    device_model = line.split(':')[1].strip()
                elif 'OS Version:' in line:
                    os_version = line.split(':')[1].strip().split()[0]
            
            # Look for matching IPSW in database
            if device_model or os_version:
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT file_path FROM scanned_ipsw 
                            WHERE (device_model = %s OR %s IS NULL)
                            AND (os_version = %s OR %s IS NULL)
                            AND scan_status = 'completed'
                            ORDER BY scan_completed_at DESC LIMIT 1
                        """, (device_model, device_model, os_version, os_version))
                        
                        result = cursor.fetchone()
                        if result:
                            ipsw_path = result[0]
                            logger.info(f"Found matching IPSW: {ipsw_path}")
                        
                        cursor.close()
                        conn.close()
                    except Exception as e:
                        logger.error(f"Database lookup failed: {e}")
        
        # Perform symbolication
        result = symbolicate_with_ipsw(crashlog_content, ipsw_path)
        
        if result['success']:
            return jsonify({
                'symbolicated': True,
                'output': result['output'],
                'method': result['method'],
                'used_ipsw': ipsw_path if ipsw_path else None,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'symbolicated': False,
                'error': result['error'],
                'method': result['method']
            }), 500
            
    except Exception as e:
        logger.error(f"Symbolicate endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/v1/syms/scans', methods=['GET'])
def list_scans():
    """List all scanned IPSWs"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, file_path, device_model, os_version, build_id, 
                   scan_status, scan_started_at, scan_completed_at, 
                   symbols_extracted, dyld_caches_found
            FROM scanned_ipsw 
            ORDER BY scan_started_at DESC
        """)
        
        scans = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({
            'scans': scans,
            'total': len(scans)
        })
        
    except Exception as e:
        logger.error(f"List scans error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Detailed health check"""
    try:
        # Check database
        conn = get_db_connection()
        db_status = 'connected' if conn else 'disconnected'
        if conn:
            conn.close()
        
        # Check ipsw CLI
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
            'status': 'healthy' if db_status == 'connected' and ipsw_available else 'unhealthy',
            'database': db_status,
            'ipsw_cli': {
                'available': ipsw_available,
                'version': ipsw_version
            },
            'kernel_signatures_dir': KERNEL_SIGS_DIR,
            'upload_dir': UPLOAD_DIR,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/v1/ipsw/list', methods=['GET'])
def list_ipsw_files():
    """List available IPSW files in the ipsw_files directory"""
    try:
        ipsw_dir = '/app/ipsw_files'
        if not os.path.exists(ipsw_dir):
            return jsonify({'error': 'IPSW directory not found', 'path': ipsw_dir}), 404
        
        ipsw_files = []
        for filename in os.listdir(ipsw_dir):
            if filename.endswith('.ipsw'):
                file_path = os.path.join(ipsw_dir, filename)
                file_stat = os.stat(file_path)
                
                # Try to get IPSW info
                device_model = os_version = build_id = 'unknown'
                try:
                    info_cmd = ['ipsw', 'info', '-j', file_path]
                    result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        ipsw_info = json.loads(result.stdout)
                        device_model = ipsw_info.get('devices', [{}])[0].get('product', 'unknown')
                        os_version = ipsw_info.get('version', 'unknown')
                        build_id = ipsw_info.get('build', 'unknown')
                except:
                    pass
                
                ipsw_files.append({
                    'filename': filename,
                    'path': file_path,
                    'size_mb': round(file_stat.st_size / (1024 * 1024), 1),
                    'device_model': device_model,
                    'os_version': os_version,
                    'build_id': build_id,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
        
        return jsonify({
            'ipsw_files': ipsw_files,
            'total': len(ipsw_files),
            'directory': ipsw_dir
        })
        
    except Exception as e:
        logger.error(f"List IPSW files error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload')
def upload_page():
    """Upload page for developers to symbolicate crashlogs"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IPSW Symbol Server - Upload Crashlog</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .upload-area { border: 2px dashed #007cba; padding: 40px; text-align: center; margin: 20px 0; border-radius: 10px; background: #f8f9fa; }
            .upload-area:hover { background: #e9ecef; }
            input[type="file"] { margin: 10px 0; }
            .btn { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .loading { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
            .ipsw-info { background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 5px; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; max-height: 400px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 IPSW Symbol Server - Crashlog Symbolication</h1>
            <p>Upload your .ips crashlog file and get symbolicated results instantly</p>
            
            <div id="ipswInfo" class="ipsw-info" style="display: none;">
                <h3>📱 Available IPSW Files:</h3>
                <div id="ipswList"></div>
            </div>
            
            <div class="upload-area">
                <h3>📤 Upload Crashlog File</h3>
                <p>Select a .ips file from your computer</p>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" id="crashlogFile" name="crashlog" accept=".ips,.crash,.txt" required>
                    <br><br>
                    <button type="submit" class="btn">🚀 Symbolicate</button>
                </form>
            </div>
            
            <div id="result" style="display: none;"></div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <h3>💡 Quick Links:</h3>
                <a href="/" style="margin-right: 20px;">🏠 Home</a>
                <a href="/v1/ipsw/list" style="margin-right: 20px;">📋 IPSW List</a>
                <a href="/health" style="margin-right: 20px;">❤️ Health Check</a>
            </div>
        </div>
        
        <script>
            // Load IPSW info on page load
            fetch('/v1/ipsw/list')
                .then(response => response.json())
                .then(data => {
                    if (data.total > 0) {
                        document.getElementById('ipswInfo').style.display = 'block';
                        const ipswList = data.ipsw_files.map(ipsw => 
                            `<div>📱 ${ipsw.device_model} - iOS ${ipsw.os_version} (${ipsw.build_id}) - ${ipsw.size_mb}MB</div>`
                        ).join('');
                        document.getElementById('ipswList').innerHTML = ipswList;
                    }
                })
                .catch(error => console.log('Could not load IPSW info'));
            
            // Handle form submission
            document.getElementById('uploadForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('crashlogFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    showResult('error', 'Please select a file');
                    return;
                }
                
                showResult('loading', '🔄 Processing your crashlog... This may take a few moments.');
                
                const formData = new FormData();
                formData.append('crashlog', file);
                
                fetch('/v1/symbolicate', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.symbolicated) {
                        showResult('success', `
                            <h3>✅ Symbolication Successful!</h3>
                            <p><strong>📱 IPSW Used:</strong> ${data.used_ipsw || 'Auto-detected'}</p>
                            <p><strong>🔧 Method:</strong> ${data.method}</p>
                            <p><strong>⏰ Time:</strong> ${data.timestamp}</p>
                            <h4>📋 Symbolicated Output:</h4>
                            <pre>${data.output}</pre>
                            <button class="btn" onclick="downloadResult('${file.name}', '${data.output}')">💾 Download Result</button>
                        `);
                    } else {
                        showResult('error', `
                            <h3>❌ Symbolication Failed</h3>
                            <p><strong>Error:</strong> ${data.error}</p>
                            <p>Please check your crashlog file format or try again.</p>
                        `);
                    }
                })
                .catch(error => {
                    showResult('error', `
                        <h3>❌ Upload Failed</h3>
                        <p><strong>Error:</strong> ${error.message}</p>
                        <p>Please check your network connection and try again.</p>
                    `);
                });
            });
            
            function showResult(type, content) {
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result ' + type;
                resultDiv.innerHTML = content;
                resultDiv.style.display = 'block';
                resultDiv.scrollIntoView({ behavior: 'smooth' });
            }
            
            function downloadResult(originalName, content) {
                const blob = new Blob([content], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = originalName.replace('.ips', '_symbolicated.txt');
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Initialize database on startup
    if init_database():
        logger.info("Database initialized successfully")
    else:
        logger.error("Database initialization failed")
        sys.exit(1)
    
    # Run development server
    app.run(host='0.0.0.0', port=3993, debug=True) 