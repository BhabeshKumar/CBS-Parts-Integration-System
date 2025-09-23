# 🐳 CBS Parts System - Docker Deployment Guide

## 🚀 **One-Command Deployment**

Deploy your CBS Parts System anywhere with Docker in **under 5 minutes**!

### **Requirements**
- Docker & Docker Compose installed
- 2GB RAM minimum
- Internet connection

### **Quick Start**

```bash
# 1. Clone/Download the CBS Parts System
git clone <your-repo> # or download ZIP
cd CBS_Parts_System_Production

# 2. Deploy with one command
docker-compose up -d

# 3. Access your system
open http://localhost
```

**That's it! Your CBS Parts System is now live! 🎉**

---

## 🌐 **Cloud Deployment Options**

### **Option 1: Google Cloud Platform**

```bash
# 1. Create GCP VM
gcloud compute instances create cbs-parts-vm \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server,https-server

# 2. SSH and deploy
gcloud compute ssh cbs-parts-vm
git clone <your-repo> && cd CBS_Parts_System_Production
sudo apt update && sudo apt install -y docker.io docker-compose
sudo docker-compose up -d

# 3. Get external IP
gcloud compute instances describe cbs-parts-vm \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### **Option 2: AWS EC2**

```bash
# 1. Launch EC2 instance (t3.medium, Ubuntu 20.04)
# 2. Connect and deploy
ssh -i your-key.pem ubuntu@your-ec2-ip
git clone <your-repo> && cd CBS_Parts_System_Production
sudo apt update && sudo apt install -y docker.io docker-compose
sudo docker-compose up -d
```

### **Option 3: DigitalOcean**

```bash
# 1. Create Droplet (2GB RAM, Ubuntu 20.04)
# 2. Connect and deploy
ssh root@your-droplet-ip
git clone <your-repo> && cd CBS_Parts_System_Production
apt update && apt install -y docker.io docker-compose
docker-compose up -d
```

### **Option 4: Azure**

```bash
# 1. Create VM (Standard_B2s, Ubuntu 20.04)
# 2. Connect and deploy
ssh azureuser@your-vm-ip
git clone <your-repo> && cd CBS_Parts_System_Production
sudo apt update && sudo apt install -y docker.io docker-compose
sudo docker-compose up -d
```

---

## 🔧 **Configuration**

### **Environment Variables**

Create `.env` file for custom configuration:

```bash
# Smartsheet Configuration
SMARTSHEET_API_TOKEN=your_api_token
ORDERS_INTAKE_SHEET_ID=your_sheet_id
SALES_WORKS_ORDERS_SHEET_ID=your_sheet_id
CBS_PARTS_SHEET_ID=your_parts_sheet_id
CBS_DISCOUNTS_SHEET_ID=your_discounts_sheet_id

# Email Configuration
CBS_DIRECTOR_EMAIL=your_email@company.com

# Domain Configuration (for production)
DOMAIN=yourdomain.com
ENVIRONMENT=production
```

### **Custom Domain Setup**

```bash
# 1. Point your domain to server IP
# Add DNS A record: @ -> YOUR_SERVER_IP

# 2. Update docker-compose.yml
environment:
  - DOMAIN=yourdomain.com

# 3. Restart container
docker-compose restart
```

---

## 📊 **Management Commands**

### **Basic Operations**

```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# Restart system
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### **Service Management**

```bash
# Restart specific service
docker-compose restart cbs-parts-system

# View service logs
docker logs cbs-parts-system -f

# Access container shell
docker exec -it cbs-parts-system sh

# Check service health
curl http://localhost/health
```

### **Updates & Maintenance**

```bash
# Update system
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean old images
docker system prune -f

# Backup volumes
docker run --rm -v cbs_logs:/data -v $(pwd):/backup ubuntu \
    tar czf /backup/cbs_backup_$(date +%Y%m%d).tar.gz /data
```

---

## 🔍 **Monitoring & Health Checks**

### **Health Check Endpoints**

```bash
# System health
curl http://localhost/health

# Individual services
curl http://localhost:8002/api/parts/health    # Parts API
curl http://localhost:8003/api/health          # Form API
curl http://localhost:8000/health              # Web Server
curl http://localhost:5173                     # Quotation Generator
```

### **Log Monitoring**

```bash
# All logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f cbs-parts-system

# Error logs only
docker-compose logs --tail=100 | grep -i error

# Live log monitoring
tail -f /var/lib/docker/volumes/cbs_logs/_data/*.log
```

