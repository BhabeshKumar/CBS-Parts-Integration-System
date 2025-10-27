#!/usr/bin/env python3
"""
CBS Email API - FastAPI endpoint for sending quotation emails
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import sys

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.email_service import email_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/email", tags=["email"])

class QuotationEmailRequest(BaseModel):
    """Request model for sending quotation emails"""
    quotation_data: Dict[str, Any]
    customer_email: EmailStr
    test_mode: Optional[bool] = False

class EmailTestRequest(BaseModel):
    """Request model for testing email connection"""
    test_email: EmailStr

@router.post("/send-quotation")
async def send_quotation_email(request: QuotationEmailRequest):
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
        
        if not request.quotation_data.get('quotationNo'):
            raise HTTPException(status_code=400, detail="Quotation number is required")
        
        if not request.quotation_data.get('customer', {}).get('name'):
            raise HTTPException(status_code=400, detail="Customer name is required")
        
        # Send email
        result = email_service.send_quotation_email(
            request.quotation_data, 
            request.customer_email
        )
        
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

@router.post("/test-connection")
async def test_email_connection():
    """
    Test email service connection
    
    Returns:
        JSON response with connection status
    """
    try:
        logger.info("Testing email connection")
        
        is_connected = email_service.test_email_connection()
        
        if is_connected:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Email connection successful",
                    "smtp_host": email_service.smtp_host,
                    "smtp_port": email_service.smtp_port,
                    "email_username": email_service.email_username
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Email connection failed",
                    "error": "Unable to connect to SMTP server"
                }
            )
            
    except Exception as e:
        logger.error(f"Error testing email connection: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/test-email")
async def send_test_email(request: EmailTestRequest):
    """
    Send a test email to verify email functionality
    
    Args:
        request: EmailTestRequest containing test email address
        
    Returns:
        JSON response with test result
    """
    try:
        logger.info(f"Sending test email to {request.test_email}")
        
        # Create test quotation data
        test_quotation_data = {
            "quotationNo": "TEST-001",
            "customer": {
                "name": "Test Customer",
                "email": request.test_email,
                "phone": "+1 234 567 8900"
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
        
        # Send test email
        result = email_service.send_quotation_email(
            test_quotation_data, 
            request.test_email
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Test email sent successfully",
                    "test_email": request.test_email,
                    "acceptance_link": result["acceptance_link"]
                }
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to send test email: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending test email: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def email_health_check():
    """
    Health check endpoint for email service
    
    Returns:
        JSON response with service status
    """
    try:
        # Check if email credentials are configured
        has_credentials = bool(email_service.email_username and email_service.email_password)
        
        return JSONResponse(
            status_code=200,
            content={
                "service": "email",
                "status": "healthy" if has_credentials else "misconfigured",
                "smtp_host": email_service.smtp_host,
                "smtp_port": email_service.smtp_port,
                "has_credentials": has_credentials,
                "company_name": email_service.company_name
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

# Export router for use in main application
email_router = router
