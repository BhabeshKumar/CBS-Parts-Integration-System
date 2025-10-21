#!/bin/bash

echo "🔧 Deploying fixed CBS Parts System..."

# Stop existing container
sudo docker stop cbs-parts-system 2>/dev/null || true
sudo docker rm cbs-parts-system 2>/dev/null || true

# Load fixed image
echo "📂 Loading fixed image..."
sudo docker load < cbs-system-fixed.tar.gz

# Run with fixed imports
echo "🚀 Starting fixed system..."
sudo docker run -d \
    --name cbs-parts-system \
    --restart unless-stopped \
    -p 80:8000 \
    -p 5173:5173 \
    -p 8002:8002 \
    -p 8003:8003 \
    -v /opt/cbs-data:/app/data \
    -e DOMAIN=34.10.76.247 \
    -e ORDERS_INTAKE_SHEET_ID=p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1 \
    -e SMARTSHEET_API_TOKEN=7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB \
    -e CBS_PARTS_SHEET_ID=4695255724019588 \
    -e CBS_DISCOUNTS_SHEET_ID=8920011042148228 \
    cbs-parts-system-fixed:latest

sleep 20
echo "📊 Status:"
sudo docker ps | grep cbs-parts-system
echo "✅ Fixed system deployed!"

