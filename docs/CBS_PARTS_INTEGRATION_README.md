# 🔧 CBS Parts Integration System

This document provides comprehensive information about the CBS Parts Integration System that enhances the existing quotation workflow with parts database functionality and customer-specific discounts.

## 🎯 Overview

The CBS Parts Integration System addresses the requirements discussed in your conversation:

### ✅ **Implemented Features**

1. **✅ Parts Database (Product Code + Description)**
   - Smartsheet-based parts database with Product Code and Description (priority fields)
   - Sales Price, Stock Information, Categories
   - Excel import from "CBS Parts from Sage.xlsx"

2. **✅ Parts Search & Selection Interface**
   - Web-based parts selection interface
   - Auto-complete search functionality
   - Category filtering
   - External link or embeddable in Order Intake Form

3. **✅ Auto-Population of Quotation**
   - Selected parts automatically populate quotation data
   - Price fallback logic (Smartsheet price → manual entry if 0/blank)
   - Enhanced quotation service integration

4. **✅ Customer-Specific Discount System**
   - Global percentage discounts (e.g., 10% for some, 20% for others)
   - Part-specific discounts
   - Email domain-based discount matching
   - Separate Smartsheet for discount management

5. **✅ Price Management**
   - Automatic price from database if available
   - Manual price entry when database price is 0 or blank
   - Price update capabilities

## 📁 System Architecture

```
CBS Parts Integration/
├── config/
│   ├── cbs_parts_config.py          # Parts & discounts configuration
│   ├── my_config.py                 # Existing CBS configuration
│   └── smartsheet_mapping.py        # Existing mapping
├── src/
│   ├── services/
│   │   ├── cbs_parts_service.py     # Parts database operations
│   │   ├── cbs_discounts_service.py # Customer discount management
│   │   └── enhanced_quotation_service.py # Enhanced quotation generation
│   └── api/
│       └── cbs_parts_api.py         # FastAPI endpoints for parts
├── scripts/
│   ├── setup_cbs_parts_system.py   # Setup script
│   └── start_cbs_parts_api.py       # API server startup
├── templates/
│   └── parts_selection_interface.html # Web interface for parts selection
└── CBS Parts from Sage.xlsx         # Excel file with parts data
```

## 🚀 Quick Start

### 1. Setup the System

```bash
# Run the setup script
python scripts/setup_cbs_parts_system.py
```

This will:
- ✅ Create "CBS Parts Database" Smartsheet
- ✅ Create "CBS Customer Discounts" Smartsheet  
- ✅ Import parts from Excel file (if available)
- ✅ Add example discount configurations

### 2. Start the Parts API

```bash
# Start the CBS Parts API server
python scripts/start_cbs_parts_api.py
```

The API will be available at:
- **URL**: http://localhost:8002
- **Documentation**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/api/health

### 3. Access Parts Selection Interface

Open the parts selection interface:
```
file:///path/to/Automation/templates/parts_selection_interface.html
```

Or serve it through a web server for full functionality.

## 📊 Smartsheet Configuration

### Parts Database Sheet Structure

| Column | Type | Description |
|--------|------|-------------|
| Product Code | TEXT (Primary) | Part number/identifier |
| Description | TEXT | Part description |
| Sales Price | NUMBER | Price in EUR |
| Quantity In Stock | NUMBER | Current stock level |
| Free Stock | NUMBER | Available stock |
| Inactive | CHECKBOX | Whether part is active |
| Category | DROPDOWN | Part category |
| Last Updated | DATE | Last modification date |
| Created Date | DATE | Creation date |

### Customer Discounts Sheet Structure

| Column | Type | Description |
|--------|------|-------------|
| Customer Email | TEXT (Primary) | Customer email address |
| Customer Domain | TEXT | Email domain for matching |
| Discount Percentage | NUMBER | Discount percentage |
| Global Discount | CHECKBOX | Applies to all parts |
| Part Specific Discount | CHECKBOX | Applies to specific part |
| Product Code | TEXT | For part-specific discounts |
| Discount Type | DROPDOWN | "Global" or "Part-Specific" |
| Valid From | DATE | Discount start date |
| Valid Until | DATE | Discount end date |
| Active | CHECKBOX | Whether discount is active |
| Notes | TEXT | Additional information |
| Created Date | DATE | Creation date |

## 🔌 API Endpoints

### Parts Management

