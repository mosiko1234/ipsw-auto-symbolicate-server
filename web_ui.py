#!/usr/bin/env python3
"""
Web UI for IPSW Symbol Server
Allows developers to upload IPS crash files and get symbolicated results
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
import requests
import json
import os
import tempfile
import uuid
from datetime import datetime
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
SYMBOL_SERVER_URL = "http://localhost:8000"
UPLOAD_FOLDER = tempfile.mkdtemp()
RESULTS_FOLDER = tempfile.mkdtemp()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension"""
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in {'ips', 'crash', 'txt', 'json'}

def extract_kernel_addresses(crash_data):
    """Extract kernel addresses from crash log data"""
    addresses = []
    
    # Look for kernelFrames sections in the crash log
    kernel_frames_pattern = r'"kernelFrames"\s*:\s*\[(.*?)\]'
    matches = re.findall(kernel_frames_pattern, crash_data, re.DOTALL)
    
    for match in matches:
        # Extract long numbers (10+ digits) which are likely kernel addresses
        address_pattern = r'(\d{10,})'
        addr_matches = re.findall(address_pattern, match)
        
        for addr_str in addr_matches:
            try:
                addr = int(addr_str)
                # Convert to virtual address by ORing with kernel base
                virtual_addr = addr | 0xfffffff000000000
                addresses.append(virtual_addr)
            except ValueError:
                continue
    
    return list(set(addresses))  # Remove duplicates

