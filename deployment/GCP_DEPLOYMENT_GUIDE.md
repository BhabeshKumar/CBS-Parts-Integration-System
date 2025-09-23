# 🌐 CBS Parts System - GCP Deployment Guide

## 🚀 **Quick GCP Deployment (15 minutes)**

### **Prerequisites**
- GCP Account with billing enabled
- Domain name (optional, can use GCP external IP)
- Basic terminal knowledge

## **Step 1: Create GCP Compute Engine Instance**

### **Option A: Using GCP Console (Recommended)**
```bash
1. Go to: https://console.cloud.google.com/compute/instances
2. Click "CREATE INSTANCE"
3. Configure:
   - Name: cbs-parts-system
   - Region: us-central1 (or closest to your users)
   - Zone: us-central1-a
   - Machine type: e2-standard-2 (2 vCPU, 8GB RAM)
   - Boot disk: Ubuntu 20.04 LTS, 20GB SSD
   - Firewall: ✅ Allow HTTP traffic ✅ Allow HTTPS traffic
4. Click "CREATE"
```

### **Option B: Using gcloud CLI**
```bash
# Install gcloud CLI first: https://cloud.google.com/sdk/docs/install

# Create instance
gcloud compute instances create cbs-parts-system \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-ssd \
    --tags=http-server,https-server

# Create firewall rules
gcloud compute firewall-rules create cbs-parts-allow-http \
    --allow tcp:80,tcp:443,tcp:8000,tcp:8002,tcp:8003,tcp:5173 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server

gcloud compute firewall-rules create cbs-parts-allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags https-server
```

## **Step 2: Connect to Your Instance**

```bash
# Get external IP
gcloud compute instances describe cbs-parts-system \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# SSH into instance
gcloud compute ssh cbs-parts-system --zone=us-central1-a

# OR use the external IP with any SSH client
ssh username@EXTERNAL_IP
```

## **Step 3: Upload CBS System**

### **Option A: Direct Upload**
```bash
# From your local machine, upload the production folder
gcloud compute scp --recurse CBS_Parts_System_Production/ \
    cbs-parts-system:~/CBS_Parts_System_Production/ \
    --zone=us-central1-a

# SSH into the instance
gcloud compute ssh cbs-parts-system --zone=us-central1-a
```

### **Option B: Git Clone (if you have a repository)**
```bash
# On the GCP instance
git clone YOUR_REPOSITORY_URL
cd CBS_Parts_System_Production
```

### **Option C: Manual Upload via SCP**
```bash
# Get your instance external IP first
EXTERNAL_IP=$(gcloud compute instances describe cbs-parts-system \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Upload from your local machine
scp -r CBS_Parts_System_Production/ username@$EXTERNAL_IP:~/
```

## **Step 4: Deploy the System**

```bash
# SSH into your GCP instance
gcloud compute ssh cbs-parts-system --zone=us-central1-a

# Get your external IP for configuration
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "Your external IP: $EXTERNAL_IP"

# Navigate to the uploaded folder
cd CBS_Parts_System_Production

# Make deployment script executable
chmod +x deployment/deploy_production.sh

# Deploy with your domain OR external IP
sudo ./deployment/deploy_production.sh your-domain.com
# OR if no domain:
sudo ./deployment/deploy_production.sh $EXTERNAL_IP
```

## **Step 5: Configure Domain (Optional)**

### **If You Have a Domain:**
```bash
# Point your domain to GCP external IP
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Add A record: @ -> YOUR_GCP_EXTERNAL_IP
3. Add A record: www -> YOUR_GCP_EXTERNAL_IP
4. Wait 5-10 minutes for DNS propagation

# Then deploy with domain:
sudo ./deployment/deploy_production.sh yourdomain.com
```

### **If Using External IP Only:**
```bash
# Your system will be available at:
http://YOUR_EXTERNAL_IP
https://YOUR_EXTERNAL_IP (with self-signed certificate)
```

## **Step 6: Test Your Live System**

```bash
# Get your external IP
EXTERNAL_IP=$(curl -s ifconfig.me)

# Test all endpoints
curl https://$EXTERNAL_IP/health
curl https://$EXTERNAL_IP/api/parts/health
curl https://$EXTERNAL_IP/api/health

# Open in browser:
echo "🌐 Your CBS Parts System is live at:"
echo "📋 Order Form: https://$EXTERNAL_IP/enhanced_order_form.html"
echo "🔍 Review Interface: https://$EXTERNAL_IP/parts_review_interface.html"
echo "📄 Quotation Generator: https://$EXTERNAL_IP/quotation/"
```

## **🔧 GCP-Specific Configuration**

