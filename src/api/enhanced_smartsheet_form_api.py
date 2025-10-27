"""
Enhanced Smartsheet Form API with production-ready error handling and stability
"""
import logging
import time
import asyncio
import json
from functools import wraps
from typing import Optional, Dict, List, Any
import traceback
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
import uvicorn
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import urllib.parse
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/form_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CBS Form API",
    description="Production-ready CBS Smartsheet Form API",
    version="1.0.0"
)

# Enhanced CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request models with validation
class OrderSubmissionRequest(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_company: Optional[str] = ""
    customer_address: Optional[str] = ""
    customer_phone: Optional[str] = ""
    additional_notes: Optional[str] = ""
    selected_parts: List[Dict[str, Any]] = []
    
    @validator('customer_name')
    def validate_customer_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Customer name must be at least 2 characters')
        return v.strip()
    
    @validator('selected_parts')
    def validate_selected_parts(cls, v):
        if not v:
            raise ValueError('At least one part must be selected')
        return v

class OrderUpdateRequest(BaseModel):
    selected_parts: Optional[List[Dict[str, Any]]] = None
    pricing_updates: Optional[Dict[str, Any]] = None
    discount_percentage: Optional[float] = None
    additional_notes: Optional[str] = None

class QuotationEmailRequest(BaseModel):
    """Request model for sending quotation emails"""
    quotation_data: Dict[str, Any]
    customer_email: EmailStr

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": time.time(),
            "path": str(request.url),
            "message": "Please try again or contact support"
        }
    )

# Retry decorator
def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator

# Circuit breaker for external service calls
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e

smartsheet_circuit_breaker = CircuitBreaker()

