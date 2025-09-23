"""
CBS Configuration - Production Ready
All your actual API tokens and Sheet IDs configured for production deployment
"""

import os

# =============================================================================
# SMARTSHEET CONFIGURATION
# =============================================================================
# Your actual Smartsheet API token
SMARTSHEET_API_TOKEN = os.getenv('SMARTSHEET_API_TOKEN', "7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB")

# Your actual Sheet IDs
ORDERS_INTAKE_SHEET_ID = os.getenv('ORDERS_INTAKE_SHEET_ID', "p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1")
SALES_WORKS_ORDERS_SHEET_ID = os.getenv('SALES_WORKS_ORDERS_SHEET_ID', "G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391")

# CBS Parts System Sheet IDs
CBS_PARTS_SHEET_ID = os.getenv('CBS_PARTS_SHEET_ID', "4695255724019588")
CBS_DISCOUNTS_SHEET_ID = os.getenv('CBS_DISCOUNTS_SHEET_ID', "8920011042148228")

# =============================================================================
# BUSINESS SETTINGS
# =============================================================================
CBS_DIRECTOR_EMAIL = os.getenv('CBS_DIRECTOR_EMAIL', "bhabesh.kumar@sheaney.ie")

# =============================================================================
# AUTO-NUMBERING SETTINGS
# =============================================================================
QUOTE_REF_PREFIX = "Q"
QUOTE_REF_START_NUMBER = 1001
SO_NUMBER_PREFIX = "SO"
SO_NUMBER_START_NUMBER = 2001

# =============================================================================
# FILE PATHS
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FILE_PATH = "logs"
QR_CODE_STORAGE_PATH = "qr_codes"
TEMP_FILE_PATH = "temp_files"
PDF_TEMPLATE_PATH = "templates/pdfs"

# =============================================================================
# COMPANY INFORMATION
# =============================================================================
COMPANY_NAME = os.getenv('COMPANY_NAME', "Concrete Batching Systems")
COMPANY_ADDRESS = "123 Industrial Way, Business Park, City, Country"
COMPANY_PHONE = os.getenv('COMPANY_PHONE', "+1 234 567 8900")
COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', "info@cbs.com")
COMPANY_WEBSITE = os.getenv('COMPANY_WEBSITE', "www.cbs.com")

# =============================================================================
# PRODUCTION ENVIRONMENT SETTINGS
# =============================================================================
CBS_ENVIRONMENT = os.getenv('CBS_ENVIRONMENT', 'production')
CBS_DOMAIN = os.getenv('CBS_DOMAIN', 'localhost')
CBS_USE_SSL = os.getenv('CBS_USE_SSL', 'true').lower() == 'true'
CBS_BASE_URL = os.getenv('CBS_BASE_URL', f"{'https' if CBS_USE_SSL else 'http'}://{CBS_DOMAIN}")

# =============================================================================
# VALIDATION
# =============================================================================
def validate_configuration():
    """Validate that all required configuration is present"""
    required_vars = [
        ('SMARTSHEET_API_TOKEN', SMARTSHEET_API_TOKEN),
        ('ORDERS_INTAKE_SHEET_ID', ORDERS_INTAKE_SHEET_ID),
        ('SALES_WORKS_ORDERS_SHEET_ID', SALES_WORKS_ORDERS_SHEET_ID),
        ('CBS_PARTS_SHEET_ID', CBS_PARTS_SHEET_ID),
        ('CBS_DISCOUNTS_SHEET_ID', CBS_DISCOUNTS_SHEET_ID),
        ('CBS_DIRECTOR_EMAIL', CBS_DIRECTOR_EMAIL)
    ]
    
    missing_vars = []
    for var_name, var_value in required_vars:
        if not var_value or var_value == 'your_token_here':
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
    
    return True

# Validate on import
if __name__ != "__main__":
    try:
        validate_configuration()
        print("✅ CBS Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")

# =============================================================================
# SHEET ID REFERENCE (for your records)
# =============================================================================
"""
Your current Sheet IDs:
- Orders Intake: p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1
- Sales/Works Orders: G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391
- CBS Parts Database: 4695255724019588
- CBS Discounts: 8920011042148228

API Token: 7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB
CBS Director: bhabesh.kumar@sheaney.ie
"""