### **Firewall Rules (Already included in deployment)**
```bash
# Verify firewall rules
gcloud compute firewall-rules list --filter="name~cbs-parts"

# If needed, create additional rules:
gcloud compute firewall-rules create cbs-parts-custom \
    --allow tcp:8000,tcp:8002,tcp:8003,tcp:5173 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server
```

### **Static IP (Optional but Recommended)**
```bash
# Reserve a static IP
gcloud compute addresses create cbs-parts-static-ip --region=us-central1

# Get the static IP
gcloud compute addresses describe cbs-parts-static-ip --region=us-central1

# Assign to your instance
gcloud compute instances delete-access-config cbs-parts-system \
    --access-config-name="External NAT" --zone=us-central1-a

gcloud compute instances add-access-config cbs-parts-system \
    --access-config-name="External NAT" \
    --address=cbs-parts-static-ip \
    --zone=us-central1-a
```

## **💰 Cost Estimation**

### **Monthly Costs:**
- **Compute Engine (e2-standard-2)**: ~$50/month
- **Static IP**: $3/month (if reserved)
- **Storage (20GB SSD)**: ~$3/month
- **Network egress**: ~$1-5/month (depending on traffic)
- **Total**: ~$55-60/month

### **Cost Optimization:**
```bash
# Use smaller instance for testing
--machine-type=e2-micro  # Free tier eligible (~$5/month)
--machine-type=e2-small  # ~$15/month

# Use preemptible instances (up to 80% savings)
--preemptible
```

## **🔒 Security Best Practices**

### **SSH Key Setup**
```bash
# Generate SSH key locally
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Add to GCP metadata
gcloud compute project-info add-metadata \
    --metadata-from-file ssh-keys=~/.ssh/id_rsa.pub
```

### **Firewall Restrictions**
```bash
# Restrict SSH access to your IP only
gcloud compute firewall-rules create ssh-restricted \
    --allow tcp:22 \
    --source-ranges YOUR_IP_ADDRESS/32 \
    --target-tags ssh-restricted

# Add tag to your instance
gcloud compute instances add-tags cbs-parts-system \
    --tags ssh-restricted \
    --zone us-central1-a
```

## **📊 Monitoring & Logging**

### **GCP Monitoring Setup**
```bash
# Enable monitoring agent (included in deployment script)
curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
sudo bash add-monitoring-agent-repo.sh
sudo apt-get update
sudo apt-get install stackdriver-agent
sudo service stackdriver-agent start
```

### **View Logs**
```bash
# On your GCP instance
sudo journalctl -u cbs-parts-system -f
tail -f /opt/cbs-parts-system/logs/*.log

# In GCP Console: Logging > Logs Explorer
```

## **🚨 Troubleshooting**

### **Common Issues**

**❌ Can't connect to external IP**
```bash
# Check firewall rules
gcloud compute firewall-rules list
# Verify instance is running
gcloud compute instances list
```

**❌ SSL certificate issues**
```bash
# Check certificate status
sudo certbot certificates
# Renew if needed
sudo certbot renew
```

**❌ Services not starting**
```bash
# Check systemd status
sudo systemctl status cbs-parts-system
# View detailed logs
sudo journalctl -u cbs-parts-system -f
```

## **🔄 Updates & Maintenance**

### **System Updates**
```bash
# SSH into instance
gcloud compute ssh cbs-parts-system --zone=us-central1-a

# Update system
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart cbs-parts-system
```

### **Application Updates**
```bash
# Upload new version
gcloud compute scp --recurse NEW_VERSION/ \
    cbs-parts-system:~/CBS_Parts_System_Production/ \
    --zone=us-central1-a

# Redeploy
cd CBS_Parts_System_Production
sudo ./deployment/deploy_production.sh yourdomain.com
```

## **📱 Mobile Testing**

Once deployed, your system will be accessible from any mobile device worldwide:

```bash
# Test URLs (replace with your domain/IP)
https://yourdomain.com/enhanced_order_form.html
https://yourdomain.com/parts_review_interface.html
https://yourdomain.com/quotation/
```

## **🎯 Success Checklist**

✅ GCP instance created and running  
✅ Firewall rules configured  
✅ CBS system uploaded to instance  
✅ Deployment script executed successfully  
✅ All services running (check with `systemctl status`)  
✅ External IP accessible  
✅ Domain configured (if applicable)  
✅ SSL certificate installed  
✅ Mobile testing completed  
✅ Monitoring and alerts configured  

## **🚀 You're Live!**

Your CBS Parts System is now running 24/7 on Google Cloud Platform with:
- ✅ **Global accessibility** from any device
- ✅ **99.9% uptime** with auto-recovery
- ✅ **HTTPS security** with SSL certificates
- ✅ **Scalable infrastructure** ready for growth
- ✅ **Professional monitoring** and alerts

**Access your system at**: `https://yourdomain.com` or `https://YOUR_EXTERNAL_IP`
