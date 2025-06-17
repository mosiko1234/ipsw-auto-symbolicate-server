#!/bin/bash

# 🚀 IPSW Symbol Server - Full System Deployment
# ==================================================
# Complete deployment script for advanced symbolication system
# Support for: API, Symbol Server, S3, Web UI, PostgreSQL

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration defaults
DEFAULT_S3_ENDPOINT="http://host.docker.internal:9000"
DEFAULT_S3_ACCESS_KEY="minioadmin"
DEFAULT_S3_SECRET_KEY="minioadmin"
DEFAULT_S3_BUCKET="ipsw"
DEFAULT_CACHE_SIZE_GB="100"
DEFAULT_WEB_UI_PORT="5001"
DEFAULT_API_PORT="8000"
DEFAULT_SYMBOL_PORT="3993"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get user input with default
get_input() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        echo -n -e "${CYAN}$prompt [$default]: ${NC}"
    else
        echo -n -e "${CYAN}$prompt: ${NC}"
    fi
    
    read -r result
    echo "${result:-$default}"
}

# Function to get yes/no input
get_yes_no() {
    local prompt="$1"
    local default="$2"
    local result
    
    while true; do
        if [ "$default" = "y" ]; then
            echo -n -e "${CYAN}$prompt [Y/n]: ${NC}"
        else
            echo -n -e "${CYAN}$prompt [y/N]: ${NC}"
        fi
        
        read -r result
        result="${result:-$default}"
        
        case "$result" in
            [Yy]|[Yy][Ee][Ss]) echo "y"; return 0;;
            [Nn]|[Nn][Oo]) echo "n"; return 1;;
            *) echo -e "${RED}Please answer yes or no.${NC}";;
        esac
    done
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("docker")
    else
        print_step "Docker found: $(docker --version)"
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    else
        print_step "Docker Compose found: $(docker-compose --version)"
    fi
    
    # Check curl
    if ! command_exists curl; then
        missing_deps+=("curl")
    else
        print_step "curl found"
    fi
    
    # Check jq (optional but recommended)
    if ! command_exists jq; then
        print_warning "jq not found (recommended for JSON parsing)"
    else
        print_step "jq found"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo "Please install the missing dependencies and run again."
        exit 1
    fi
    
    print_step "All prerequisites met!"
}

