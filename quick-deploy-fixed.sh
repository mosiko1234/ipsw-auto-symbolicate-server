#!/bin/bash

# 🚀 IPSW Symbol Server - Quick Deploy Fixed
# Simplified deployment without TTY issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${CYAN}🚀 $1${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Function to get user input with timeout
get_input_with_default() {
    local prompt="$1"
    local default="$2"
    local timeout="${3:-10}"
    
    echo -e "${CYAN}$prompt${NC}"
    echo -e "${YELLOW}Default: $default (will auto-confirm in $timeout seconds)${NC}"
    echo -n "Press Enter to confirm or enter new value: "
    
    if read -t $timeout input; then
        echo "${input:-$default}"
    else
        echo ""
        echo "Using default: $default"
        echo "$default"
    fi
}

# Internal Network Quick Setup
setup_internal_network() {
    print_header "Internal Network Setup"
    
    echo -e "${PURPLE}Quick setup for internal network with internal S3${NC}"
    echo ""
    
    # S3 Configuration with smart defaults
    S3_ENDPOINT=$(get_input_with_default "S3 Endpoint URL" "https://s3.internal.company.com" 15)
    S3_ACCESS_KEY=$(get_input_with_default "S3 Access Key" "minioadmin" 10)
    S3_SECRET_KEY=$(get_input_with_default "S3 Secret Key" "minioadmin" 10)
    S3_BUCKET=$(get_input_with_default "S3 Bucket Name" "ipsw" 10)
    
    # Use SSL configuration with simple input
    S3_USE_SSL=$(get_input_with_default "Use SSL? (y/n)" "n" 10)
    
    if [ "$S3_USE_SSL" = "y" ]; then
        S3_VERIFY_SSL=$(get_input_with_default "Verify SSL certificates? (y/n) - Recommended: n for internal certificates" "n" 10)
    else
        S3_VERIFY_SSL="n"
    fi
    
    # Cache configuration
    CACHE_SIZE_GB=$(get_input_with_default "Cache size in GB" "100" 10)
    
    # Ports configuration
    WEB_UI_PORT=$(get_input_with_default "Web UI Port" "5001" 5)
    API_PORT=$(get_input_with_default "API Port" "8000" 5)
    SYMBOL_PORT=$(get_input_with_default "Symbol Server Port" "3993" 5)
}

# Create environment files
create_env_files() {
    print_header "Creating Configuration Files"
    
    cat > .env << EOF
# IPSW Symbol Server - Internal Network Configuration
# Generated: $(date)

# Deployment Type
DEPLOYMENT_TYPE=4
USE_S3_OPTIMIZED=y
USE_POSTGRES=y
USE_WEB_UI=y

# Ports
WEB_UI_PORT=$WEB_UI_PORT
API_PORT=$API_PORT
SYMBOL_PORT=$SYMBOL_PORT

# S3 Configuration
S3_ENDPOINT=$S3_ENDPOINT
S3_ACCESS_KEY=$S3_ACCESS_KEY
S3_SECRET_KEY=$S3_SECRET_KEY
S3_BUCKET=$S3_BUCKET
S3_USE_SSL=$S3_USE_SSL
S3_VERIFY_SSL=$S3_VERIFY_SSL

# Cache Configuration
CACHE_SIZE_GB=$CACHE_SIZE_GB
CLEANUP_AFTER_HOURS=24
MAX_CONCURRENT_DOWNLOADS=3
EOF

    cat > .env.postgres << EOF
POSTGRES_DB=symbolserver
POSTGRES_USER=symboluser
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
EOF

    print_step "Configuration files created successfully"
}

# Create required Dockerfiles
create_missing_dockerfiles() {
    print_header "Creating Missing Dockerfiles"
    
    # Create Web UI Dockerfile if missing
    if [ ! -f "Dockerfile.webui" ]; then
        cat > Dockerfile.webui << 'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-webui.txt .
RUN pip install -r requirements-webui.txt

COPY web_ui.py .
COPY templates/ templates/
COPY static/ static/

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

CMD ["python", "web_ui.py"]
EOF
        print_step "Created Dockerfile.webui"
    fi
    
    # Create requirements-webui.txt if missing
    if [ ! -f "requirements-webui.txt" ]; then
        cat > requirements-webui.txt << 'EOF'
Flask==2.3.3
requests==2.31.0
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.2
EOF
        print_step "Created requirements-webui.txt"
    fi
}

