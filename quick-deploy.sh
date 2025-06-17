#!/bin/bash

# 🚀 Quick Deploy Script for IPSW Symbol Server
# ==============================================
# Fast deployment with pre-configured options

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Show quick deploy options
show_options() {
    clear
    print_header "🚀 IPSW Symbol Server - Quick Deploy"
    
    echo -e "${PURPLE}Choose Quick Deployment Option:${NC}\n"
    
    echo -e "${CYAN}1)${NC} 🖥️  Local Development"
    echo -e "   • Symbol Server + Web UI + MinIO"
    echo -e "   • Fast setup, perfect for development"
    echo ""
    
    echo -e "${CYAN}2)${NC} ☁️  Production with S3"
    echo -e "   • All services + PostgreSQL + S3 Optimized"
    echo -e "   • Ready for production environment"
    echo ""
    
    echo -e "${CYAN}3)${NC} 🏢 Internal Network"
    echo -e "   • Configuration for internal networks"
    echo -e "   • Internal S3 + SSL support"
    echo ""
    
    echo -e "${CYAN}4)${NC} 🛠️  Custom Setup"
    echo -e "   • Run full deployment script with options"
    echo ""
    
    echo -e "${CYAN}5)${NC} 📊 System Status Check"
    echo -e "   • Check current system status"
    echo ""
    
    echo -n -e "${YELLOW}Choose option [1-5]: ${NC}"
    read -r choice </dev/tty
    
    case $choice in
        1) deploy_local_dev ;;
        2) deploy_production_s3 ;;
        3) deploy_internal_network ;;
        4) deploy_custom ;;
        5) check_system_status ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
}

# Option 1: Local Development
deploy_local_dev() {
    print_header "🖥️ Local Development Deployment"
    
    print_info "Setting up local development environment..."
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Create environment
    cat > .env.quick << 'EOF'
# Quick Deploy - Local Development
DEPLOYMENT_TYPE=1
WEB_UI_PORT=5001
API_PORT=8000
SYMBOL_PORT=3993
USE_S3_OPTIMIZED=n
USE_POSTGRES=n
USE_WEB_UI=y
USE_NGINX=n
USE_SSL_CERTS=n
BACKUP_ENABLED=n
EOF
    
    # Deploy using existing docker-compose
    print_info "Starting services..."
    
    # Use the existing symbol server setup
    docker-compose -f docker-compose.symbol-server.yml up -d --build
    
    # Wait for services
    sleep 10
    
    # Start Web UI
    if [ -f "web_ui.py" ]; then
        print_info "Starting Web UI..."
        ./run_webui.sh &
        sleep 5
    fi
    
    print_step "Local development environment deployed!"
    echo ""
    echo -e "${CYAN}🌐 Web UI: http://localhost:5001${NC}"
    echo -e "${CYAN}🔧 Symbol Server: http://localhost:8000${NC}"
    echo -e "${CYAN}📊 Stats: http://localhost:8000/stats${NC}"
    echo ""
}

# Option 2: Production with S3
deploy_production_s3() {
    print_header "☁️ Production S3 Deployment"
    
    print_info "Setting up production environment with S3..."
    
    # Get S3 configuration
    echo -n -e "${CYAN}S3 Endpoint [http://host.docker.internal:9000]: ${NC}"
    read -r s3_endpoint </dev/tty
    s3_endpoint=${s3_endpoint:-"http://host.docker.internal:9000"}
    
    echo -n -e "${CYAN}S3 Access Key [minioadmin]: ${NC}"
    read -r s3_access_key </dev/tty
    s3_access_key=${s3_access_key:-"minioadmin"}
    
    echo -n -e "${CYAN}S3 Secret Key [minioadmin]: ${NC}"
    read -r s3_secret_key </dev/tty
    s3_secret_key=${s3_secret_key:-"minioadmin"}
    
    echo -n -e "${CYAN}Cache Size GB [100]: ${NC}"
    read -r cache_size </dev/tty
    cache_size=${cache_size:-"100"}
    
    # Create environment
    cat > .env.production << EOF
# Quick Deploy - Production S3
DEPLOYMENT_TYPE=2
WEB_UI_PORT=5001
API_PORT=8000
SYMBOL_PORT=3993
USE_S3_OPTIMIZED=y
USE_POSTGRES=y
USE_WEB_UI=y
S3_ENDPOINT=$s3_endpoint
S3_ACCESS_KEY=$s3_access_key
S3_SECRET_KEY=$s3_secret_key
S3_BUCKET=ipsw
S3_USE_SSL=false
S3_VERIFY_SSL=false
CACHE_SIZE_GB=$cache_size
CLEANUP_AFTER_HOURS=24
MAX_CONCURRENT_DOWNLOADS=3
EOF
    
    # Deploy S3 optimized version
    print_info "Deploying S3 optimized system..."
    CACHE_SIZE_GB=$cache_size S3_ENDPOINT=$s3_endpoint S3_ACCESS_KEY=$s3_access_key S3_SECRET_KEY=$s3_secret_key ./deploy-s3-optimized.sh
    
    print_step "Production S3 environment deployed!"
    echo ""
    echo -e "${CYAN}🌐 Web UI: http://localhost:5001${NC}"
    echo -e "${CYAN}🚀 API Server: http://localhost:8000${NC}"
    echo -e "${CYAN}📊 Cache Stats: http://localhost:8000/cache-stats${NC}"
    echo ""
}

