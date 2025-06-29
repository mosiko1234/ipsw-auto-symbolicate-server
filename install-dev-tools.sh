#!/bin/bash
# 🛠️ IPSW Symbol Server v3.1.0 - Professional Developer Tools Installation
# One-click installation for development teams

set -e

VERSION="3.1.0"
INSTALL_DIR="/usr/local/bin"
CURRENT_DIR="$(pwd)"

# Colors and styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m'
BOLD='\033[1m'

# Unicode symbols
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
CHART="📊"
TOOLS="🛠️"
COMPUTER="💻"
SPARKLE="✨"
PACKAGE="📦"
DIAMOND="💎"

function print_banner() {
    echo -e "${BOLD}${BLUE}"
    echo "╔═════════════════════════════════════════════════════════════════════════════╗"
    echo "║                  ${TOOLS} IPSW Symbol Server v${VERSION} ${TOOLS}                    ║"
    echo "║                Professional Developer Tools Installation                    ║"
    echo "║                    One-Click Setup for Development Teams                   ║"
    echo "╚═════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

function log_info() {
    echo -e "${BLUE}${INFO} ${1}${NC}"
}

function log_success() {
    echo -e "${GREEN}${CHECK} ${1}${NC}"
}

function log_warning() {
    echo -e "${YELLOW}${WARNING} ${1}${NC}"
}

function log_error() {
    echo -e "${RED}${CROSS} ${1}${NC}"
}

function log_progress() {
    echo -e "${PURPLE}${GEAR} ${1}${NC}"
}

function check_requirements() {
    log_progress "Checking system requirements..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python 3 found: v$PYTHON_VERSION"
    else
        log_error "Python 3 is required but not found"
        echo -e "${YELLOW}${INFO} Install Python 3: https://python.org/downloads/${NC}"
        exit 1
    fi
    
    # Check curl
    if command -v curl &> /dev/null; then
        log_success "curl found"
    else
        log_error "curl is required but not found"
        exit 1
    fi
    
    # Check jq (optional)
    if command -v jq &> /dev/null; then
        log_success "jq found"
    else
        log_warning "jq not found - JSON parsing will be limited"
        echo -e "${YELLOW}${INFO} Install jq: brew install jq (macOS) or apt install jq (Linux)${NC}"
    fi
    
    # Check write permissions
    if [ -w "$INSTALL_DIR" ] || [ "$(id -u)" -eq 0 ]; then
        log_success "Installation directory writable"
    else
        log_warning "Installation requires sudo privileges"
        echo -e "${YELLOW}${INFO} You may be prompted for your password${NC}"
    fi
}

function install_python_dependencies() {
    log_progress "Installing Python dependencies..."
    
    # Check if pip is available
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        log_error "pip not found"
        exit 1
    fi
    
    # Install required packages
    echo -e "${CYAN}${PACKAGE} Installing required packages:${NC}"
    echo -e "  ${WHITE}• requests - HTTP client${NC}"
    
    $PIP_CMD install requests --user --quiet
    log_success "requests installed"
    
    # Try to install rich (optional)
    if $PIP_CMD install rich --user --quiet 2>/dev/null; then
        log_success "rich installed (enhanced UI available)"
    else
        log_warning "rich installation failed (basic UI will be used)"
    fi
}

function install_tools() {
    log_progress "Installing IPSW developer tools..."
    
    # Determine if we need sudo
    if [ -w "$INSTALL_DIR" ]; then
        SUDO_CMD=""
    else
        SUDO_CMD="sudo"
    fi
    
    # Install symbolicate_v3.1.py
    if [ -f "symbolicate_v3.1.py" ]; then
        $SUDO_CMD cp "symbolicate_v3.1.py" "$INSTALL_DIR/symbolicate_v3.1.py"
        $SUDO_CMD chmod +x "$INSTALL_DIR/symbolicate_v3.1.py"
        log_success "symbolicate_v3.1.py installed"
    else
        log_error "symbolicate_v3.1.py not found in current directory"
        exit 1
    fi
    
    # Install add_ipsw_v3.1.py
    if [ -f "add_ipsw_v3.1.py" ]; then
        $SUDO_CMD cp "add_ipsw_v3.1.py" "$INSTALL_DIR/add_ipsw_v3.1.py"
        $SUDO_CMD chmod +x "$INSTALL_DIR/add_ipsw_v3.1.py"
        log_success "add_ipsw_v3.1.py installed"
    else
        log_error "add_ipsw_v3.1.py not found in current directory"
        exit 1
    fi
    
    # Install ipsw-dev-cli
    if [ -f "ipsw-dev-cli" ]; then
        $SUDO_CMD cp "ipsw-dev-cli" "$INSTALL_DIR/ipsw-dev-cli"
        $SUDO_CMD chmod +x "$INSTALL_DIR/ipsw-dev-cli"
        log_success "ipsw-dev-cli installed"
    else
        log_error "ipsw-dev-cli not found in current directory"
        exit 1
    fi
    
    # Create convenient aliases
    echo -e "${CYAN}${GEAR} Creating convenient aliases:${NC}"
    
    # Create ipsw-symbolicate alias
    $SUDO_CMD ln -sf "$INSTALL_DIR/symbolicate_v3.1.py" "$INSTALL_DIR/ipsw-symbolicate" 2>/dev/null || true
    echo -e "  ${WHITE}• ipsw-symbolicate → symbolicate_v3.1.py${NC}"
    
    # Create ipsw-add alias  
    $SUDO_CMD ln -sf "$INSTALL_DIR/add_ipsw_v3.1.py" "$INSTALL_DIR/ipsw-add" 2>/dev/null || true
    echo -e "  ${WHITE}• ipsw-add → add_ipsw_v3.1.py${NC}"
    
    log_success "All tools installed successfully"
}

function test_installation() {
    log_progress "Testing installation..."
    
    # Test each tool
    echo -e "${CYAN}${CHART} Testing installed tools:${NC}"
    
    if command -v ipsw-dev-cli &> /dev/null; then
        echo -e "  ${WHITE}• ipsw-dev-cli: ${GREEN}Available${NC}"
    else
        echo -e "  ${WHITE}• ipsw-dev-cli: ${RED}Not found${NC}"
    fi
    
    if command -v ipsw-symbolicate &> /dev/null; then
        echo -e "  ${WHITE}• ipsw-symbolicate: ${GREEN}Available${NC}"
    else
        echo -e "  ${WHITE}• ipsw-symbolicate: ${RED}Not found${NC}"
    fi
    
    if command -v ipsw-add &> /dev/null; then
        echo -e "  ${WHITE}• ipsw-add: ${GREEN}Available${NC}"
    else
        echo -e "  ${WHITE}• ipsw-add: ${RED}Not found${NC}"
    fi
    
    # Test help command
    if ipsw-dev-cli --help >/dev/null 2>&1; then
        log_success "Tools are working correctly"
    else
        log_warning "Tools installed but may have issues"
    fi
}

function show_usage_guide() {
    echo ""
    echo -e "${GREEN}${SPARKLE} ${BOLD}Installation Complete!${NC}"
    echo -e "${WHITE}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}${ROCKET} IPSW Symbol Server v${VERSION} Developer Tools are ready!${NC}"
    echo ""
    echo -e "${CYAN}${COMPUTER} ${BOLD}Available Commands:${NC}"
    echo -e "  ${WHITE}• ${BOLD}ipsw-dev-cli status${NC}                    ${GRAY}# Show system status${NC}"
    echo -e "  ${WHITE}• ${BOLD}ipsw-dev-cli symbolicate crash.ips${NC}     ${GRAY}# Symbolicate crash file${NC}"
    echo -e "  ${WHITE}• ${BOLD}ipsw-dev-cli add-ipsw file.ipsw${NC}        ${GRAY}# Add IPSW with symbol extraction${NC}"
    echo ""
    echo -e "${CYAN}${TOOLS} ${BOLD}Quick Access Aliases:${NC}"
    echo -e "  ${WHITE}• ${BOLD}ipsw-symbolicate crash.ips${NC}             ${GRAY}# Direct symbolication${NC}"
    echo -e "  ${WHITE}• ${BOLD}ipsw-add file.ipsw${NC}                     ${GRAY}# Direct IPSW management${NC}"
    echo ""
    echo -e "${YELLOW}${INFO} ${BOLD}Getting Started:${NC}"
    echo -e "  1. Start the server: ${BOLD}docker-compose up -d${NC}"
    echo -e "  2. Check status: ${BOLD}ipsw-dev-cli status${NC}"
    echo -e "  3. Add an IPSW: ${BOLD}ipsw-add ~/Downloads/iPhone_IPSW.ipsw${NC}"
    echo -e "  4. Symbolicate: ${BOLD}ipsw-symbolicate crash.ips${NC}"
    echo ""
    echo -e "${GREEN}${CHECK} ${BOLD}Ready for professional iOS development!${NC} ${SPARKLE}"
}

function main() {
    print_banner
    
    echo -e "${WHITE}${BOLD}Professional Developer Tools Installation${NC}"
    echo -e "${GRAY}Installing enhanced CLI tools for v3.1.0 with database symbols support${NC}"
    echo ""
    
    check_requirements
    echo ""
    
    install_python_dependencies
    echo ""
    
    install_tools
    echo ""
    
    test_installation
    
    show_usage_guide
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        print_banner
        echo -e "${WHITE}${BOLD}USAGE:${NC}"
        echo -e "  $0                    # Install all tools"
        echo -e "  $0 --test             # Test installation"
        echo -e "  $0 --uninstall        # Remove all tools"
        echo ""
        echo -e "${WHITE}${BOLD}FEATURES:${NC}"
        echo -e "  ${ROCKET} ${GREEN}One-click installation${NC}"
        echo -e "  ${TOOLS} ${GREEN}Professional CLI tools${NC}"
        echo -e "  ${COMPUTER} ${GREEN}Shell completions${NC}"
        echo -e "  ${SPARKLE} ${GREEN}Development team ready${NC}"
        exit 0
        ;;
    --test)
        print_banner
        test_installation
        exit 0
        ;;
    --uninstall)
        print_banner
        log_progress "Uninstalling IPSW developer tools..."
        
        if [ -w "$INSTALL_DIR" ]; then
            SUDO_CMD=""
        else
            SUDO_CMD="sudo"
        fi
        
        $SUDO_CMD rm -f "$INSTALL_DIR/symbolicate_v3.1.py"
        $SUDO_CMD rm -f "$INSTALL_DIR/add_ipsw_v3.1.py"
        $SUDO_CMD rm -f "$INSTALL_DIR/ipsw-dev-cli"
        $SUDO_CMD rm -f "$INSTALL_DIR/ipsw-symbolicate"
        $SUDO_CMD rm -f "$INSTALL_DIR/ipsw-add"
        
        log_success "Tools uninstalled successfully"
        exit 0
        ;;
    *)
        main
        ;;
esac
