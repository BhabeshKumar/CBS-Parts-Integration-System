"""
CBS Parts API
FastAPI endpoints for CBS parts integration and management.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from fastapi import FastAPI, HTTPException, Query, Body, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.cbs_parts_service import CBSPartsService
from services.cbs_discounts_service import CBSDiscountsService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CBS Parts API",
    description="API for CBS parts database and customer discount management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
parts_service = CBSPartsService()
discounts_service = CBSDiscountsService()

# Pydantic models for request/response
class PartSearchRequest(BaseModel):
    search_term: str
    limit: Optional[int] = 50

class PartResponse(BaseModel):
    product_code: str
    description: str
    sales_price: float
    quantity_in_stock: float
    free_stock: float
    category: str
    inactive: bool

class DiscountRequest(BaseModel):
    customer_email: str
    discount_percentage: float
    discount_type: str = "Global"
    product_code: Optional[str] = None
    notes: Optional[str] = ""
    valid_days: Optional[int] = 365

class QuotationCalculationRequest(BaseModel):
    customer_email: str
    items: List[Dict[str, Any]]  # List of {product_code, quantity, unit_price}

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CBS Parts API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/api/health",
            "parts_search": "/api/parts/search",
            "part_details": "/api/parts/{product_code}",
            "customer_discount": "/api/discounts/customer/{email}",
            "calculate_quote": "/api/quotes/calculate"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test parts service
        parts_sheet_id = parts_service.get_or_create_parts_sheet()
        parts_status = "operational" if parts_sheet_id else "error"
        
        # Test discounts service
        discounts_sheet_id = discounts_service.get_or_create_discounts_sheet()
        discounts_status = "operational" if discounts_sheet_id else "error"
        
        overall_status = "operational" if (parts_status == "operational" and 
                                         discounts_status == "operational") else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "parts_database": parts_status,
                "discounts_database": discounts_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# =============================================================================
# PARTS ENDPOINTS
# =============================================================================

@app.get("/api/parts/search")
async def search_parts(
    q: str = Query(..., description="Search term for product code or description"),
    limit: int = Query(50, description="Maximum number of results to return")
):
    """Search for parts by product code or description."""
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")
        
        results = parts_service.search_parts(q.strip(), limit)
        
        return {
            "query": q,
            "limit": limit,
            "count": len(results),
            "parts": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching parts: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching parts: {str(e)}")

@app.post("/api/parts/search")
async def search_parts_post(request: PartSearchRequest):
    """Search for parts by product code or description (POST method)."""
    try:
        if not request.search_term or len(request.search_term.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")
        
        results = parts_service.search_parts(request.search_term.strip(), request.limit)
        
        return {
            "query": request.search_term,
            "limit": request.limit,
            "count": len(results),
            "parts": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching parts: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching parts: {str(e)}")

@app.get("/api/parts/{product_code}")
async def get_part_details(product_code: str):
    """Get details for a specific part by product code."""
    try:
        part = parts_service.get_part_by_code(product_code.strip())
        
        if not part:
            raise HTTPException(status_code=404, detail=f"Part not found: {product_code}")
        
        return part
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting part details for {product_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting part details: {str(e)}")

@app.get("/api/parts")
async def get_all_parts(
    include_inactive: bool = Query(False, description="Include inactive parts"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get all parts from the database."""
    try:
        parts = parts_service.get_all_parts(include_inactive)
        
        # Filter by category if specified
        if category:
            parts = [part for part in parts if part.get("category", "").lower() == category.lower()]
        
        return {
            "count": len(parts),
            "include_inactive": include_inactive,
            "category_filter": category,
            "parts": parts
        }
        
    except Exception as e:
        logger.error(f"Error getting all parts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting parts: {str(e)}")

@app.post("/api/parts/import")
async def import_parts_from_excel(
    file: UploadFile = File(..., description="Excel file with parts data")
):
    """Import parts from Excel file."""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
        
        # Save uploaded file temporarily
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Import parts
        success = parts_service.import_parts_from_excel(temp_file_path)
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        if success:
            return {
                "message": "Parts imported successfully",
                "filename": file.filename,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to import parts")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing parts: {e}")
        raise HTTPException(status_code=500, detail=f"Error importing parts: {str(e)}")

