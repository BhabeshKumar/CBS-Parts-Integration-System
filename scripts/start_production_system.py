#!/usr/bin/env python3
"""
Production System Startup Script
Starts all services including the Smartsheet polling service
"""
import asyncio
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionSystemManager:
    def __init__(self):
        self.is_running = False
        self.tasks = []
        
    async def start_all_services(self):
        """Start all production services"""
        logger.info("🚀 Starting CBS Parts Production System...")
        self.is_running = True
        
        try:
            # Start Smartsheet polling service
            from src.services.smartsheet_polling_service import start_polling_service
            polling_task = asyncio.create_task(start_polling_service())
            self.tasks.append(polling_task)
            logger.info("✅ Smartsheet polling service started")
            
            # Start Parts API (port 8002)
            parts_api_task = asyncio.create_task(self._start_parts_api())
            self.tasks.append(parts_api_task)
            logger.info("✅ Parts API starting on port 8002")
            
            # Start Form API (port 8003)
            form_api_task = asyncio.create_task(self._start_form_api())
            self.tasks.append(form_api_task)
            logger.info("✅ Form API starting on port 8003")
            
            # Start Web Server (port 8000)
            web_server_task = asyncio.create_task(self._start_web_server())
            self.tasks.append(web_server_task)
            logger.info("✅ Web server starting on port 8000")
            
            logger.info("🎉 All services started successfully!")
            logger.info("📋 System Status:")
            logger.info("   🔄 Smartsheet polling: Every 1 minute")
            logger.info("   🔍 Parts API: http://localhost:8002")
            logger.info("   📝 Form API: http://localhost:8003") 
            logger.info("   🌐 Web Server: http://localhost:8000")
            
            # Wait for all tasks
            await asyncio.gather(*self.tasks)
            
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            await self.shutdown()
    
    async def _start_parts_api(self):
        """Start the Parts API"""
        try:
            # Import and run the parts API
            from src.api.enhanced_cbs_parts_api import app as parts_app
            config = uvicorn.Config(parts_app, host="0.0.0.0", port=8002, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Parts API error: {e}")
    
    async def _start_form_api(self):
        """Start the Form API"""
        try:
            # Import and run the form API
            from src.api.enhanced_smartsheet_form_api import app as form_app
            config = uvicorn.Config(form_app, host="0.0.0.0", port=8003, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Form API error: {e}")
    
    async def _start_web_server(self):
        """Start the Web Server"""
        try:
            # Import and run the web server
            import subprocess
            import os
            
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            web_server_script = os.path.join(project_root, 'scripts', 'start_web_server.py')
            
            # Run the web server in a subprocess
            process = subprocess.Popen([sys.executable, web_server_script])
            
            # Wait for the process to complete
            process.wait()
            
        except Exception as e:
            logger.error(f"Web server error: {e}")
    
    async def shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("🛑 Shutting down production system...")
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Stop polling service
        try:
            from src.services.smartsheet_polling_service import stop_polling_service
            stop_polling_service()
            logger.info("✅ Smartsheet polling service stopped")
        except Exception as e:
            logger.error(f"Error stopping polling service: {e}")
        
        logger.info("🏁 Production system shutdown complete")

# Global system manager
system_manager = ProductionSystemManager()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    asyncio.create_task(system_manager.shutdown())

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the production system
        asyncio.run(system_manager.start_all_services())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        logger.info("System stopped")
