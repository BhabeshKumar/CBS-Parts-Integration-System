# 🔗 CBS Connected Parts System - Complete Integration Guide

## 🎯 **System Overview**

Your CBS Parts system is now fully connected end-to-end! Here's how all the components work together:

## 🔄 **Complete Connected Workflow**

### 1. **Customer Submits Order**
- **Form**: `http://localhost:8000/templates/enhanced_order_form.html`
- Customer fills details and selects parts
- Form submits to API (port 8003)
- **Result**: Row created in Smartsheet Orders Intake + Review link generated

### 2. **CBS Reviews & Prices Order**
- **Review Interface**: `http://localhost:8000/templates/parts_review_interface.html?review_id=QUOTE_ID`
- Loads real customer data from Smartsheet
- CBS sets prices for each part
- Updates back to Smartsheet
- **Result**: Approved order ready for quotation

### 3. **Quotation Generation**
- Ready to integrate with your existing quotation generator
- All data available in structured format

## 🌐 **Running Services**

| Service | Port | Purpose | URL |
|---------|------|---------|-----|
| **Parts API** | 8002 | Search 3,683 parts | `http://localhost:8002` |
| **Form API** | 8003 | Submit/retrieve orders | `http://localhost:8003` |
| **Web Server** | 8000 | Serve interfaces | `http://localhost:8000` |

## 📋 **Customer Interface**

### **Enhanced Order Form**
**URL**: `http://localhost:8000/templates/enhanced_order_form.html`

**Features**:
- ✅ Customer information collection
- ✅ Real-time parts search (3,683 parts)
- ✅ Multi-part selection with quantities
- ✅ Direct Smartsheet integration
- ✅ Auto-generated Quote ID & Review Link

**Workflow**:
1. Customer fills name, email, delivery address
2. Searches and selects parts
3. Submits form
4. Gets success message with CBS review link
5. Order added to Smartsheet Orders Intake

## 🔍 **CBS Management Interface**

### **Parts Review & Pricing**
**URL**: `http://localhost:8000/templates/parts_review_interface.html?review_id=QUOTE_ID`

**Features**:
- ✅ Loads real order data from Smartsheet
- ✅ Customer information display
- ✅ Individual part pricing
- ✅ Quantity editing
- ✅ Discount system (% or fixed)
- ✅ VAT calculation (23%)
- ✅ Real-time totals
- ✅ Save/Update/Approve workflow

**Workflow**:
1. CBS opens review link from order
2. System loads customer details & selected parts
3. CBS sets price for each part
4. Reviews totals with discounts & VAT
5. Approves order for quotation generation

## 🔌 **API Endpoints**

### **Form Submission API** (Port 8003)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/submit-order` | POST | Submit new order |
| `/api/order/{quote_id}` | GET | Get order details |
| `/api/order/{quote_id}` | PUT | Update order pricing |
| `/api/health` | GET | Health check |

### **Parts Search API** (Port 8002)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/parts/search` | GET | Search parts |
| `/api/parts/{code}` | GET | Get specific part |
| `/api/discounts/customer/{email}` | GET | Get customer discount |
| `/api/health` | GET | Health check |

## 📊 **Data Flow**

```
Customer Form → Parts API (search) → Form Submission → Smartsheet Orders Intake
                     ↓
CBS Review Link ← Quote ID ← API Response ← Row Created
                     ↓
Review Interface → Load Order API → Display Real Data → Update Pricing → Save to Smartsheet
```

## 🚀 **Starting the Complete System**

### **Option 1: Start All Services at Once**
```bash
python3 scripts/start_all_services.py
```

### **Option 2: Start Services Individually**
```bash
# Parts API (8002)
python3 scripts/start_cbs_parts_api.py &

# Form API (8003)  
python3 src/api/smartsheet_form_api.py &

# Web Server (8000)
python3 scripts/start_review_server.py &
```

## 🧪 **Testing the Connected System**

### **Step 1: Submit Test Order**
1. Open: `http://localhost:8000/templates/enhanced_order_form.html`
2. Fill customer details
3. Search for parts (try "mixer", "pump", etc.)
4. Select 2-3 parts with quantities
5. Submit form
6. **Copy the review link from success message**

### **Step 2: Review Order as CBS**
1. Open the review link from Step 1
2. Verify customer details loaded correctly
3. Verify selected parts displayed
4. Set prices for each part
5. Review calculated totals
6. Test Save/Update/Approve functions

### **Step 3: Verify Smartsheet Integration**
1. Check Orders Intake sheet for new row
2. Verify all customer data populated
3. Verify selected parts in Additional Notes
4. Check Quote ID auto-generation

## 🔗 **Integration Points**

### **With Existing Quotation Generator**
- Order data available via API: `GET /api/order/{quote_id}`
- Structured parts data with pricing
- Customer information ready
- Can trigger from "Approve & Generate" button

### **With Smartsheet**
- Direct read/write to Orders Intake sheet
- Parts stored in Additional Notes (parsed format)
- Status updates reflected in Smartsheet
- Quote ID auto-generated

## 🛠️ **Configuration Files**

| File | Purpose |
|------|---------|
| `config/my_config.py` | Smartsheet tokens & sheet IDs |
| `config/smartsheet_mapping.py` | Column mappings |
| `config/cbs_parts_config.py` | Parts database settings |

## 📈 **Next Steps**

1. **Connect to Quotation Generator**: Add API call in approve function
2. **Email Notifications**: Send emails when orders submitted/approved
3. **Advanced Discounts**: Customer-specific discount rules
4. **Inventory Integration**: Real-time stock levels
5. **Reporting Dashboard**: Order analytics and reporting

## 🎉 **What's Working Now**

✅ **Complete end-to-end workflow**
✅ **Real-time parts search (3,683 parts)**
✅ **Form submission to Smartsheet**
✅ **CBS review interface with real data**
✅ **Pricing and approval workflow**
✅ **Auto-generated Quote IDs**
✅ **VAT and discount calculations**
✅ **All services connected via APIs**

**The system is fully functional and connected!** 🚀