# Health check
@app.get("/api/health")
async def health_check():
    try:
        from src.services.smartsheet_service import SmartsheetService
        from config.my_config import ORDERS_INTAKE_SHEET_ID
        
        # Test Smartsheet connectivity
        smartsheet_status = "healthy"
        try:
            service = SmartsheetService()
            sheet_info = service.client.Sheets.get_sheet(ORDERS_INTAKE_SHEET_ID, include="summary")
            if not sheet_info:
                smartsheet_status = "degraded"
        except Exception as e:
            logger.warning(f"Smartsheet health check failed: {e}")
            smartsheet_status = "unhealthy"
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "smartsheet": smartsheet_status,
                "circuit_breaker": smartsheet_circuit_breaker.state
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/api/submit-order")
@retry_on_failure(max_retries=3, delay=2.0)
async def submit_order(order_data: OrderSubmissionRequest):
    """Enhanced order submission with validation and error handling"""
    try:
        logger.info(f"Processing order submission for {order_data.customer_email}")
        
        # Generate quote ID
        import uuid
        from datetime import datetime
        
        quote_id = f"Q-{int(datetime.now().timestamp())}"
        
        # Prepare row data with validation (using correct Smartsheet column names)
        row_data = {
            # Skip Quote ID - it's a system AUTO_NUMBER column
            "Buyer's Name": order_data.customer_name[:100],  # Limit length
            "Buyer's Email Address": str(order_data.customer_email),
            "Buyer's Mobile No.": (order_data.customer_phone or "")[:50],
            "Delivery Address": (order_data.customer_address or "")[:500],
            "Order Date": str(order_data.order_date) if hasattr(order_data, 'order_date') else datetime.now().strftime('%Y-%m-%d'),
            "Required-By Date": str(order_data.required_by_date) if hasattr(order_data, 'required_by_date') else "",
            "Additional Notes": (order_data.additional_notes or "")[:1000],
            "Order Status": "Not Started"
            # Skip Created Date - it's a system column
            # Note: Quotation Link will be added after we get the actual Quote ID
        }
        
        # Add parts data if we have selected parts
        if order_data.selected_parts:
            # Create formatted additional notes with parts
            parts_text = "SELECTED PARTS:\n"
            for part in order_data.selected_parts:
                # Try both 'product_code' and 'code' field names
                code = part.get('product_code') or part.get('code', 'N/A')
                parts_text += f"{code} - {part.get('description', 'N/A')} (Qty: {part.get('quantity', 1)})\n"
            
            if row_data["Additional Notes"]:
                row_data["Additional Notes"] = f"{row_data['Additional Notes']}\n\n{parts_text}"
            else:
                row_data["Additional Notes"] = parts_text
        
        # Generate review link
        domain = os.getenv('CBS_DOMAIN', 'localhost')  # Default to localhost for development
        protocol = 'http'  # Use HTTP for GCP deployment
        port = ''  # No port needed for production
        review_link = f"{protocol}://{domain}/parts_review_interface.html?quote_id={quote_id}"
        
        # Submit to Smartsheet with circuit breaker
        from src.services.smartsheet_service import SmartsheetService
        from config.my_config import ORDERS_INTAKE_SHEET_ID
        
        def submit_to_smartsheet():
            service = SmartsheetService()
            result = service.add_row(ORDERS_INTAKE_SHEET_ID, row_data)
            return result
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: smartsheet_circuit_breaker.call(submit_to_smartsheet)
        )
        
        if not result or not hasattr(result, 'id'):
            raise HTTPException(status_code=500, detail="Failed to create order record")
        
        # Get the actual Quote ID from Smartsheet (it's an AUTO_NUMBER column)
        actual_quote_id = None
        try:
            # Fetch the row to get the actual Quote ID
            service = SmartsheetService()
            sheet = service.client.Sheets.get_sheet(ORDERS_INTAKE_SHEET_ID)
            for row in sheet.rows:
                if row.id == result.id:
                    row_data_dict = service.get_row_data(sheet, row)
                    actual_quote_id = row_data_dict.get('Quote ID', quote_id)
                    break
        except Exception as e:
            logger.warning(f"Could not fetch actual Quote ID: {e}")
            actual_quote_id = quote_id
        
        # Update review link with actual Quote ID
        actual_review_link = f"{protocol}://{domain}/parts_review_interface.html?quote_id={actual_quote_id}"
        
        # Update the Smartsheet row with the quotation link now that we have the actual Quote ID
        try:
            from smartsheet.models import Cell, Row
            
            # Find the Quotation Link column
            quotation_link_column = None
            for col in sheet.columns:
                if col.title == "Quotation Link":
                    quotation_link_column = col
                    break
            
            if quotation_link_column:
                # Create update row with the quotation link
                update_row = Row()
                update_row.id = result.id
                update_row.cells.append(Cell({
                    'column_id': quotation_link_column.id,
                    'value': actual_review_link
                }))
                
                # Update the row in Smartsheet
                service.client.Sheets.update_rows(ORDERS_INTAKE_SHEET_ID, [update_row])
                logger.info(f"Updated quotation link for Quote ID: {actual_quote_id}")
            else:
                logger.warning("Quotation Link column not found in sheet")
                
        except Exception as e:
            logger.warning(f"Could not update quotation link: {e}")
        
        logger.info(f"Order submitted successfully: {actual_quote_id}, Row ID: {result.id}")
        
        return {
            "success": True,
            "quote_id": actual_quote_id,
            "row_id": result.id,
            "review_link": actual_review_link,
            "parts_count": len(order_data.selected_parts),
            "timestamp": time.time(),
            "message": f"Order submitted successfully with Quote ID: {actual_quote_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order submission failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to submit order: {str(e)}"
        )

