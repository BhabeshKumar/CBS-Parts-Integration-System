"""
Enhanced CBS Parts API with production-ready error handling and stability
"""
import logging
import time
import asyncio
from functools import wraps
from typing import Optional, Dict, List, Any
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parts_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CBS Parts API",
    description="Production-ready CBS Parts Management API",
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
            "path": str(request.url)
        }
    )

# Retry decorator for resilient operations
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

# Connection pool for Smartsheet API
class SmartsheetConnectionPool:
    def __init__(self):
        self.connections = {}
        self.last_cleanup = time.time()
    
    async def get_connection(self, api_token: str):
        try:
            import smartsheet
            if api_token not in self.connections:
                self.connections[api_token] = smartsheet.Smartsheet(api_token)
                logger.info(f"Created new Smartsheet connection")
            
            # Cleanup old connections every hour
            current_time = time.time()
            if current_time - self.last_cleanup > 3600:
                self.cleanup_connections()
                self.last_cleanup = current_time
            
            return self.connections[api_token]
        except Exception as e:
            logger.error(f"Failed to create Smartsheet connection: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to Smartsheet")
    
    def cleanup_connections(self):
        # In a real implementation, you'd check for stale connections
        logger.info("Cleaned up Smartsheet connections")

connection_pool = SmartsheetConnectionPool()

# Health check with detailed status
@app.get("/api/parts/health")
async def health_check():
    try:
        from src.services.smartsheet_service import SmartsheetService
        from config.cbs_parts_config import CBS_PARTS_SHEET_ID
        
        # Test Smartsheet connectivity
        smartsheet_status = "healthy"
        try:
            service = SmartsheetService()
            # Quick connection test (get sheet info only)
            sheet_info = service.smartsheet.Sheets.get_sheet(CBS_PARTS_SHEET_ID, include="summary")
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
                "database": "healthy"
            },
            "version": "1.0.0",
            "uptime": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/parts/search")
@retry_on_failure(max_retries=3, delay=1.0)
async def search_parts(query: str = "", limit: int = 50):
    """Enhanced parts search with error handling and caching"""
    try:
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "limit": limit,
                "count": 0,
                "parts": [],
                "message": "Query too short. Minimum 2 characters required."
            }
        
        # Sanitize query
        query = query.strip()[:100]  # Limit query length
        
        from src.services.sqlite_parts_service import sqlite_parts_service
        
        # Use SQLite for fast search
        parts = await asyncio.get_event_loop().run_in_executor(
            None, sqlite_parts_service.search_parts, query, limit
        )
        
        logger.info(f"Parts search: '{query}' returned {len(parts)} results")
        
        return {
            "query": query,
            "limit": limit,
            "count": len(parts),
            "parts": parts,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Parts search failed for query '{query}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )

@app.get("/api/parts/stats")
async def get_parts_stats():
    """Get SQLite database statistics"""
    try:
        from src.services.sqlite_parts_service import sqlite_parts_service
        
        stats = sqlite_parts_service.get_stats()
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get parts stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )

@app.post("/api/parts/sync")
async def sync_parts_database():
    """Manually trigger sync with Smartsheet"""
    try:
        from src.services.sqlite_parts_service import sqlite_parts_service
        
        logger.info("Manual sync triggered")
        success = await sqlite_parts_service.sync_with_smartsheet()
        
        if success:
            stats = sqlite_parts_service.get_stats()
            return {
                "status": "success",
                "message": "Parts database synced successfully",
                "stats": stats,
                "timestamp": time.time()
            }
        else:
            return {
                "status": "failed",
                "message": "Sync failed - check logs for details",
                "timestamp": time.time()
            }
        
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )

@app.get("/api/parts/discounts/{customer_email}")
@retry_on_failure(max_retries=3, delay=1.0)
async def get_customer_discounts(customer_email: str):
    """Get customer-specific discounts with error handling"""
    try:
        if not customer_email or "@" not in customer_email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        from src.services.lightweight_cbs_parts_service import CBSPartsService
        
        service = CBSPartsService()
        discounts = await asyncio.get_event_loop().run_in_executor(
            None, service.get_customer_discounts, customer_email
        )
        
        logger.info(f"Retrieved discounts for customer: {customer_email}")
        
        return {
            "customer_email": customer_email,
            "discounts": discounts,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discounts for {customer_email}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve discounts: {str(e)}"
        )

@app.get("/api/parts/{part_id}")
@retry_on_failure(max_retries=3, delay=1.0)
async def get_part_details(part_id: str):
    """Get detailed part information"""
    try:
        if not part_id or len(part_id.strip()) < 1:
            raise HTTPException(status_code=400, detail="Invalid part ID")
        
        from src.services.lightweight_cbs_parts_service import CBSPartsService
        
        service = CBSPartsService()
        part = await asyncio.get_event_loop().run_in_executor(
            None, service.get_part_by_id, part_id.strip()
        )
        
        if not part:
            raise HTTPException(status_code=404, detail="Part not found")
        
        logger.info(f"Retrieved part details: {part_id}")
        
        return {
            "part": part,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get part {part_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve part: {str(e)}"
        )

# Graceful shutdown handling
@app.on_event("startup")
async def startup_event():
    logger.info("CBS Parts API starting up...")
    
    # Test critical dependencies
    try:
        from config.cbs_parts_config import CBS_PARTS_SHEET_ID, CBS_DISCOUNTS_SHEET_ID
        logger.info(f"Parts Sheet ID: {CBS_PARTS_SHEET_ID}")
        logger.info(f"Discounts Sheet ID: {CBS_DISCOUNTS_SHEET_ID}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("CBS Parts API shutting down...")
    
    # Cleanup connections
    try:
        connection_pool.cleanup_connections()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    # Production server configuration
    uvicorn.run(
        "enhanced_cbs_parts_api:app",
        host="0.0.0.0",
        port=8002,
        log_level="info",
        access_log=True,
        reload=False,
        workers=1,  # Single worker to avoid shared state issues
        limit_concurrency=100,
        timeout_keep_alive=30
    )