### **Performance Monitoring**

```bash
# Container stats
docker stats cbs-parts-system

# System resources
docker system df

# Memory usage
docker exec cbs-parts-system free -h

# Disk usage
docker exec cbs-parts-system df -h
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

**❌ Container won't start**
```bash
# Check logs
docker-compose logs cbs-parts-system

# Check container status
docker ps -a

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**❌ Port conflicts**
```bash
# Check what's using port 80
sudo lsof -i :80

# Use different ports
docker-compose down
# Edit docker-compose.yml: "8080:80"
docker-compose up -d
```

**❌ Permission issues**
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix file permissions
sudo chown -R $USER:$USER .
```

**❌ Out of memory**
```bash
# Check memory usage
free -h

# Restart with more memory
docker-compose down
# Upgrade server RAM or use smaller instance
docker-compose up -d
```

**❌ Network issues**
```bash
# Reset Docker network
docker network prune -f
docker-compose down
docker-compose up -d

# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 🔒 **Security**

### **Production Security**

```bash
# 1. Enable firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 2. SSL certificates (with domain)
# Let's Encrypt auto-setup included in container

# 3. Regular updates
sudo apt update && sudo apt upgrade -y
docker-compose pull
docker-compose up -d

# 4. Monitor access logs
docker-compose logs nginx | grep -i "POST\|GET"
```

### **Access Control**

```bash
# Restrict API access by IP
# Edit nginx config in container or rebuild with custom config

# Environment secrets
# Use Docker secrets or external secret management
docker secret create smartsheet_token your_token_file
```

---

## 📈 **Scaling**

### **Horizontal Scaling**

```bash
# Scale with multiple replicas
docker-compose up -d --scale cbs-parts-system=3

# Load balancer setup
# Use external load balancer (AWS ALB, GCP Load Balancer)
```

### **Vertical Scaling**

```bash
# Allocate more resources
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

---

## 💰 **Cost Optimization**

### **Cloud Provider Costs**

| Provider | Instance Type | Monthly Cost |
|----------|---------------|--------------|
| **DigitalOcean** | 2GB/2vCPU | $18/month |
| **Linode** | 4GB/2vCPU | $20/month |
| **Vultr** | 2GB/1vCPU | $12/month |
| **AWS** | t3.medium | $30/month |
| **GCP** | e2-standard-2 | $45/month |

### **Optimization Tips**

```bash
# 1. Use smaller base image
FROM node:18-alpine  # Already optimized

# 2. Multi-stage build (advanced)
# Separate build and runtime stages

# 3. Resource limits
# Set memory/CPU limits in docker-compose.yml

# 4. Auto-shutdown for dev environments
# Use cloud provider scheduling
```

---

## 🎯 **Production Checklist**

### **Pre-Deployment**

✅ **Environment Variables**: All tokens and IDs configured  
✅ **Domain Setup**: DNS pointing to server  
✅ **SSL Certificate**: HTTPS enabled  
✅ **Firewall**: Only necessary ports open  
✅ **Backups**: Data backup strategy in place  
✅ **Monitoring**: Health checks configured  
✅ **Testing**: All workflows tested  

### **Post-Deployment**

✅ **Health Check**: All services responding  
✅ **Form Testing**: Order submission works  
✅ **API Testing**: Parts search functional  
✅ **Mobile Testing**: Responsive on mobile  
✅ **Email Testing**: Notifications working  
✅ **Performance**: Response times acceptable  
✅ **Security**: No unnecessary ports open  

---

## 🆘 **Support**

### **Quick Commands Reference**

```bash
# Emergency restart
docker-compose restart

# View all logs
docker-compose logs -f

# Check system health
curl http://localhost/health

# Container shell access
docker exec -it cbs-parts-system sh

# Full system restart
docker-compose down && docker-compose up -d
```

### **Getting Help**

- **Container Issues**: Check `docker-compose logs`
- **Network Issues**: Verify firewall settings
- **Performance Issues**: Monitor with `docker stats`
- **Configuration Issues**: Check environment variables

---

## 🎉 **Success!**

Your CBS Parts System is now running in production with:

✅ **Professional Docker deployment**  
✅ **Auto-restart and health monitoring**  
✅ **Load balancing with Nginx**  
✅ **Scalable architecture**  
✅ **Production-ready security**  
✅ **Easy maintenance and updates**  

**Access your system at**: `http://your-server-ip` or `https://yourdomain.com`

**🚀 Your CBS Parts System is ready for business!**