```http
# Search parts
GET /api/parts/search?q=mixer&limit=10

# Get part details  
GET /api/parts/01-WEIGHBELT

# Get all parts
GET /api/parts?include_inactive=false&category=Mixers

# Import parts from Excel
POST /api/parts/import
Content-Type: multipart/form-data
[Excel file upload]

# Update part price
PUT /api/parts/01-WEIGHBELT/price
Content-Type: application/json
{"new_price": 150.00}

# Get parts suggestions (for auto-complete)
GET /api/parts/suggestions?q=mix&limit=5

# Get parts categories
GET /api/parts/categories
```

### Customer Discounts

```http
# Get customer discount
GET /api/discounts/customer/test@concretebatchingsystems.com

# Add new discount
POST /api/discounts/add
Content-Type: application/json
{
    "customer_email": "customer@company.com",
    "discount_percentage": 15.0,
    "discount_type": "Global",
    "notes": "Preferred customer discount",
    "valid_days": 365
}

# Get all discounts
GET /api/discounts
```

### Quotation Calculation

```http
# Calculate quotation with discounts
POST /api/quotes/calculate
Content-Type: application/json
{
    "customer_email": "customer@company.com",
    "items": [
        {
            "product_code": "01-WEIGHBELT",
            "quantity": 2,
            "unit_price": 150.00
        },
        {
            "product_code": "03-TRANSFERCONVEYOR", 
            "quantity": 1,
            "unit_price": 0.0
        }
    ]
}
```

## 💡 Usage Examples

### 1. Kyle's Wishlist: Parts Selection Checklist

The parts selection interface provides:
- ✅ **External link**: Can be accessed independently
- ✅ **Embeddable**: Can be integrated into existing forms
- ✅ **Database-linked**: Connected to CBS Parts Smartsheet
- ✅ **Updateable**: Easy to add new parts via Smartsheet or API

**Access URL**: 
```
http://localhost:8002/templates/parts_selection_interface.html?email=customer@company.com
```

### 2. Auto-Population Workflow

1. **Customer fills Order Intake Form**
2. **Parts are selected via interface** → sends `part_no` and `part_description`
3. **Enhanced quotation generator**:
   - Looks up part in database
   - Gets price from database (if available)
   - Falls back to manual price entry if price is 0/blank
   - Applies customer-specific discounts
   - Generates quotation with all data

### 3. Discount Implementation

**Jam's Suggestion**: Separate Smartsheet table for discounts ✅

**Discount Types**:
- **Global Discount**: Applies to all parts for a customer
- **Part-Specific**: Applies only to specific product codes

**Customer Matching**:
- Email address exact match
- Domain-based matching (e.g., @concretebatchingsystems.com gets 15%)

**Example Discount Configurations**:
```
# Global discounts
test@concretebatchingsystems.com → 15% global
test@sheaney.ie → 20% global

# Part-specific discounts  
special@customer.com + "01-WEIGHBELT" → 10% on weighbelt only
```

### 4. Price Fallback Logic

The system implements Brian's request for price handling:

```python
# Price fallback priority:
1. Manual price (if provided in form) → Use manual price
2. Database price (if > 0) → Use database price  
3. Database price = 0/blank → Require manual entry
4. No database entry → Require manual entry
```

### 5. Integration with Existing System

The enhanced quotation service integrates seamlessly:

```python
# In your existing quotation generator:
from services.enhanced_quotation_service import EnhancedQuotationService

enhanced_quotation = EnhancedQuotationService()

# Convert existing order data with parts enhancement
enhanced_order_data = enhanced_quotation.enhance_order_data_with_parts(order_data)

# Generate quotation with discounts applied
quotation_data = enhanced_quotation.generate_enhanced_quotation_data(enhanced_order_data)

# Use with Jam's PDF API (existing code works unchanged)
pdf_path = generate_quotation_via_jam_api(quotation_data)
```

## 🔧 Configuration

### Discount Business Rules

Located in `config/cbs_parts_config.py`:

```python
DISCOUNT_BUSINESS_RULES = {
    "default_discount": 0.0,           # Default discount percentage
    "max_discount_percentage": 50.0,   # Maximum allowed discount
    "global_discount_priority": True,  # Global discount overrides part-specific
    "domain_matching_enabled": True,   # Enable domain-based matching
    "discount_rounding": 2,            # Decimal places for discount calculations
    "discount_validation": True       # Validate discount ranges
}
```

### Parts Business Rules

