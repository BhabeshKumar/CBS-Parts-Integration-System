"""
CBS Parts Service
Handles CBS parts database operations and integration with Smartsheet.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import smartsheet
import pandas as pd

# Add config to path
config_path = Path(__file__).parent.parent.parent / "config"
sys.path.insert(0, str(config_path))

from cbs_parts_config import (
    CBS_PARTS_SHEET_ID, CBS_PARTS_SHEET_NAME,
    PARTS_DATABASE_COLUMNS, PARTS_COLUMN_TYPES,
    PARTS_CATEGORIES, PARTS_BUSINESS_RULES,
    get_parts_column_name, get_parts_business_rule
)
from my_config import SMARTSHEET_API_TOKEN
from services.smartsheet_service import SmartsheetService

logger = logging.getLogger(__name__)

class CBSPartsService:
    """Service for managing CBS parts database in Smartsheet."""
    
    def __init__(self):
        """Initialize CBS Parts service."""
        self.smartsheet_service = SmartsheetService()
        self.client = smartsheet.Smartsheet(SMARTSHEET_API_TOKEN)
        self.client.errors_as_exceptions(True)
        
        # Parts sheet management
        self.parts_sheet_id = CBS_PARTS_SHEET_ID
        self.parts_sheet_name = CBS_PARTS_SHEET_NAME
        
        # Column ID cache for performance
        self.parts_column_cache = {}
        
        logger.info("CBS Parts Service initialized")
    
    def get_or_create_parts_sheet(self) -> Optional[int]:
        """Get existing parts sheet or create a new one."""
        try:
            # First try to get existing sheet by ID
            if self.parts_sheet_id:
                try:
                    sheet = self.client.Sheets.get_sheet(self.parts_sheet_id)
                    logger.info(f"Found existing parts sheet: {sheet.name}")
                    return self.parts_sheet_id
                except Exception as e:
                    logger.warning(f"Parts sheet ID {self.parts_sheet_id} not found: {e}")
            
            # Try to find sheet by name
            all_sheets = self.client.Sheets.list_sheets()
            for sheet in all_sheets.data:
                if sheet.name == self.parts_sheet_name:
                    self.parts_sheet_id = sheet.id
                    logger.info(f"Found parts sheet by name: {sheet.name}")
                    return sheet.id
            
            # Create new sheet
            logger.info(f"Creating new parts sheet: {self.parts_sheet_name}")
            return self._create_parts_sheet()
            
        except Exception as e:
            logger.error(f"Error getting/creating parts sheet: {e}")
            return None
    
    def _create_parts_sheet(self) -> Optional[int]:
        """Create a new parts sheet with proper columns."""
        try:
            # Define columns for the parts sheet
            columns = []
            for field_name, column_title in PARTS_DATABASE_COLUMNS.items():
                column_type = PARTS_COLUMN_TYPES.get(column_title, "TEXT_NUMBER")
                
                # Create column specification as dictionary
                column_spec = {
                    "title": column_title,
                    "type": column_type,
                    "primary": (field_name == "product_code")  # Product Code is primary
                }
                
                # Add dropdown options for category
                if column_title == "Category":
                    column_spec["options"] = PARTS_CATEGORIES
                
                columns.append(column_spec)
            
            # Create sheet specification
            sheet_spec = smartsheet.models.Sheet({
                "name": self.parts_sheet_name,
                "columns": columns
            })
            
            # Create the sheet using the correct method
            response = self.client.Home.create_sheet(sheet_spec)
            
            if response.message == 'SUCCESS':
                self.parts_sheet_id = response.result.id
                logger.info(f"Created parts sheet: {self.parts_sheet_name} (ID: {self.parts_sheet_id})")
                
                # Update config file with new sheet ID
                self._update_parts_config_with_sheet_id(self.parts_sheet_id)
                
                return self.parts_sheet_id
            else:
                logger.error(f"Failed to create parts sheet: {response.message}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating parts sheet: {e}")
            return None
    
    def _update_parts_config_with_sheet_id(self, sheet_id: int):
        """Update the config file with the new sheet ID."""
        try:
            config_file = config_path / "cbs_parts_config.py"
            
            # Read current config
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Update the parts sheet ID
            updated_content = content.replace(
                'CBS_PARTS_SHEET_ID = None',
                f'CBS_PARTS_SHEET_ID = "{sheet_id}"'
            )
            
            # Write back to file
            with open(config_file, 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Updated config with parts sheet ID: {sheet_id}")
            
        except Exception as e:
            logger.error(f"Error updating config with parts sheet ID: {e}")
    
    def import_parts_from_excel(self, excel_file_path: str) -> bool:
        """Import parts data from Excel file to Smartsheet."""
        try:
            # Read Excel file
            logger.info(f"Reading parts data from: {excel_file_path}")
            df = pd.read_excel(excel_file_path)
            
            # Validate required columns
            required_columns = ['Product Code', 'Description']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Get or create parts sheet
            sheet_id = self.get_or_create_parts_sheet()
            if not sheet_id:
                logger.error("Could not get or create parts sheet")
                return False
            
            # Get sheet and column info
            sheet = self.client.Sheets.get_sheet(sheet_id)
            column_map = {col.title: col.id for col in sheet.columns}
            
            # Prepare rows for import
            rows_to_add = []
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            for index, row in df.iterrows():
                try:
                    # Create cells for this row
                    cells = []
                    
                    # Map Excel columns to Smartsheet columns
                    for field_name, smartsheet_column in PARTS_DATABASE_COLUMNS.items():
                        if smartsheet_column in column_map:
                            column_id = column_map[smartsheet_column]
                            
                            # Get value from Excel
                            if field_name == "product_code":
                                value = str(row.get('Product Code', '')).strip()
                            elif field_name == "description":
                                value = str(row.get('Description', '')).strip()
                            elif field_name == "sales_price":
                                value = float(row.get('Sales Price', 0.0))
                            elif field_name == "quantity_in_stock":
                                value = float(row.get('Quantity In Stock', 0.0))
                            elif field_name == "free_stock":
                                value = float(row.get('Free Stock', 0.0))
                            elif field_name == "inactive":
                                value = bool(row.get('Inactive', False))
                            elif field_name == "category":
                                # Try to categorize based on product code/description
                                value = self._categorize_part(
                                    str(row.get('Product Code', '')),
                                    str(row.get('Description', ''))
                                )
                            elif field_name in ["last_updated", "created_date"]:
                                value = current_date
                            else:
                                value = ""
                            
                            # Only add non-empty values
                            if value != "" and value is not None:
                                cells.append({
                                    "columnId": column_id,
                                    "value": value
                                })
                    
                    # Skip rows without product code
                    if not any(cell.get("value") for cell in cells if column_map.get("Product Code") == cell.get("columnId")):
                        continue
                    
                    rows_to_add.append(smartsheet.models.Row({"cells": cells}))
                    
                    # Add in batches of 100 to avoid API limits
                    if len(rows_to_add) >= 100:
                        self._add_rows_to_sheet(sheet_id, rows_to_add)
                        rows_to_add = []
                
                except Exception as e:
                    logger.warning(f"Error processing row {index}: {e}")
                    continue
            
            # Add remaining rows
            if rows_to_add:
                self._add_rows_to_sheet(sheet_id, rows_to_add)
            
            logger.info(f"Successfully imported {len(df)} parts to Smartsheet")
            return True
            
        except Exception as e:
            logger.error(f"Error importing parts from Excel: {e}")
            return False
    
    def _add_rows_to_sheet(self, sheet_id: int, rows: List[smartsheet.models.Row]):
        """Add rows to sheet in batch."""
        try:
            result = self.client.Sheets.add_rows(sheet_id, rows)
            logger.debug(f"Added {len(rows)} rows to parts sheet")
        except Exception as e:
            logger.error(f"Error adding rows to sheet: {e}")
    
    def _categorize_part(self, product_code: str, description: str) -> str:
        """Automatically categorize parts based on code and description."""
        code_desc = f"{product_code} {description}".lower()
        
        for category in PARTS_CATEGORIES:
            if category.lower() in code_desc:
                return category
        
        # Additional categorization rules
        if any(keyword in code_desc for keyword in ["mixer", "mix"]):
            return "Mixers"
        elif any(keyword in code_desc for keyword in ["conveyor", "belt"]):
            return "Conveyors"
        elif any(keyword in code_desc for keyword in ["platform", "deck"]):
            return "Platforms"
        elif any(keyword in code_desc for keyword in ["roller", "roll"]):
            return "Rollers"
        elif any(keyword in code_desc for keyword in ["weigh", "weight"]):
            return "Weighbelt"
        elif "bom" in code_desc:
            return "BOM"
        else:
            return "Other"
    
    def search_parts(self, search_term: str, limit: int = None) -> List[Dict[str, Any]]:
        """Search for parts by product code or description."""
        try:
            if len(search_term) < get_parts_business_rule("search_minimum_chars"):
                return []
            
            sheet_id = self.get_or_create_parts_sheet()
            if not sheet_id:
                return []
            
            # Get sheet data
            sheet = self.client.Sheets.get_sheet(sheet_id)
            column_map = {col.title: col.id for col in sheet.columns}
            reverse_column_map = {col.id: col.title for col in sheet.columns}
            
            results = []
            search_lower = search_term.lower() if not get_parts_business_rule("case_sensitive_search") else search_term
            
            for row in sheet.rows:
                try:
                    # Extract row data
                    row_data = {}
                    for cell in row.cells:
                        column_title = reverse_column_map.get(cell.column_id, "Unknown")
                        row_data[column_title] = cell.value
                    
                    # Check if search term matches product code or description
                    product_code = str(row_data.get("Product Code", "")).lower()
                    description = str(row_data.get("Description", "")).lower()
                    
                    if (search_lower in product_code or search_lower in description):
                        # Skip inactive parts if configured
                        if (not get_parts_business_rule("inactive_parts_visible") and 
                            row_data.get("Inactive", False)):
                            continue
                        
                        results.append({
                            "product_code": row_data.get("Product Code", ""),
                            "description": row_data.get("Description", ""),
                            "sales_price": float(row_data.get("Sales Price", 0.0) or 0.0),
                            "quantity_in_stock": float(row_data.get("Quantity In Stock", 0.0) or 0.0),
                            "free_stock": float(row_data.get("Free Stock", 0.0) or 0.0),
                            "category": row_data.get("Category", "Other"),
                            "inactive": bool(row_data.get("Inactive", False))
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing search row: {e}")
                    continue
            
            # Apply limit
            max_results = limit or get_parts_business_rule("max_search_results")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching parts: {e}")
            return []
    
    def get_part_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Get specific part details by product code."""
        try:
            results = self.search_parts(product_code, limit=1)
            
            # Find exact match
            for result in results:
                if result["product_code"].lower() == product_code.lower():
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting part by code {product_code}: {e}")
            return None
    
    def get_all_parts(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all parts from the database."""
        try:
            sheet_id = self.get_or_create_parts_sheet()
            if not sheet_id:
                return []
            
            # Get sheet data
            sheet = self.client.Sheets.get_sheet(sheet_id)
            reverse_column_map = {col.id: col.title for col in sheet.columns}
            
            results = []
            for row in sheet.rows:
                try:
                    # Extract row data
                    row_data = {}
                    for cell in row.cells:
                        column_title = reverse_column_map.get(cell.column_id, "Unknown")
                        row_data[column_title] = cell.value
                    
                    # Skip inactive parts if not requested
                    if (not include_inactive and row_data.get("Inactive", False)):
                        continue
                    
                    results.append({
                        "product_code": row_data.get("Product Code", ""),
                        "description": row_data.get("Description", ""),
                        "sales_price": float(row_data.get("Sales Price", 0.0) or 0.0),
                        "quantity_in_stock": float(row_data.get("Quantity In Stock", 0.0) or 0.0),
                        "free_stock": float(row_data.get("Free Stock", 0.0) or 0.0),
                        "category": row_data.get("Category", "Other"),
                        "inactive": bool(row_data.get("Inactive", False))
                    })
                
                except Exception as e:
                    logger.warning(f"Error processing part row: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting all parts: {e}")
            return []
    
    def update_part_price(self, product_code: str, new_price: float) -> bool:
        """Update the price of a specific part."""
        try:
            sheet_id = self.get_or_create_parts_sheet()
            if not sheet_id:
                return False
            
            # Get sheet data
            sheet = self.client.Sheets.get_sheet(sheet_id)
            column_map = {col.title: col.id for col in sheet.columns}
            
            # Find the row with matching product code
            for row in sheet.rows:
                for cell in row.cells:
                    if (cell.column_id == column_map.get("Product Code") and 
                        str(cell.value).lower() == product_code.lower()):
                        
                        # Update the price cell
                        price_column_id = column_map.get("Sales Price")
                        updated_cell = smartsheet.models.Cell({
                            "column_id": price_column_id,
                            "value": new_price
                        })
                        
                        updated_row = smartsheet.models.Row({
                            "id": row.id,
                            "cells": [updated_cell]
                        })
                        
                        self.client.Sheets.update_rows(sheet_id, [updated_row])
                        logger.info(f"Updated price for {product_code}: {new_price}")
                        return True
            
            logger.warning(f"Part not found for price update: {product_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating part price: {e}")
            return False