# Function to collect configuration
collect_configuration() {
    print_header "Configuration Setup"
    
    echo -e "${PURPLE}Choose deployment type:${NC}"
    echo "1) Local Development"
    echo "2) Local with MinIO"
    echo "3) External S3"
    echo "4) Internal Network"
    echo "5) Custom Configuration"
    
    while true; do
        echo -n -e "${CYAN}Choose option [1-5]: ${NC}"
        read -r DEPLOYMENT_TYPE
        case $DEPLOYMENT_TYPE in
            1|2|3|4|5) break;;
            *) print_error "Invalid option. Please choose 1-5.";;
        esac
    done
    
    # Set defaults based on deployment type
    case $DEPLOYMENT_TYPE in
        1) # Local Development
            USE_S3_OPTIMIZED="n"
            USE_POSTGRES="n"
            USE_WEB_UI="y"
            S3_ENDPOINT="$DEFAULT_S3_ENDPOINT"
            ;;
        2) # Local with MinIO
            USE_S3_OPTIMIZED="y"
            USE_POSTGRES="y"
            USE_WEB_UI="y"
            S3_ENDPOINT="$DEFAULT_S3_ENDPOINT"
            ;;
        3) # External S3
            USE_S3_OPTIMIZED="y"
            USE_POSTGRES="y"
            USE_WEB_UI="y"
            S3_ENDPOINT=""
            ;;
        4) # Internal Network
            USE_S3_OPTIMIZED="y"
            USE_POSTGRES="y"
            USE_WEB_UI="y"
            S3_ENDPOINT=""
            ;;
        5) # Custom
            USE_S3_OPTIMIZED=$(get_yes_no "Use S3 optimized storage?" "y")
            USE_POSTGRES=$(get_yes_no "Use PostgreSQL database?" "y")
            USE_WEB_UI=$(get_yes_no "Deploy Web UI?" "y")
            S3_ENDPOINT=""
            ;;
    esac
    
    # Collect S3 configuration if needed
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        print_info "S3 Configuration"
        S3_ENDPOINT=$(get_input "S3 Endpoint" "${S3_ENDPOINT:-$DEFAULT_S3_ENDPOINT}")
        S3_ACCESS_KEY=$(get_input "S3 Access Key" "$DEFAULT_S3_ACCESS_KEY")
        S3_SECRET_KEY=$(get_input "S3 Secret Key" "$DEFAULT_S3_SECRET_KEY")
        S3_BUCKET=$(get_input "S3 Bucket" "$DEFAULT_S3_BUCKET")
        S3_USE_SSL=$(get_yes_no "Use SSL for S3?" "n")
        
        if [ "$S3_USE_SSL" = "y" ]; then
            S3_VERIFY_SSL=$(get_yes_no "Verify SSL certificates?" "y")
        else
            S3_VERIFY_SSL="n"
        fi
    fi
    
    # Collect cache configuration
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        CACHE_SIZE_GB=$(get_input "Cache size in GB" "$DEFAULT_CACHE_SIZE_GB")
        CLEANUP_AFTER_HOURS=$(get_input "Cleanup files after hours" "24")
    fi
    
    # Collect port configuration
    WEB_UI_PORT=$(get_input "Web UI port" "$DEFAULT_WEB_UI_PORT")
    API_PORT=$(get_input "API port" "$DEFAULT_API_PORT")
    SYMBOL_PORT=$(get_input "Symbol Server port" "$DEFAULT_SYMBOL_PORT")
    
    # Advanced options
    if [ "$DEPLOYMENT_TYPE" = "5" ]; then
        USE_NGINX=$(get_yes_no "Use Nginx reverse proxy?" "n")
        USE_SSL_CERTS=$(get_yes_no "Use SSL certificates?" "n")
        BACKUP_ENABLED=$(get_yes_no "Enable automatic backups?" "n")
    else
        USE_NGINX="n"
        USE_SSL_CERTS="n"
        BACKUP_ENABLED="n"
    fi
}

# Function to display configuration summary
display_configuration() {
    print_header "Configuration Summary"
    
    echo -e "${CYAN}Deployment Type:${NC} $DEPLOYMENT_TYPE"
    echo -e "${CYAN}S3 Optimized:${NC} $USE_S3_OPTIMIZED"
    echo -e "${CYAN}PostgreSQL:${NC} $USE_POSTGRES"
    echo -e "${CYAN}Web UI:${NC} $USE_WEB_UI"
    
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        echo -e "${CYAN}S3 Endpoint:${NC} $S3_ENDPOINT"
        echo -e "${CYAN}S3 Bucket:${NC} $S3_BUCKET"
        echo -e "${CYAN}Cache Size:${NC} ${CACHE_SIZE_GB}GB"
    fi
    
    echo -e "${CYAN}Ports:${NC} Web UI: $WEB_UI_PORT, API: $API_PORT, Symbol: $SYMBOL_PORT"
    
    echo -n -e "${CYAN}Continue with this configuration? [Y/n]: ${NC}"
    read -r continue_choice
    continue_choice="${continue_choice:-y}"
    
    case "$continue_choice" in
        [Yy]|[Yy][Ee][Ss]) ;;
        [Nn]|[Nn][Oo]) echo "Deployment cancelled."; exit 0;;
        *) echo "Deployment cancelled."; exit 0;;
    esac
}