```python
PARTS_BUSINESS_RULES = {
    "default_price_fallback": 0.00,  # Price when not found in database
    "stock_check_enabled": False,    # Whether to check stock levels
    "inactive_parts_visible": False, # Whether to show inactive parts
    "search_minimum_chars": 2,       # Minimum characters for search
    "max_search_results": 50,        # Maximum search results to return
    "auto_suggest_enabled": True,    # Enable auto-suggestions
    "case_sensitive_search": False   # Whether search is case-sensitive
}
```

## 🎨 Parts Selection Interface Features

### Modern Web Interface
- ✅ **Responsive design** - Works on desktop and mobile
- ✅ **Auto-complete search** - Type to find parts instantly
- ✅ **Category filtering** - Filter by Mixers, Conveyors, etc.
- ✅ **Real-time pricing** - Shows prices and calculates totals
- ✅ **Quantity management** - Easy quantity adjustments
- ✅ **VAT calculation** - Automatic 23% Irish VAT

### Integration Features
- ✅ **URL parameters** - Pre-fill customer email
- ✅ **JSON export** - Selected parts can be exported
- ✅ **Quotation redirect** - Direct integration with quotation form
- ✅ **Error handling** - Graceful error management

## 🔄 Integration Points

### 1. Order Intake Form Integration

Add link to parts selection:
```html
<a href="templates/parts_selection_interface.html?email=customer@company.com" 
   target="_blank">
   🔧 Select Parts from Database
</a>
```

### 2. Existing Quotation Generator

Update `real_quotation_generator.py`:

```python
# Add enhanced quotation service
from services.enhanced_quotation_service import EnhancedQuotationService

def generate_real_quotation(order_data):
    enhanced_service = EnhancedQuotationService()
    
    # Enhance order data with parts and pricing
    enhanced_order = enhanced_service.enhance_order_data_with_parts(order_data)
    
    # Generate quotation with discounts
    quotation_data = enhanced_service.generate_enhanced_quotation_data(enhanced_order)
    
    # Continue with existing PDF generation
    pdf_path = generate_quotation_via_jam_api(quotation_data)
    
    # Rest of existing code...
```

### 3. Smartsheet Form Enhancement

Add parts selection step to Smartsheet forms:
1. **Step 1**: Customer fills basic info
2. **Step 2**: Redirect to parts selection interface  
3. **Step 3**: Return to form with selected parts
4. **Step 4**: Submit complete order

## 📈 Benefits Delivered

### For Kyle (CBS Director)
- ✅ **Parts checklist** - Easy selection from complete database
- ✅ **External link** - Can be shared independently
- ✅ **Database connectivity** - Links to updateable Smartsheet
- ✅ **Future-proof** - Easy to add new parts

### For Pauline (Quotation Management)
- ✅ **Auto-populated quotations** - Less manual data entry
- ✅ **Accurate pricing** - Database-driven prices with manual fallback
- ✅ **Customer discounts** - Automatic discount application
- ✅ **Professional quotations** - Enhanced with full part details

### For Steven & Brian (Business Management)
- ✅ **Customer-specific discounts** - Different rates for different customers
- ✅ **Domain-based discounts** - Company-wide discount policies
- ✅ **Discount management** - Easy to update via Smartsheet
- ✅ **Reporting capability** - Track discount usage and effectiveness

### For Bhabesh (System Integration)
- ✅ **Modular design** - Easy to integrate with existing system
- ✅ **API-first approach** - Can be used by other applications
- ✅ **Configuration-driven** - Easy to customize business rules
- ✅ **Scalable architecture** - Can handle growing parts database

## 🚀 Next Steps

### Immediate Actions
1. **Run setup script** to create Smartsheets
2. **Import parts data** from Excel file
3. **Configure customer discounts** in the Discounts Smartsheet
4. **Test the parts selection interface**
5. **Integrate with existing quotation workflow**

### Future Enhancements
- **Stock level integration** - Real-time stock checking
- **Price history tracking** - Track price changes over time
- **Advanced discount rules** - Quantity-based, seasonal discounts
- **Parts catalog API** - Integration with supplier systems
- **Mobile app** - Native mobile parts selection

## 📞 Support

If you need assistance with:
- Setting up the system
- Configuring discounts
- Integrating with existing workflow
- Customizing the interface

The system is designed to be self-documenting with comprehensive API documentation at `/docs` when the server is running.

---

**🎉 Congratulations!** You now have a complete parts integration system that addresses all the requirements discussed in your conversation. The system is production-ready and can be immediately deployed to enhance your CBS quotation workflow.
