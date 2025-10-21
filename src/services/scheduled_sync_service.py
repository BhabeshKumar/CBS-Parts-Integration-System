"""
Scheduled Sync Service
Syncs SQLite parts database with Smartsheet every 24 hours
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional

logger = logging.getLogger(__name__)

class ScheduledSyncService:
    def __init__(self):
        self.is_running = False
        self.sync_time = time(hour=2, minute=0)  # 2:00 AM daily
        
    async def start_scheduled_sync(self):
        """Start the scheduled sync service"""
        logger.info("🕐 Starting scheduled sync service...")
        logger.info(f"📅 Daily sync scheduled for {self.sync_time}")
        self.is_running = True
        
        while self.is_running:
            try:
                # Calculate seconds until next sync time
                now = datetime.now()
                next_sync = datetime.combine(now.date(), self.sync_time)
                
                # If sync time has passed today, schedule for tomorrow
                if now.time() > self.sync_time:
                    next_sync = datetime.combine(now.date().replace(day=now.day + 1), self.sync_time)
                
                seconds_until_sync = (next_sync - now).total_seconds()
                
                logger.info(f"⏰ Next sync in {seconds_until_sync/3600:.1f} hours at {next_sync}")
                
                # Wait until sync time
                await asyncio.sleep(seconds_until_sync)
                
                if self.is_running:
                    await self.perform_sync()
                    
            except Exception as e:
                logger.error(f"Error in scheduled sync service: {e}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    async def perform_sync(self):
        """Perform the actual sync"""
        try:
            logger.info("🔄 Starting scheduled parts database sync...")
            
            from src.services.sqlite_parts_service import sqlite_parts_service
            
            success = await sqlite_parts_service.sync_with_smartsheet()
            
            if success:
                stats = sqlite_parts_service.get_stats()
                logger.info(f"✅ Scheduled sync completed successfully - {stats.get('parts_count', 0)} parts synced")
            else:
                logger.error("❌ Scheduled sync failed")
                
        except Exception as e:
            logger.error(f"❌ Error during scheduled sync: {e}")
    
    def stop_scheduled_sync(self):
        """Stop the scheduled sync service"""
        logger.info("🛑 Stopping scheduled sync service...")
        self.is_running = False

# Global scheduled sync service
scheduled_sync_service = ScheduledSyncService()

async def start_scheduled_sync():
    """Start the scheduled sync service"""
    await scheduled_sync_service.start_scheduled_sync()

def stop_scheduled_sync():
    """Stop the scheduled sync service"""
    scheduled_sync_service.stop_scheduled_sync()
