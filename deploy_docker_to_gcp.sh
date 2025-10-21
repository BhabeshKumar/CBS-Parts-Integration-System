#!/bin/bash

# CBS Parts System - Docker Container Deployment to GCP
echo "🚀 CBS Parts System - Docker Deployment to GCP"
echo "================================================"

# Configuration
PROJECT_ID="cbs-parts-live-441711"
INSTANCE_NAME="cbs-parts-system"
ZONE="us-central1-a"
MACHINE_TYPE="e2-medium"
CONTAINER_IMAGE="cbsparts/cbs-system:latest"
DOMAIN="34.10.76.247"  # Current GCP VM IP

echo "📋 Deployment Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Instance: $INSTANCE_NAME"
echo "   Zone: $ZONE"
echo "   Container: $CONTAINER_IMAGE"
echo ""

# Step 1: Upload container image (if using tar.gz method)
echo "🐳 Step 1: Preparing container..."
if [ -f "cbs-system-container.tar.gz" ]; then
    echo "   Found local container file"
    echo "   Upload to GCP VM: scp cbs-system-container.tar.gz $INSTANCE_NAME:~/"
else
    echo "   Will use Docker Hub image: $CONTAINER_IMAGE"
fi

# Step 2: Create GCP deployment script
echo "📝 Step 2: Creating GCP deployment script..."
cat > gcp_deploy_commands.sh << 'EOF'
#!/bin/bash

# Commands to run on GCP VM
echo "🚀 Setting up CBS Parts System on GCP..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
sudo docker stop cbs-parts-system 2>/dev/null || true
sudo docker rm cbs-parts-system 2>/dev/null || true

# Load container (if using tar.gz method)
if [ -f "cbs-system-container.tar.gz" ]; then
    echo "📂 Loading container from file..."
    sudo docker load < cbs-system-container.tar.gz
    CONTAINER_IMAGE="cbsparts/cbs-system:latest"
else
    # Pull from Docker Hub
    echo "📥 Pulling container from Docker Hub..."
    sudo docker pull cbsparts/cbs-system:latest
    CONTAINER_IMAGE="cbsparts/cbs-system:latest"
fi

# Run the container
echo "🏃 Starting CBS Parts System container..."
sudo docker run -d \
    --name cbs-parts-system \
    --restart unless-stopped \
    -p 80:8000 \
    -p 5173:5173 \
    -p 8002:8002 \
    -p 8003:8003 \
    -e DOMAIN=34.10.76.247 \
    $CONTAINER_IMAGE

# Check status
echo "✅ Deployment complete!"
echo "📊 Container status:"
sudo docker ps | grep cbs-parts-system

echo ""
echo "🌐 Your CBS Parts System is now live at:"
echo "   Review Interface: http://34.10.76.247/parts_review_interface.html"
echo "   Parts API: http://34.10.76.247:8002/api/parts/search"
echo "   Quotation Generator: http://34.10.76.247:5173/"
echo "   🔄 Smartsheet Polling: Every 1 minute (background service)"
echo ""
echo "🔧 To check logs:"
echo "   sudo docker logs cbs-parts-system"
EOF

chmod +x gcp_deploy_commands.sh

echo "✅ Deployment scripts created!"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "Method 1 - Using Docker Hub:"
echo "1. Push container: docker login && docker push cbsparts/cbs-system:latest"
echo "2. Copy script to GCP: gcloud compute scp gcp_deploy_commands.sh $INSTANCE_NAME:~/ --zone=$ZONE"
echo "3. Run on GCP: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='~/gcp_deploy_commands.sh'"
echo ""
echo "Method 2 - Using container file:"
echo "1. Upload container: gcloud compute scp cbs-system-container.tar.gz $INSTANCE_NAME:~/ --zone=$ZONE"
echo "2. Upload script: gcloud compute scp gcp_deploy_commands.sh $INSTANCE_NAME:~/ --zone=$ZONE"
echo "3. Run deployment: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='~/gcp_deploy_commands.sh'"
echo ""
echo "🔥 Your system will be live and running 24/7!"
