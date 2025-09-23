#!/usr/bin/env python3
"""
Start script for CBS Parts API
This script starts the CBS Parts API server.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start the CBS Parts API server."""
    print("=" * 70)
    print("🚀 STARTING CBS PARTS API SERVER")
    print("=" * 70)
    
    try:
        # Import the FastAPI app
        from api.cbs_parts_api import app
        
        print("\n📋 CBS Parts API Server Configuration:")
        print("   • Host: 0.0.0.0")
        print("   • Port: 8002")
        print("   • URL: http://localhost:8002")
        print("   • Documentation: http://localhost:8002/docs")
        print("   • Health Check: http://localhost:8002/api/health")
        
        print("\n🌐 Available Endpoints:")
        print("   • GET  /api/parts/search - Search for parts")
        print("   • GET  /api/parts/{code} - Get part details")
        print("   • GET  /api/discounts/customer/{email} - Get customer discount")
        print("   • POST /api/quotes/calculate - Calculate quotation with discounts")
        print("   • POST /api/parts/import - Import parts from Excel")
        print("   • GET  /api/parts/suggestions - Get auto-complete suggestions")
        
        print("\n🚀 Starting server...")
        print("   Press Ctrl+C to stop the server")
        print("-" * 70)
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8002,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
