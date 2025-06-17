#!/bin/bash

# IPSW Auto-Symbolication with Symbol Server Edition
# Deployment Script for Internal Networks
# Version: 2.0 - Symbol Server Edition

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ipsw-symbol-server"
COMPOSE_FILE="docker-compose.symbol-server.yml"
ENV_FILE=".env"

# Functions
print_header() {
    echo -e "${PURPLE}================================================================================================${NC}"
    echo -e "${WHITE}🚀 IPSW Auto-Symbolication with Symbol Server Edition${NC}"
    echo -e "${WHITE}   Deployment Script for Internal Networks${NC}"
    echo -e "${PURPLE}================================================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "System requirements met"
}

configure_environment() {
    print_step "Configuring environment..."
    
    # Use env.symbol-server.txt as source, not .env
    ENV_SOURCE_FILE="env.symbol-server.txt"
    
    if [ ! -f "$ENV_SOURCE_FILE" ]; then
        print_error "Environment source file $ENV_SOURCE_FILE not found!"
        exit 1
    fi
    
    # Copy environment file only if it doesn't exist or is different
    if [ ! -f ".env" ] || ! cmp -s "$ENV_SOURCE_FILE" ".env"; then
        cp "$ENV_SOURCE_FILE" .env
        print_info "Environment file copied from $ENV_SOURCE_FILE"
    else
        print_info "Environment file already exists and is up to date"
    fi
    
    # Prompt for S3 configuration
    echo ""
    print_info "S3 Configuration Required:"
    echo "Please configure your internal S3 endpoint in the .env file"
    echo ""
    
    read -p "S3 Endpoint (e.g., https://s3.company.com): " s3_endpoint
    read -p "S3 Bucket (e.g., ipsw-files): " s3_bucket
    
    if [[ ! -z "$s3_endpoint" ]]; then
        sed -i.bak "s|S3_ENDPOINT=.*|S3_ENDPOINT=$s3_endpoint|" .env
    fi
    
    if [[ ! -z "$s3_bucket" ]]; then
        sed -i.bak "s|S3_BUCKET=.*|S3_BUCKET=$s3_bucket|" .env
    fi
    
    print_success "Environment configured"
}

load_images_from_files() {
    print_step "Loading Docker images from files..."
    
    DOCKER_IMAGES_DIR="$SCRIPT_DIR/docker_images"
    
    if [ ! -d "$DOCKER_IMAGES_DIR" ]; then
        print_error "Docker images directory not found: $DOCKER_IMAGES_DIR"
        return 1
    fi
    
    # Image file mappings - using simple approach
    local image_files=(
        "ipsw-symbol-server.tar.gz"
        "postgres-15-alpine.tar.gz"
        "blacktop-ipswd.tar.gz"
        "nginx-alpine.tar.gz"
    )
    
    local loaded_count=0
    for file in "${image_files[@]}"; do
        local file_path="$DOCKER_IMAGES_DIR/$file"
        
        if [ -f "$file_path" ]; then
            print_info "Loading Docker image from $file..."
            if docker load -i "$file_path"; then
                print_success "Loaded image from $file"
                ((loaded_count++))
            else
                print_error "Failed to load image from $file"
                return 1
            fi
        else
            print_warning "Image file not found: $file_path"
        fi
    done
    
    if [ $loaded_count -gt 0 ]; then
        print_success "Successfully loaded $loaded_count Docker images"
    else
        print_warning "No image files were found to load"
        return 1
    fi
    
    return 0
}

