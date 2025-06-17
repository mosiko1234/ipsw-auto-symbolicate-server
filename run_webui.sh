#!/bin/bash

echo "🚀 Starting IPSW Symbol Server Web UI..."
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install requirements if needed
if [ ! -d "venv-webui" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv-webui
    
    echo "📋 Installing dependencies..."
    source venv-webui/bin/activate
    pip install -r requirements-webui.txt
else
    echo "📋 Activating virtual environment..."
    source venv-webui/bin/activate
fi

# Check if Symbol Server API is running
echo "🔍 Checking Symbol Server API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Symbol Server API is running on port 8000"
else
    echo "⚠️  Symbol Server API is not responding on port 8000"
    echo "   Make sure to start the Docker services first:"
    echo "   docker-compose -f docker-compose.symbol-server.yml up -d"
    echo ""
    echo "   Continuing anyway - you can start the API later..."
fi

echo ""
echo "🌐 Starting Web UI on http://localhost:5001"
echo "📁 Upload folder: $(python3 -c 'import tempfile; print(tempfile.gettempdir())')"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================"

# Run the Flask app
python3 web_ui.py 