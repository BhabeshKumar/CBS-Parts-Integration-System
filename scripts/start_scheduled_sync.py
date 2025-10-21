#!/usr/bin/env python3
"""
Startup script for Scheduled Sync Service
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
        logger.info("🕐 Starting Scheduled Sync Service...")
        
        # Import and start the scheduled sync service
        from src.services.scheduled_sync_service import start_scheduled_sync
        
        # Run the scheduled sync service
        asyncio.run(start_scheduled_sync())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Scheduled sync service error: {e}")
        sys.exit(1)
