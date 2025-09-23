# 🌐 CBS Parts System - Production URL Configuration

## 🎯 **Automatic URL Conversion**

Your CBS Parts System automatically converts all `localhost` URLs to production URLs when deployed. Here's how it works:

## 📝 **URL Conversion Examples**

### **Before (Development/Localhost)**
```
Customer Order Form:
http://localhost:8000/templates/enhanced_order_form.html

CBS Review Interface:
http://localhost:8000/templates/parts_review_interface.html

Quotation Generator:
http://localhost:5173/?data=...

API Endpoints:
http://localhost:8002/api/search
http://localhost:8003/api/submit-order
```

### **After (Production Domain)**
```
Customer Order Form:
https://cbsparts.yourcompany.com/templates/enhanced_order_form.html

CBS Review Interface:
https://cbsparts.yourcompany.com/templates/parts_review_interface.html

Quotation Generator:
https://cbsparts.yourcompany.com/quotation/?data=...

API Endpoints:
https://cbsparts.yourcompany.com/api/parts/search
https://cbsparts.yourcompany.com/api/submit-order
```

## 🔧 **How to Configure for Your Domain**

### **Option 1: Automatic During Deployment**
```bash
# Deploy with your domain - URLs automatically configured
./deployment/deploy_production.sh cbsparts.yourcompany.com
```

### **Option 2: Manual Configuration**
```bash
# Configure URLs for your domain
python3 scripts/configure_production_urls.py cbsparts.yourcompany.com --ssl

# Results:
# ✅ All HTML templates updated
# ✅ All Python files updated  
# ✅ Nginx configuration created
# ✅ Docker environment configured
```

## 🌍 **Real-World Example**

Let's say your domain is **`cbsparts.acmecorp.com`**:

### **Customer Workflow**
1. **Customer visits**: `https://cbsparts.acmecorp.com/templates/enhanced_order_form.html`
2. **Selects parts**: API calls to `https://cbsparts.acmecorp.com/api/parts/search`
3. **Submits order**: Posts to `https://cbsparts.acmecorp.com/api/submit-order`

### **CBS Internal Workflow**
1. **CBS reviews**: `https://cbsparts.acmecorp.com/templates/parts_review_interface.html?quote_id=Q-25023`
2. **Sets prices**: Updates via `https://cbsparts.acmecorp.com/api/order/Q-25023`
3. **Generates quote**: Opens `https://cbsparts.acmecorp.com/quotation/?data=...`

## 🔗 **Nginx Proxy Configuration**

The system uses Nginx to route URLs properly:

```nginx
# Your domain routes to internal services
https://cbsparts.acmecorp.com/api/parts/* → localhost:8002/api/*
https://cbsparts.acmecorp.com/api/*       → localhost:8003/api/*
https://cbsparts.acmecorp.com/quotation/* → localhost:5173/*
https://cbsparts.acmecorp.com/*           → localhost:8000/*
```

## 📱 **Mobile & External Access**

✅ **Works from anywhere**:
- Office computers
- Mobile devices  
- Customer locations
- Remote CBS staff

✅ **Professional URLs**:
- Easy to remember
- Brandable domains
- SSL certificates
- Professional appearance

## 🚀 **Deployment Steps**

### **1. Choose Your Domain**
```bash
# Examples:
cbsparts.yourcompany.com
orders.cbscompany.co.uk  
parts.concretebatching.com
```

### **2. Configure DNS**
Point your domain to your server's IP address:
```
A Record: cbsparts.yourcompany.com → 123.456.789.101
```

### **3. Deploy with Domain**
```bash
sudo ./deployment/deploy_production.sh cbsparts.yourcompany.com
```

### **4. Automatic Configuration**
The deployment script automatically:
- ✅ Updates all localhost URLs to your domain
- ✅ Configures SSL certificates  
- ✅ Sets up Nginx proxy
- ✅ Configures all services
- ✅ Enables 24/7 monitoring

### **5. Test Your URLs**
```bash
# Test customer form
curl https://cbsparts.yourcompany.com/templates/enhanced_order_form.html

# Test API health
curl https://cbsparts.yourcompany.com/api/parts/health

# Test parts search
curl "https://cbsparts.yourcompany.com/api/parts/search?q=mixer"
```

## 🎉 **Benefits of Production URLs**

### **✅ Professional Appearance**
- Branded domain names
- HTTPS security
- Professional customer experience

### **✅ Global Access**
- Access from anywhere in the world
- Mobile-friendly URLs
- No VPN requirements

### **✅ Easy Integration**
- Share links via email
- Bookmark important pages
- Integrate with other systems

### **✅ Security & Reliability**
- SSL encryption
- Professional certificates
- Load balancing
- 24/7 monitoring

## 🔧 **Customization Options**

### **Different Domains for Different Services**
```bash
# Customer-facing
orders.yourcompany.com → Enhanced order form

# Internal CBS
admin.yourcompany.com → Review interface + quotation generator
```

### **Subdirectory Deployment**
```bash
# Deploy under a subdirectory
yourcompany.com/cbs-parts/
yourcompany.com/orders/
```

---

## 📞 **Need Help?**

Your URLs will be automatically configured during deployment. If you need custom configuration:

1. **Edit**: `scripts/configure_production_urls.py`
2. **Run**: `python3 scripts/configure_production_urls.py your-domain.com --ssl`
3. **Deploy**: `./deployment/deploy_production.sh your-domain.com`

**🌍 Your CBS Parts System will work perfectly with any domain you choose!** 🚀
