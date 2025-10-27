#!/usr/bin/env python3
"""
CBS Email API Service - Start the email API server
"""

import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.email_api import email_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CBS Email API",
    description="Email service for sending quotation emails with acceptance links",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include email router
app.include_router(email_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CBS Email API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "send_quotation": "/api/email/send-quotation",
            "test_connection": "/api/email/test-connection",
            "test_email": "/api/email/test-email",
            "health": "/api/email/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "email-api",
        "port": 8004
    }

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv('EMAIL_API_PORT', '8004'))
    
    logger.info(f"🚀 Starting CBS Email API on port {port}")
    logger.info(f"📧 Email SMTP Host: {os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')}")
    logger.info(f"📧 Email Username: {os.getenv('EMAIL_USERNAME', 'Not configured')}")
    
    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
