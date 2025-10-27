#!/usr/bin/env python3
"""
CBS Email Service - Gmail SMTP Implementation
Handles sending quotation emails with PDF attachments and acceptance links
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
import urllib.parse
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Email service using Gmail SMTP for sending quotation emails"""
    
    def __init__(self):
        self.smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.company_name = os.getenv('COMPANY_NAME', 'Concrete Batching Systems')
        self.company_email = os.getenv('COMPANY_EMAIL', 'info@cbs.com')
        
        if not self.email_username or not self.email_password:
            logger.warning("Email credentials not configured. Email functionality will be disabled.")
    
    def generate_acceptance_link(self, quotation_data: Dict[str, Any]) -> str:
        """Generate Smartsheet acceptance link with auto-populated data"""
        base_url = "https://app.smartsheet.com/b/form/0198be05b2ce78a2995a10328e1d92fb"
        
        params = {
            "Quote Reference No.": quotation_data.get('quotationNo', ''),
            "Buyer's Name": quotation_data.get('customer', {}).get('name', ''),
            "Your Accounts Email Address": quotation_data.get('customer', {}).get('email', '')
        }
        
        # URL encode parameters
        encoded_params = []
        for key, value in params.items():
            encoded_key = urllib.parse.quote(key)
            encoded_value = urllib.parse.quote(str(value))
            encoded_params.append(f'{encoded_key}={encoded_value}')
        
        return f"{base_url}?{'&'.join(encoded_params)}"
    
    def generate_pdf_url(self, quotation_data: Dict[str, Any]) -> str:
        """Generate PDF URL for the quotation"""
        quotation_no = quotation_data.get('quotationNo', '')
        return f"http://{os.getenv('CBS_DOMAIN', 'localhost')}:5173/?data={self._encode_quotation_data(quotation_data)}"
    
    def _encode_quotation_data(self, quotation_data: Dict[str, Any]) -> str:
        """Encode quotation data for URL parameter"""
        import json
        import base64
        
        # Create abbreviated format for URL
        abbreviated_data = {
            'c': quotation_data.get('company', {}).get('name', ''),
            'qn': quotation_data.get('quotationNo', ''),
            'cu': quotation_data.get('customer', {}).get('name', ''),
            'ce': quotation_data.get('customer', {}).get('email', ''),
            'cp': quotation_data.get('customer', {}).get('phone', ''),
            'i': [
                {
                    'item': item.get('item', ''),
                    'code': item.get('code', ''),
                    'd': item.get('description', ''),
                    'q': item.get('quantity', 1),
                    'p': item.get('unitPrice', 0)
                }
                for item in quotation_data.get('items', [])
            ],
            't': quotation_data.get('taxRatePercent', 23),
            'carriage': quotation_data.get('carriage', 0)
        }
        
        json_data = json.dumps(abbreviated_data)
        return base64.b64encode(json_data.encode()).decode()
    
    def create_email_template(self, quotation_data: Dict[str, Any], acceptance_link: str) -> str:
        """Create HTML email template for quotation"""
        customer_name = quotation_data.get('customer', {}).get('name', 'Valued Customer')
        quotation_no = quotation_data.get('quotationNo', '')
        company_name = self.company_name
        
        # Calculate totals
        items = quotation_data.get('items', [])
        subtotal = sum(item.get('quantity', 0) * item.get('unitPrice', 0) for item in items)
        tax_rate = quotation_data.get('taxRatePercent', 23)
        tax_amount = subtotal * (tax_rate / 100)
        carriage = quotation_data.get('carriage', 0)
        grand_total = subtotal + tax_amount + carriage
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Quotation from {company_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .quotation-summary {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .acceptance-button {{
                    display: inline-block;
                    background: #28a745;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 18px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .acceptance-button:hover {{
                    background: #218838;
                }}
                .terms {{
                    background: #e9ecef;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .item-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }}
                .total-row {{
                    font-weight: bold;
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{company_name}</h1>
                <h2>Sales Quotation</h2>
            </div>
            
            <div class="content">
                <p>Dear {customer_name},</p>
                
                <p>Thank you for your interest in our products. Please find attached your quotation <strong>{quotation_no}</strong>.</p>
                
                <div class="quotation-summary">
                    <h3>Quotation Summary</h3>
                    <div class="item-row">
                        <span>Quotation Number:</span>
                        <span>{quotation_no}</span>
                    </div>
                    <div class="item-row">
                        <span>Date:</span>
                        <span>{datetime.now().strftime('%B %d, %Y')}</span>
                    </div>
                    <div class="item-row">
                        <span>Subtotal:</span>
                        <span>€{subtotal:,.2f}</span>
                    </div>
                    <div class="item-row">
                        <span>Tax ({tax_rate}%):</span>
                        <span>€{tax_amount:,.2f}</span>
                    </div>
                    <div class="item-row">
                        <span>Carriage:</span>
                        <span>€{carriage:,.2f}</span>
                    </div>
                    <div class="total-row">
                        <span>Total:</span>
                        <span>€{grand_total:,.2f}</span>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <a href="{acceptance_link}" class="acceptance-button">
                        ✓ ACCEPT QUOTATION
                    </a>
                </div>
                
                <div class="terms">
                    <h4>Terms and Conditions:</h4>
                    <ul>
                        <li>Customer will be billed after indicating acceptance of this Sales Quotation.</li>
                        <li>Payment will be due prior to delivery of the service/goods.</li>
                        <li>Please return the signed Sales Quotation to the address above.</li>
                    </ul>
                </div>
                
                <p><strong>Please click the "ACCEPT QUOTATION" button above to proceed with your order.</strong></p>
                
                <p>If you have any questions about this quotation, please don't hesitate to contact us.</p>
                
                <p>Best regards,<br>
                <strong>{company_name}</strong><br>
                Email: {self.company_email}</p>
            </div>
            
            <div class="footer">
                <p>This email was sent automatically from the {company_name} quotation system.</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def send_quotation_email(self, quotation_data: Dict[str, Any], customer_email: str) -> Dict[str, Any]:
        """Send quotation email with PDF attachment and acceptance link"""
        
        if not self.email_username or not self.email_password:
            return {
                "success": False,
                "error": "Email credentials not configured"
            }
        
        try:
            # Generate acceptance link
            acceptance_link = self.generate_acceptance_link(quotation_data)
            
            # Create email content
            html_content = self.create_email_template(quotation_data, acceptance_link)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.company_name} <{self.email_username}>"
            msg['To'] = customer_email
            msg['Subject'] = f"Quotation {quotation_data.get('quotationNo', '')} - {self.company_name}"
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Quotation email sent successfully to {customer_email}")
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "acceptance_link": acceptance_link,
                "customer_email": customer_email,
                "quotation_no": quotation_data.get('quotationNo', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to send quotation email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_email_connection(self) -> bool:
        """Test email connection"""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False

# Global email service instance
email_service = EmailService()
