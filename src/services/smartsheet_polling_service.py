"""
Smartsheet Polling Service
Checks for new orders every minute and generates review links
"""
import asyncio
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartsheetPollingService:
    def __init__(self):
        self.is_running = False
        self.poll_interval = 60  # 1 minute
        self.processed_orders = set()  # Track processed order IDs
        
    async def start_polling(self):
        """Start the polling service"""
        logger.info("🔄 Starting Smartsheet polling service...")
        self.is_running = True
        
        while self.is_running:
            try:
                await self.check_for_new_orders()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in polling cycle: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying
    
    def stop_polling(self):
        """Stop the polling service"""
        logger.info("🛑 Stopping Smartsheet polling service...")
        self.is_running = False
    
    async def check_for_new_orders(self):
        """Check for new orders without review links"""
        try:
            from src.services.smartsheet_service import SmartsheetService
            from config.my_config import ORDERS_INTAKE_SHEET_ID
            
            service = SmartsheetService()
            sheet = service.client.Sheets.get_sheet(ORDERS_INTAKE_SHEET_ID)
            
            # Get column mappings
            column_map = self._get_column_mapping(sheet)
            
            new_orders_count = 0
            
            for row in sheet.rows:
                order_data = self._extract_row_data(row, column_map)
                
                # Check if this order needs a review link
                if self._needs_review_link(order_data):
                    await self._generate_and_update_review_link(service, sheet, row, order_data)
                    new_orders_count += 1
                    
                    # Add to processed set
                    quote_id = order_data.get('quote_id')
                    if quote_id:
                        self.processed_orders.add(quote_id)
            
            if new_orders_count > 0:
                logger.info(f"✅ Processed {new_orders_count} new orders")
            else:
                logger.debug("🔍 No new orders found")
                
        except Exception as e:
            logger.error(f"Error checking for new orders: {e}")
    
    def _get_column_mapping(self, sheet) -> Dict[str, int]:
        """Get column ID mapping from sheet"""
        column_map = {}
        for col in sheet.columns:
            if col.title == "Quote ID":
                column_map['quote_id'] = col.id
            elif col.title == "Quotation Link":
                column_map['quotation_link'] = col.id
            elif col.title == "Buyer's Name":
                column_map['customer_name'] = col.id
            elif col.title == "Buyer's Email Address":
                column_map['customer_email'] = col.id
            elif col.title == "Created Date":
                column_map['created_date'] = col.id
        
        return column_map
    
    def _extract_row_data(self, row, column_map: Dict[str, int]) -> Dict:
        """Extract data from a Smartsheet row"""
        data = {}
        
        for cell in row.cells:
            if cell.column_id == column_map.get('quote_id'):
                data['quote_id'] = cell.value
            elif cell.column_id == column_map.get('quotation_link'):
                data['quotation_link'] = cell.value
            elif cell.column_id == column_map.get('customer_name'):
                data['customer_name'] = cell.value
            elif cell.column_id == column_map.get('customer_email'):
                data['customer_email'] = cell.value
            elif cell.column_id == column_map.get('created_date'):
                data['created_date'] = cell.value
        
        data['row_id'] = row.id
        return data
    
    def _needs_review_link(self, order_data: Dict) -> bool:
        """Check if an order needs a review link generated"""
        quote_id = order_data.get('quote_id')
        quotation_link = order_data.get('quotation_link')
        
        # Skip if no quote ID
        if not quote_id:
            return False
        
        # Skip if already processed
        if quote_id in self.processed_orders:
            return False
        
        # Skip if already has a review link
        if quotation_link and quotation_link.strip():
            self.processed_orders.add(quote_id)  # Mark as processed
            return False
        
        return True
    
    async def _generate_and_update_review_link(self, service, sheet, row, order_data: Dict):
        """Generate review link and update the Smartsheet row"""
        try:
            quote_id = order_data.get('quote_id')
            customer_name = order_data.get('customer_name', 'Unknown')
            
            # Generate review link  
            domain = os.getenv('DOMAIN', 'localhost:8000')
            protocol = 'http'  # Always use HTTP for now
            review_link = f"{protocol}://{domain}/parts_review_interface.html?quote_id={quote_id}"
            
            # Update the row in Smartsheet
            from smartsheet.models import Cell, Row
            
            # Find the Quotation Link column
            quotation_link_column = None
            for col in sheet.columns:
                if col.title == "Quotation Link":
                    quotation_link_column = col
                    break
            
            if quotation_link_column:
                # Create update row with the quotation link
                update_row = Row()
                update_row.id = row.id
                update_row.cells.append(Cell({
                    'column_id': quotation_link_column.id,
                    'value': review_link
                }))
                
                # Update the row in Smartsheet
                service.client.Sheets.update_rows(sheet.id, [update_row])
                
                logger.info(f"✅ Generated review link for {quote_id} ({customer_name}): {review_link}")
            else:
                logger.warning("❌ Quotation Link column not found in sheet")
                
        except Exception as e:
            logger.error(f"Error generating review link for {order_data.get('quote_id', 'unknown')}: {e}")

# Global polling service instance
polling_service = SmartsheetPollingService()

async def start_polling_service():
    """Start the polling service"""
    await polling_service.start_polling()

def stop_polling_service():
    """Stop the polling service"""
    polling_service.stop_polling()

if __name__ == "__main__":
    # Test the polling service
    import asyncio
    asyncio.run(start_polling_service())
