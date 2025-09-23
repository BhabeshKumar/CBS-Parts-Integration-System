"""
CBS Discounts Service
Handles customer discount management and calculations.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import smartsheet
import re

# Add config to path
config_path = Path(__file__).parent.parent.parent / "config"
sys.path.insert(0, str(config_path))

from cbs_parts_config import (
    CBS_DISCOUNTS_SHEET_ID, CBS_DISCOUNTS_SHEET_NAME,
    DISCOUNTS_DATABASE_COLUMNS, DISCOUNTS_COLUMN_TYPES,
    DISCOUNT_TYPES, DISCOUNT_BUSINESS_RULES,
    get_discounts_column_name, get_discount_business_rule
)
from my_config import SMARTSHEET_API_TOKEN
from services.smartsheet_service import SmartsheetService

logger = logging.getLogger(__name__)

class CBSDiscountsService:
    """Service for managing customer discounts in Smartsheet."""
    
    def __init__(self):
        """Initialize CBS Discounts service."""
        self.smartsheet_service = SmartsheetService()
        self.client = smartsheet.Smartsheet(SMARTSHEET_API_TOKEN)
        self.client.errors_as_exceptions(True)
        
        # Discounts sheet management
        self.discounts_sheet_id = CBS_DISCOUNTS_SHEET_ID
        self.discounts_sheet_name = CBS_DISCOUNTS_SHEET_NAME
        
        # Column ID cache for performance
        self.discounts_column_cache = {}
        
        logger.info("CBS Discounts Service initialized")
    
    def get_or_create_discounts_sheet(self) -> Optional[int]:
        """Get existing discounts sheet or create a new one."""
        try:
            # First try to get existing sheet by ID
            if self.discounts_sheet_id:
                try:
                    sheet = self.client.Sheets.get_sheet(self.discounts_sheet_id)
                    logger.info(f"Found existing discounts sheet: {sheet.name}")
                    return self.discounts_sheet_id
                except Exception as e:
                    logger.warning(f"Discounts sheet ID {self.discounts_sheet_id} not found: {e}")
            
            # Try to find sheet by name
            all_sheets = self.client.Sheets.list_sheets()
            for sheet in all_sheets.data:
                if sheet.name == self.discounts_sheet_name:
                    self.discounts_sheet_id = sheet.id
                    logger.info(f"Found discounts sheet by name: {sheet.name}")
                    return sheet.id
            
            # Create new sheet
            logger.info(f"Creating new discounts sheet: {self.discounts_sheet_name}")
            return self._create_discounts_sheet()
            
        except Exception as e:
            logger.error(f"Error getting/creating discounts sheet: {e}")
            return None
    
    def _create_discounts_sheet(self) -> Optional[int]:
        """Create a new discounts sheet with proper columns."""
        try:
            # Define columns for the discounts sheet
            columns = []
            for field_name, column_title in DISCOUNTS_DATABASE_COLUMNS.items():
                column_type = DISCOUNTS_COLUMN_TYPES.get(column_title, "TEXT_NUMBER")
                
                # Create column specification as dictionary
                column_spec = {
                    "title": column_title,
                    "type": column_type,
                    "primary": (field_name == "customer_email")  # Customer Email is primary
                }
                
                # Add dropdown options for discount type
                if column_title == "Discount Type":
                    column_spec["options"] = DISCOUNT_TYPES
                
                columns.append(column_spec)
            
            # Create sheet specification
            sheet_spec = smartsheet.models.Sheet({
                "name": self.discounts_sheet_name,
                "columns": columns
            })
            
            # Create the sheet using the correct method
            response = self.client.Home.create_sheet(sheet_spec)
            
            if response.message == 'SUCCESS':
                self.discounts_sheet_id = response.result.id
                logger.info(f"Created discounts sheet: {self.discounts_sheet_name} (ID: {self.discounts_sheet_id})")
                
                # Update config file with new sheet ID
                self._update_discounts_config_with_sheet_id(self.discounts_sheet_id)
                
                # Add some example rows
                self._add_example_discount_rows(self.discounts_sheet_id)
                
                return self.discounts_sheet_id
            else:
                logger.error(f"Failed to create discounts sheet: {response.message}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating discounts sheet: {e}")
            return None
    
    def _update_discounts_config_with_sheet_id(self, sheet_id: int):
        """Update the config file with the new sheet ID."""
        try:
            config_file = config_path / "cbs_parts_config.py"
            
            # Read current config
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Update the discounts sheet ID
            updated_content = content.replace(
                'CBS_DISCOUNTS_SHEET_ID = None',
                f'CBS_DISCOUNTS_SHEET_ID = "{sheet_id}"'
            )
            
            # Write back to file
            with open(config_file, 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Updated config with discounts sheet ID: {sheet_id}")
            
        except Exception as e:
            logger.error(f"Error updating config with discounts sheet ID: {e}")
    
    def _add_example_discount_rows(self, sheet_id: int):
        """Add example discount rows to help understand the system."""
        try:
            # Get sheet and column info
            sheet = self.client.Sheets.get_sheet(sheet_id)
            column_map = {col.title: col.id for col in sheet.columns}
            
            example_discounts = [
                {
                    "Customer Email": "test@concretebatchingsystems.com",
                    "Customer Domain": "concretebatchingsystems.com",
                    "Discount Percentage": 15.0,
                    "Global Discount": True,
                    "Part Specific Discount": False,
                    "Discount Type": "Global",
                    "Valid From": datetime.now().strftime("%Y-%m-%d"),
                    "Valid Until": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
                    "Active": True,
                    "Notes": "Corporate discount for CBS company emails",
                    "Created Date": datetime.now().strftime("%Y-%m-%d")
                },
                {
                    "Customer Email": "test@sheaney.ie",
                    "Customer Domain": "sheaney.ie", 
                    "Discount Percentage": 20.0,
                    "Global Discount": True,
                    "Part Specific Discount": False,
                    "Discount Type": "Global",
                    "Valid From": datetime.now().strftime("%Y-%m-%d"),
                    "Valid Until": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
                    "Active": True,
                    "Notes": "Partner company discount",
                    "Created Date": datetime.now().strftime("%Y-%m-%d")
                },
                {
                    "Customer Email": "special@customer.com",
                    "Customer Domain": "customer.com",
                    "Discount Percentage": 10.0,
                    "Global Discount": False,
                    "Part Specific Discount": True,
                    "Product Code": "01-WEIGHBELT",
                    "Discount Type": "Part-Specific",
                    "Valid From": datetime.now().strftime("%Y-%m-%d"),
                    "Valid Until": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
                    "Active": True,
                    "Notes": "Special discount on weighbelt parts only",
                    "Created Date": datetime.now().strftime("%Y-%m-%d")
                }
            ]
            
            rows_to_add = []
            for discount_data in example_discounts:
                cells = []
                for column_title, value in discount_data.items():
                    if column_title in column_map:
                        cells.append({
                            "columnId": column_map[column_title],
                            "value": value
                        })
                
                rows_to_add.append(smartsheet.models.Row({"cells": cells}))
            
            # Add rows to sheet
            self.client.Sheets.add_rows(sheet_id, rows_to_add)
            logger.info(f"Added {len(example_discounts)} example discount rows")
            
        except Exception as e:
            logger.error(f"Error adding example discount rows: {e}")
    
    def get_customer_discount(self, customer_email: str) -> Dict[str, Any]:
        """Get discount information for a customer by email."""
        try:
            sheet_id = self.get_or_create_discounts_sheet()
            if not sheet_id:
                return self._get_default_discount()
            
            # Get sheet data
            sheet = self.client.Sheets.get_sheet(sheet_id)
            reverse_column_map = {col.id: col.title for col in sheet.columns}
            
            customer_domain = self._extract_domain_from_email(customer_email)
            discounts = []
            
            for row in sheet.rows:
                try:
                    # Extract row data
                    row_data = {}
                    for cell in row.cells:
                        column_title = reverse_column_map.get(cell.column_id, "Unknown")
                        row_data[column_title] = cell.value
                    
                    # Skip inactive discounts
                    if not row_data.get("Active", False):
                        continue
                    
                    # Check if discount applies to this customer
                    if self._discount_applies_to_customer(row_data, customer_email, customer_domain):
                        # Validate discount dates
                        if self._is_discount_valid_by_date(row_data):
                            discounts.append(row_data)
                
                except Exception as e:
                    logger.warning(f"Error processing discount row: {e}")
                    continue
            
            # Process discounts and return the best applicable discount
            return self._process_customer_discounts(discounts)
            
        except Exception as e:
            logger.error(f"Error getting customer discount for {customer_email}: {e}")
            return self._get_default_discount()
    
    def _extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email address."""
        try:
            if "@" in email:
                return email.split("@")[1].lower()
            return ""
        except:
            return ""
    
    def _discount_applies_to_customer(self, discount_data: Dict[str, Any], 
                                    customer_email: str, customer_domain: str) -> bool:
        """Check if a discount applies to a customer."""
        # Check email match
        discount_email = str(discount_data.get("Customer Email", "")).lower()
        if discount_email and discount_email == customer_email.lower():
            return True
        
        # Check domain match if enabled
        if get_discount_business_rule("domain_matching_enabled"):
            discount_domain = str(discount_data.get("Customer Domain", "")).lower()
            if discount_domain and discount_domain == customer_domain:
                return True
        
        return False
    
    def _is_discount_valid_by_date(self, discount_data: Dict[str, Any]) -> bool:
        """Check if discount is valid by date range."""
        try:
            current_date = datetime.now().date()
            
            # Check valid from date
            valid_from = discount_data.get("Valid From")
            if valid_from:
                if isinstance(valid_from, str):
                    valid_from_date = datetime.strptime(valid_from, "%Y-%m-%d").date()
                else:
                    valid_from_date = valid_from.date() if hasattr(valid_from, 'date') else valid_from
                
                if current_date < valid_from_date:
                    return False
            
            # Check valid until date
            valid_until = discount_data.get("Valid Until")
            if valid_until:
                if isinstance(valid_until, str):
                    valid_until_date = datetime.strptime(valid_until, "%Y-%m-%d").date()
                else:
                    valid_until_date = valid_until.date() if hasattr(valid_until, 'date') else valid_until
                
                if current_date > valid_until_date:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating discount dates: {e}")
            return True  # Default to valid if can't parse dates
    
    def _process_customer_discounts(self, discounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple discounts and return the best applicable discount structure."""
        if not discounts:
            return self._get_default_discount()
        
        # Separate global and part-specific discounts
        global_discounts = [d for d in discounts if d.get("Global Discount", False)]
        part_specific_discounts = [d for d in discounts if d.get("Part Specific Discount", False)]
        
        # Find best global discount
        best_global_discount = 0.0
        global_discount_info = None
        for discount in global_discounts:
            discount_percentage = float(discount.get("Discount Percentage", 0.0))
            if discount_percentage > best_global_discount:
                best_global_discount = discount_percentage
                global_discount_info = discount
        
        # Build part-specific discounts map
        part_discounts = {}
        for discount in part_specific_discounts:
            product_code = str(discount.get("Product Code", "")).strip()
            discount_percentage = float(discount.get("Discount Percentage", 0.0))
            
            if product_code and discount_percentage > 0:
                # Keep the highest discount for each part
                if (product_code not in part_discounts or 
                    discount_percentage > part_discounts[product_code]["percentage"]):
                    part_discounts[product_code] = {
                        "percentage": discount_percentage,
                        "info": discount
                    }
        
        return {
            "has_discount": bool(global_discounts or part_specific_discounts),
            "global_discount": {
                "percentage": best_global_discount,
                "info": global_discount_info
            },
            "part_specific_discounts": part_discounts,
            "discount_priority": get_discount_business_rule("global_discount_priority")
        }
    
    def _get_default_discount(self) -> Dict[str, Any]:
        """Get default discount structure when no discounts are found."""
        return {
            "has_discount": False,
            "global_discount": {
                "percentage": get_discount_business_rule("default_discount"),
                "info": None
            },
            "part_specific_discounts": {},
            "discount_priority": get_discount_business_rule("global_discount_priority")
        }
    
    def calculate_discount_for_item(self, customer_discount: Dict[str, Any], 
                                  product_code: str, unit_price: float, 
                                  quantity: int = 1) -> Dict[str, Any]:
        """Calculate discount for a specific item."""
        try:
            if not customer_discount.get("has_discount", False):
                return {
                    "original_price": unit_price,
                    "discount_percentage": 0.0,
                    "discount_amount": 0.0,
                    "discounted_price": unit_price,
                    "total_original": unit_price * quantity,
                    "total_discount": 0.0,
                    "total_discounted": unit_price * quantity,
                    "discount_type": "None"
                }
            
            discount_percentage = 0.0
            discount_type = "None"
            
            # Check for part-specific discount first
            part_discounts = customer_discount.get("part_specific_discounts", {})
            if product_code in part_discounts:
                discount_percentage = part_discounts[product_code]["percentage"]
                discount_type = "Part-Specific"
            
            # Check for global discount (may override part-specific based on priority)
            global_discount = customer_discount.get("global_discount", {})
            global_percentage = global_discount.get("percentage", 0.0)
            
            if global_percentage > 0:
                if (customer_discount.get("discount_priority", True) or 
                    discount_percentage == 0.0):  # Global priority or no part-specific discount
                    discount_percentage = global_percentage
                    discount_type = "Global"
                elif global_percentage > discount_percentage:  # Use higher discount
                    discount_percentage = global_percentage
                    discount_type = "Global"
            
            # Validate discount range
            if get_discount_business_rule("discount_validation"):
                max_discount = get_discount_business_rule("max_discount_percentage")
                if discount_percentage > max_discount:
                    logger.warning(f"Discount {discount_percentage}% exceeds maximum {max_discount}%")
                    discount_percentage = max_discount
            
            # Calculate discount amounts
            discount_decimal = discount_percentage / 100.0
            discount_amount = unit_price * discount_decimal
            discounted_price = unit_price - discount_amount
            
            # Calculate totals
            total_original = unit_price * quantity
            total_discount = discount_amount * quantity
            total_discounted = discounted_price * quantity
            
            # Round to configured decimal places
            decimal_places = get_discount_business_rule("discount_rounding")
            
            return {
                "original_price": round(unit_price, decimal_places),
                "discount_percentage": round(discount_percentage, decimal_places),
                "discount_amount": round(discount_amount, decimal_places),
                "discounted_price": round(discounted_price, decimal_places),
                "total_original": round(total_original, decimal_places),
                "total_discount": round(total_discount, decimal_places),
                "total_discounted": round(total_discounted, decimal_places),
                "discount_type": discount_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating discount for item: {e}")
            # Return original pricing on error
            return {
                "original_price": unit_price,
                "discount_percentage": 0.0,
                "discount_amount": 0.0,
                "discounted_price": unit_price,
                "total_original": unit_price * quantity,
                "total_discount": 0.0,
                "total_discounted": unit_price * quantity,
                "discount_type": "Error"
            }
    
    def add_customer_discount(self, customer_email: str, discount_percentage: float,
                            discount_type: str = "Global", product_code: str = None,
                            notes: str = "", valid_days: int = 365) -> bool:
        """Add a new customer discount."""
        try:
            sheet_id = self.get_or_create_discounts_sheet()
            if not sheet_id:
                return False
            
            # Validate inputs
            if not customer_email or discount_percentage < 0:
                logger.error("Invalid customer email or discount percentage")
                return False
            
            if discount_type not in DISCOUNT_TYPES:
                logger.error(f"Invalid discount type: {discount_type}")
                return False
            
            if discount_type == "Part-Specific" and not product_code:
                logger.error("Product code required for part-specific discounts")
                return False
            
            # Get sheet and column info
            sheet = self.client.Sheets.get_sheet(sheet_id)
            column_map = {col.title: col.id for col in sheet.columns}
            
            # Prepare discount data
            customer_domain = self._extract_domain_from_email(customer_email)
            valid_from = datetime.now().strftime("%Y-%m-%d")
            valid_until = (datetime.now() + timedelta(days=valid_days)).strftime("%Y-%m-%d")
            
            discount_data = {
                "Customer Email": customer_email,
                "Customer Domain": customer_domain,
                "Discount Percentage": discount_percentage,
                "Global Discount": discount_type == "Global",
                "Part Specific Discount": discount_type == "Part-Specific",
                "Product Code": product_code or "",
                "Discount Type": discount_type,
                "Valid From": valid_from,
                "Valid Until": valid_until,
                "Active": True,
                "Notes": notes,
                "Created Date": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Create cells for the new row
            cells = []
            for column_title, value in discount_data.items():
                if column_title in column_map and value is not None:
                    cells.append({
                        "columnId": column_map[column_title],
                        "value": value
                    })
            
            # Add row to sheet
            new_row = smartsheet.models.Row({"cells": cells})
            result = self.client.Sheets.add_rows(sheet_id, [new_row])
            
            logger.info(f"Added discount for {customer_email}: {discount_percentage}% ({discount_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding customer discount: {e}")
            return False
    
    def get_all_customer_discounts(self) -> List[Dict[str, Any]]:
        """Get all customer discounts for management."""
        try:
            sheet_id = self.get_or_create_discounts_sheet()
            if not sheet_id:
                return []
            
            # Get sheet data
            sheet = self.client.Sheets.get_sheet(sheet_id)
            reverse_column_map = {col.id: col.title for col in sheet.columns}
            
            discounts = []
            for row in sheet.rows:
                try:
                    # Extract row data
                    row_data = {"row_id": row.id}
                    for cell in row.cells:
                        column_title = reverse_column_map.get(cell.column_id, "Unknown")
                        row_data[column_title] = cell.value
                    
                    discounts.append(row_data)
                
                except Exception as e:
                    logger.warning(f"Error processing discount row: {e}")
                    continue
            
            return discounts
            
        except Exception as e:
            logger.error(f"Error getting all customer discounts: {e}")
            return []