# Function to create environment files
create_environment_files() {
    print_header "Creating Environment Files"
    
    # Create main environment file
    cat > .env << EOF
# IPSW Symbol Server Configuration
# Generated on $(date)

# Deployment Type
DEPLOYMENT_TYPE=$DEPLOYMENT_TYPE

# Ports
WEB_UI_PORT=$WEB_UI_PORT
API_PORT=$API_PORT
SYMBOL_PORT=$SYMBOL_PORT

# Features
USE_S3_OPTIMIZED=$USE_S3_OPTIMIZED
USE_POSTGRES=$USE_POSTGRES
USE_WEB_UI=$USE_WEB_UI
USE_NGINX=$USE_NGINX
USE_SSL_CERTS=$USE_SSL_CERTS
BACKUP_ENABLED=$BACKUP_ENABLED
EOF
    
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        cat >> .env << EOF

# S3 Configuration
S3_ENDPOINT=$S3_ENDPOINT
S3_ACCESS_KEY=$S3_ACCESS_KEY
S3_SECRET_KEY=$S3_SECRET_KEY
S3_BUCKET=$S3_BUCKET
S3_USE_SSL=$S3_USE_SSL
S3_VERIFY_SSL=$S3_VERIFY_SSL

# Cache Configuration
CACHE_SIZE_GB=$CACHE_SIZE_GB
CLEANUP_AFTER_HOURS=$CLEANUP_AFTER_HOURS
MAX_CONCURRENT_DOWNLOADS=3
EOF
    fi
    
    # Create PostgreSQL environment if needed
    if [ "$USE_POSTGRES" = "y" ]; then
        cat > .env.postgres << EOF
POSTGRES_DB=symbolserver
POSTGRES_USER=symboluser
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
EOF
        print_step "PostgreSQL environment file created"
    fi
    
    print_step "Environment files created"
}

