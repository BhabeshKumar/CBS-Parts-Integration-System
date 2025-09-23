#!/bin/bash
# CBS Parts System - 100% Ready Production Deployment
# All your API tokens and Sheet IDs are pre-configured

set -e

echo "🚀 CBS Parts System - Ready for Production!"
echo "==========================================="
echo ""
echo "✅ Your configuration is 100% ready:"
echo "   • Smartsheet API Token: 7R7hgaXfL3...SgB (configured)"
echo "   • Orders Intake Sheet: GxQx8H8...3c71 (configured)"
echo "   • Sales Orders Sheet: G7Wm6pV...Q391 (configured)"
echo "   • CBS Parts Sheet: 4695255...9588 (configured)"
echo "   • CBS Discounts Sheet: 8920011...8228 (configured)"
echo "   • CBS Director: bhabesh.kumar@sheaney.ie (configured)"
echo ""

# Check if domain provided
if [ -z "$1" ]; then
    echo "❌ Please provide your domain name:"
    echo ""
    echo "Usage: ./DEPLOY_NOW.sh your-domain.com"
    echo ""
    echo "Examples:"
    echo "   ./DEPLOY_NOW.sh cbsparts.yourcompany.com"
    echo "   ./DEPLOY_NOW.sh orders.cbsltd.ie"
    echo "   ./DEPLOY_NOW.sh parts.concretebatching.com"
    echo ""
    exit 1
fi

DOMAIN=$1

echo "🎯 Deploying to domain: $DOMAIN"
echo ""

# Confirm deployment
read -p "🤔 Ready to deploy CBS Parts System to $DOMAIN? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "🏗️  Starting production deployment..."
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "⚠️  This script needs to run as root for production deployment"
   echo "   Re-running with sudo..."
   echo ""
   sudo "$0" "$@"
   exit $?
fi

# Run the main deployment script
echo "🚀 Executing production deployment script..."
echo ""

chmod +x deployment/deploy_production.sh
./deployment/deploy_production.sh "$DOMAIN"

echo ""
echo "🎉 CBS Parts System Deployment Complete!"
echo ""
echo "🌐 Your system is now live at:"
echo "   • Customer Orders: https://$DOMAIN/templates/enhanced_order_form.html"
echo "   • CBS Review: https://$DOMAIN/templates/parts_review_interface.html"
echo "   • Quotation Generator: https://$DOMAIN/quotation/"
echo ""
echo "🔧 System Management:"
echo "   • Status: systemctl status cbs-parts-system"
echo "   • Logs: journalctl -u cbs-parts-system -f"
echo "   • Restart: systemctl restart cbs-parts-system"
echo ""
echo "📊 All your Smartsheet data is connected and ready!"
echo "✅ 24/7 monitoring and auto-restart enabled"
echo "🔒 SSL/HTTPS configured automatically"
echo ""
echo "🎯 Next Steps:"
echo "   1. Test customer order form"
echo "   2. Test CBS review interface" 
echo "   3. Configure email/Slack alerts if needed"
echo "   4. Share URLs with your team"
echo ""
echo "💼 Your CBS Parts System is ready for business! 🚀"