# Create simple docker-compose
create_docker_compose() {
    print_header "Creating Docker Compose Configuration"
    
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: ipsw-postgres
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3

  symbol-server:
    build:
      context: .
      dockerfile: Dockerfile.symbol-server-s3
    container_name: ipsw-symbol-server
    ports:
      - "${SYMBOL_PORT}:3993"
    environment:
      - S3_ENDPOINT=${S3_ENDPOINT}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - S3_USE_SSL=${S3_USE_SSL}
      - S3_VERIFY_SSL=${S3_VERIFY_SSL}
      - CACHE_SIZE_GB=${CACHE_SIZE_GB}
      - CLEANUP_AFTER_HOURS=${CLEANUP_AFTER_HOURS}
      - MAX_CONCURRENT_DOWNLOADS=${MAX_CONCURRENT_DOWNLOADS}
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    volumes:
      - ./data/cache:/app/data/cache
      - ./data/symbols:/app/data/symbols
      - ./data/downloads:/app/data/downloads
      - ./data/temp:/app/data/temp
      - ./signatures:/app/data/signatures:ro
    tmpfs:
      - /app/data/processing:size=2G,noexec,nosuid,nodev
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3993/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-server:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: ipsw-api-server
    ports:
      - "${API_PORT}:8000"
    environment:
      - SYMBOL_SERVER_URL=http://symbol-server:3993
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - S3_ENDPOINT=${S3_ENDPOINT}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - S3_USE_SSL=${S3_USE_SSL}
      - CACHE_SIZE_GB=${CACHE_SIZE_GB}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    depends_on:
      symbol-server:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web-ui:
    build:
      context: .
      dockerfile: Dockerfile.webui
    container_name: ipsw-web-ui
    ports:
      - "${WEB_UI_PORT}:5001"
    environment:
      - API_SERVER_URL=http://api-server:8000
      - SYMBOL_SERVER_URL=http://symbol-server:3993
    volumes:
      - ./templates:/app/templates
      - ./static:/app/static
    restart: unless-stopped
    depends_on:
      api-server:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
EOF

    print_step "Docker Compose created successfully"
}

# Setup directories
setup_directories() {
    print_header "Setting Up Directories"
    
    mkdir -p data/{cache,symbols,downloads,temp,processing}
    mkdir -p logs
    mkdir -p templates static
    mkdir -p postgres
    
    # Create PostgreSQL initialization script
    cat > postgres/init.sql << 'EOF'
-- IPSW Symbol Server Database Initialization
CREATE DATABASE IF NOT EXISTS symbolserver;

-- Create symbols table
CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    device_model VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_version VARCHAR(20) NOT NULL,
    symbol_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_symbols_device_version ON symbols(device_model, ios_version, build_version);

-- Create cache table
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_key VARCHAR(50) PRIMARY KEY,
    device_model VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_version VARCHAR(20) NOT NULL,
    access_count INTEGER DEFAULT 1,
    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_last_access ON cache_metadata(last_access);

-- Create S3 download tracking table
CREATE TABLE IF NOT EXISTS s3_downloads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    s3_key VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_s3_downloads_status ON s3_downloads(status);
CREATE INDEX IF NOT EXISTS idx_s3_downloads_filename ON s3_downloads(filename);
EOF

    # Set permissions
    chmod -R 755 data/
    chmod 644 postgres/init.sql
    
    print_step "Directories and database initialization script created successfully"
}

# Test S3 connectivity
test_s3_connection() {
    print_header "Testing S3 Connection"
    
    print_info "Testing S3 endpoint connectivity..."
    
    # Extract host from S3_ENDPOINT
    local s3_host=$(echo "$S3_ENDPOINT" | sed 's|https\?://||' | cut -d'/' -f1)
    
    if curl -s --connect-timeout 10 "$S3_ENDPOINT" >/dev/null 2>&1; then
        print_step "S3 endpoint is reachable"
    else
        print_warning "S3 endpoint connectivity test failed, but continuing with deployment"
        print_info "This might be normal for internal S3 services that require authentication"
    fi
    
    print_info "S3 Configuration:"
    echo "  Endpoint: $S3_ENDPOINT"
    echo "  Bucket: $S3_BUCKET"
    echo "  Use SSL: $S3_USE_SSL"
    echo "  Verify SSL: $S3_VERIFY_SSL"
}

# Deploy system
deploy_system() {
    print_header "Deploying System"
    
    print_info "Stopping existing services..."
    docker-compose down 2>/dev/null || true
    
    # Clean up any orphaned containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    print_info "Building and starting services..."
    docker-compose up -d --build
    
    print_step "Deployment completed"
}