# Function to create docker-compose file
create_docker_compose() {
    print_header "Creating Docker Compose Configuration"
    
    local compose_file="docker-compose.full-system.yml"
    
    cat > $compose_file << 'EOF'
version: '3.8'

services:
EOF
    
    # Add PostgreSQL if needed
    if [ "$USE_POSTGRES" = "y" ]; then
        cat >> $compose_file << 'EOF'
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

EOF
    fi
    
    # Add Symbol Server (S3 optimized or regular)
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        cat >> $compose_file << 'EOF'
  s3-mount:
    image: s3fs/s3fs:latest
    container_name: ipsw-s3-mount
    environment:
      - S3_ENDPOINT=${S3_ENDPOINT}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - S3_USE_SSL=${S3_USE_SSL}
    volumes:
      - s3_mount:/mnt/s3:shared
    cap_add:
      - SYS_ADMIN
    devices:
      - /dev/fuse
    security_opt:
      - apparmor:unconfined
    command: >
      sh -c "
        echo '$${S3_ACCESS_KEY}:$${S3_SECRET_KEY}' > /etc/passwd-s3fs &&
        chmod 600 /etc/passwd-s3fs &&
        s3fs $${S3_BUCKET} /mnt/s3 -o url=$${S3_ENDPOINT} -o use_path_request_style -o passwd_file=/etc/passwd-s3fs -o allow_other -o use_cache=/tmp -o ensure_diskfree=500
      "
    restart: unless-stopped

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
      - CACHE_SIZE_GB=${CACHE_SIZE_GB}
      - CLEANUP_AFTER_HOURS=${CLEANUP_AFTER_HOURS}
      - MAX_CONCURRENT_DOWNLOADS=${MAX_CONCURRENT_DOWNLOADS}
    volumes:
      - ./data/cache:/app/data/cache
      - ./data/symbols:/app/data/symbols
      - ./signatures:/app/data/signatures:ro
      - s3_mount:/app/data/s3-ipsw:shared
      - processing_temp:/app/data/temp
    tmpfs:
      - /app/data/processing:size=2G,noexec,nosuid,nodev
    cap_add:
      - SYS_ADMIN
    devices:
      - /dev/fuse
    security_opt:
      - apparmor:unconfined
    restart: unless-stopped
    depends_on:
      - s3-mount
EOF
        
        if [ "$USE_POSTGRES" = "y" ]; then
            cat >> $compose_file << 'EOF'
      - postgres
EOF
        fi
    else
        # Regular symbol server
        cat >> $compose_file << 'EOF'
  symbol-server:
    build:
      context: .
      dockerfile: Dockerfile.symbol-server
    container_name: ipsw-symbol-server
    ports:
      - "${SYMBOL_PORT}:3993"
    volumes:
      - ./data:/app/data
      - ./signatures:/app/data/signatures:ro
    restart: unless-stopped
EOF
        if [ "$USE_POSTGRES" = "y" ]; then
            cat >> $compose_file << 'EOF'
    depends_on:
      - postgres
EOF
        fi
    fi
    
    # Add API Server
    cat >> $compose_file << 'EOF'

  api-server:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: ipsw-api-server
    ports:
      - "${API_PORT}:8000"
    environment:
      - SYMBOL_SERVER_URL=http://symbol-server:3993
EOF
    
    if [ "$USE_POSTGRES" = "y" ]; then
        cat >> $compose_file << 'EOF'
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
EOF
    fi
    
    cat >> $compose_file << 'EOF'
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    depends_on:
      - symbol-server
EOF
    
    if [ "$USE_POSTGRES" = "y" ]; then
        cat >> $compose_file << 'EOF'
      - postgres
EOF
    fi
    
    # Add Web UI if enabled
    if [ "$USE_WEB_UI" = "y" ]; then
        cat >> $compose_file << 'EOF'

  web-ui:
    build:
      context: .
      dockerfile: Dockerfile.webui
    container_name: ipsw-web-ui
    ports:
      - "${WEB_UI_PORT}:5001"
    environment:
      - API_SERVER_URL=http://api-server:8000
    volumes:
      - ./templates:/app/templates
      - ./static:/app/static
    restart: unless-stopped
    depends_on:
      - api-server
EOF
    fi
    
    # Add Nginx if enabled
    if [ "$USE_NGINX" = "y" ]; then
        cat >> $compose_file << 'EOF'

  nginx:
    image: nginx:alpine
    container_name: ipsw-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    restart: unless-stopped
    depends_on:
      - web-ui
      - api-server
EOF
    fi
    
    # Add volumes section
    cat >> $compose_file << 'EOF'

volumes:
EOF
    
    if [ "$USE_POSTGRES" = "y" ]; then
        cat >> $compose_file << 'EOF'
  postgres_data:
    driver: local
EOF
    fi
    
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        cat >> $compose_file << 'EOF'
  s3_mount:
    driver: local
  processing_temp:
    driver: local
EOF
    fi
    
    print_step "Docker Compose configuration created: $compose_file"
}

# Function to create additional Dockerfiles
create_dockerfiles() {
    print_header "Creating Additional Dockerfiles"
    
    # Create Web UI Dockerfile if needed
    if [ "$USE_WEB_UI" = "y" ] && [ ! -f "Dockerfile.webui" ]; then
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
        print_step "Web UI Dockerfile created"
    fi
    
    # Create API Dockerfile if needed
    if [ ! -f "Dockerfile.api" ]; then
        print_info "API Dockerfile already exists or will be created by the system"
    fi
}

