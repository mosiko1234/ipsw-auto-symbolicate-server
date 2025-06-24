#!/bin/bash

# IPSW Symbol Server Unified CLI Installer
# This script installs the unified CLI (local + network) on any machine

set -e

echo "🚀 IPSW Symbol Server Unified CLI Installer"
echo "==========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create installation directory
CLI_DIR="$HOME/.ipsw-cli"
mkdir -p "$CLI_DIR"

echo "📁 Installing to: $CLI_DIR"

# Check if we're in the source directory
if [ -f "ipsw_cli_unified.py" ]; then
    # Local installation from source
    cp ipsw_cli_unified.py "$CLI_DIR/"
    cp requirements.txt "$CLI_DIR/"
    if [ -f "CLI_UNIFIED_USAGE.md" ]; then
        cp CLI_UNIFIED_USAGE.md "$CLI_DIR/"
    fi
    echo "✅ Copied files from local directory"
elif [ -f "ipsw-unified-cli-v1.2.5.tar.gz" ]; then
    # Installation from package
    tar -xzf ipsw-unified-cli-v1.2.5.tar.gz -C "$CLI_DIR" --strip-components=0
    echo "✅ Extracted from package"
else
    echo "❌ Error: No installation files found"
    echo "Please run this script from the IPSW Symbol Server directory"
    echo "or ensure ipsw-unified-cli-v1.2.5.tar.gz is present"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r "$CLI_DIR/requirements.txt" --user --quiet
elif command -v pip &> /dev/null; then
    pip install -r "$CLI_DIR/requirements.txt" --user --quiet
else
    echo "❌ Error: pip is required but not found"
    exit 1
fi

# Make executable
chmod +x "$CLI_DIR/ipsw_cli_unified.py"

# Create global CLI wrapper
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/ipsw-cli" << 'EOF'
#!/bin/bash

# IPSW Symbol Server CLI - Unified Local & Network Client
# Global wrapper for the unified CLI

CLI_DIR="$HOME/.ipsw-cli"
CLI_SCRIPT="$CLI_DIR/ipsw_cli_unified.py"

# Check if installation exists
if [ ! -f "$CLI_SCRIPT" ]; then
    echo "❌ Error: IPSW CLI not found at $CLI_DIR"
    echo "Please run install-unified-cli.sh to install"
    exit 1
fi

# Run the unified CLI
python3 "$CLI_SCRIPT" "$@"
EOF

chmod +x "$BIN_DIR/ipsw-cli"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Usage Instructions:"
echo "----------------------"
echo ""
echo "1. Add ~/.local/bin to your PATH if not already done:"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "2. Use the unified CLI:"
echo ""
echo "   # Local server (auto-detect and start)"
echo "   ipsw-cli crash.ips"
echo "   ipsw-cli --local-ipsw firmware.ipsw crash.ips"
echo ""
echo "   # Remote server"
echo "   ipsw-cli --server http://SERVER_IP:8000 crash.ips"
echo "   ipsw-cli --server http://SERVER_IP:8000 --local-ipsw firmware.ipsw crash.ips"
echo ""
echo "   # Check server status"
echo "   ipsw-cli --check"
echo "   ipsw-cli --server http://SERVER_IP:8000 --check"
echo ""
echo "3. For help and examples:"
echo "   ipsw-cli --help"
echo ""

# Check PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  Note: ~/.local/bin is not in your PATH"
    echo "   Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "📚 Documentation:"
echo "   - Full usage guide: $CLI_DIR/CLI_UNIFIED_USAGE.md"
echo "   - One CLI for local AND network usage!"
echo ""
echo "🎉 Happy symbolication!" 