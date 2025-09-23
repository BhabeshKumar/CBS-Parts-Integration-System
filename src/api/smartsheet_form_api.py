"""
Smartsheet Form API
Handles form submissions to Smartsheet Orders Intake sheet.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.smartsheet_service import SmartsheetService
from src.services.quotation_integration_service import QuotationIntegrationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CBS Smartsheet Form API",
    description="API for submitting form data to Smartsheet",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
smartsheet_service = SmartsheetService()
quotation_service = QuotationIntegrationService()

class SelectedPart(BaseModel):
    product_code: str
    description: str
    sales_price: float
    quantity: int
    line_total: float

class OrderFormSubmission(BaseModel):
    buyerName: str
    buyerEmail: str
    buyerMobile: Optional[str] = ""
    deliveryAddress: str
    requiredDate: Optional[str] = ""
    orderDate: Optional[str] = ""
    additionalNotes: Optional[str] = ""
    selectedParts: List[SelectedPart]
    partsCount: int
    partsReviewStatus: str = "Pending"
    quoteId: str
    partsReviewLink: str

@app.post("/api/submit-order")
async def submit_order_form(submission: OrderFormSubmission):
    """Submit order form data to Smartsheet Orders Intake sheet."""
    try:
        logger.info(f"Received order submission for {submission.buyerName}")
        
        # Prepare data for Smartsheet
        # For now, we'll use the first part as the main part and store others in additional notes
        main_part = submission.selectedParts[0] if submission.selectedParts else None
        
        # Create parts summary for additional notes
        parts_summary = []
        for part in submission.selectedParts:
            parts_summary.append(f"{part.product_code} - {part.description} (Qty: {part.quantity})")
        
        additional_parts_text = "\n".join(parts_summary)
        
        # Combine additional notes with parts summary
        combined_notes = f"SELECTED PARTS:\n{additional_parts_text}"
        if submission.additionalNotes:
            combined_notes += f"\n\nADDITIONAL NOTES:\n{submission.additionalNotes}"
        
        # Generate review link
        review_link = f"https://cbsparts.yourcompany.com/templates/parts_review_interface.html?review_id={submission.quoteId}"
        
        # Prepare row data according to existing column structure
        # Note: Skip system columns (Quote ID is AUTO_NUMBER, Created Date is CREATED_DATE)
        row_data = {
            "Buyer's Name": submission.buyerName,
            "Buyer's Email Address": submission.buyerEmail,
            "Buyer's Mobile No.": submission.buyerMobile or "",
            "Delivery Address": submission.deliveryAddress,
            "Required-By Date": submission.requiredDate or "",
            "Order Date": submission.orderDate or datetime.now().strftime("%Y-%m-%d"),
            "Part No.": main_part.product_code if main_part else "",
            "Part Description": main_part.description if main_part else "",
            "Quantity Required": str(main_part.quantity) if main_part else "1",
            "Additional Notes": combined_notes,
            "Priority": "Medium",  # Default priority
            "Quotation Update": "Not Started",
            "Order Status": "Not Started",
            "Assigned to": "",  # Will be assigned later
            "Quotation Link": review_link,  # Add review link to Smartsheet
        }
        
        # Add row to Orders Intake sheet
        result = smartsheet_service.add_order_row(row_data)
        
        if result.get('success'):
            logger.info(f"Successfully added order {submission.quoteId} to Smartsheet")
            
            # Generate actual review link
            review_link = f"https://cbsparts.yourcompany.com/templates/parts_review_interface.html?review_id={submission.quoteId}"
            
            return {
                "success": True,
                "message": "Order submitted successfully",
                "quote_id": submission.quoteId,
                "row_id": result.get('row_id'),
                "parts_count": submission.partsCount,
                "review_link": review_link,
                "smartsheet_updated": True
            }
        else:
            logger.error(f"Failed to add order to Smartsheet: {result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Failed to submit order: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error submitting order: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting order: {str(e)}")

@app.get("/api/order/{quote_id}")
async def get_order_details(quote_id: str):
    """Get order details by Quote ID from Smartsheet."""
    try:
        logger.info(f"Fetching order details for Quote ID: {quote_id}")
        
        # Get the Orders Intake sheet
        sheet = smartsheet_service.client.Sheets.get_sheet(smartsheet_service.orders_intake_sheet_id)
        
        # Find the row with matching Quote ID
        order_row = None
        for row in sheet.rows:
            for cell in row.cells:
                if cell.column_id == smartsheet_service.get_column_id("orders_intake", "Quote ID"):
                    if str(cell.value) == quote_id:
                        order_row = row
                        break
            if order_row:
                break
        
        if not order_row:
            raise HTTPException(status_code=404, detail=f"Order with Quote ID {quote_id} not found")
        
        # Extract order data from the row
        order_data = {}
        for cell in order_row.cells:
            column = next((col for col in sheet.columns if col.id == cell.column_id), None)
            if column:
                order_data[column.title] = cell.value
        
        # Parse selected parts from Additional Notes
        additional_notes = order_data.get("Additional Notes", "")
        selected_parts = []
        
        if "SELECTED PARTS:" in additional_notes:
            parts_section = additional_notes.split("SELECTED PARTS:")[1]
            if "ADDITIONAL NOTES:" in parts_section:
                parts_section = parts_section.split("ADDITIONAL NOTES:")[0]
            
            # Parse each part line
            for line in parts_section.strip().split("\n"):
                if " - " in line and "(Qty:" in line:
                    try:
                        # Format: "PRODUCT_CODE - Description (Qty: X)"
                        code_desc, qty_part = line.rsplit("(Qty:", 1)
                        product_code, description = code_desc.split(" - ", 1)
                        quantity = int(qty_part.strip().rstrip(")"))
                        
                        selected_parts.append({
                            "product_code": product_code.strip(),
                            "description": description.strip(),
                            "quantity": quantity,
                            "sales_price": 0.0,  # To be set by CBS
                            "line_total": 0.0
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse part line: {line} - {e}")
        
        # Format response
        response_data = {
            "quoteId": order_data.get("Quote ID", quote_id),
            "customerName": order_data.get("Buyer's Name", ""),
            "customerEmail": order_data.get("Buyer's Email Address", ""),
            "customerMobile": order_data.get("Buyer's Mobile No.", ""),
            "orderDate": order_data.get("Order Date", ""),
            "requiredDate": order_data.get("Required-By Date", ""),
            "deliveryAddress": order_data.get("Delivery Address", ""),
            "orderStatus": order_data.get("Order Status", "Not Started"),
            "quotationUpdate": order_data.get("Quotation Update", "Not Started"),
            "priority": order_data.get("Priority", "Medium"),
            "additionalNotes": additional_notes,
            "selectedParts": selected_parts,
            "rowId": order_row.id
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order details: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching order: {str(e)}")

@app.put("/api/order/{quote_id}")
async def update_order_pricing(quote_id: str, order_update: dict):
    """Update order pricing and status."""
    try:
        logger.info(f"Updating order pricing for Quote ID: {quote_id}")
        
        # Here you would update the Smartsheet with new pricing
        # For now, just return success
        
        return {
            "success": True,
            "message": f"Order {quote_id} updated successfully",
            "updated_fields": list(order_update.keys())
        }
        
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

@app.post("/api/generate-quotation/{quote_id}")
async def generate_quotation(quote_id: str):
    """Generate quotation for an approved order."""
    try:
        logger.info(f"Generating quotation for Quote ID: {quote_id}")
        
        # First, get the order data
        order_response = await get_order_details(quote_id)
        
        # Generate quotation
        quotation_result = quotation_service.trigger_quotation_generation(order_response)
        
        if quotation_result.get('success'):
            return {
                "success": True,
                "message": "Quotation generated successfully",
                "quoteId": quote_id,
                "pdfUrl": quotation_result.get('quotationResult', {}).get('pdfUrl'),
                "generatedAt": quotation_result.get('quotationResult', {}).get('generatedAt')
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=quotation_result.get('message', 'Failed to generate quotation')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quotation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating quotation: {str(e)}")

@app.get("/api/quotation-template/{quote_id}")
async def get_quotation_template(quote_id: str):
    """Get quotation template data for integration with existing generator."""
    try:
        # Get order data
        order_data = await get_order_details(quote_id)
        
        # Get template data
        template_data = quotation_service.get_quotation_template_data(quote_id)
        
        # Combine with order data
        complete_data = {
            **template_data,
            "orderData": order_data,
            "quotationData": quotation_service.prepare_quotation_data(order_data)
        }
        
        return complete_data
        
    except Exception as e:
        logger.error(f"Error getting quotation template: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting template: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "service": "Smartsheet Form API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