check_images() {
    print_step "Checking Docker images..."
    
    # Required images for Symbol Server Edition
    REQUIRED_IMAGES=(
        "ipsw-symbol-server:latest"
        "postgres:15-alpine"
        "blacktop/ipswd:latest"
        "nginx:alpine"
    )
    
    missing_images=()
    
    for image in "${REQUIRED_IMAGES[@]}"; do
        if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image"; then
            missing_images+=("$image")
        fi
    done
    
    if [ ${#missing_images[@]} -eq 0 ]; then
        print_success "All required Docker images are available"
        return 0
    fi
    
    print_warning "Missing Docker images:"
    for image in "${missing_images[@]}"; do
        echo "   ❌ $image"
    done
    echo ""
    
    # Try to load images from files
    print_info "Attempting to load missing images from docker_images directory..."
    if load_images_from_files; then
        # Check again after loading
        missing_images=()
        for image in "${REQUIRED_IMAGES[@]}"; do
            if ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image"; then
                missing_images+=("$image")
            fi
        done
        
        if [ ${#missing_images[@]} -eq 0 ]; then
            print_success "All required Docker images are now available"
            return 0
        else
            print_error "Still missing images after loading:"
            for image in "${missing_images[@]}"; do
                echo "   ❌ $image"
            done
            exit 1
        fi
    else
        print_error "Failed to load images from files"
        print_error "Please ensure all image files are present in docker_images/ directory"
        exit 1
    fi
}

start_services() {
    print_step "Starting Symbol Server Edition services..."
    
    # Start all services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_success "Services started"
}

wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    echo "Waiting for PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T symbols-postgres pg_isready -U symbols_admin -d symbols &> /dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "PostgreSQL failed to start within 60 seconds"
        exit 1
    fi
    
    # Wait for API
    echo "Waiting for API..."
    timeout=120
    while [ $timeout -gt 0 ]; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            break
        fi
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "API failed to start within 120 seconds"
        exit 1
    fi
    
    print_success "All services are ready"
}

test_deployment() {
    print_step "Testing deployment..."
    
    # Test API health
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "API health check passed"
    else
        print_warning "API health check failed"
    fi
    
    # Test Symbol Server connection
    if curl -s http://localhost:8000/symbol-server/health | grep -q "available"; then
        print_success "Symbol Server connection verified"
    else
        print_warning "Symbol Server connection failed"
    fi
    
    # Test S3 connection
    if curl -s http://localhost:8000/s3/stats | grep -q "success"; then
        print_success "S3 connection verified"
    else
        print_warning "S3 connection failed - please check your S3 configuration"
    fi
}

show_status() {
    print_step "Deployment Status:"
    echo ""
    
    # Show running containers
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    print_info "Service URLs:"
    echo "   🌐 Web Interface: http://localhost:8000"
    echo "   📊 API Health: http://localhost:8000/health"
    echo "   🔧 Symbol Server: http://localhost:8000/symbol-server/health"
    echo "   📦 S3 Stats: http://localhost:8000/s3/stats"
    echo "   🗄️  Database: localhost:5433 (symbols_admin/SymbolsSecurePass2024!)"
    echo ""
    
    print_info "Logs:"
    echo "   docker-compose -f $COMPOSE_FILE logs -f api"
    echo "   docker-compose -f $COMPOSE_FILE logs -f ipswd-symbol-server"
    echo "   docker-compose -f $COMPOSE_FILE logs -f symbols-postgres"
    echo ""
}

cleanup() {
    print_step "Cleaning up previous deployment..."
    
    # Stop and remove containers
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    # Remove old images (optional)
    if [ "$1" = "--clean-images" ]; then
        docker image prune -f
    fi
    
    print_success "Cleanup completed"
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --clean             Clean up previous deployment"
    echo "  --clean-images      Clean up previous deployment and remove old images"
    echo "  --status            Show deployment status"
    echo "  --logs              Show service logs"
    echo "  --stop              Stop all services"
    echo ""
    echo "Examples:"
    echo "  $0                  Deploy Symbol Server Edition"
    echo "  $0 --clean          Clean and redeploy"
    echo "  $0 --status         Show current status"
    echo ""
}

# Main execution
main() {
    case "${1:-}" in
        --help)
            show_help
            exit 0
            ;;
        --clean)
            print_header
            cleanup
            exit 0
            ;;
        --clean-images)
            print_header
            cleanup --clean-images
            exit 0
            ;;
        --status)
            print_header
            show_status
            exit 0
            ;;
        --logs)
            docker-compose -f "$COMPOSE_FILE" logs -f
            exit 0
            ;;
        --stop)
            print_header
            print_step "Stopping services..."
            docker-compose -f "$COMPOSE_FILE" down
            print_success "Services stopped"
            exit 0
            ;;
        "")
            # Default deployment
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    
    # Main deployment flow
    print_header
    
    check_requirements
    check_images
    configure_environment
    cleanup
    start_services
    wait_for_services
    test_deployment
    show_status
    
    echo ""
    print_success "🎉 Symbol Server Edition deployed successfully!"
    echo ""
    print_info "Next steps:"
    echo "1. Open http://localhost:8000 in your browser"
    echo "2. Configure your S3 endpoint if needed"
    echo "3. Upload IPSW files to your S3 bucket"
    echo "4. Test symbolication with crash logs"
    echo ""
    print_info "For support, check the logs or documentation."
}

# Run main function
main "$@" 