"""
Lightweight CBS Parts Service without pandas dependency
"""
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CBSPartsService:
    def __init__(self):
        self.parts_cache = {}
        
    def search_parts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for parts in the CBS parts database"""
        try:
            from src.services.smartsheet_service import SmartsheetService
            from config.cbs_parts_config import CBS_PARTS_SHEET_ID
            
            service = SmartsheetService()
            sheet = service.client.Sheets.get_sheet(CBS_PARTS_SHEET_ID)
            
            if not sheet or not sheet.rows:
                logger.warning("No parts data found in sheet")
                return []
            
            # Get column mapping
            columns = {col.title: col.id for col in sheet.columns}
            
            parts = []
            query_lower = query.lower()
            
            for row in sheet.rows:
                row_data = {}
                for cell in row.cells:
                    col_title = next((title for title, col_id in columns.items() if col_id == cell.column_id), None)
                    if col_title and cell.value:
                        row_data[col_title] = str(cell.value)
                
                # Search in product code and description
                product_code = row_data.get('Product Code', '').lower()
                description = row_data.get('Description', '').lower()
                
                if (query_lower in product_code or 
                    query_lower in description or
                    any(query_lower in str(value).lower() for value in row_data.values())):
                    
                    # Format the part data
                    part = {
                        'product_code': row_data.get('Product Code', ''),
                        'description': row_data.get('Description', ''),
                        'sales_price': self._parse_price(row_data.get('Sales Price', '0')),
                        'cost_price': self._parse_price(row_data.get('Cost Price', '0')),
                        'stock_level': row_data.get('Stock Level', 'Unknown'),
                        'category': row_data.get('Category', ''),
                        'supplier': row_data.get('Supplier', ''),
                        'notes': row_data.get('Notes', ''),
                        'row_id': row.id
                    }
                    parts.append(part)
                    
                    if len(parts) >= limit:
                        break
            
            logger.info(f"Found {len(parts)} parts for query: {query}")
            return parts
            
        except Exception as e:
            logger.error(f"Error searching parts: {e}")
            return []
    
    def get_part_by_id(self, part_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific part by product code"""
        try:
            # Search for exact match
            results = self.search_parts(part_id, limit=1)
            for part in results:
                if part.get('product_code', '').upper() == part_id.upper():
                    return part
            return None
            
        except Exception as e:
            logger.error(f"Error getting part {part_id}: {e}")
            return None
    
    def get_customer_discounts(self, customer_email: str) -> List[Dict[str, Any]]:
        """Get customer-specific discounts"""
        try:
            from src.services.smartsheet_service import SmartsheetService
            from config.cbs_parts_config import CBS_DISCOUNTS_SHEET_ID
            
            service = SmartsheetService()
            sheet = service.client.Sheets.get_sheet(CBS_DISCOUNTS_SHEET_ID)
            
            if not sheet or not sheet.rows:
                logger.info("No discount data found")
                return []
            
            # Get column mapping
            columns = {col.title: col.id for col in sheet.columns}
            
            discounts = []
            for row in sheet.rows:
                row_data = {}
                for cell in row.cells:
                    col_title = next((title for title, col_id in columns.items() if col_id == cell.column_id), None)
                    if col_title and cell.value:
                        row_data[col_title] = str(cell.value)
                
                # Check if this discount applies to the customer
                discount_email = row_data.get('Customer Email', '').lower()
                if discount_email == customer_email.lower():
                    discount = {
                        'customer_email': customer_email,
                        'product_code': row_data.get('Product Code', ''),
                        'discount_percentage': self._parse_percentage(row_data.get('Discount Percentage', '0')),
                        'discount_type': row_data.get('Discount Type', 'percentage'),
                        'valid_from': row_data.get('Valid From', ''),
                        'valid_until': row_data.get('Valid Until', ''),
                        'notes': row_data.get('Notes', ''),
                        'row_id': row.id
                    }
                    discounts.append(discount)
            
            logger.info(f"Found {len(discounts)} discounts for customer: {customer_email}")
            return discounts
            
        except Exception as e:
            logger.error(f"Error getting discounts for {customer_email}: {e}")
            return []
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float"""
        try:
            # Remove currency symbols and spaces
            price_clean = str(price_str).replace('£', '').replace('$', '').replace('€', '').replace(',', '').strip()
            return float(price_clean) if price_clean else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_percentage(self, percentage_str: str) -> float:
        """Parse percentage string to float"""
        try:
            # Remove % symbol and spaces
            percentage_clean = str(percentage_str).replace('%', '').strip()
            return float(percentage_clean) if percentage_clean else 0.0
        except (ValueError, TypeError):
            return 0.0
