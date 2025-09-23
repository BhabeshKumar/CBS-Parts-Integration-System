# 🏭 CBS Parts System - Production Ready

**Complete End-to-End Parts Management & Quotation System**

## 🎯 **System Overview**

This is the production-ready CBS Parts automation system that provides:

- **Customer Order Forms** - Web-based forms for part selection
- **Parts Database Management** - 3,683+ CBS parts with search functionality  
- **Pricing & Discount Management** - CBS team pricing controls
- **Quotation Generation** - Automated PDF quotation creation
- **Smartsheet Integration** - Complete workflow management

## 📁 **Folder Structure**

```
CBS_Parts_System_Production/
├── config/                          # Configuration files
│   ├── my_config.py                 # Smartsheet API tokens & sheet IDs
│   ├── smartsheet_mapping.py        # Column mappings
│   └── cbs_parts_config.py         # Parts database configuration
├── src/
│   ├── api/                         # API endpoints
│   │   ├── cbs_parts_api.py         # Parts search API
│   │   └── smartsheet_form_api.py   # Form submission API
│   └── services/                    # Business logic services
│       ├── smartsheet_service.py    # Core Smartsheet operations
│       ├── cbs_parts_service.py     # Parts database management
│       ├── cbs_discounts_service.py # Discount management
│       └── quotation_integration_service.py # Quotation generation
├── templates/                       # Web interfaces
│   ├── enhanced_order_form.html     # Customer order form
│   ├── parts_review_interface.html  # CBS review & pricing
│   └── parts_selection_interface.html # Parts search interface
├── scripts/                         # Startup & utility scripts
│   ├── setup_cbs_parts_system.py    # System initialization
│   ├── start_cbs_parts_api.py       # Start parts API
│   ├── start_review_server.py       # Start web server
│   └── start_all_services.py        # Start all services
├── cbs_pdf_generator/               # Quotation PDF generator (React app)
├── docs/                           # Documentation
├── CBS Parts from Sage.xlsx        # Parts database
└── requirements.txt                 # Python dependencies
```

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Configure System**
Edit `config/my_config.py`:
```python
SMARTSHEET_API_TOKEN = "your_token_here"
ORDERS_INTAKE_SHEET_ID = "your_sheet_id"
```

### **3. Initialize System**
```bash
python scripts/setup_cbs_parts_system.py
```

### **4. Start All Services**
```bash
python scripts/start_all_services.py
```

### **5. Start Quotation Generator**
```bash
cd cbs_pdf_generator
npm install
npm run dev
```

## 🌐 **System URLs**

| Service | URL | Purpose |
|---------|-----|---------|
| **Customer Order Form** | `http://localhost:8000/templates/enhanced_order_form.html` | Customer interface |
| **CBS Review Interface** | `http://localhost:8000/templates/parts_review_interface.html?review_id=QUOTE_ID` | CBS pricing & approval |
| **Parts Search API** | `http://localhost:8002/api/parts/search?q=SEARCH_TERM` | Parts database API |
| **Quotation Generator** | `http://localhost:5173` | PDF generation |

## 🔄 **Complete Workflow**

### **For Customers:**
1. Open customer order form
2. Fill contact details & delivery address
3. Search and select parts
4. Submit order request

### **For CBS Team:**
1. Receive notification with review link
2. Open review interface from Smartsheet
3. Set prices for all selected parts
4. Apply discounts if needed
5. Approve & generate quotation
6. PDF quotation opens automatically

## ⚙️ **Configuration**

### **Smartsheet Setup**
- Orders Intake Sheet: Customer orders & review links
- CBS Parts Database: 3,683+ parts with codes & descriptions
- CBS Customer Discounts: Customer-specific discount rules

### **API Endpoints**
- **Port 8000**: Web server for forms & interfaces
- **Port 8002**: Parts search & database API  
- **Port 8003**: Form submission & Smartsheet integration
- **Port 5173**: Quotation generator (React/Vite)

## 📊 **Key Features**

### **Parts Management**
- ✅ Search 3,683+ CBS parts by code or description
- ✅ Real-time parts selection with quantities
- ✅ Parts categorization and filtering
- ✅ Inactive parts visibility control

### **Pricing & Discounts**
- ✅ Individual part pricing by CBS team
- ✅ Percentage or fixed amount discounts
- ✅ Customer-specific discount rules
- ✅ Real-time total calculations with VAT

### **Quotation Generation**
- ✅ Automated PDF generation with current prices
- ✅ Customer details auto-population
- ✅ Professional quotation formatting
- ✅ Discount display as negative line item

### **Smartsheet Integration**
- ✅ Automatic row creation in Orders Intake
- ✅ Review links in Quotation Link column
- ✅ Status tracking & workflow management
- ✅ Quote ID auto-generation

## 🔧 **Customization**

### **Adding New Parts**
Update `CBS Parts from Sage.xlsx` and run:
```bash
python scripts/setup_cbs_parts_system.py
```

### **Modifying Quotation Format**
Edit files in `cbs_pdf_generator/src/components/quotation/`

### **Changing Smartsheet Columns**
Update `config/smartsheet_mapping.py`

## 🔗 **System Integration**

### **With Existing Systems**
- Smartsheet integration for order management
- Excel database import for parts data
- Email notifications (can be added)
- ERP integration endpoints available

### **API Documentation**
- Parts Search API: `/api/parts/search`
- Order Submission: `/api/submit-order`
- Quotation Generation: `/api/generate-quotation/{quote_id}`
- Full API docs: `http://localhost:8002/docs`

## 🛡️ **Production Considerations**

### **Security**
- Store API tokens in environment variables
- Use HTTPS in production
- Implement rate limiting for APIs
- Add authentication for CBS interfaces

### **Deployment**
- Use process manager (PM2, systemd) for APIs
- Set up reverse proxy (Nginx) for web interfaces
- Configure SSL certificates
- Set up monitoring & logging

### **Backup**
- Regular Smartsheet data backup
- Parts database version control
- Configuration file backup

## 📞 **Support**

For system support or modifications, contact the development team with:
- System logs from `/logs/` directory
- Configuration details from `/config/`
- Error messages and screenshots

---

**🎉 This is a complete, production-ready system for CBS parts management and quotation generation!**
