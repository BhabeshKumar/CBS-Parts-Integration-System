#!/usr/bin/env python3
"""
Start CBS Smartsheet Form API
Production-ready startup script with your actual configuration
"""

import os
import sys
import logging
import uvicorn

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/form-api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Start the Form API server"""
    logger.info("🚀 Starting CBS Smartsheet Form API...")
    
    # Set environment variables with your actual values
    os.environ.setdefault('SMARTSHEET_API_TOKEN', '7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB')
    os.environ.setdefault('ORDERS_INTAKE_SHEET_ID', 'p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1')
    os.environ.setdefault('SALES_WORKS_ORDERS_SHEET_ID', 'G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391')
    os.environ.setdefault('CBS_PARTS_SHEET_ID', '4695255724019588')
    os.environ.setdefault('CBS_DISCOUNTS_SHEET_ID', '8920011042148228')
    os.environ.setdefault('CBS_DIRECTOR_EMAIL', 'bhabesh.kumar@sheaney.ie')
    
    logger.info(f"✅ Configuration loaded:")
    logger.info(f"   • Orders Intake Sheet: {os.environ.get('ORDERS_INTAKE_SHEET_ID')}")
    logger.info(f"   • CBS Parts Sheet: {os.environ.get('CBS_PARTS_SHEET_ID')}")
    logger.info(f"   • CBS Director: {os.environ.get('CBS_DIRECTOR_EMAIL')}")
    
    try:
        # Start the server
        uvicorn.run(
            "api.smartsheet_form_api:app",
            host="0.0.0.0",
            port=8003,
            log_level="info",
            access_log=True,
            reload=False
        )
    except Exception as e:
        logger.error(f"❌ Failed to start Form API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