def format_analysis_results(data):
    """Format the symbolication results for web display"""
    result = {
        'success': data.get('success', False),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'timing': {},
        'device_info': {},
        'kernel_analysis': {},
        'symbolication': {},
        'summary': {}
    }
    
    # Timing information
    if 'total_time' in data:
        result['timing']['total'] = f"{data['total_time']:.3f}s"
    if 'symbolication_time' in data:
        result['timing']['symbolication'] = f"{data['symbolication_time']:.3f}s"
    if 'download_time' in data and data['download_time']:
        result['timing']['download'] = f"{data['download_time']:.3f}s"
    
    # Extract device info and analyze crash log
    crash_data = data.get('symbolicated_output', '')
    if crash_data:
        # Device info
        os_match = re.search(r'"os_version"\s*:\s*"([^"]+)"', crash_data)
        if os_match:
            result['device_info']['os_version'] = os_match.group(1)
        
        model_match = re.search(r'"model"\s*:\s*"([^"]+)"', crash_data)
        if model_match:
            result['device_info']['model'] = model_match.group(1)
        
        # Kernel analysis
        kernel_addresses = extract_kernel_addresses(crash_data)
        result['kernel_analysis']['addresses_found'] = len(kernel_addresses)
        result['kernel_analysis']['addresses'] = [f"0x{addr:016x}" for addr in kernel_addresses[:10]]
        
        # Symbolication analysis
        lines = crash_data.split('\n')
        symbol_lines = [l for l in lines if '+' in l and '0x' in l and '<unknown>' not in l and any(func in l for func in ['_', 'kernel', 'IOKit', 'com.apple'])]
        unknown_lines = [l for l in lines if '<unknown>' in l and '+0x' in l]
        
        result['symbolication']['symbol_lines'] = len(symbol_lines)
        result['symbolication']['unknown_lines'] = len(unknown_lines)
        result['symbolication']['sample_symbols'] = [line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip() for line in symbol_lines[:5]]
        
        result['symbolication']['output_size'] = f"{len(crash_data):,} characters"
    
    # Server message
    if 'message' in data:
        result['message'] = data['message']
    
    # Error handling
    if not data.get('success') and 'error' in data:
        result['error'] = data['error']
    
    # Summary
    if result['success']:
        if result['kernel_analysis'].get('addresses_found', 0) > 0:
            if result['symbolication'].get('symbol_lines', 0) > 0:
                result['summary']['status'] = 'success'
                result['summary']['message'] = 'Kernel symbolication successful!'
            else:
                result['summary']['status'] = 'partial'
                result['summary']['message'] = 'Addresses found but no symbols resolved'
        else:
            result['summary']['status'] = 'no_addresses'
            result['summary']['message'] = 'No kernel addresses found in crash log'
    else:
        result['summary']['status'] = 'error'
        result['summary']['message'] = 'Symbolication failed'
    
    return result

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and symbolication"""
    print(f"🔍 Upload request received. Method: {request.method}")
    print(f"📋 Form keys: {list(request.form.keys())}")
    print(f"📁 Files keys: {list(request.files.keys())}")
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    print(f"📄 File object: {file}")
    print(f"📝 Filename: '{file.filename}'")
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        print(f"📁 Processing file: {file.filename}, size: {len(file.read())} bytes")
        file.seek(0)  # Reset file pointer after reading
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        original_filename = filename
        filename = f"{analysis_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Send to symbolication API
            with open(filepath, 'rb') as f:
                files = {'file': (original_filename, f, 'application/octet-stream')}
                response = requests.post(f"{SYMBOL_SERVER_URL}/symbolicate", files=files, timeout=300)
            
            if response.status_code == 200:
                api_data = response.json()
                
                # Format results
                formatted_results = format_analysis_results(api_data)
                
                # Save results
                results_file = os.path.join(app.config['RESULTS_FOLDER'], f"{analysis_id}_results.json")
                with open(results_file, 'w') as f:
                    json.dump({
                        'api_response': api_data,
                        'formatted_results': formatted_results,
                        'original_filename': original_filename,
                        'analysis_id': analysis_id
                    }, f, indent=2)
                
                # Clean up uploaded file
                os.remove(filepath)
                
                return render_template('results.html', 
                                     results=formatted_results, 
                                     analysis_id=analysis_id,
                                     original_filename=original_filename)
            else:
                flash(f'Symbolication API error: {response.status_code}', 'error')
                
        except requests.exceptions.RequestException as e:
            flash(f'Connection error: {str(e)}', 'error')
        except Exception as e:
            flash(f'Processing error: {str(e)}', 'error')
        finally:
            # Clean up uploaded file if it still exists
            if os.path.exists(filepath):
                os.remove(filepath)
    
    else:
        flash('Invalid file type. Please upload .ips, .crash, .txt, or .json files', 'error')
    
    return redirect(url_for('index'))

@app.route('/download/<analysis_id>')
def download_results(analysis_id):
    """Download results as JSON file"""
    try:
        results_file = os.path.join(app.config['RESULTS_FOLDER'], f"{analysis_id}_results.json")
        
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            # Create formatted output
            output = {
                "analysis_id": analysis_id,
                "timestamp": datetime.now().isoformat(),
                "original_file": data.get('original_filename', 'unknown'),
                "results": data.get('formatted_results', {}),
                "raw_api_response": data.get('api_response', {})
            }
            
            # Create temporary file for download
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            json.dump(output, temp_file, indent=2, ensure_ascii=False)
            temp_file.close()
            
            filename = f"symbolication_results_{analysis_id[:8]}.json"
            
            def remove_file(response):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass
                return response
            
            return send_file(temp_file.name, 
                           as_attachment=True, 
                           download_name=filename,
                           mimetype='application/json')
        else:
            flash('Results not found', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'Download error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """Check if symbolication API is available"""
    try:
        response = requests.get(f"{SYMBOL_SERVER_URL}/health", timeout=5)
        return jsonify({
            'status': 'online' if response.status_code == 200 else 'error',
            'api_url': SYMBOL_SERVER_URL
        })
    except:
        return jsonify({
            'status': 'offline',
            'api_url': SYMBOL_SERVER_URL
        })

if __name__ == '__main__':
    print("🚀 Starting IPSW Symbol Server Web UI...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Results folder: {RESULTS_FOLDER}")
    print(f"🔗 Symbol Server API: {SYMBOL_SERVER_URL}")
    print("🌐 Web UI will be available at: http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 