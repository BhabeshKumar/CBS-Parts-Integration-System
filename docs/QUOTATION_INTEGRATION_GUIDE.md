# 📄 CBS Quotation Generator Integration Guide

## 🎯 **Integration Overview**

Your CBS Parts system is now connected to quotation generation! Here's how it integrates with your existing quotation generator:

## 🔗 **New Features Added**

### ✅ **1. Review Link in Smartsheet**
- **What**: Review links are now automatically added to the "Quotation Link" column
- **Where**: Orders Intake sheet → Quotation Link column
- **Format**: `http://localhost:8000/templates/parts_review_interface.html?review_id=QUOTE_ID`

### ✅ **2. Quotation Generation API**
- **Endpoint**: `POST /api/generate-quotation/{quote_id}`
- **Purpose**: Auto-generate quotations from approved orders
- **Integration**: Connects to your existing quotation generator

### ✅ **3. Template Data API**
- **Endpoint**: `GET /api/quotation-template/{quote_id}`
- **Purpose**: Get structured data for your quotation generator
- **Format**: JSON with customer info, parts, pricing, etc.

## 🔄 **Complete Workflow**

### **Step 1: Customer Submits Order**
```
Customer Form → Parts Selection → Submit → Smartsheet Row Created
                                        ↓
                              Review Link Added to "Quotation Link" Column
```

### **Step 2: CBS Reviews & Prices**
```
CBS Opens Review Link → Sets Prices → Approves Order
                                   ↓
                        Auto-triggers Quotation Generation
```

### **Step 3: Quotation Generation**
```
Approved Order → API Call → Your Quotation Generator → PDF Created → Customer Notified
```

## 🔌 **Integration Options**

### **Option A: Auto-Generation (Current Implementation)**
- When CBS approves order → Automatically generates quotation
- Uses the quotation integration service
- Updates Smartsheet with quotation status

### **Option B: Manual Integration (Button Click)**
- CBS clicks "Open Quotation Generator" 
- Opens your existing quotation generator with pre-populated data
- CBS manually generates quotation in your system

### **Option C: Hybrid Approach**
- Use both options based on preference
- Auto-generation for simple orders
- Manual for complex orders requiring customization

## 📊 **Data Structure for Your Quotation Generator**

### **Customer Information**
```json
{
  "customerInfo": {
    "name": "Customer Name",
    "email": "customer@example.com",
    "mobile": "+353 123 456 789",
    "deliveryAddress": "Full delivery address",
    "requiredDate": "2025-01-15"
  }
}
```

### **Order Details**
```json
{
  "orderDetails": {
    "quoteId": "CBS-2025-001",
    "orderDate": "2025-01-08",
    "priority": "Medium",
    "additionalNotes": "Any special requirements"
  }
}
```

### **Parts/Items**
```json
{
  "items": [
    {
      "lineNumber": 1,
      "productCode": "MIXER-001",
      "description": "High Capacity Mixer Unit",
      "quantity": 2,
      "unitPrice": 1500.00,
      "lineTotal": 3000.00,
      "category": "Parts"
    }
  ]
}
```

### **Pricing Summary**
```json
{
  "pricing": {
    "subtotal": 3800.00,
    "discountAmount": 190.00,
    "discountedTotal": 3610.00,
    "vatRate": 0.23,
    "vatAmount": 830.30,
    "grandTotal": 4440.30,
    "currency": "EUR"
  }
}
```

## 🛠️ **Connecting Your Existing Quotation Generator**

### **Method 1: URL Parameters**
Update the quotation generator URL in the review interface:
```javascript
// In parts_review_interface.html, line ~743
const quotationUrl = `http://YOUR_QUOTATION_URL/generate?quote_id=${reviewId}`;
```

### **Method 2: API Integration**
Update the quotation service configuration:
```python
# In quotation_integration_service.py
self.quotation_generator_url = "http://YOUR_QUOTATION_GENERATOR_URL"
```

### **Method 3: Direct Database Integration**
If your quotation generator uses a database, the service can write directly:
```python
# Add database connection in quotation_integration_service.py
def save_to_quotation_database(self, quotation_data):
    # Your database integration code here
```

## 📱 **API Endpoints for Integration**

| Endpoint | Method | Purpose | Use Case |
|----------|--------|---------|----------|
| `/api/submit-order` | POST | Submit new order | Customer form |
| `/api/order/{quote_id}` | GET | Get order details | Load in review |
| `/api/order/{quote_id}` | PUT | Update pricing | Save pricing |
| `/api/generate-quotation/{quote_id}` | POST | Generate quotation | Auto-generation |
| `/api/quotation-template/{quote_id}` | GET | Get template data | Manual integration |

## 🔧 **Configuration**

### **Quotation Generator URL**
```python
# In src/services/quotation_integration_service.py
class QuotationIntegrationService:
    def __init__(self):
        # Update these URLs to match your quotation generator
        self.quotation_api_base = "http://localhost:3000"  # Your API
        self.quotation_generator_url = "http://localhost:8080"  # Your UI
```

### **Smartsheet Column Mapping**
```python
# Review links are automatically added to "Quotation Link" column
# Make sure this column exists in your Orders Intake sheet
```

## 🧪 **Testing the Integration**

### **Test Auto-Generation**
1. Submit an order via the customer form
2. Open the review link from Smartsheet
3. Set prices and click "Approve & Generate Quote"
4. Check if quotation is generated automatically

### **Test Manual Integration**
1. Open any review link
2. Click "Open Quotation Generator"
3. Verify it opens your quotation generator
4. Check if data is pre-populated

### **Test API Endpoints**
```bash
# Test quotation template data
curl "http://localhost:8003/api/quotation-template/CBS-2025-001"

# Test quotation generation
curl -X POST "http://localhost:8003/api/generate-quotation/CBS-2025-001"
```

## 🔄 **Customizing for Your Quotation Generator**

### **If your generator uses different data format:**
1. Edit `prepare_quotation_data()` in `quotation_integration_service.py`
2. Map the fields to match your requirements
3. Adjust the JSON structure

### **If your generator has different endpoints:**
1. Update URLs in the configuration section
2. Modify the API calls in `generate_quotation_pdf()`
3. Adjust error handling as needed

### **If your generator is file-based:**
1. Modify the service to write files instead of API calls
2. Update file paths and formats
3. Implement file watching for completion

## 📈 **Next Steps**

1. **Test with your quotation generator**
2. **Customize data format if needed**
3. **Set up proper URLs and endpoints**
4. **Add email notifications** (when quotations are sent)
5. **Implement status tracking** (quotation sent, accepted, etc.)

## 🎉 **What's Working Now**

✅ **Review links automatically added to Smartsheet**
✅ **Quotation generation API ready**
✅ **Template data API for integration**
✅ **Auto-generation on approval**
✅ **Manual quotation generator opening**
✅ **Structured data format for easy integration**

**Ready to connect with your existing quotation generator!** 🚀