# Option 3: Internal Network
deploy_internal_network() {
    print_header "🏢 Internal Network Deployment"
    
    print_info "Setting up internal network configuration..."
    
    # Get internal network configuration
    echo -n -e "${CYAN}Internal S3 Endpoint: ${NC}"
    read -r internal_s3 </dev/tty
    
    echo -n -e "${CYAN}S3 Access Key: ${NC}"
    read -r s3_key </dev/tty
    
    echo -n -e "${CYAN}S3 Secret Key: ${NC}"
    read -r s3_secret </dev/tty
    
    echo -n -e "${CYAN}Use SSL? [y/N]: ${NC}"
    read -r use_ssl </dev/tty
    use_ssl=${use_ssl:-"n"}
    
    if [ "$use_ssl" = "y" ]; then
        ssl_setting="true"
        echo -n -e "${CYAN}Verify SSL certificates? [y/N]: ${NC}"
        read -r verify_ssl </dev/tty
        verify_ssl=${verify_ssl:-"n"}
        if [ "$verify_ssl" = "y" ]; then
            verify_ssl_setting="true"
        else
            verify_ssl_setting="false"
        fi
    else
        ssl_setting="false"
        verify_ssl_setting="false"
    fi
    
    # Create internal network environment
    cat > .env.internal << EOF
# Quick Deploy - Internal Network
DEPLOYMENT_TYPE=4
S3_ENDPOINT=$internal_s3
S3_ACCESS_KEY=$s3_key
S3_SECRET_KEY=$s3_secret
S3_BUCKET=ipsw
S3_USE_SSL=$ssl_setting
S3_VERIFY_SSL=$verify_ssl_setting
CACHE_SIZE_GB=200
USE_S3_OPTIMIZED=y
USE_POSTGRES=y
USE_WEB_UI=y
WEB_UI_PORT=5001
API_PORT=8000
SYMBOL_PORT=3993
EOF
    
    # Deploy with internal settings
    export S3_ENDPOINT=$internal_s3
    export S3_ACCESS_KEY=$s3_key
    export S3_SECRET_KEY=$s3_secret
    export S3_USE_SSL=$ssl_setting
    export S3_VERIFY_SSL=$verify_ssl_setting
    export CACHE_SIZE_GB=200
    
    ./deploy-s3-optimized.sh
    
    print_step "Internal network environment deployed!"
}

# Option 4: Custom Setup
deploy_custom() {
    print_header "🛠️ Custom Setup"
    
    print_info "Running full deployment script..."
    ./deploy-full-system.sh
}

# Option 5: System Status
check_system_status() {
    print_header "📊 System Status Check"
    
    print_info "Checking system status..."
    
    # Check existing containers
    echo -e "${CYAN}Docker Containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(ipsw|symbol|web-ui)" || echo "No IPSW containers running"
    echo ""
    
    # Check services
    services=(
        "localhost:5001:Web UI"
        "localhost:8000:API Server"
        "localhost:3993:Symbol Server"
    )
    
    echo -e "${CYAN}Service Health Checks:${NC}"
    for service in "${services[@]}"; do
        IFS=':' read -r host port name <<< "$service"
        if curl -s --connect-timeout 3 "http://${host}:${port}" >/dev/null 2>&1; then
            echo -e "✅ $name ($host:$port) - ${GREEN}Running${NC}"
        else
            echo -e "❌ $name ($host:$port) - ${YELLOW}Not accessible${NC}"
        fi
    done
    echo ""
    
    # Check docker-compose files
    echo -e "${CYAN}Available Configurations:${NC}"
    for file in docker-compose*.yml; do
        if [ -f "$file" ]; then
            echo "📄 $file"
        fi
    done
    echo ""
    
    # Check for S3 optimized
    if docker ps | grep -q "s3-mount"; then
        echo -e "${CYAN}S3 Mount Status:${NC}"
        docker exec ipsw-symbol-server ls -la /app/data/s3-ipsw/ 2>/dev/null | head -5 || echo "S3 mount not accessible"
        echo ""
        
        echo -e "${CYAN}Cache Statistics:${NC}"
        curl -s http://localhost:8000/cache-stats 2>/dev/null | jq '.' || echo "Cache stats not available"
        echo ""
    fi
    
    # Management commands
    echo -e "${CYAN}Quick Management Commands:${NC}"
    echo "🔄 Restart all: docker-compose restart"
    echo "📋 View logs: docker-compose logs -f"
    echo "🛑 Stop all: docker-compose down"
    echo "🚀 Deploy again: ./quick-deploy.sh"
    echo ""
}

# Helper function to create quick management aliases
create_aliases() {
    cat > manage-system.sh << 'EOF'
#!/bin/bash
# Quick management commands

case "$1" in
    start)
        docker-compose up -d
        echo "✅ System started"
        ;;
    stop)
        docker-compose down
        echo "✅ System stopped"
        ;;
    restart)
        docker-compose restart
        echo "✅ System restarted"
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        ./quick-deploy.sh
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status}"
        echo ""
        echo "start   - Start all services"
        echo "stop    - Stop all services"  
        echo "restart - Restart all services"
        echo "logs    - Show logs (follow)"
        echo "status  - Show system status"
        ;;
esac
EOF
    chmod +x manage-system.sh
}

# Main function
main() {
    # Create management helper
    create_aliases
    
    # Show options and deploy
    show_options
    
    # Final message
    echo ""
    print_step "Deployment completed!"
    echo -e "${CYAN}💡 Tip: Use ${NC}./manage-system.sh status${CYAN} to check system later${NC}"
    echo -e "${CYAN}💡 Tip: Use ${NC}./quick-deploy.sh${CYAN} to redeploy quickly${NC}"
}

# Run main function
main "$@" 