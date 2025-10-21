#!/usr/bin/env python3
"""
Startup script for Smartsheet Polling Service
"""
import sys
import os
import asyncio
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("🔄 Starting Smartsheet Polling Service...")
        
        # Import and start the polling service
        from src.services.smartsheet_polling_service import start_polling_service
        
        # Run the polling service
        asyncio.run(start_polling_service())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Polling service error: {e}")
        sys.exit(1)