# Function to create nginx configuration
create_nginx_config() {
    if [ "$USE_NGINX" = "y" ]; then
        print_header "Creating Nginx Configuration"
        
        mkdir -p nginx/ssl
        
        cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream web_ui {
        server web-ui:5001;
    }
    
    upstream api_server {
        server api-server:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://web_ui;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        location /api/ {
            proxy_pass http://api_server/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
        
        print_step "Nginx configuration created"
    fi
}

# Function to setup directories
setup_directories() {
    print_header "Setting Up Directories"
    
    # Create data directories
    mkdir -p data/{cache,symbols,downloads,temp,processing}
    mkdir -p logs
    mkdir -p backups
    
    # Create PostgreSQL init script if needed
    if [ "$USE_POSTGRES" = "y" ]; then
        mkdir -p postgres
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
EOF
        print_step "PostgreSQL initialization script created"
    fi
    
    # Set permissions
    chmod -R 755 data/
    
    print_step "Directories setup completed"
}

# Function to deploy services
deploy_services() {
    print_header "Deploying Services"
    
    local compose_file="docker-compose.full-system.yml"
    
    # Stop existing containers
    print_info "Stopping existing containers..."
    docker-compose -f $compose_file --env-file .env down 2>/dev/null || true
    
    # Build and start services
    print_info "Building and starting services..."
    
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        # Check if s3fs image exists
        if ! docker images | grep -q "s3fs/s3fs"; then
            print_info "Building S3FS image..."
            cat > Dockerfile.s3fs << 'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    s3fs \
    fuse \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /mnt/s3
WORKDIR /mnt

CMD ["s3fs"]
EOF
            docker build -t s3fs/s3fs -f Dockerfile.s3fs .
            rm Dockerfile.s3fs
        fi
    fi
    
    # Start services
    docker-compose -f $compose_file --env-file .env up -d --build
    
    print_step "Services deployment initiated"
}

# Function to wait for services
wait_for_services() {
    print_header "Waiting for Services"
    
    local max_wait=300  # 5 minutes
    local wait_time=0
    
    # Wait for PostgreSQL if enabled
    if [ "$USE_POSTGRES" = "y" ]; then
        print_info "Waiting for PostgreSQL..."
        while ! docker exec ipsw-postgres pg_isready -U "${POSTGRES_USER:-symboluser}" >/dev/null 2>&1; do
            if [ $wait_time -ge $max_wait ]; then
                print_error "PostgreSQL failed to start within $max_wait seconds"
                return 1
            fi
            sleep 5
            wait_time=$((wait_time + 5))
            echo -n "."
        done
        print_step "PostgreSQL is ready"
    fi
    
    # Wait for Symbol Server
    print_info "Waiting for Symbol Server..."
    wait_time=0
    while ! curl -sf http://localhost:$SYMBOL_PORT/health >/dev/null 2>&1; do
        if [ $wait_time -ge $max_wait ]; then
            print_error "Symbol Server failed to start within $max_wait seconds"
            return 1
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        echo -n "."
    done
    print_step "Symbol Server is ready"
    
    # Wait for API Server
    print_info "Waiting for API Server..."
    wait_time=0
    while ! curl -sf http://localhost:$API_PORT/health >/dev/null 2>&1; do
        if [ $wait_time -ge $max_wait ]; then
            print_error "API Server failed to start within $max_wait seconds"
            return 1
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        echo -n "."
    done
    print_step "API Server is ready"
    
    # Wait for Web UI if enabled
    if [ "$USE_WEB_UI" = "y" ]; then
        print_info "Waiting for Web UI..."
        wait_time=0
        while ! curl -sf http://localhost:$WEB_UI_PORT/ >/dev/null 2>&1; do
            if [ $wait_time -ge $max_wait ]; then
                print_error "Web UI failed to start within $max_wait seconds"
                return 1
            fi
            sleep 5
            wait_time=$((wait_time + 5))
            echo -n "."
        done
        print_step "Web UI is ready"
    fi
    
    print_step "All services are ready!"
}

# Function to run tests
run_tests() {
    print_header "System Testing"
    
    # Test Symbol Server
    print_info "Testing Symbol Server..."
    if curl -sf http://localhost:$SYMBOL_PORT/health | grep -q "ok"; then
        print_step "Symbol Server health check passed"
    else
        print_warning "Symbol Server health check failed"
    fi
    
    # Test API Server
    print_info "Testing API Server..."
    if curl -sf http://localhost:$API_PORT/health | grep -q "ok"; then
        print_step "API Server health check passed"
    else
        print_warning "API Server health check failed"
    fi
    
    # Test Web UI if enabled
    if [ "$USE_WEB_UI" = "y" ]; then
        print_info "Testing Web UI..."
        if curl -sf http://localhost:$WEB_UI_PORT/ >/dev/null; then
            print_step "Web UI accessibility check passed"
        else
            print_warning "Web UI accessibility check failed"
        fi
    fi
    
    # Test S3 mount if enabled
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        print_info "Testing S3 mount..."
        if docker exec ipsw-symbol-server ls /app/data/s3-ipsw/ >/dev/null 2>&1; then
            print_step "S3 mount check passed"
        else
            print_warning "S3 mount check failed"
        fi
    fi
    
    # Test cache stats if S3 optimized
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        print_info "Testing cache statistics..."
        if curl -sf http://localhost:$API_PORT/cache-stats >/dev/null; then
            print_step "Cache statistics check passed"
        else
            print_warning "Cache statistics check failed"
        fi
    fi
}

# Function to display final information
display_final_info() {
    print_header "Deployment Completed Successfully"
    
    echo -e "${GREEN}🎉 System deployed and ready for use!${NC}"
    echo ""
    
    echo -e "${CYAN}📋 Service Information:${NC}"
    echo ""
    
    # Symbol Server
    echo -e "${PURPLE}🔧 Symbol Server:${NC}"
    echo -e "   URL: http://localhost:$SYMBOL_PORT"
    echo -e "   Health: http://localhost:$SYMBOL_PORT/health"
    echo -e "   Stats: http://localhost:$SYMBOL_PORT/stats"
    echo ""
    
    # API Server
    echo -e "${PURPLE}🚀 API Server:${NC}"
    echo -e "   URL: http://localhost:$API_PORT"
    echo -e "   Health: http://localhost:$API_PORT/health"
    echo -e "   Docs: http://localhost:$API_PORT/docs"
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        echo -e "   Cache Stats: http://localhost:$API_PORT/cache-stats"
    fi
    echo ""
    
    # Web UI
    if [ "$USE_WEB_UI" = "y" ]; then
        echo -e "${PURPLE}🌐 Web UI:${NC}"
        echo -e "   URL: http://localhost:$WEB_UI_PORT"
        echo -e "   Upload files and analyze crashes"
        echo ""
    fi
    
    # PostgreSQL
    if [ "$USE_POSTGRES" = "y" ]; then
        echo -e "${PURPLE}🗄️  PostgreSQL:${NC}"
        echo -e "   Host: localhost:5432"
        echo -e "   Database: ${POSTGRES_DB:-symbolserver}"
        echo -e "   User: ${POSTGRES_USER:-symboluser}"
        echo ""
    fi
    
    # S3 Info
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        echo -e "${PURPLE}☁️  S3 Storage:${NC}"
        echo -e "   Endpoint: $S3_ENDPOINT"
        echo -e "   Bucket: $S3_BUCKET"
        echo -e "   Cache Size: ${CACHE_SIZE_GB}GB"
        echo ""
    fi
    
    echo -e "${CYAN}🛠️  Management Commands:${NC}"
    echo ""
    echo -e "${YELLOW}# View all services status:${NC}"
    echo "docker-compose -f docker-compose.full-system.yml ps"
    echo ""
    echo -e "${YELLOW}# View logs:${NC}"
    echo "docker-compose -f docker-compose.full-system.yml logs -f [service-name]"
    echo ""
    echo -e "${YELLOW}# Stop all services:${NC}"
    echo "docker-compose -f docker-compose.full-system.yml down"
    echo ""
    echo -e "${YELLOW}# Restart services:${NC}"
    echo "docker-compose -f docker-compose.full-system.yml restart"
    echo ""
    
    if [ "$USE_S3_OPTIMIZED" = "y" ]; then
        echo -e "${YELLOW}# Check S3 mount:${NC}"
        echo "docker exec ipsw-symbol-server ls -lh /app/data/s3-ipsw/"
        echo ""
        echo -e "${YELLOW}# Check cache usage:${NC}"
        echo "curl http://localhost:$API_PORT/cache-stats | jq"
        echo ""
    fi
    
    echo -e "${CYAN}📁 Configuration Files Created:${NC}"
    echo "   .env - Main configuration"
    if [ "$USE_POSTGRES" = "y" ]; then
        echo "   .env.postgres - Database configuration"
    fi
    echo "   docker-compose.full-system.yml - Docker Compose configuration"
    echo ""
    
    echo -e "${GREEN}✅ Ready to process IPS files!${NC}"
    
    if [ "$USE_WEB_UI" = "y" ]; then
        echo -e "${PURPLE}👉 Open http://localhost:$WEB_UI_PORT in your browser to get started${NC}"
    fi
}

# Function to create management scripts
create_management_scripts() {
    print_header "Creating Management Scripts"
    
    # Create start script
    cat > start-system.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting IPSW Symbol Server System..."
docker-compose -f docker-compose.full-system.yml --env-file .env up -d
echo "✅ System started!"
echo "📊 Check status: docker-compose -f docker-compose.full-system.yml ps"
EOF
    
    # Create stop script
    cat > stop-system.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping IPSW Symbol Server System..."
docker-compose -f docker-compose.full-system.yml down
echo "✅ System stopped!"
EOF
    
    # Create status script
    cat > status-system.sh << 'EOF'
#!/bin/bash
echo "📊 IPSW Symbol Server System Status:"
echo "=================================="
docker-compose -f docker-compose.full-system.yml ps
echo ""
echo "🔍 Quick Health Checks:"
EOF
    
    echo "curl -s http://localhost:$API_PORT/health 2>/dev/null && echo '✅ API Server: OK' || echo '❌ API Server: DOWN'" >> status-system.sh
    echo "curl -s http://localhost:$SYMBOL_PORT/health 2>/dev/null && echo '✅ Symbol Server: OK' || echo '❌ Symbol Server: DOWN'" >> status-system.sh
    
    if [ "$USE_WEB_UI" = "y" ]; then
        echo "curl -s http://localhost:$WEB_UI_PORT/ 2>/dev/null >/dev/null && echo '✅ Web UI: OK' || echo '❌ Web UI: DOWN'" >> status-system.sh
    fi
    
    # Create backup script
    if [ "$BACKUP_ENABLED" = "y" ]; then
        cat > backup-system.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating system backup..."
cp .env* "$BACKUP_DIR/"
cp docker-compose.full-system.yml "$BACKUP_DIR/"

if [ -d "data" ]; then
    echo "📁 Backing up data directory..."
    tar -czf "$BACKUP_DIR/data_backup.tar.gz" data/
fi

echo "✅ Backup created in: $BACKUP_DIR"
EOF
        chmod +x backup-system.sh
    fi
    
    # Make scripts executable
    chmod +x start-system.sh stop-system.sh status-system.sh
    
    print_step "Management scripts created"
}

# Main deployment function
main() {
    clear
    print_header "IPSW Symbol Server - Full System Deployment"
    
    echo -e "${PURPLE}Welcome to the complete deployment system for advanced symbolication server${NC}"
    echo ""
    
    # Run deployment steps
    check_prerequisites
    collect_configuration
    display_configuration
    create_environment_files
    setup_directories
    create_docker_compose
    create_dockerfiles
    create_nginx_config
    create_management_scripts
    deploy_services
    
    # Wait for services and test
    if wait_for_services; then
        run_tests
        display_final_info
    else
        print_error "Some services failed to start. Check logs with:"
        echo "docker-compose -f docker-compose.full-system.yml logs"
        exit 1
    fi
}

# Run main function
main "$@" 