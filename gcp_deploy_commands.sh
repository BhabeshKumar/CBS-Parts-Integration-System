#!/bin/bash

# Commands to run on GCP VM - CBS Parts System Deployment
echo "🚀 Setting up CBS Parts System on GCP..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "✅ Docker installed!"
fi

# Stop any existing containers
echo "🛑 Stopping existing CBS containers..."
sudo docker stop cbs-parts-system 2>/dev/null || true
sudo docker rm cbs-parts-system 2>/dev/null || true

# Load container from the uploaded file
if [ -f "cbs-system-container.tar.gz" ]; then
    echo "📂 Loading CBS container from file..."
    sudo docker load < cbs-system-container.tar.gz
    echo "✅ Container loaded!"
else
    echo "❌ Container file not found!"
    exit 1
fi

# Run the CBS Parts System container
echo "🏃 Starting CBS Parts System container..."
sudo docker run -d \
    --name cbs-parts-system \
    --restart unless-stopped \
    -p 80:8000 \
    -p 5173:5173 \
    -p 8002:8002 \
    -p 8003:8003 \
    cbsparts/cbs-system:latest

# Wait a moment for container to start
sleep 5

# Check status
echo "📊 Container status:"
sudo docker ps | grep cbs-parts-system

echo ""
echo "✅ CBS Parts System deployment complete!"
echo ""
echo "🌐 Your system is now live at:"
echo "   Order Form: http://$(curl -s ifconfig.me)/enhanced_order_form.html"
echo "   Parts API: http://$(curl -s ifconfig.me):8002/api/parts/search"
echo "   Review Interface: http://$(curl -s ifconfig.me)/parts_review_interface.html"
echo "   Quotation Generator: http://$(curl -s ifconfig.me):5173/"
echo ""
echo "🔧 Useful commands:"
echo "   Check logs: sudo docker logs cbs-parts-system"
echo "   Restart: sudo docker restart cbs-parts-system"
echo "   Stop: sudo docker stop cbs-parts-system"
echo ""
echo "🎉 CBS Parts System is ready for production use!"
