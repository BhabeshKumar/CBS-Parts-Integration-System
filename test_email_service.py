#!/usr/bin/env python3
"""
CBS Email Service Test Script
Test the email functionality with Gmail SMTP
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.email_service import email_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_connection():
    """Test email connection"""
    print("🔍 Testing email connection...")
    
    if email_service.test_email_connection():
        print("✅ Email connection successful!")
        print(f"   SMTP Host: {email_service.smtp_host}")
        print(f"   SMTP Port: {email_service.smtp_port}")
        print(f"   Email Username: {email_service.email_username}")
        return True
    else:
        print("❌ Email connection failed!")
        print("   Please check your email credentials in production.env")
        return False

def test_acceptance_link():
    """Test acceptance link generation"""
    print("\n🔗 Testing acceptance link generation...")
    
    test_quotation_data = {
        "quotationNo": "Q-TEST-001",
        "customer": {
            "name": "Test Customer",
            "email": "test@example.com"
        }
    }
    
    acceptance_link = email_service.generate_acceptance_link(test_quotation_data)
    print(f"✅ Acceptance link generated:")
    print(f"   {acceptance_link}")
    return acceptance_link

def test_email_template():
    """Test email template generation"""
    print("\n📧 Testing email template generation...")
    
    test_quotation_data = {
        "quotationNo": "Q-TEST-001",
        "customer": {
            "name": "Test Customer",
            "email": "test@example.com"
        },
        "company": {
            "name": "Concrete Batching Systems"
        },
        "items": [
            {
                "item": "Test Item",
                "code": "TEST-001",
                "description": "Test Product Description",
                "quantity": 1,
                "unitPrice": 100.00
            }
        ],
        "taxRatePercent": 23,
        "carriage": 0
    }
    
    acceptance_link = email_service.generate_acceptance_link(test_quotation_data)
    html_content = email_service.create_email_template(test_quotation_data, acceptance_link)
    
    print("✅ Email template generated successfully!")
    print(f"   Template length: {len(html_content)} characters")
    
    # Save template to file for inspection
    with open('/tmp/test_email_template.html', 'w') as f:
        f.write(html_content)
    print("   Template saved to: /tmp/test_email_template.html")
    
    return html_content

def test_send_email():
    """Test sending actual email (optional)"""
    print("\n📤 Testing email sending...")
    
    test_email = input("Enter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("⏭️  Skipping email send test")
        return
    
    test_quotation_data = {
        "quotationNo": "Q-TEST-001",
        "customer": {
            "name": "Test Customer",
            "email": test_email
        },
        "company": {
            "name": "Concrete Batching Systems"
        },
        "items": [
            {
                "item": "Test Item",
                "code": "TEST-001",
                "description": "Test Product Description",
                "quantity": 1,
                "unitPrice": 100.00
            }
        ],
        "taxRatePercent": 23,
        "carriage": 0
    }
    
    result = email_service.send_quotation_email(test_quotation_data, test_email)
    
    if result["success"]:
        print("✅ Test email sent successfully!")
        print(f"   To: {result['customer_email']}")
        print(f"   Quotation: {result['quotation_no']}")
        print(f"   Acceptance Link: {result['acceptance_link']}")
    else:
        print(f"❌ Failed to send test email: {result.get('error', 'Unknown error')}")

def main():
    """Main test function"""
    print("🧪 CBS Email Service Test")
    print("=" * 50)
    
    # Test 1: Email connection
    if not test_email_connection():
        print("\n❌ Email connection failed. Please configure email credentials first.")
        print("   Update production.env with your Gmail credentials:")
        print("   EMAIL_USERNAME=your_email@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        return
    
    # Test 2: Acceptance link generation
    test_acceptance_link()
    
    # Test 3: Email template generation
    test_email_template()
    
    # Test 4: Send test email (optional)
    test_send_email()
    
    print("\n🎉 All tests completed!")
    print("\n📋 Next steps:")
    print("   1. Start the email API: python scripts/start_email_api.py")
    print("   2. Test the quotation editor email button")
    print("   3. Check your email for the test message")

if __name__ == "__main__":
    main()
