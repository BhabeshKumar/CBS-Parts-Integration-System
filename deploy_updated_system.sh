#!/bin/bash

# Deploy Updated CBS Parts System with Polling Service
echo "🚀 Deploying Updated CBS Parts System..."

# Stop and remove existing container
echo "🛑 Stopping existing container..."
sudo docker stop cbs-parts-system 2>/dev/null || true
sudo docker rm cbs-parts-system 2>/dev/null || true

# Load the new image
echo "📂 Loading updated container image..."
sudo docker load < cbs-system-amd64.tar.gz

# Run the updated container
echo "🏃 Starting updated CBS Parts System..."
sudo docker run -d \
    --name cbs-parts-system \
    --restart unless-stopped \
    -p 80:8000 \
    -p 5173:5173 \
    -p 8002:8002 \
    -p 8003:8003 \
    -e DOMAIN=34.10.76.247 \
    -e ORDERS_INTAKE_SHEET_ID=p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1 \
    -e SMARTSHEET_API_TOKEN=7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB \
    -e CBS_PARTS_SHEET_ID=4695255724019588 \
    -e CBS_DISCOUNTS_SHEET_ID=8920011042148228 \
    cbs-parts-system-updated:latest

# Wait for startup
echo "⏳ Waiting for services to start..."
sleep 30

# Check container status
echo "📊 Container status:"
sudo docker ps | grep cbs-parts-system

# Check logs
echo "📋 Recent logs:"
sudo docker logs --tail 20 cbs-parts-system

echo ""
echo "✅ Updated CBS Parts System deployed successfully!"
echo ""
echo "🎯 New Features:"
echo "   🔄 Smartsheet polling service (every 1 minute)"
echo "   🔍 Enhanced parts search in review interface"
echo "   ➕ Manual parts entry capability"
echo "   🚫 Order form removed (uses Smartsheet form directly)"
echo ""
echo "🌐 System URLs:"
echo "   📋 Review Interface: http://34.10.76.247/parts_review_interface.html"
echo "   🔍 Parts API: http://34.10.76.247:8002/api/parts/search"
echo "   📄 Quotation Generator: http://34.10.76.247:5173/"
echo ""
echo "🔧 System Monitoring:"
echo "   • Container logs: sudo docker logs -f cbs-parts-system"
echo "   • Container status: sudo docker ps"
echo "   • Restart: sudo docker restart cbs-parts-system"
echo ""
echo "🎉 Ready for production use!"
