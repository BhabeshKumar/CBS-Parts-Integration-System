#!/bin/bash

echo "🚀 Deploying CBS Parts System HOTFIX..."
echo "🔧 Fixes:"
echo "   ✅ Fixed quotation link variable issue"
echo "   ✅ Updated all sheet IDs to production"
echo "   ✅ Fixed domain to use 34.10.76.247 instead of localhost"
echo ""

# Build new container for AMD64 (GCP compatible)
echo "🔨 Building Docker container..."
docker build --platform linux/amd64 -t cbsparts/cbs-system:hotfix .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    
    # Save container for upload
    echo "💾 Saving container..."
    docker save cbsparts/cbs-system:hotfix | gzip > cbs-system-hotfix.tar.gz
    
    if [ $? -eq 0 ]; then
        echo "✅ Container saved: cbs-system-hotfix.tar.gz"
        echo ""
        echo "🚚 Uploading to GCP..."
        
        # Upload to GCP
        gcloud compute scp cbs-system-hotfix.tar.gz cbs-parts-system:~/
        
        if [ $? -eq 0 ]; then
            echo "✅ Upload successful!"
            echo ""
            echo "🔄 Deploying hotfix on GCP..."
            
            # Deploy on GCP
            gcloud compute ssh cbs-parts-system --command='
                sudo docker stop cbs-parts-system 2>/dev/null || true
                sudo docker rm cbs-parts-system 2>/dev/null || true
                sudo docker load < cbs-system-hotfix.tar.gz
                sudo docker run -d --name cbs-parts-system --restart unless-stopped -p 80:8000 -p 5173:5173 -p 8002:8002 -p 8003:8003 cbsparts/cbs-system:hotfix
                sleep 5
                sudo docker ps | grep cbs-parts-system
                echo ""
                echo "✅ CBS Parts System HOTFIX deployed successfully!"
                echo "🌐 Test form: http://34.10.76.247/enhanced_order_form.html"
                echo "📋 Review: http://34.10.76.247/parts_review_interface.html?quote_id=YOUR_QUOTE_ID"
            '
            
            if [ $? -eq 0 ]; then
                echo ""
                echo "🎉 HOTFIX DEPLOYMENT COMPLETE!"
                echo ""
                echo "🔧 Issues Fixed:"
                echo "   • Order submission with quotation link working"
                echo "   • Review interface using correct sheet ID"
                echo "   • All links using 34.10.76.247 domain"
                echo ""
                echo "✅ Ready to test! Submit a new order to verify the fix."
            else
                echo "❌ Deployment failed on GCP"
                exit 1
            fi
        else
            echo "❌ Upload to GCP failed"
            exit 1
        fi
    else
        echo "❌ Failed to save container"
        exit 1
    fi
else
    echo "❌ Docker build failed"
    exit 1
fi