@app.put("/api/parts/{product_code}/price")
async def update_part_price(
    product_code: str,
    new_price: float = Body(..., description="New price for the part")
):
    """Update the price of a specific part."""
    try:
        if new_price < 0:
            raise HTTPException(status_code=400, detail="Price cannot be negative")
        
        success = parts_service.update_part_price(product_code.strip(), new_price)
        
        if success:
            return {
                "message": f"Price updated for {product_code}",
                "product_code": product_code,
                "new_price": new_price,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Part not found: {product_code}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating part price: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating part price: {str(e)}")

# =============================================================================
# DISCOUNTS ENDPOINTS
# =============================================================================

@app.get("/api/discounts/customer/{customer_email}")
async def get_customer_discount(customer_email: str):
    """Get discount information for a specific customer."""
    try:
        discount_info = discounts_service.get_customer_discount(customer_email.strip())
        
        return {
            "customer_email": customer_email,
            "discount_info": discount_info
        }
        
    except Exception as e:
        logger.error(f"Error getting customer discount: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting customer discount: {str(e)}")

@app.post("/api/discounts/add")
async def add_customer_discount(request: DiscountRequest):
    """Add a new customer discount."""
    try:
        success = discounts_service.add_customer_discount(
            customer_email=request.customer_email.strip(),
            discount_percentage=request.discount_percentage,
            discount_type=request.discount_type,
            product_code=request.product_code,
            notes=request.notes,
            valid_days=request.valid_days
        )
        
        if success:
            return {
                "message": "Discount added successfully",
                "customer_email": request.customer_email,
                "discount_percentage": request.discount_percentage,
                "discount_type": request.discount_type,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add discount")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding customer discount: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding discount: {str(e)}")

@app.get("/api/discounts")
async def get_all_discounts():
    """Get all customer discounts for management."""
    try:
        discounts = discounts_service.get_all_customer_discounts()
        
        return {
            "count": len(discounts),
            "discounts": discounts
        }
        
    except Exception as e:
        logger.error(f"Error getting all discounts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting discounts: {str(e)}")

# =============================================================================
# QUOTATION CALCULATION ENDPOINTS
# =============================================================================

@app.post("/api/quotes/calculate")
async def calculate_quotation_with_discounts(request: QuotationCalculationRequest):
    """Calculate quotation totals with customer discounts applied."""
    try:
        # Get customer discount information
        customer_discount = discounts_service.get_customer_discount(request.customer_email.strip())
        
        # Calculate discounts for each item
        calculated_items = []
        total_original = 0.0
        total_discount = 0.0
        total_final = 0.0
        
        for item in request.items:
            product_code = item.get("product_code", "")
            quantity = int(item.get("quantity", 1))
            unit_price = float(item.get("unit_price", 0.0))
            
            # Get part details to fill in missing price if needed
            if unit_price == 0.0:
                part_details = parts_service.get_part_by_code(product_code)
                if part_details:
                    unit_price = float(part_details.get("sales_price", 0.0))
            
            # Calculate discount for this item
            discount_calc = discounts_service.calculate_discount_for_item(
                customer_discount, product_code, unit_price, quantity
            )
            
            calculated_items.append({
                "product_code": product_code,
                "quantity": quantity,
                **discount_calc
            })
            
            total_original += discount_calc["total_original"]
            total_discount += discount_calc["total_discount"]
            total_final += discount_calc["total_discounted"]
        
        return {
            "customer_email": request.customer_email,
            "customer_discount_info": customer_discount,
            "items": calculated_items,
            "summary": {
                "total_original": round(total_original, 2),
                "total_discount": round(total_discount, 2),
                "total_final": round(total_final, 2),
                "overall_discount_percentage": round((total_discount / total_original * 100) if total_original > 0 else 0.0, 2),
                "currency": "EUR"
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating quotation: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating quotation: {str(e)}")

# =============================================================================
# PARTS SELECTION INTERFACE ENDPOINTS
# =============================================================================

@app.get("/api/parts/suggestions")
async def get_parts_suggestions(
    q: str = Query(..., description="Search term for auto-suggestions"),
    limit: int = Query(10, description="Maximum number of suggestions")
):
    """Get parts suggestions for auto-complete functionality."""
    try:
        if len(q.strip()) < 2:
            return {"suggestions": []}
        
        parts = parts_service.search_parts(q.strip(), limit)
        
        suggestions = []
        for part in parts:
            suggestions.append({
                "product_code": part["product_code"],
                "description": part["description"],
                "display_text": f"{part['product_code']} - {part['description']}",
                "sales_price": part["sales_price"],
                "category": part["category"]
            })
        
        return {
            "query": q,
            "count": len(suggestions),
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting parts suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@app.get("/api/parts/categories")
async def get_parts_categories():
    """Get all available parts categories."""
    try:
        # Import categories from config
        config_path = Path(__file__).parent.parent.parent / "config"
        sys.path.insert(0, str(config_path))
        from cbs_parts_config import PARTS_CATEGORIES
        
        return {
            "categories": PARTS_CATEGORIES
        }
        
    except Exception as e:
        logger.error(f"Error getting parts categories: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
