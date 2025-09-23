"""
CBS Parts Database Configuration
Configuration for the CBS parts integration system.
"""

# =============================================================================
# CBS PARTS SMARTSHEET CONFIGURATION
# =============================================================================

# This will be the new CBS Parts Database sheet ID
# Set this after creating the Smartsheet
CBS_PARTS_SHEET_ID = "4695255724019588"  # To be set after sheet creation
CBS_PARTS_SHEET_NAME = "CBS Parts Database"

# CBS Discounts sheet for customer-specific discounts
CBS_DISCOUNTS_SHEET_ID = "8920011042148228"  # To be set after sheet creation
CBS_DISCOUNTS_SHEET_NAME = "CBS Customer Discounts"

# =============================================================================
# PARTS DATABASE COLUMN MAPPING
# =============================================================================
PARTS_DATABASE_COLUMNS = {
    "product_code": "Product Code",
    "description": "Description", 
    "sales_price": "Sales Price",
    "quantity_in_stock": "Quantity In Stock",
    "free_stock": "Free Stock",
    "inactive": "Inactive",
    "category": "Category",
    "last_updated": "Last Updated",
    "created_date": "Created Date"
}

# =============================================================================
# DISCOUNTS DATABASE COLUMN MAPPING
# =============================================================================
DISCOUNTS_DATABASE_COLUMNS = {
    "customer_email": "Customer Email",
    "customer_domain": "Customer Domain", 
    "discount_percentage": "Discount Percentage",
    "global_discount": "Global Discount",
    "part_specific_discount": "Part Specific Discount",
    "product_code": "Product Code",
    "discount_type": "Discount Type",  # "Global" or "Part-Specific"
    "valid_from": "Valid From",
    "valid_until": "Valid Until",
    "active": "Active",
    "notes": "Notes",
    "created_date": "Created Date"
}

# =============================================================================
# BUSINESS RULES FOR PARTS
# =============================================================================
PARTS_BUSINESS_RULES = {
    "default_price_fallback": 0.00,  # Price when not found in database
    "stock_check_enabled": False,    # Whether to check stock levels
    "inactive_parts_visible": True,  # Whether to show inactive parts
    "price_decimal_places": 2,       # Number of decimal places for prices
    "search_minimum_chars": 2,       # Minimum characters for search
    "max_search_results": 50,        # Maximum search results to return
    "auto_suggest_enabled": True,    # Enable auto-suggestions
    "case_sensitive_search": False   # Whether search is case-sensitive
}

# =============================================================================
# DISCOUNT BUSINESS RULES
# =============================================================================
DISCOUNT_BUSINESS_RULES = {
    "default_discount": 0.0,           # Default discount percentage
    "max_discount_percentage": 50.0,   # Maximum allowed discount
    "global_discount_priority": True,  # Global discount overrides part-specific
    "domain_matching_enabled": True,   # Enable domain-based matching
    "discount_rounding": 2,            # Decimal places for discount calculations
    "discount_validation": True       # Validate discount ranges
}

# =============================================================================
# PARTS CATEGORIES (Optional - for organization)
# =============================================================================
PARTS_CATEGORIES = [
    "Mixers",
    "Conveyors", 
    "Platforms",
    "Rollers",
    "Weighbelt",
    "BOM",
    "Other"
]

# =============================================================================
# SMARTSHEET COLUMN TYPES
# =============================================================================
PARTS_COLUMN_TYPES = {
    "Product Code": "TEXT_NUMBER",
    "Description": "TEXT_NUMBER",
    "Sales Price": "TEXT_NUMBER", 
    "Quantity In Stock": "TEXT_NUMBER",
    "Free Stock": "TEXT_NUMBER",
    "Inactive": "CHECKBOX",
    "Category": "PICKLIST",
    "Last Updated": "DATE",
    "Created Date": "DATE"
}

DISCOUNTS_COLUMN_TYPES = {
    "Customer Email": "TEXT_NUMBER",
    "Customer Domain": "TEXT_NUMBER",
    "Discount Percentage": "TEXT_NUMBER",
    "Global Discount": "CHECKBOX",
    "Part Specific Discount": "CHECKBOX", 
    "Product Code": "TEXT_NUMBER",
    "Discount Type": "PICKLIST",
    "Valid From": "DATE",
    "Valid Until": "DATE",
    "Active": "CHECKBOX",
    "Notes": "TEXT_NUMBER",
    "Created Date": "DATE"
}

# =============================================================================
# DISCOUNT TYPES
# =============================================================================
DISCOUNT_TYPES = ["Global", "Part-Specific"]

# =============================================================================
# API ENDPOINTS FOR PARTS INTEGRATION
# =============================================================================
PARTS_API_ENDPOINTS = {
    "search_parts": "/api/parts/search",
    "get_part_details": "/api/parts/{product_code}",
    "get_customer_discount": "/api/discounts/customer/{email}",
    "calculate_quote_with_discounts": "/api/quotes/calculate"
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_parts_column_name(field_name: str) -> str:
    """Get the actual column name for parts database."""
    return PARTS_DATABASE_COLUMNS.get(field_name, field_name)

def get_discounts_column_name(field_name: str) -> str:
    """Get the actual column name for discounts database."""
    return DISCOUNTS_DATABASE_COLUMNS.get(field_name, field_name)

def get_parts_business_rule(rule_name: str):
    """Get business rule value for parts."""
    return PARTS_BUSINESS_RULES.get(rule_name)

def get_discount_business_rule(rule_name: str):
    """Get business rule value for discounts."""
    return DISCOUNT_BUSINESS_RULES.get(rule_name)

def is_valid_discount_type(discount_type: str) -> bool:
    """Check if discount type is valid."""
    return discount_type in DISCOUNT_TYPES

def is_valid_category(category: str) -> bool:
    """Check if parts category is valid."""
    return category in PARTS_CATEGORIES
