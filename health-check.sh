#!/bin/bash

# 🏥 IPSW Symbol Server - Health Check
# ===================================
# Comprehensive health check for all system components

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Icons
CHECK="✅"
FAIL="❌"
WARN="⚠️"
INFO="ℹ️"

print_header() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
}

print_section() {
    echo -e "\n${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(echo "$1" | sed 's/./-/g')${NC}"
}

test_service() {
    local name="$1"
    local url="$2"
    local timeout="${3:-5}"
    
    if curl -s --connect-timeout "$timeout" "$url" >/dev/null 2>&1; then
        echo -e "${CHECK} ${GREEN}$name${NC} - Running (${url})"
        return 0
    else
        echo -e "${FAIL} ${RED}$name${NC} - Not accessible (${url})"
        return 1
    fi
}

test_container() {
    local name="$1"
    
    if docker ps --format "{{.Names}}" | grep -q "^${name}$"; then
        local status=$(docker ps --format "{{.Status}}" --filter "name=^${name}$")
        echo -e "${CHECK} ${GREEN}$name${NC} - $status"
        return 0
    else
        echo -e "${FAIL} ${RED}$name${NC} - Not running"
        return 1
    fi
}

check_disk_space() {
    local path="$1"
    local min_gb="$2"
    
    # macOS/BSD compatible df command
    local available_gb=$(df -h "$path" | tail -1 | awk '{print $4}' | sed 's/G.*//')
    
    # Handle different units (T, G, M)
    if [[ "$available_gb" =~ [0-9]*T ]]; then
        available_gb=$((${available_gb%T} * 1024))
    elif [[ "$available_gb" =~ [0-9]*M ]]; then
        available_gb=$((${available_gb%M} / 1024))
    elif [[ "$available_gb" =~ [0-9]*G ]]; then
        available_gb=${available_gb%G}
    fi
    
    # Ensure we have a number
    if ! [[ "$available_gb" =~ ^[0-9]+$ ]]; then
        available_gb=0
    fi
    
    if [ "$available_gb" -gt "$min_gb" ]; then
        echo -e "${CHECK} ${GREEN}Disk Space${NC} - ${available_gb}GB available (minimum: ${min_gb}GB)"
        return 0
    else
        echo -e "${WARN} ${YELLOW}Disk Space${NC} - Only ${available_gb}GB available (minimum: ${min_gb}GB)"
        return 1
    fi
}

