#!/bin/bash

echo "🚀 Building Optimized CBS Parts System..."
echo "📦 Creating clean, fast-loading container..."
echo ""

# Build optimized container
docker build --platform linux/amd64 -t cbsparts/cbs-system:optimized .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    # Save container
    docker save cbsparts/cbs-system:optimized | gzip > cbs-optimized.tar.gz
    
    # Upload to GCP
    gcloud compute scp cbs-optimized.tar.gz cbs-parts-system:~/
    
    # Deploy
    gcloud compute ssh cbs-parts-system --command="
        sudo docker stop cbs-parts-system
        sudo docker rm cbs-parts-system
        sudo docker load < cbs-optimized.tar.gz
        sudo docker run -d --name cbs-parts-system --restart unless-stopped -p 80:8000 -p 5173:5173 -p 8002:8002 -p 8003:8003 cbsparts/cbs-system:optimized
        sudo docker ps | grep cbs-parts-system
        echo '✅ Optimized container deployed - should load much faster now!'
    "
    
    echo "🎉 Deployment complete! Forms should load much faster now."
else
    echo "❌ Build failed"
    exit 1
fi
