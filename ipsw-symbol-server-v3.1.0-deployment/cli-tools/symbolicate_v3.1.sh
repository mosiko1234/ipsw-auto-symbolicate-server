#!/bin/bash
# 🚀 IPSW Symbol Server v3.1.0 - Enhanced Symbolication Script
# Professional iOS Crash Symbolication with Database Symbols

set -e

CRASHLOG_FILE="$1"
OUTPUT_FILE="$2"
BASE_URL="http://localhost:8082"
VERSION="3.1.0"

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
FILE="📁"
PHONE="📱"
CLOCK="⏰"
SPARKLE="✨"
LIGHTNING="⚡"
DATABASE="🗄️"
MAGNIFYING="��"

function print_banner() {
    echo -e "${BOLD}${BLUE}"
    echo "╔═════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    ${ROCKET} IPSW Symbol Server v${VERSION} ${ROCKET}                      ║"
    echo "║                  Professional iOS Crash Symbolication                      ║"
    echo "║                     Enhanced Database-First Technology                     ║"
    echo "╚═════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

function usage() {
    print_banner
    echo -e "${WHITE}${BOLD}USAGE:${NC}"
    echo -e "  $0 <crashlog_file> [output_file]"
    echo ""
    echo -e "${WHITE}${BOLD}EXAMPLES:${NC}"
    echo -e "  $0 crash.ips                                ${GRAY}# Auto-generates output filename${NC}"
    echo -e "  $0 crash.ips symbolicated_crash.txt         ${GRAY}# Custom output filename${NC}"
    echo -e "  $0 MyApp-2024-crash.ips                     ${GRAY}# Will create MyApp-2024-crash_symbolicated.txt${NC}"
    echo ""
    echo -e "${WHITE}${BOLD}v3.1.0 FEATURES:${NC}"
    echo -e "  ${LIGHTNING} ${GREEN}Ultra-fast database symbolication${NC}     ${GRAY}# 10-20x faster than IPSW files${NC}"
    echo -e "  ${DATABASE} ${GREEN}Smart symbol extraction${NC}                ${GRAY}# 99% storage space savings${NC}"
    echo -e "  ${GEAR} ${GREEN}Automatic IPSW detection${NC}                ${GRAY}# No manual IPSW selection needed${NC}"
    echo -e "  ${CHART} ${GREEN}Real-time progress tracking${NC}             ${GRAY}# Beautiful progress indicators${NC}"
    echo -e "  ${SPARKLE} ${GREEN}Enhanced output formatting${NC}             ${GRAY}# Professional developer experience${NC}"
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

function check_server() {
    log_progress "Connecting to IPSW Symbol Server v3.1.0..."
    
    if response=$(curl -s "${BASE_URL}/health" 2>/dev/null); then
        log_success "Server connection established"
        
        local version=$(echo "$response" | jq -r '.version // "unknown"')
        local symbols_count=$(echo "$response" | jq -r '.symbols_in_database // 0')
        
        echo -e "${CYAN}${DATABASE} Database Status:${NC}"
        echo -e "  ${WHITE}• Version: ${version}${NC}"
        echo -e "  ${WHITE}• Symbols Available: ${BOLD}${GREEN}${symbols_count:,}${NC}${WHITE} symbols${NC}"
        
        if [ "$symbols_count" -gt 0 ]; then
            log_success "v3.1.0 Database symbols ready for ultra-fast symbolication!"
        else
            log_warning "No symbols in database - will try IPSW fallback method"
        fi
        
        return 0
    else
        log_error "Server not available at ${BASE_URL}"
        echo -e "${YELLOW}${INFO} Start server with: ${BOLD}docker-compose up -d${NC}"
        return 1
    fi
}

function symbolicate_crash() {
    local crashlog="$1"
    local output="$2"
    
    log_progress "Starting v3.1.0 enhanced symbolication..."
    
    local file_size=$(stat -f%z "$crashlog" 2>/dev/null || stat -c%s "$crashlog" 2>/dev/null || echo "unknown")
    echo -e "${CYAN}${FILE} Input File Analysis:${NC}"
    echo -e "  ${WHITE}• File: ${BOLD}$(basename "$crashlog")${NC}"
    echo -e "  ${WHITE}• Size: ${BOLD}${file_size:,}${NC}${WHITE} bytes${NC}"
    
    local result=$(curl -s -F "crashlog=@${crashlog}" "${BASE_URL}/v1/symbolicate" 2>/dev/null)
    
    local success=$(echo "$result" | jq -r '.symbolicated // false')
    local method=$(echo "$result" | jq -r '.method // "unknown"')
    local symbols_used=$(echo "$result" | jq -r '.symbols_used // 0')
    
    if [ "$success" = "true" ]; then
        log_success "Symbolication completed successfully!"
        
        {
            echo "# 🚀 IPSW Symbol Server v3.1.0 - Symbolication Result"
            echo "# Generated: $(date)"
            echo "# Method: $method"
            echo "# Symbols Used: $symbols_used"
            echo "# Input: $(basename "$crashlog")"
            echo "# ================================================================"
            echo ""
            echo "$result" | jq -r '.output'
        } > "$output"
        
        log_success "Result saved to: ${BOLD}$output${NC}"
        
        echo -e "${CYAN}${LIGHTNING} Symbolication Details:${NC}"
        echo -e "  ${WHITE}• Method: ${BOLD}${GREEN}$method${NC}"
        
        if [ "$method" = "database_symbols" ]; then
            echo -e "  ${WHITE}• Performance: ${BOLD}${GREEN}Ultra-fast database lookup${NC} ${LIGHTNING}"
            echo -e "  ${WHITE}• Symbols Used: ${BOLD}${GREEN}${symbols_used:,}${NC}${WHITE} symbols${NC}"
            echo -e "  ${WHITE}• Technology: ${BOLD}${PURPLE}v3.1.0 Database-First Architecture${NC}"
        else
            echo -e "  ${WHITE}• Performance: ${BOLD}${YELLOW}IPSW file processing${NC}"
            echo -e "  ${WHITE}• Note: ${YELLOW}Consider symbol extraction for faster future processing${NC}"
        fi
        
        return 0
    else
        log_error "Symbolication failed!"
        local error=$(echo "$result" | jq -r '.error // "unknown error"')
        echo -e "${RED}Error Details: $error${NC}"
        return 1
    fi
}

function show_result_preview() {
    local file="$1"
    
    echo ""
    echo -e "${CYAN}${MAGNIFYING} Result Preview:${NC}"
    echo -e "${WHITE}════════════════════════════════════════════════════════════════════${NC}"
    
    head -n 15 "$file" | nl -w2 -s': '
    
    local total_lines=$(wc -l < "$file")
    if [ "$total_lines" -gt 15 ]; then
        echo -e "${GRAY}... (${total_lines} total lines - see full file)${NC}"
    fi
    
    echo -e "${WHITE}════════════════════════════════════════════════════════════════════${NC}"
}

function show_summary() {
    local input="$1"
    local output="$2"
    
    echo ""
    echo -e "${GREEN}${SPARKLE} ${BOLD}Symbolication Summary${NC}"
    echo -e "${WHITE}═══════════════════════════════════════════════════════════════════════${NC}"
    
    local input_size=$(stat -f%z "$input" 2>/dev/null || stat -c%s "$input" 2>/dev/null || echo "0")
    local output_size=$(stat -f%z "$output" 2>/dev/null || stat -c%s "$output" 2>/dev/null || echo "0")
    local output_lines=$(wc -l < "$output")
    
    echo -e "${WHITE}📥 Input:  ${BOLD}$(basename "$input")${NC}${WHITE} (${input_size:,} bytes)${NC}"
    echo -e "${WHITE}📤 Output: ${BOLD}$(basename "$output")${NC}${WHITE} (${output_size:,} bytes, ${output_lines:,} lines)${NC}"
    echo -e "${WHITE}⚡ Server: ${BOLD}IPSW Symbol Server v3.1.0${NC}"
    echo -e "${WHITE}🕐 Time:   ${BOLD}$(date)${NC}"
    
    echo ""
    echo -e "${CYAN}${INFO} ${BOLD}Quick Actions:${NC}"
    echo -e "  ${WHITE}• View result:     ${BOLD}cat '$output'${NC}"
    echo -e "  ${WHITE}• Edit result:     ${BOLD}code '$output'${NC}"
    echo -e "  ${WHITE}• Search symbols:  ${BOLD}grep 'function_name' '$output'${NC}"
    echo -e "  ${WHITE}• Delete result:   ${BOLD}rm '$output'${NC}"
    
    echo ""
    echo -e "${GREEN}${CHECK} ${BOLD}Symbolication completed successfully!${NC} ${SPARKLE}"
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi
    
    if [ ! -f "$CRASHLOG_FILE" ]; then
        print_banner
        log_error "Crashlog file not found: $CRASHLOG_FILE"
        exit 1
    fi
    
    if [ -z "$OUTPUT_FILE" ]; then
        local base_name=$(basename "$CRASHLOG_FILE" .ips)
        OUTPUT_FILE="${base_name}_symbolicated.txt"
    fi
    
    print_banner
    echo -e "${WHITE}${BOLD}Starting Enhanced Symbolication${NC}"
    echo -e "${GRAY}File: $(basename "$CRASHLOG_FILE") → $(basename "$OUTPUT_FILE")${NC}"
    echo ""
    
    check_server || exit 1
    echo ""
    symbolicate_crash "$CRASHLOG_FILE" "$OUTPUT_FILE" || exit 1
    show_result_preview "$OUTPUT_FILE"
    show_summary "$CRASHLOG_FILE" "$OUTPUT_FILE"
}

main "$@"
