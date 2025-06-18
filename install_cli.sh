#!/bin/bash

# IPSW Symbol Server CLI Installation Script
# Beautiful terminal interface for iOS crash symbolication

echo "🚀 Installing IPSW Symbol Server CLI..."
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is required but not installed.${NC}"
    echo "Please install pip3 and try again."
    exit 1
fi

echo -e "${GREEN}✅ pip3 found${NC}"

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
pip3 install --user requests rich colorama

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Download the CLI script
echo -e "${YELLOW}📥 Downloading CLI script...${NC}"

# Create local bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Copy the CLI script
if [ -f "ipsw_cli.py" ]; then
    cp ipsw_cli.py ~/.local/bin/ipsw-cli
    chmod +x ~/.local/bin/ipsw-cli
    echo -e "${GREEN}✅ CLI script installed to ~/.local/bin/ipsw-cli${NC}"
else
    echo -e "${RED}❌ ipsw_cli.py not found in current directory${NC}"
    exit 1
fi

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠️  Adding ~/.local/bin to PATH...${NC}"
    
    # Add to appropriate shell config file
    if [ -f ~/.zshrc ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo -e "${GREEN}✅ Added to ~/.zshrc${NC}"
    elif [ -f ~/.bashrc ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${GREEN}✅ Added to ~/.bashrc${NC}"
    elif [ -f ~/.bash_profile ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bash_profile
        echo -e "${GREEN}✅ Added to ~/.bash_profile${NC}"
    fi
    
    echo -e "${YELLOW}📋 Please restart your terminal or run:${NC}"
    echo -e "${BLUE}source ~/.zshrc${NC}  (or ~/.bashrc, ~/.bash_profile)"
fi

echo ""
echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
echo ""
echo -e "${BLUE}Usage examples:${NC}"
echo -e "  ${YELLOW}ipsw-cli crash.ips${NC}                          # Symbolicate local file"
echo -e "  ${YELLOW}ipsw-cli crash.ips --server http://my-server:8000${NC}  # Custom server"
echo -e "  ${YELLOW}ipsw-cli crash.ips --full${NC}                   # Show complete output"
echo -e "  ${YELLOW}ipsw-cli crash.ips --save result.json${NC}       # Save result to file"
echo -e "  ${YELLOW}ipsw-cli --help${NC}                            # Show all options"
echo ""
echo -e "${GREEN}Ready to use! 🚀${NC}" 