main() {
    clear
    print_header "🏥 IPSW Symbol Server Health Check"
    
    echo -e "${CYAN}Running comprehensive system health check...${NC}"
    echo -e "${CYAN}Timestamp: $(date)${NC}"
    
    local errors=0
    
    # Docker Environment Check
    print_section "🐳 Docker Environment"
    
    if command -v docker >/dev/null 2>&1; then
        echo -e "${CHECK} ${GREEN}Docker${NC} - $(docker --version)"
    else
        echo -e "${FAIL} ${RED}Docker${NC} - Not installed"
        ((errors++))
    fi
    
    if command -v docker-compose >/dev/null 2>&1; then
        echo -e "${CHECK} ${GREEN}Docker Compose${NC} - $(docker-compose --version)"
    else
        echo -e "${FAIL} ${RED}Docker Compose${NC} - Not installed"
        ((errors++))
    fi
    
    # System Resources
    print_section "💻 System Resources"
    
    # Memory check (macOS compatible)
    if command -v free >/dev/null 2>&1; then
        # Linux
        local mem_total=$(free -g | grep '^Mem:' | awk '{print $2}')
        local mem_available=$(free -g | grep '^Mem:' | awk '{print $7}')
    else
        # macOS
        local mem_total_bytes=$(sysctl -n hw.memsize)
        local mem_total=$((mem_total_bytes / 1024 / 1024 / 1024))
        local mem_available=$((mem_total / 2))  # Rough estimate
    fi
    
    if [ "$mem_available" -gt 2 ]; then
        echo -e "${CHECK} ${GREEN}Memory${NC} - ${mem_available}GB available / ${mem_total}GB total"
    else
        echo -e "${WARN} ${YELLOW}Memory${NC} - Only ${mem_available}GB available / ${mem_total}GB total"
        ((errors++))
    fi
    
    # Disk space check
    check_disk_space "." 10 || ((errors++))
    
    # CPU check
    local cpu_cores=$(nproc)
    echo -e "${CHECK} ${GREEN}CPU Cores${NC} - $cpu_cores available"
    
    # Docker Containers
    print_section "📦 Docker Containers"
    
    if docker ps >/dev/null 2>&1; then
        # Check for common container names
        test_container "ipsw-symbol-server" || ((errors++))
        test_container "ipsw-api-server" || true  # Optional
        test_container "ipsw-web-ui" || true      # Optional
        test_container "ipsw-postgres" || true    # Optional
        test_container "ipsw-s3-mount" || true    # Optional
        
        # Show all IPSW related containers
        echo ""
        echo -e "${INFO} All IPSW containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -1
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -i ipsw || echo "No IPSW containers found"
    else
        echo -e "${FAIL} ${RED}Docker daemon${NC} - Not accessible"
        ((errors++))
    fi
    
    # Service Health Checks
    print_section "🌐 Service Health Checks"
    
    # Check common ports
    test_service "Web UI" "http://localhost:5001" 3 || ((errors++))
    test_service "API Server" "http://localhost:8000/health" 3 || ((errors++))
    test_service "Symbol Server" "http://localhost:3993/health" 3 || ((errors++))
    
    # Advanced checks if services are running
    if curl -s --connect-timeout 3 "http://localhost:8000/health" >/dev/null 2>&1; then
        echo ""
        echo -e "${INFO} API Server details:"
        
        # Check cache stats if S3 optimized
        if curl -s --connect-timeout 3 "http://localhost:8000/cache-stats" >/dev/null 2>&1; then
            local cache_info=$(curl -s "http://localhost:8000/cache-stats" | grep -o '"cache_utilization_percent":[0-9]*' | cut -d':' -f2)
            if [ -n "$cache_info" ]; then
                echo -e "  ${CHECK} ${GREEN}S3 Cache${NC} - ${cache_info}% utilization"
            fi
        fi
        
        # Check symbol stats
        if curl -s --connect-timeout 3 "http://localhost:8000/stats" >/dev/null 2>&1; then
            echo -e "  ${CHECK} ${GREEN}Symbol Stats${NC} - Available"
        fi
    fi
    
    # Configuration Files
    print_section "📁 Configuration Files"
    
    local config_files=(
        ".env"
        "docker-compose.yml"
        "docker-compose.symbol-server.yml"
        "docker-compose.s3-optimized.yml"
        "custom_symbol_server.py"
        "web_ui.py"
    )
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${CHECK} ${GREEN}$file${NC} - Present"
        else
            echo -e "${INFO} ${YELLOW}$file${NC} - Missing (may not be required)"
        fi
    done
    
    # Data Directories
    print_section "📂 Data Directories"
    
    local data_dirs=(
        "data"
        "data/cache"
        "data/symbols"
        "signatures"
        "signatures/symbolicator"
    )
    
    for dir in "${data_dirs[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
            echo -e "${CHECK} ${GREEN}$dir${NC} - Present ($size)"
        else
            echo -e "${WARN} ${YELLOW}$dir${NC} - Missing"
        fi
    done
    
    # Network Connectivity
    print_section "🌍 Network Connectivity"
    
    # Test internet connectivity (for Docker pulls)
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo -e "${CHECK} ${GREEN}Internet${NC} - Available"
    else
        echo -e "${WARN} ${YELLOW}Internet${NC} - Limited (may affect Docker image pulls)"
    fi
    
    # Test MinIO/S3 if configured
    if [ -f ".env" ] && grep -q "S3_ENDPOINT" .env; then
        local s3_endpoint=$(grep "S3_ENDPOINT" .env | head -1 | cut -d'=' -f2 | tr -d '"' | tr -d '\n')
        if [ -n "$s3_endpoint" ] && [ "$s3_endpoint" != "S3_ENDPOINT" ]; then
            if curl -s --connect-timeout 5 "$s3_endpoint" >/dev/null 2>&1; then
                echo -e "${CHECK} ${GREEN}S3 Endpoint${NC} - Accessible ($s3_endpoint)"
            else
                echo -e "${WARN} ${YELLOW}S3 Endpoint${NC} - Not accessible ($s3_endpoint)"
                # Don't count as error since S3 might be internal
            fi
        fi
    fi
    
    # Available Management Scripts
    print_section "🛠️ Management Scripts"
    
    local scripts=(
        "quick-deploy.sh"
        "deploy-full-system.sh"
        "deploy-s3-optimized.sh"
        "manage-system.sh"
        "health-check.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            echo -e "${CHECK} ${GREEN}$script${NC} - Executable"
        elif [ -f "$script" ]; then
            echo -e "${WARN} ${YELLOW}$script${NC} - Not executable (run: chmod +x $script)"
        else
            echo -e "${INFO} ${YELLOW}$script${NC} - Not found"
        fi
    done
    
    # Summary
    print_section "📊 Health Check Summary"
    
    if [ $errors -eq 0 ]; then
        echo -e "${CHECK} ${GREEN}System Status: HEALTHY${NC}"
        echo -e "${GREEN}All critical components are functioning properly.${NC}"
    elif [ $errors -le 2 ]; then
        echo -e "${WARN} ${YELLOW}System Status: WARNING${NC}"
        echo -e "${YELLOW}System is mostly functional but has $errors minor issues.${NC}"
    else
        echo -e "${FAIL} ${RED}System Status: CRITICAL${NC}"
        echo -e "${RED}System has $errors issues that need attention.${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Quick Actions:${NC}"
    echo -e "  • Start system: ${GREEN}./quick-deploy.sh${NC}"
    echo -e "  • Check logs: ${GREEN}docker-compose logs -f${NC}"
    echo -e "  • System status: ${GREEN}docker-compose ps${NC}"
    echo -e "  • Full redeploy: ${GREEN}./deploy-full-system.sh${NC}"
    
    # URLs if services are running
    if curl -s --connect-timeout 2 "http://localhost:5001" >/dev/null 2>&1; then
        echo ""
        echo -e "${CYAN}Available Services:${NC}"
        echo -e "  • Web UI: ${GREEN}http://localhost:5001${NC}"
        echo -e "  • API Docs: ${GREEN}http://localhost:8000/docs${NC}"
        echo -e "  • Symbol Stats: ${GREEN}http://localhost:8000/stats${NC}"
    fi
    
    echo ""
    return $errors
}

# Run main function
main "$@" 