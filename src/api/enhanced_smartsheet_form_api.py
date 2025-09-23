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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/form_api.log'),
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
        domain = os.getenv('DOMAIN', '34.10.76.247')  # Default to live domain
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
