"""
Smartsheet service for CBS Automation.
Handles all Smartsheet API interactions.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import smartsheet

# Column mappings for Orders Intake sheet
ORDERS_INTAKE_COLUMNS = {
    "quote_id": "Quote ID",
    "customer_name": "Buyer's Name",
    "customer_email": "Buyer's Email Address",
    "customer_phone": "Buyer's Mobile No.",
    "customer_address": "Delivery Address",
    "order_date": "Order Date",
    "required_by_date": "Required-By Date",
    "quotation_update": "Quotation Update",
    "order_status": "Order Status",
    "quantity_required": "Quantity Required",
    "part_no": "Part No.",
    "part_description": "Part Description",
    "additional_notes": "Additional Notes",
    "quotation_link": "Quotation Link",
    "quote_generated_date": "Quote Generated Date"
}

logger = logging.getLogger(__name__)

class SmartsheetService:
    """Service for interacting with Smartsheet API."""
    
    def __init__(self):
        """Initialize Smartsheet service."""
        # Import configuration
        config_path = Path(__file__).parent.parent.parent / "config"
        sys.path.insert(0, str(config_path))
        
        try:
            from my_config import SMARTSHEET_API_TOKEN, ORDERS_INTAKE_SHEET_ID, SALES_WORKS_ORDERS_SHEET_ID
        except ImportError:
            # Fallback: try to read config directly
            logger.warning("Could not import config, trying direct file read")
            self._load_config_directly()
            return
        
        self.api_token = SMARTSHEET_API_TOKEN
        self.orders_intake_sheet_id = ORDERS_INTAKE_SHEET_ID
        self.sales_works_orders_sheet_id = SALES_WORKS_ORDERS_SHEET_ID
        
        # Initialize Smartsheet client
        self.client = smartsheet.Smartsheet(self.api_token)
        self.client.errors_as_exceptions(True)
        
        # Column ID cache
        self.column_cache = {
            "orders_intake": {},
            "sales_works_orders": {}
        }
        
        logger.info("Smartsheet service initialized")
    
    def _load_config_directly(self):
        """Load configuration directly from the config file."""
        try:
            config_file = Path(__file__).parent.parent.parent / "config" / "my_config.py"
            
            # Read the config file and extract values
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Extract values using simple parsing
            import re
            
            # Extract API token
            token_match = re.search(r'SMARTSHEET_API_TOKEN\s*=\s*["\']([^"\']+)["\']', content)
            self.api_token = token_match.group(1) if token_match else ""
            
            # Extract sheet IDs
            orders_match = re.search(r'ORDERS_INTAKE_SHEET_ID\s*=\s*["\']([^"\']+)["\']', content)
            self.orders_intake_sheet_id = orders_match.group(1) if orders_match else ""
            
            sales_match = re.search(r'SALES_WORKS_ORDERS_SHEET_ID\s*=\s*["\']([^"\']+)["\']', content)
            self.sales_works_orders_sheet_id = sales_match.group(1) if sales_match else ""
            
            # Initialize Smartsheet client
            if self.api_token:
                self.client = smartsheet.Smartsheet(self.api_token)
                self.client.errors_as_exceptions(True)
            else:
                self.client = None
            
            # Column ID cache
            self.column_cache = {
                "orders_intake": {},
                "sales_works_orders": {}
            }
            
            logger.info("Smartsheet service initialized (direct config load)")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.api_token = ""
            self.orders_intake_sheet_id = ""
            self.sales_works_orders_sheet_id = ""
            self.client = None
            self.column_cache = {}
    
    def test_connection(self) -> bool:
        """Test connection to Smartsheet API."""
        try:
            if not self.client:
                logger.error("Smartsheet client not initialized")
                return False
            
            # Try to get user info
            user = self.client.Users.get_current_user()
            logger.info(f"Connected to Smartsheet as: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Smartsheet connection failed: {e}")
            return False
    
    def get_sheet(self, sheet_id: str) -> Optional[smartsheet.models.Sheet]:
        """Get a sheet by ID."""
        try:
            sheet = self.client.Sheets.get_sheet(sheet_id)
            return sheet
        except Exception as e:
            logger.error(f"Error getting sheet {sheet_id}: {e}")
            return None
    
    def get_orders_intake_sheet(self) -> Optional[smartsheet.models.Sheet]:
        """Get the orders intake sheet."""
        return self.get_sheet(self.orders_intake_sheet_id)
    
    def get_sales_works_orders_sheet(self) -> Optional[smartsheet.models.Sheet]:
        """Get the sales and works orders sheet."""
        return self.get_sheet(self.sales_works_orders_sheet_id)
    
    def get_column_id(self, sheet_type: str, column_name: str) -> Optional[int]:
        """Get column ID by name from cache or API."""
        if sheet_type not in self.column_cache:
            self.column_cache[sheet_type] = {}
        
        # Check cache first
        if column_name in self.column_cache[sheet_type]:
            return self.column_cache[sheet_type][column_name]
        
        # Get sheet and find column
        sheet_id = self.orders_intake_sheet_id if sheet_type == "orders_intake" else self.sales_works_orders_sheet_id
        sheet = self.get_sheet(sheet_id)
        
        if not sheet:
            return None
        
        # Find column by name
        for column in sheet.columns:
            if column.title == column_name:
                self.column_cache[sheet_type][column_name] = column.id
                return column.id
        
        logger.warning(f"Column '{column_name}' not found in {sheet_type} sheet")
        return None
    
    def _get_cell_by_column_title(self, row: smartsheet.models.Row, column_title: str) -> Optional[smartsheet.models.Cell]:
        """Get cell value by column title from a row."""
        try:
            # Find column ID by title
            column_id = None
            for column in row.sheet.columns if hasattr(row, 'sheet') and row.sheet else []:
                if column.title == column_title:
                    column_id = column.id
                    break
            
            if not column_id:
                # Try to get from cache
                sheet_type = "orders_intake" if hasattr(self, 'orders_intake_sheet_id') else "sales_works_orders"
                column_id = self.get_column_id(sheet_type, column_title)
            
            if not column_id:
                return None
            
            # Find cell in row
            for cell in row.cells:
                if cell.column_id == column_id:
                    return cell
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cell by column title '{column_title}': {e}")
            return None
    
    def get_row_data(self, sheet: smartsheet.models.Sheet, row: smartsheet.models.Row) -> Dict[str, Any]:
        """Extract data from a row as a dictionary with column titles as keys."""
        try:
            result = {}
            
            # Create column lookup by ID
            column_lookup = {col.id: col.title for col in sheet.columns}
            
            # Extract cell values
            for cell in row.cells:
                if cell.column_id in column_lookup:
                    column_title = column_lookup[cell.column_id]
                    result[column_title] = cell.value
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting row data: {e}")
            return {}
    
    def add_row(self, sheet_id: str, row_data: Dict[str, Any]) -> Optional[smartsheet.models.Row]:
        """Add a new row to a sheet."""
        try:
            # Create row object
            row = smartsheet.models.Row()
            row.to_top = True
            
            # Add cells
            cells = []
            for column_name, value in row_data.items():
                column_id = self.get_column_id("orders_intake" if sheet_id == self.orders_intake_sheet_id else "sales_works_orders", column_name)
                if column_id:
                    cell = smartsheet.models.Cell()
                    cell.column_id = column_id
                    cell.value = value
                    cells.append(cell)
            
            row.cells = cells
            
            # Add row to sheet
            result = self.client.Sheets.add_rows(sheet_id, [row])
            if result and hasattr(result, 'data') and len(result.data) > 0:
                logger.info(f"Row added successfully to sheet {sheet_id}")
                return result.data[0]
            else:
                logger.error("Failed to add row")
                return None
                
        except Exception as e:
            logger.error(f"Error adding row to sheet {sheet_id}: {e}")
            return None
    
    def add_order_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new order row to the Orders Intake sheet."""
        try:
            # Use the existing add_row method
            result = self.add_row(self.orders_intake_sheet_id, row_data)
            
            if result:
                return {
                    'success': True,
                    'row_id': result.id,
                    'message': 'Order added successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add row to Orders Intake sheet'
                }
                
        except Exception as e:
            logger.error(f"Error adding order row: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_row(self, sheet_id: str, row_id: int, row_data: Dict[str, Any]) -> bool:
        """Update an existing row in a sheet."""
        try:
            # Create row object
            row = smartsheet.models.Row()
            row.id = row_id
            
            # Add cells
            cells = []
            for column_name, value in row_data.items():
                column_id = self.get_column_id("orders_intake" if sheet_id == self.orders_intake_sheet_id else "sales_works_orders", column_name)
                if column_id:
                    cell = smartsheet.models.Cell()
                    cell.column_id = column_id
                    cell.value = value
                    cells.append(cell)
            
            row.cells = cells
            
            # Update row
            self.client.Sheets.update_rows(sheet_id, [row])
            logger.info(f"Row {row_id} updated successfully in sheet {sheet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating row {row_id} in sheet {sheet_id}: {e}")
            return False
    
    def get_rows(self, sheet_id: str, row_ids: Optional[List[int]] = None) -> List[smartsheet.models.Row]:
        """Get rows from a sheet."""
        try:
            if row_ids:
                rows = self.client.Sheets.get_rows(sheet_id, row_ids=row_ids)
            else:
                sheet = self.get_sheet(sheet_id)
                rows = sheet.rows if sheet else []
            
            return rows
        except Exception as e:
            logger.error(f"Error getting rows from sheet {sheet_id}: {e}")
            return []
    
    def search_rows(self, sheet_id: str, search_criteria: Dict[str, Any]) -> List[smartsheet.models.Row]:
        """Search for rows based on criteria."""
        try:
            rows = self.get_rows(sheet_id)
            matching_rows = []
            
            for row in rows:
                if self._row_matches_criteria(row, search_criteria):
                    matching_rows.append(row)
            
            return matching_rows
            
        except Exception as e:
            logger.error(f"Error searching rows in sheet {sheet_id}: {e}")
            return []
    
    def _row_matches_criteria(self, row: smartsheet.models.Row, criteria: Dict[str, Any]) -> bool:
        """Check if a row matches search criteria."""
        try:
            for column_name, expected_value in criteria.items():
                # Find cell value for this column
                cell_value = None
                for cell in row.cells:
                    # This is a simplified check - in practice you'd need to map column IDs
                    if hasattr(cell, 'column_id'):
                        # For now, just check if any cell contains the expected value
                        if str(expected_value) in str(cell.value):
                            cell_value = cell.value
                            break
                
                if cell_value != expected_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking row criteria: {e}")
            return False
    
    def add_attachment(self, sheet_id: str, row_id: int, file_path: str, filename: Optional[str] = None) -> bool:
        """Add attachment to a row."""
        try:
            if not filename:
                filename = os.path.basename(file_path)
            
            # Add attachment to row using the correct SDK method
            # The method signature is: attach_file_to_row(sheet_id, row_id, file_path)
            result = self.client.Attachments.attach_file_to_row(sheet_id, row_id, file_path)
            
            if result:
                logger.info(f"Attachment '{filename}' added to row {row_id}")
                return True
            else:
                logger.error("Failed to add attachment")
                return False
                
        except Exception as e:
            logger.error(f"Error adding attachment to row {row_id}: {e}")
            return False
    
    def get_attachments(self, sheet_id: str, row_id: int) -> List[smartsheet.models.Attachment]:
        """Get attachments for a row."""
        try:
            attachments = self.client.Sheets.get_row_attachments(sheet_id, row_id)
            return attachments
        except Exception as e:
            logger.error(f"Error getting attachments for row {row_id}: {e}")
            return []
    
    def delete_row(self, sheet_id: str, row_id: int) -> bool:
        """Delete a row from a sheet."""
        try:
            self.client.Sheets.delete_rows(sheet_id, [row_id])
            logger.info(f"Row {row_id} deleted from sheet {sheet_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting row {row_id} from sheet {sheet_id}: {e}")
            return False
    
    def get_sheet_summary(self, sheet_id: str) -> Dict[str, Any]:
        """Get summary information about a sheet."""
        try:
            sheet = self.get_sheet(sheet_id)
            if not sheet:
                return {}
            
            return {
                "id": sheet.id,
                "name": sheet.name,
                "total_rows": len(sheet.rows),
                "total_columns": len(sheet.columns),
                "access_level": sheet.access_level,
                "permalink": sheet.permalink,
                "modified_at": sheet.modified_at.isoformat() if sheet.modified_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting sheet summary for {sheet_id}: {e}")
            return {}

    def add_column(self, sheet_id: str, column_title: str, column_type: str = "TEXT_NUMBER") -> Optional[int]:
        """Add a new column to a sheet."""
        try:
            # Get the current sheet
            sheet = self.get_sheet(sheet_id)
            if not sheet:
                logger.error(f"Could not get sheet {sheet_id}")
                return None
            
            # Create new column
            new_column = smartsheet.models.Column()
            new_column.title = column_title
            new_column.type = column_type
            new_column.primary = False
            
            # Add the new column to the existing columns
            sheet.columns.append(new_column)
            
            # Update the sheet with the new column
            result = self.client.Sheets.update_sheet(sheet_id, sheet)
            
            if result and hasattr(result, 'columns'):
                # Find the new column ID
                for col in result.columns:
                    if col.title == column_title:
                        logger.info(f"Column '{column_title}' added to sheet {sheet_id} with ID {col.id}")
                        # Update column cache
                        sheet_type = "orders_intake" if sheet_id == self.orders_intake_sheet_id else "sales_works_orders"
                        self.column_cache[sheet_type][column_title] = col.id
                        return col.id
                
                logger.error(f"Column '{column_title}' not found after update")
                return None
            else:
                logger.error(f"Failed to update sheet with new column '{column_title}'")
                return None
                
        except Exception as e:
            logger.error(f"Error adding column '{column_title}' to sheet {sheet_id}: {e}")
            return None

    def ensure_required_columns(self, sheet_id: str, required_columns: Dict[str, str]) -> bool:
        """Ensure all required columns exist in the sheet."""
        try:
            sheet = self.get_sheet(sheet_id)
            if not sheet:
                logger.error(f"Could not get sheet {sheet_id}")
                return False
            
            existing_columns = {col.title: col.id for col in sheet.columns}
            missing_columns = []
            
            for column_key, column_title in required_columns.items():
                if column_title not in existing_columns:
                    missing_columns.append(column_title)
            
            if not missing_columns:
                logger.info(f"All required columns already exist in sheet {sheet_id}")
                return True
            
            logger.info(f"Adding {len(missing_columns)} missing columns to sheet {sheet_id}")
            
            for column_title in missing_columns:
                column_id = self.add_column(sheet_id, column_title)
                if not column_id:
                    logger.error(f"Failed to add column '{column_title}'")
                    return False
            
            logger.info(f"Successfully added all missing columns to sheet {sheet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring required columns in sheet {sheet_id}: {e}")
            return False
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Get the column mapping for Orders Intake sheet."""
        return ORDERS_INTAKE_COLUMNS
    
    def get_orders_intake_sheet(self):
        """Get the Orders Intake sheet."""
        try:
            if not self.orders_intake_sheet_id:
                logger.error("Orders Intake sheet ID not configured")
                return None
            
            sheet = self.client.Sheets.get_sheet(self.orders_intake_sheet_id)
            return sheet
            
        except Exception as e:
            logger.error(f"Error getting Orders Intake sheet: {e}")
            return None