@app.get("/api/order/{quote_id}")
@retry_on_failure(max_retries=3, delay=1.0)
async def get_order_details(quote_id: str):
    """Get order details with enhanced error handling"""
    try:
        if not quote_id or not quote_id.startswith('Q-'):
            raise HTTPException(status_code=400, detail="Invalid quote ID format")
        
        from src.services.smartsheet_service import SmartsheetService
        from config.my_config import ORDERS_INTAKE_SHEET_ID
        
        logger.info(f"Looking for Quote ID {quote_id} in sheet: {ORDERS_INTAKE_SHEET_ID}")
        
        def get_from_smartsheet():
            service = SmartsheetService()
            sheet = service.client.Sheets.get_sheet(ORDERS_INTAKE_SHEET_ID)
            
            for row in sheet.rows:
                for cell in row.cells:
                    if (hasattr(cell, 'column_id') and 
                        hasattr(cell, 'value') and 
                        cell.value == quote_id):
                        return service.get_row_data(sheet, row)
            return None
        
        order_data = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: smartsheet_circuit_breaker.call(get_from_smartsheet)
        )
        
        if not order_data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Parse parts data safely
        selected_parts = []
        if order_data.get('Parts Data'):
            try:
                selected_parts = json.loads(order_data['Parts Data'])
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in Parts Data for {quote_id}")
                selected_parts = []
        
        result = {
            "quote_id": quote_id,
            "customerName": order_data.get("Buyer's Name", ''),
            "customerEmail": order_data.get("Buyer's Email Address", ''),
            "customerCompany": order_data.get('Customer Company', ''),  # This column may not exist
            "customerAddress": order_data.get('Delivery Address', ''),
            "customerPhone": order_data.get("Buyer's Mobile No.", ''),
            "additionalNotes": order_data.get('Additional Notes', ''),
            "selectedParts": selected_parts,
            "orderStatus": order_data.get('Order Status', 'Unknown'),
            "createdDate": order_data.get('Created Date', ''),
            "timestamp": time.time()
        }
        
        logger.info(f"Retrieved order details for {quote_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order {quote_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve order: {str(e)}"
        )

@app.put("/api/order/{quote_id}")
@retry_on_failure(max_retries=3, delay=2.0)
async def update_order(quote_id: str, update_data: OrderUpdateRequest):
    """Update order with enhanced validation"""
    try:
        if not quote_id or not quote_id.startswith('Q-'):
            raise HTTPException(status_code=400, detail="Invalid quote ID format")
        
        logger.info(f"Updating order {quote_id}")
        
        # Get current order data first
        current_order = await get_order_details(quote_id)
        
        # Prepare updates
        updates = {}
        if update_data.selected_parts is not None:
            updates["Parts Data"] = json.dumps(update_data.selected_parts)
            updates["Parts Count"] = len(update_data.selected_parts)
        
        if update_data.additional_notes is not None:
            updates["Additional Notes"] = update_data.additional_notes[:1000]
        
        # Update in Smartsheet
        from src.services.smartsheet_service import SmartsheetService
        from config.my_config import ORDERS_INTAKE_SHEET_ID
        
        def update_in_smartsheet():
            service = SmartsheetService()
            return service.update_row_by_quote_id(ORDERS_INTAKE_SHEET_ID, quote_id, updates)
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: smartsheet_circuit_breaker.call(update_in_smartsheet)
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update order")
        
        logger.info(f"Order {quote_id} updated successfully")
        
        return {
            "success": True,
            "quote_id": quote_id,
            "timestamp": time.time(),
            "message": "Order updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order {quote_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update order: {str(e)}"
        )