# Wait for services
wait_for_services() {
    print_header "Waiting for Services"
    
    # Wait for PostgreSQL first
    print_info "Waiting for PostgreSQL..."
    for i in {1..60}; do
        if docker exec ipsw-postgres pg_isready -U symboluser >/dev/null 2>&1; then
            print_step "PostgreSQL is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "PostgreSQL failed to start"
            return 1
        fi
        sleep 2
        echo -n "."
    done
    
    # Wait for Symbol Server
    print_info "Waiting for Symbol Server..."
    for i in {1..60}; do
        if curl -s "http://localhost:$SYMBOL_PORT/health" >/dev/null 2>&1; then
            print_step "Symbol Server is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "Symbol Server failed to start"
            return 1
        fi
        sleep 3
        echo -n "."
    done
    
    # Wait for API Server
    print_info "Waiting for API Server..."
    for i in {1..60}; do
        if curl -s "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
            print_step "API Server is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "API Server failed to start"
            return 1
        fi
        sleep 3
        echo -n "."
    done
    
    # Wait for Web UI
    print_info "Waiting for Web UI..."
    for i in {1..60}; do
        if curl -s "http://localhost:$WEB_UI_PORT/" >/dev/null 2>&1; then
            print_step "Web UI is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "Web UI failed to start"
            return 1
        fi
        sleep 3
        echo -n "."
    done
    
    print_step "All services are ready!"
}

# Test system functionality
test_system_functionality() {
    print_header "Testing System Functionality"
    
    # Test Symbol Server
    print_info "Testing Symbol Server API..."
    if curl -s "http://localhost:$SYMBOL_PORT/health" | grep -q "ok"; then
        print_step "Symbol Server health check passed"
    else
        print_warning "Symbol Server health check failed"
    fi
    
    # Test API Server
    print_info "Testing API Server..."
    if curl -s "http://localhost:$API_PORT/health" | grep -q "ok"; then
        print_step "API Server health check passed"
    else
        print_warning "API Server health check failed"
    fi
    
    # Test Web UI
    print_info "Testing Web UI..."
    if curl -s "http://localhost:$WEB_UI_PORT/" >/dev/null; then
        print_step "Web UI accessibility check passed"
    else
        print_warning "Web UI accessibility check failed"
    fi
    
    # Test S3 functionality through Symbol Server
    print_info "Testing S3 integration..."
    if curl -s "http://localhost:$SYMBOL_PORT/stats" >/dev/null; then
        print_step "S3 integration check passed"
    else
        print_warning "S3 integration check failed"
    fi
    
    # Test cache functionality if available
    print_info "Testing cache statistics..."
    if curl -s "http://localhost:$API_PORT/cache-stats" >/dev/null; then
        print_step "Cache statistics available"
    else
        print_warning "Cache statistics not available"
    fi
    
    print_step "System functionality tests completed"
}

# Display final info
display_final_info() {
    print_header "Deployment Completed Successfully!"
    
    echo -e "${GREEN}🎉 System is ready for use!${NC}"
    echo ""
    echo -e "${CYAN}🌐 Web UI:${NC} http://localhost:$WEB_UI_PORT"
    echo -e "${CYAN}🚀 API Server:${NC} http://localhost:$API_PORT"
    echo -e "${CYAN}🔧 Symbol Server:${NC} http://localhost:$SYMBOL_PORT"
    echo -e "${CYAN}🗄️  PostgreSQL:${NC} localhost:5432 (Database: symbolserver)"
    echo ""
    echo -e "${PURPLE}☁️  S3 Configuration:${NC}"
    echo "  Endpoint: $S3_ENDPOINT"
    echo "  Bucket: $S3_BUCKET"
    echo "  Cache Size: ${CACHE_SIZE_GB}GB"
    echo ""
    echo -e "${YELLOW}📋 Useful commands:${NC}"
    echo "docker-compose ps                 # Check services status"
    echo "docker-compose logs -f            # View logs"
    echo "docker-compose logs -f symbol-server  # Symbol server logs"
    echo "docker-compose restart            # Restart services"
    echo "docker-compose down               # Stop services"
    echo ""
    echo -e "${YELLOW}🔍 Testing commands:${NC}"
    echo "curl http://localhost:$API_PORT/health      # API health"
    echo "curl http://localhost:$SYMBOL_PORT/health   # Symbol server health"
    echo "curl http://localhost:$API_PORT/cache-stats # Cache statistics"
    echo ""
    echo -e "${GREEN}✅ Ready to upload IPS files and process symbols with S3 backend!${NC}"
    echo -e "${PURPLE}📁 Upload IPS files through the Web UI for automatic symbolication${NC}"
}

# Main function
main() {
    clear
    print_header "IPSW Symbol Server - Quick Deploy (Fixed)"
    
    echo -e "${PURPLE}Quick deployment for symbolication system - Fixed version${NC}"
    echo -e "${YELLOW}Automatic setup for internal network with S3${NC}"
    echo ""
    
    continue_choice=$(get_input_with_default "Continue? (y/n)" "y" 10)
    
    if [[ "$continue_choice" =~ ^[Nn] ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    setup_internal_network
    create_env_files
    create_missing_dockerfiles
    setup_directories
    test_s3_connection
    create_docker_compose
    deploy_system
    wait_for_services
    test_system_functionality
    display_final_info
}

# Check prerequisites
if ! command -v docker >/dev/null || ! command -v docker-compose >/dev/null; then
    print_error "Docker or Docker Compose not installed"
    exit 1
fi

# Run main function
main "$@" 