#!/bin/bash
# CBS Parts System - One-Click GCP Deployment
# Creates GCP instance and deploys CBS system automatically

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

echo "🌐 CBS Parts System - GCP Deployment"
echo "===================================="

# Configuration
PROJECT_ID=${1:-""}
DOMAIN=${2:-""}
ZONE="us-central1-a"
REGION="us-central1"
INSTANCE_NAME="cbs-parts-system"
MACHINE_TYPE="e2-standard-2"

if [ -z "$PROJECT_ID" ]; then
    error "Usage: $0 <GCP_PROJECT_ID> [domain.com]"
fi

info "🎯 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Instance: $INSTANCE_NAME"
echo "   Zone: $ZONE"
echo "   Machine Type: $MACHINE_TYPE"
echo "   Domain: ${DOMAIN:-'Will use external IP'}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI is not installed. Install from: https://cloud.google.com/sdk/docs/install"
fi

# Set project
log "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
log "Enabling required GCP APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable dns.googleapis.com

# Create firewall rules
log "Creating firewall rules..."
gcloud compute firewall-rules create cbs-parts-http --allow tcp:80,tcp:8000,tcp:8002,tcp:8003,tcp:5173 --source-ranges 0.0.0.0/0 --target-tags http-server 2>/dev/null || warn "HTTP firewall rule already exists"
gcloud compute firewall-rules create cbs-parts-https --allow tcp:443 --source-ranges 0.0.0.0/0 --target-tags https-server 2>/dev/null || warn "HTTPS firewall rule already exists"

# Create static IP (optional)
log "Creating static IP address..."
gcloud compute addresses create cbs-parts-static-ip --region=$REGION 2>/dev/null || warn "Static IP already exists"
STATIC_IP=$(gcloud compute addresses describe cbs-parts-static-ip --region=$REGION --format='get(address)')
info "Static IP: $STATIC_IP"

# Create startup script
cat > /tmp/startup-script.sh << 'EOF'
#!/bin/bash
# Update system
apt-get update
apt-get install -y git curl unzip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create deployment directory
mkdir -p /opt/cbs-deployment
cd /opt/cbs-deployment

# Download or clone your CBS system
# This will be replaced with actual deployment in the next step
echo "Ready for CBS deployment" > /tmp/ready
EOF

# Create compute instance
log "Creating GCP Compute Engine instance..."
gcloud compute instances create $INSTANCE_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-ssd \
    --tags=http-server,https-server \
    --address=cbs-parts-static-ip \
    --metadata-from-file startup-script=/tmp/startup-script.sh \
    --maintenance-policy=MIGRATE \
    --scopes=https://www.googleapis.com/auth/cloud-platform

# Wait for instance to be ready
log "Waiting for instance to be ready..."
sleep 30

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
info "Instance External IP: $EXTERNAL_IP"

# Wait for startup script to complete
log "Waiting for startup script to complete..."
while ! gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="test -f /tmp/ready" 2>/dev/null; do
    echo -n "."
    sleep 5
done
echo ""

# Upload CBS Parts System
log "Uploading CBS Parts System..."
gcloud compute scp --recurse ../CBS_Parts_System_Production/ $INSTANCE_NAME:~/CBS_Parts_System_Production/ --zone=$ZONE

# Deploy the system
log "Deploying CBS Parts System..."
DEPLOY_DOMAIN=${DOMAIN:-$EXTERNAL_IP}

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    cd CBS_Parts_System_Production
    chmod +x deployment/deploy_production.sh
    sudo ./deployment/deploy_production.sh $DEPLOY_DOMAIN
"

# Verify deployment
log "Verifying deployment..."
sleep 10

# Test endpoints
info "Testing system endpoints..."
if curl -s -k https://$EXTERNAL_IP/health > /dev/null; then
    log "✅ Web server is responding"
else
    warn "❌ Web server not responding"
fi

if curl -s -k https://$EXTERNAL_IP/api/parts/health > /dev/null; then
    log "✅ Parts API is responding"
else
    warn "❌ Parts API not responding"
fi

if curl -s -k https://$EXTERNAL_IP/api/health > /dev/null; then
    log "✅ Form API is responding"
else
    warn "❌ Form API not responding"
fi

# Display results
echo ""
echo "🎉 CBS Parts System Deployment Complete!"
echo "========================================"
echo ""
info "🌐 Your system is now live at:"
echo "   Main URL: https://${DEPLOY_DOMAIN}"
echo "   External IP: $EXTERNAL_IP"
echo ""
info "📱 Access URLs:"
echo "   Order Form: https://${DEPLOY_DOMAIN}/enhanced_order_form.html"
echo "   Review Interface: https://${DEPLOY_DOMAIN}/parts_review_interface.html"
echo "   Quotation Generator: https://${DEPLOY_DOMAIN}/quotation/"
echo ""
info "🔧 Management:"
echo "   SSH: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo "   Logs: sudo journalctl -u cbs-parts-system -f"
echo "   Status: sudo systemctl status cbs-parts-system"
echo ""
info "💰 Monthly Cost Estimate: ~$55-60/month"
echo ""

if [ -n "$DOMAIN" ]; then
    warn "🌍 Domain Setup Required:"
    echo "   1. Go to your domain registrar"
    echo "   2. Add A record: @ -> $EXTERNAL_IP"
    echo "   3. Add A record: www -> $EXTERNAL_IP"
    echo "   4. Wait 5-10 minutes for DNS propagation"
    echo ""
fi

log "🚀 Your CBS Parts System is ready for production use!"

# Clean up
rm -f /tmp/startup-script.sh
