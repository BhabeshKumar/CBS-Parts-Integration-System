#!/bin/bash
# CBS Parts System - Build and Deploy Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"; exit 1; }
info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }

echo "🐳 CBS Parts System - Docker Build & Deploy"
echo "============================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed. Please install Docker Compose first."
fi

# Configuration
BUILD_TYPE=${1:-"production"}
DEPLOY_TARGET=${2:-"local"}

info "🎯 Configuration:"
echo "   Build Type: $BUILD_TYPE"
echo "   Deploy Target: $DEPLOY_TARGET"
echo ""

# Stop existing containers
log "Stopping existing containers..."
docker-compose down 2>/dev/null || warn "No existing containers to stop"

# Clean up old images (optional)
if [ "$BUILD_TYPE" = "clean" ]; then
    log "Cleaning up old Docker images..."
    docker system prune -f
    docker-compose build --no-cache
else
    log "Building Docker image..."
    docker-compose build
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    log "Creating .env file with default values..."
    cat > .env << EOF
# CBS Parts System Configuration
SMARTSHEET_API_TOKEN=7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB
ORDERS_INTAKE_SHEET_ID=p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1
SALES_WORKS_ORDERS_SHEET_ID=G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391
CBS_PARTS_SHEET_ID=4695255724019588
CBS_DISCOUNTS_SHEET_ID=8920011042148228
CBS_DIRECTOR_EMAIL=bhabesh.kumar@sheaney.ie
ENVIRONMENT=production
DOMAIN=localhost
EOF
fi

# Deploy based on target
case $DEPLOY_TARGET in
    "local")
        log "Deploying locally..."
        docker-compose up -d
        ;;
    "gcp")
        log "Deploying to Google Cloud Platform..."
        # GCP-specific deployment
        gcloud auth configure-docker
        docker tag cbs_parts_system_production_cbs-parts-system:latest gcr.io/$GCP_PROJECT_ID/cbs-parts-system:latest
        docker push gcr.io/$GCP_PROJECT_ID/cbs-parts-system:latest
        ;;
    "aws")
        log "Deploying to AWS..."
        # AWS-specific deployment
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
        docker tag cbs_parts_system_production_cbs-parts-system:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cbs-parts-system:latest
        docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cbs-parts-system:latest
        ;;
    "digitalocean")
        log "Deploying to DigitalOcean..."
        # DigitalOcean-specific deployment
        doctl registry login
        docker tag cbs_parts_system_production_cbs-parts-system:latest registry.digitalocean.com/$DO_REGISTRY/cbs-parts-system:latest
        docker push registry.digitalocean.com/$DO_REGISTRY/cbs-parts-system:latest
        ;;
    *)
        log "Deploying locally (default)..."
        docker-compose up -d
        ;;
esac

# Wait for services to start
log "Waiting for services to start..."
sleep 10

# Health check
log "Performing health checks..."
HEALTH_CHECK_URL="http://localhost/health"
if [ "$DEPLOY_TARGET" != "local" ]; then
    HEALTH_CHECK_URL="http://$SERVER_IP/health"
fi

for i in {1..30}; do
    if curl -s -f "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        log "✅ Health check passed!"
        break
    else
        echo -n "."
        sleep 2
    fi
    
    if [ $i -eq 30 ]; then
        warn "❌ Health check failed after 60 seconds"
    fi
done

# Display deployment information
echo ""
log "🎉 CBS Parts System Deployment Complete!"
echo "========================================"
echo ""

if [ "$DEPLOY_TARGET" = "local" ]; then
    info "🌐 Local Access URLs:"
    echo "   System Health: http://localhost/health"
    echo "   Order Form: http://localhost/enhanced_order_form.html"
    echo "   Review Interface: http://localhost/parts_review_interface.html"
    echo "   Quotation Generator: http://localhost/quotation/"
    echo ""
    info "📱 Mobile Testing (same WiFi):"
    LOCAL_IP=$(ifconfig | grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}" | grep -v 127.0.0.1 | awk '{ print $2 }' | cut -f2 -d: | head -n1)
    echo "   System Health: http://$LOCAL_IP/health"
    echo "   Order Form: http://$LOCAL_IP/enhanced_order_form.html"
    echo ""
else
    info "🌐 Production Access URLs:"
    echo "   System Health: $HEALTH_CHECK_URL"
    echo "   Order Form: http://$SERVER_IP/enhanced_order_form.html"
    echo "   Review Interface: http://$SERVER_IP/parts_review_interface.html"
    echo "   Quotation Generator: http://$SERVER_IP/quotation/"
fi

info "🔧 Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Restart: docker-compose restart"
echo "   Stop: docker-compose down"
echo "   Status: docker-compose ps"
echo ""

info "📊 Container Status:"
docker-compose ps

echo ""
log "🚀 Your CBS Parts System is ready for business!"

# Optional: Open browser on local deployment
if [ "$DEPLOY_TARGET" = "local" ] && command -v open &> /dev/null; then
    read -p "Open browser to view system? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost/enhanced_order_form.html
    fi
fi