@app.post("/api/generate-quotation/{quote_id}")
@retry_on_failure(max_retries=2, delay=3.0)
async def generate_quotation(quote_id: str):
    """Generate quotation with enhanced error handling"""
    try:
        if not quote_id or not quote_id.startswith('Q-'):
            raise HTTPException(status_code=400, detail="Invalid quote ID format")
        
        logger.info(f"Generating quotation for {quote_id}")
        
        # Get order data
        order_data = await get_order_details(quote_id)
        
        if not order_data.get('selectedParts'):
            raise HTTPException(status_code=400, detail="No parts selected for quotation")
        
        # Prepare quotation data
        quotation_data = {
            "quotationNo": quote_id,
            "customer": order_data.get('customerName', ''),
            "customer_company": order_data.get('customerCompany', ''),
            "customer_email": order_data.get('customerEmail', ''),
            "customer_address": order_data.get('customerAddress', '').split('\n'),
            "cbsData": []
        }
        
        # Process parts data
        total_amount = 0
        for part in order_data['selectedParts']:
            part_data = {
                "item": part.get('product_code', ''),
                "description": part.get('description', ''),
                "unitPrice": float(part.get('sales_price', 0)) if part.get('sales_price') else 0,
                "quantity": 1,
                "taxed": True
            }
            quotation_data["cbsData"].append(part_data)
            total_amount += part_data["unitPrice"]
        
        # Calculate discount
        discount_percentage = 0  # You can add discount logic here
        discount_amount = total_amount * (discount_percentage / 100)
        quotation_data["carriage"] = -discount_amount if discount_amount > 0 else 0
        
        # Encode data for quotation generator
        import base64
        encoded_data = base64.b64encode(json.dumps(quotation_data).encode()).decode()
        
        domain = os.getenv('DOMAIN', 'localhost')
        protocol = 'https' if domain != 'localhost' else 'http'
        port = '' if domain != 'localhost' else ':5173'
        quotation_url = f"{protocol}://{domain}{port}/?data={encoded_data}"
        
        logger.info(f"Quotation generated for {quote_id}")
        
        return {
            "success": True,
            "quote_id": quote_id,
            "quotation_url": quotation_url,
            "quotation_data": quotation_data,
            "total_amount": total_amount,
            "discount_amount": discount_amount,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate quotation for {quote_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate quotation: {str(e)}"
        )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("CBS Form API starting up...")
    
    # Verify configuration
    try:
        from config.my_config import ORDERS_INTAKE_SHEET_ID, SMARTSHEET_API_TOKEN
        logger.info(f"Orders Sheet ID: {ORDERS_INTAKE_SHEET_ID}")
        logger.info("Smartsheet API token configured")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("CBS Form API shutting down...")

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_smartsheet_form_api:app",
        host="0.0.0.0",
        port=8003,
        log_level="info",
        access_log=True,
        reload=False,
        workers=1,
        limit_concurrency=100,
        timeout_keep_alive=30
    )

# Webhook endpoint for Smartsheet form submissions
@app.post("/api/smartsheet-webhook")
async def smartsheet_webhook(webhook_data: dict):
    """Handle webhook from Smartsheet form submission"""
    try:
        logger.info(f"Received Smartsheet webhook: {webhook_data}")
        
        # Extract data from Smartsheet webhook
        # Note: Smartsheet webhook format may vary, adjust as needed
        customer_name = webhook_data.get('Buyer\'s Name', '')
        customer_email = webhook_data.get('Buyer\'s Email Address', '')
        customer_phone = webhook_data.get('Buyer\'s Mobile No.', '')
        customer_address = webhook_data.get('Delivery Address', '')
        order_date = webhook_data.get('Order Date', '')
        required_date = webhook_data.get('Required-By Date', '')
        additional_notes = webhook_data.get('Additional Notes', '')
        quote_id = webhook_data.get('Quote ID', '')
        
        # Generate review link
        domain = os.getenv('CBS_DOMAIN', 'localhost')
        protocol = 'http'
        review_link = f"{protocol}://{domain}/enhanced_smartsheet_review.html?quote_id={quote_id}"
        
        logger.info(f"Generated review link: {review_link}")
        
        return {
            "success": True,
            "message": "Webhook processed successfully",
            "quote_id": quote_id,
            "review_link": review_link,
            "customer_name": customer_name,
            "customer_email": customer_email
        }
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

