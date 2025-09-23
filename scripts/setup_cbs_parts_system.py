#!/usr/bin/env python3
"""
Setup script for CBS Parts Integration System
This script initializes the CBS parts database and discount system.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "config"))

from services.cbs_parts_service import CBSPartsService
from services.cbs_discounts_service import CBSDiscountsService
from services.enhanced_quotation_service import EnhancedQuotationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_parts_system():
    """Initialize the CBS parts integration system."""
    print("=" * 70)
    print("🚀 CBS PARTS INTEGRATION SYSTEM SETUP")
    print("=" * 70)
    
    try:
        # Initialize services
        print("\n📋 Initializing services...")
        parts_service = CBSPartsService()
        discounts_service = CBSDiscountsService()
        enhanced_quotation_service = EnhancedQuotationService()
        
        # Create or verify parts database sheet
        print("\n🗃️  Setting up Parts Database...")
        parts_sheet_id = parts_service.get_or_create_parts_sheet()
        if parts_sheet_id:
            print(f"✅ Parts Database sheet ready (ID: {parts_sheet_id})")
        else:
            print("❌ Failed to create Parts Database sheet")
            return False
        
        # Create or verify discounts sheet
        print("\n💰 Setting up Customer Discounts...")
        discounts_sheet_id = discounts_service.get_or_create_discounts_sheet()
        if discounts_sheet_id:
            print(f"✅ Customer Discounts sheet ready (ID: {discounts_sheet_id})")
        else:
            print("❌ Failed to create Customer Discounts sheet")
            return False
        
        # Import parts data from Excel if file exists
        excel_file_path = project_root / "CBS Parts from Sage.xlsx"
        if excel_file_path.exists():
            print(f"\n📊 Importing parts data from {excel_file_path}...")
            success = parts_service.import_parts_from_excel(str(excel_file_path))
            if success:
                print("✅ Parts data imported successfully")
                
                # Get import summary
                all_parts = parts_service.get_all_parts(include_inactive=True)
                print(f"   • Total parts imported: {len(all_parts)}")
                
                categories = {}
                for part in all_parts:
                    category = part.get('category', 'Other')
                    categories[category] = categories.get(category, 0) + 1
                
                print("   • Parts by category:")
                for category, count in categories.items():
                    print(f"     - {category}: {count}")
            else:
                print("⚠️  Failed to import parts data (continuing anyway)")
        else:
            print(f"\n⚠️  Parts Excel file not found at {excel_file_path}")
            print("   You can import parts later using the API endpoint")
        
        # Test the system
        print("\n🧪 Testing system functionality...")
        
        # Test parts search
        test_results = parts_service.search_parts("MIXER", limit=3)
        if test_results:
            print(f"✅ Parts search working - found {len(test_results)} results for 'MIXER'")
        else:
            print("⚠️  Parts search returned no results (database may be empty)")
        
        # Test discount system
        test_discount = discounts_service.get_customer_discount("test@example.com")
        if test_discount:
            print("✅ Discount system working")
        else:
            print("❌ Discount system failed")
            return False
        
        print("\n" + "=" * 70)
        print("🎉 CBS PARTS INTEGRATION SYSTEM SETUP COMPLETE!")
        print("=" * 70)
        
        print("\n📋 SYSTEM SUMMARY:")
        print(f"   • Parts Database Sheet ID: {parts_sheet_id}")
        print(f"   • Discounts Sheet ID: {discounts_sheet_id}")
        print(f"   • Parts API will run on: http://localhost:8002")
        print(f"   • API Documentation: http://localhost:8002/docs")
        
        print("\n🔧 NEXT STEPS:")
        print("   1. Start the CBS Parts API:")
        print("      python src/api/cbs_parts_api.py")
        print("   2. Test the API endpoints:")
        print("      curl http://localhost:8002/api/health")
        print("   3. Search for parts:")
        print("      curl http://localhost:8002/api/parts/search?q=mixer")
        print("   4. Add customer discounts via the API or Smartsheet")
        
        print("\n📚 USAGE EXAMPLES:")
        print("   • Search parts: GET /api/parts/search?q=mixer")
        print("   • Get part details: GET /api/parts/{product_code}")
        print("   • Get customer discount: GET /api/discounts/customer/{email}")
        print("   • Calculate quotation: POST /api/quotes/calculate")
        
        return True
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        return False

def main():
    """Main setup function."""
    success = setup_parts_system()
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
