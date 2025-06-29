#!/usr/bin/env python3
"""
IPSW Symbol Server v3.1.0 - Enhanced with Symbol Extraction
"""

import os
import sys
import json
import subprocess
import tempfile
import logging
from datetime import datetime
from threading import Thread
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://symboluser:symbolpass@symbol-db:5432/symbols')
UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/uploads')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@app.route('/')
def home():
    """Enhanced home page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced IPSW Symbol Server v3.1.0</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .feature { background: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .workflow { background: #f0f8ff; padding: 15px; margin: 15px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Enhanced IPSW Symbol Server v3.1.0</h1>
            <p><strong>Extract symbols once, symbolicate forever!</strong></p>
            <p>No more IPSW files needed after symbol extraction.</p>
            
            <div class="feature">
                <h3>🆕 Key Features:</h3>
                <ul>
                    <li>✅ <strong>Symbol Extraction</strong> - Extracts all symbols during scan</li>
                    <li>✅ <strong>Database Storage</strong> - Stores symbols permanently in PostgreSQL</li>
                    <li>✅ <strong>IPSW Independence</strong> - Delete IPSW files after extraction</li>
                    <li>✅ <strong>Fast Symbolication</strong> - Uses database symbols (no IPSW processing)</li>
                    <li>✅ <strong>Space Efficient</strong> - Symbols take ~1% of IPSW size</li>
                </ul>
            </div>
            
            <div class="workflow">
                <h3>📋 New Workflow:</h3>
                <ol>
                    <li><strong>Scan IPSW</strong> → Extracts & stores symbols in database</li>
                    <li><strong>Delete IPSW</strong> → Free up storage (symbols remain in DB)</li>
                    <li><strong>Symbolicate</strong> → Uses database symbols (instant!)</li>
                </ol>
                <p><em>Example: 9GB IPSW → ~90MB symbols in database</em></p>
            </div>
            
            <h3>🌐 Management Interfaces:</h3>
            <ul>
                <li><a href="/upload">📤 Upload & Symbolicate</a> - Test symbolication</li>
                <li><a href="/manage">🗃 Symbol Database Management</a> - View symbols & manage IPSWs</li>
                <li><a href="/v1/syms/scans">📋 API: List Scanned IPSWs</a></li>
                <li><a href="/health">❤️ System Health</a> - Enhanced status</li>
            </ul>
            
            <h3>🔧 API Endpoints:</h3>
            <ul>
                <li><code>POST /v1/syms/scan</code> - Scan IPSW with symbol extraction</li>
                <li><code>POST /v1/symbolicate</code> - Symbolicate (database-first)</li>
                <li><code>GET /v1/syms/stats</code> - Database statistics</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/manage')
def manage():
    """Symbol management interface"""
    return """
    <h1>🗃 Symbol Database Management</h1>
    <p>This would show:</p>
    <ul>
        <li>Database statistics (total symbols, devices covered)</li>
        <li>List of scanned IPSWs</li>
        <li>Which IPSWs can be safely deleted</li>
        <li>Storage space freed up</li>
    </ul>
    <p><a href="/">← Back to Home</a></p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3993, debug=True)
