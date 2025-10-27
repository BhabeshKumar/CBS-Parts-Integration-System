#!/bin/bash
# CBS Email Service - Quick Deployment Script
# Adds email functionality to existing CBS system

echo "📧 CBS Email Service Deployment"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "src/services/email_service.py" ]; then
    echo "❌ Error: Please run this script from the CBS_Parts_System_Production directory"
    exit 1
fi

echo "✅ Email service files found"

# Make scripts executable
chmod +x scripts/start_email_api.py
chmod +x test_email_service.py

echo "✅ Scripts made executable"

# Test email service
echo ""
echo "🧪 Testing email service..."
python3 test_email_service.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Email service deployment completed!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Configure email credentials in production.env:"
    echo "      EMAIL_USERNAME=your_email@gmail.com"
    echo "      EMAIL_PASSWORD=your_app_password"
    echo ""
    echo "   2. Start the email API:"
    echo "      python3 scripts/start_email_api.py"
    echo ""
    echo "   3. Test the quotation editor:"
    echo "      http://34.10.76.247:5173"
    echo ""
    echo "   4. Click the '📧 Email' button to test email functionality"
    echo ""
    echo "🔗 Email API endpoints:"
    echo "   - Health: http://34.10.76.247:8004/api/email/health"
    echo "   - Test: http://34.10.76.247:8004/api/email/test-connection"
    echo "   - Send: http://34.10.76.247:8004/api/email/send-quotation"
else
    echo ""
    echo "❌ Email service test failed. Please check your configuration."
fi
