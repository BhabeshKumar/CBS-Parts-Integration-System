#!/bin/bash

echo "🚀 Deploying CBS Parts System Production Updates..."
echo "📝 Updates include:"
echo "   ✅ Updated Smartsheet ID to production version"
echo "   ✅ Added @ symbol to quotation links in Smartsheet"
echo "   ✅ Removed unnecessary popups and test buttons"
echo "   ✅ Added Sheaney footer to all pages"
echo ""

# Build new container for AMD64 (GCP compatible)
echo "🔨 Building Docker container for production..."
docker build --platform linux/amd64 -t cbsparts/cbs-system:production-v2 .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    
    # Save container for upload
    echo "💾 Saving container for upload..."
    docker save cbsparts/cbs-system:production-v2 | gzip > cbs-system-production-v3.tar.gz
    
    if [ $? -eq 0 ]; then
        echo "✅ Container saved successfully!"
        echo "📦 File: cbs-system-production-v2.tar.gz"
        echo ""
        echo "🚚 Uploading to GCP..."
        
        # Upload to GCP
        gcloud compute scp cbs-system-production-v2.tar.gz cbs-parts-system:~/
        
        if [ $? -eq 0 ]; then
            echo "✅ Upload successful!"
            echo ""
            echo "🔄 Deploying on GCP..."
            
            # Deploy on GCP
            gcloud compute ssh cbs-parts-system --command='
                sudo docker stop cbs-parts-system 2>/dev/null || true
                sudo docker rm cbs-parts-system 2>/dev/null || true
                sudo docker load < cbs-system-production-v2.tar.gz
                sudo docker run -d --name cbs-parts-system --restart unless-stopped -p 80:8000 -p 5173:5173 -p 8002:8002 -p 8003:8003 cbsparts/cbs-system:production-v2
                sleep 5
                sudo docker ps | grep cbs-parts-system
                echo "✅ CBS Parts System Production v2 deployed successfully!"
            '
            
            if [ $? -eq 0 ]; then
                echo ""
                echo "🎉 DEPLOYMENT COMPLETE!"
                echo "🌐 Live system: http://34.10.76.247/"
                echo "📋 Order form: http://34.10.76.247/enhanced_order_form.html"
                echo "👤 Review interface: http://34.10.76.247/parts_review_interface.html?quote_id=YOUR_QUOTE_ID"
                echo ""
                echo "🔧 New features:"
                echo "   • Production Smartsheet ID updated"
                echo "   • Quotation links with @ symbol in Smartsheet"
                echo "   • Cleaner UI with fewer popups"
                echo "   • Powered by Sheaney footer"
                echo ""
                echo "✨ Ready for production use!"
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
