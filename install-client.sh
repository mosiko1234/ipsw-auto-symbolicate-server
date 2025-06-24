#!/bin/bash

# IPSW Symbol Server Network Client Installer
# This script installs the client on any machine to connect to a remote server

set -e

echo "🌐 IPSW Symbol Server Network Client Installer"
echo "=============================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create installation directory
CLIENT_DIR="$HOME/.ipsw-client"
mkdir -p "$CLIENT_DIR"

echo "📁 Installing to: $CLIENT_DIR"

# Download or copy client files
if [ -f "ipsw-cli-network.py" ]; then
    # Local installation
    cp ipsw-cli-network.py "$CLIENT_DIR/"
    cp requirements-network-client.txt "$CLIENT_DIR/"
    echo "✅ Copied client files from local directory"
else
    echo "❌ Client files not found in current directory"
    echo "Please run this script from the IPSW Symbol Server directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r "$CLIENT_DIR/requirements-network-client.txt" --user
elif command -v pip &> /dev/null; then
    pip install -r "$CLIENT_DIR/requirements-network-client.txt" --user
else
    echo "❌ Error: pip is required but not found"
    exit 1
fi

# Make executable
chmod +x "$CLIENT_DIR/ipsw-cli-network.py"

# Create global CLI wrapper
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/ipsw-cli-network" << 'EOF'
#!/bin/bash
exec python3 "$HOME/.ipsw-client/ipsw-cli-network.py" "$@"
EOF

chmod +x "$BIN_DIR/ipsw-cli-network"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Usage Instructions:"
echo "----------------------"
echo ""
echo "1. Add ~/.local/bin to your PATH if not already done:"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "2. Use the client from anywhere:"
echo "   ipsw-cli-network --server http://SERVER_IP:8000 crash.ips"
echo ""
echo "3. Check server status:"
echo "   ipsw-cli-network --server http://SERVER_IP:8000 --check"
echo ""
echo "4. Use with local IPSW:"
echo "   ipsw-cli-network --server http://SERVER_IP:8000 --local-ipsw firmware.ipsw crash.ips"
echo ""
echo "Replace SERVER_IP with the actual IP address of the IPSW Symbol Server"
echo ""

# Check PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  Note: ~/.local/bin is not in your PATH"
    echo "   Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "🎉 Happy symbolication!" 