# Email functionality
def generate_acceptance_link(quotation_data: Dict[str, Any]) -> str:
    """Generate Smartsheet acceptance link with auto-populated data"""
    base_url = "https://app.smartsheet.com/b/form/0198be05b2ce78a2995a10328e1d92fb"
    
    params = {
        "Quote Reference No.": quotation_data.get('meta', {}).get('quotationNo', ''),
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

def create_email_template(quotation_data: Dict[str, Any], acceptance_link: str) -> str:
    """Create HTML email template for quotation"""
    customer_name = quotation_data.get('customer', {}).get('name', 'Valued Customer')
    quotation_no = quotation_data.get('meta', {}).get('quotationNo', '')
    company_name = os.getenv('COMPANY_NAME', 'Concrete Batching Systems')
    
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
                text-align: center;
                padding: 20px 0;
                border-bottom: 2px solid #e0e0e0;
                margin-bottom: 20px;
            }}
            .header img {{
                max-width: 200px;
                height: auto;
                margin-bottom: 15px;
            }}
            .header h2 {{
                margin: 5px 0 0 0;
                font-size: 18px;
                color: #2c3e50;
                font-weight: normal;
            }}
            .content {{
                padding: 0;
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
                background: #00b3ff;
                color: #ffffff;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px;
                margin: 20px 0;
                text-align: center;
                border: 2px solid #0099e6;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            }}
            .acceptance-button:hover {{
                background: #0099e6;
                color: #ffffff;
                text-decoration: none;
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
                <img src="cid:cbs_logo" alt="{company_name}">
                <h2>Sales Quotation</h2>
            </div>
        
        <div class="content">
            <p>Dear {customer_name},</p>
            
            <p>Thank you so much for choosing us for your order. Attached you'll find the quotation tied to your order with the reference number <strong>{quotation_no}</strong> for you to review at your convenience.</p>
            
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
                    ACCEPT QUOTATION
                </a>
            </div>
            
            <p>Please click the "ACCEPT QUOTATION" button above to proceed with your order.</p>
            
            <p>If you have any questions about this quotation, please don't hesitate to contact us.</p>
            
            <p>Best regards,<br>
            <strong>{company_name}</strong><br>
            Email: sales@concretebatchingsystems.com</p>
        </div>
        
        <div class="footer">
            <p>This email was sent automatically from the {company_name} quotation system.</p>
        </div>
    </body>
    </html>
    """
    
    return html_template

def generate_quotation_pdf(quotation_data: Dict[str, Any]) -> bytes:
    """Generate PDF for quotation using the PDF generator service"""
    try:
        # Call the PDF generator API
        pdf_api_url = f"http://{os.getenv('CBS_DOMAIN', 'localhost')}:5173/api/quote/pdf"
        
        logger.info(f"Generating PDF for quotation {quotation_data.get('meta', {}).get('quotationNo', '')}")
        
        response = requests.post(
            pdf_api_url,
            json=quotation_data,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info("PDF generated successfully")
            return response.content
        else:
            logger.error(f"PDF generation failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None

def send_quotation_email(quotation_data: Dict[str, Any], customer_email: str) -> Dict[str, Any]:
    """Send quotation email with PDF attachment and acceptance link"""
    
    smtp_host = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    company_name = os.getenv('COMPANY_NAME', 'Concrete Batching Systems')
    
    if not email_username or not email_password:
        return {
            "success": False,
            "error": "Email credentials not configured"
        }
    
    try:
        # Generate PDF
        pdf_data = generate_quotation_pdf(quotation_data)
        if not pdf_data:
            return {
                "success": False,
                "error": "Failed to generate PDF"
            }
        
        # Generate acceptance link
        acceptance_link = generate_acceptance_link(quotation_data)
        
        # Create email content
        html_content = create_email_template(quotation_data, acceptance_link)
        
        # Create message
        msg = MIMEMultipart('related')
        msg['From'] = f"{company_name} <{email_username}>"
        msg['To'] = customer_email
        msg['Subject'] = f"Quotation {quotation_data.get('meta', {}).get('quotationNo', '')} - {company_name}"
        
        # Create alternative container for HTML content
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        # Add text version (fallback)
        text_content = f"""
Dear {quotation_data.get('customer', {}).get('name', 'Valued Customer')},

Thank you so much for choosing us for your order. Attached you'll find the quotation tied to your order with the reference number {quotation_data.get('meta', {}).get('quotationNo', '')} for you to review at your convenience.

Please click the acceptance link below to proceed with your order:
{acceptance_link}

If you have any questions about this quotation, please don't hesitate to contact us.

Best regards,
{company_name}
Email: sales@concretebatchingsystems.com
        """
        text_part = MIMEText(text_content, 'plain')
        msg_alternative.attach(text_part)
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg_alternative.attach(html_part)
        
        # Attach CBS logo as embedded image
        try:
            logo_path = os.path.join('/app', 'logo', 'cbs_logo.png')
            logger.info(f"Looking for logo at: {logo_path}")
            
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                logo_attachment = MIMEImage(logo_data)
                logo_attachment.add_header('Content-ID', '<cbs_logo>')
                logo_attachment.add_header('Content-Disposition', 'inline', filename='cbs_logo.png')
                msg.attach(logo_attachment)
                logger.info(f"CBS logo attached successfully ({len(logo_data)} bytes)")
            else:
                logger.warning(f"CBS logo not found at {logo_path}")
                # Try alternative path
                alt_logo_path = "/Users/bhabeshmohanty/Automation/CBS_Parts_System_Production/logo/cbs_logo.png"
                if os.path.exists(alt_logo_path):
                    with open(alt_logo_path, 'rb') as logo_file:
                        logo_data = logo_file.read()
                    logo_attachment = MIMEImage(logo_data)
                    logo_attachment.add_header('Content-ID', '<cbs_logo>')
                    logo_attachment.add_header('Content-Disposition', 'inline', filename='cbs_logo.png')
                    msg.attach(logo_attachment)
                    logger.info(f"CBS logo attached from alternative path ({len(logo_data)} bytes)")
                else:
                    logger.error(f"CBS logo not found at either {logo_path} or {alt_logo_path}")
        except Exception as e:
            logger.error(f"Failed to attach CBS logo: {e}")
        
        # Add PDF attachment
        pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
        quotation_no = quotation_data.get('meta', {}).get('quotationNo', 'quotation')
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename=f"Quotation_{quotation_no}.pdf")
        msg.attach(pdf_attachment)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(email_username, email_password)
            server.send_message(msg)
        
        logger.info(f"Quotation email with PDF sent successfully to {customer_email}")
        
        return {
            "success": True,
            "message": "Email sent successfully",
            "acceptance_link": acceptance_link,
            "customer_email": customer_email,
            "quotation_no": quotation_data.get('meta', {}).get('quotationNo', '')
        }
        
    except Exception as e:
        logger.error(f"Failed to send quotation email: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/email/send-quotation")
async def send_quotation_email_endpoint(request: QuotationEmailRequest):
    """
    Send quotation email with PDF attachment and acceptance link
    
    Args:
        request: QuotationEmailRequest containing quotation data and customer email
        
    Returns:
        JSON response with success status and details
    """
    try:
        logger.info(f"Sending quotation email to {request.customer_email}")
        
        # Validate quotation data
        if not request.quotation_data:
            raise HTTPException(status_code=400, detail="Quotation data is required")
        
        if not request.quotation_data.get('meta', {}).get('quotationNo'):
            raise HTTPException(status_code=400, detail="Quotation number is required")
        
        if not request.quotation_data.get('customer', {}).get('name'):
            raise HTTPException(status_code=400, detail="Customer name is required")
        
        # Send email
        result = send_quotation_email(request.quotation_data, request.customer_email)
        
        if result["success"]:
            logger.info(f"Email sent successfully to {request.customer_email}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Quotation email sent successfully",
                    "quotation_no": result["quotation_no"],
                    "customer_email": result["customer_email"],
                    "acceptance_link": result["acceptance_link"]
                }
            )
        else:
            logger.error(f"Failed to send email: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to send email: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending quotation email: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/email/health")
async def email_health_check():
    """
    Health check endpoint for email service
    
    Returns:
        JSON response with service status
    """
    try:
        # Check if email credentials are configured
        has_credentials = bool(os.getenv('EMAIL_USERNAME') and os.getenv('EMAIL_PASSWORD'))
        
        return JSONResponse(
            status_code=200,
            content={
                "service": "email",
                "status": "healthy" if has_credentials else "misconfigured",
                "smtp_host": os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com'),
                "smtp_port": int(os.getenv('EMAIL_SMTP_PORT', '587')),
                "has_credentials": has_credentials,
                "company_name": os.getenv('COMPANY_NAME', 'Concrete Batching Systems')
            }
        )
        
    except Exception as e:
        logger.error(f"Email health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "service": "email",
                "status": "unhealthy",
                "error": str(e)
            }
        )
