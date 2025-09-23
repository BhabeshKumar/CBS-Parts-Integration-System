# 🏭 CBS Parts System - 24/7 Production Guide

## 🎯 **Ensuring 24/7 Availability**

This guide shows you how to deploy and maintain your CBS Parts System for **24/7 continuous operation**.

## 🚀 **Deployment Options**

### **Option 1: Docker + Systemd (Recommended)**
**Best for**: Medium-scale production with automatic recovery

```bash
# 1. Deploy to production server
sudo ./deployment/deploy_production.sh your-domain.com

# 2. Verify services are running
systemctl status cbs-parts-system
journalctl -u cbs-parts-system -f

# 3. Test all endpoints (automatically converts to your domain)
curl https://your-domain.com/api/parts/health  # Parts API
curl https://your-domain.com/api/health        # Form API
curl https://your-domain.com/health            # Web server
curl https://your-domain.com/quotation/        # Quotation generator
```

### **Option 2: Cloud Deployment (AWS/GCP/Azure)**
**Best for**: Large-scale production with cloud reliability

```bash
# Deploy to cloud with container orchestration
# - AWS ECS/Fargate
# - Google Cloud Run  
# - Azure Container Instances
# - Kubernetes cluster
```

### **Option 3: VPS/Dedicated Server**
**Best for**: Simple dedicated hosting

```bash
# Install on Ubuntu/CentOS server
# Use the deployment script with monitoring
```

## 🔄 **High Availability Features**

### **✅ Automatic Service Recovery**
- **Health Checks**: Every 30 seconds
- **Auto-Restart**: Failed services restart automatically  
- **Failure Tolerance**: 3 failures before restart
- **Cooldown Period**: 5 minutes between restarts

### **✅ System Monitoring**
- **24/7 Monitor**: Continuous health checking
- **Email Alerts**: Instant notifications on failures
- **Slack Integration**: Real-time team notifications
- **Log Rotation**: Automated log management

### **✅ Load Balancing & SSL**
- **Nginx Proxy**: Load balancing with failover
- **SSL Termination**: HTTPS with auto-renewal
- **Rate Limiting**: Protection against abuse
- **Security Headers**: Enterprise-grade security

## 🚨 **Monitoring & Alerts**

### **Health Check Endpoints**
```bash
# Check all services
curl http://localhost:8002/api/health    # Parts API
curl http://localhost:8003/api/health    # Form API  
curl http://localhost:8000/health        # Web Server
curl http://localhost:5173               # Quotation Generator
curl http://localhost/health             # Load Balancer
```

### **Alert Configuration**
Edit `/opt/cbs-parts-system/.env`:
```bash
# Email alerts
EMAIL_USERNAME=alerts@yourcompany.com
EMAIL_PASSWORD=your_app_password
ALERT_EMAIL=admin@yourcompany.com

# Slack alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### **Alert Types**
- 🔴 **Service Down**: Immediate notification
- 🟡 **Service Slow**: Performance warnings
- 🟠 **High CPU/Memory**: Resource alerts
- 🔵 **Disk Space**: Storage warnings
- 🟢 **Service Recovery**: Recovery notifications

## 📊 **System Management**

### **Service Control**
```bash
# Check status
systemctl status cbs-parts-system

# Start/Stop/Restart
systemctl start cbs-parts-system
systemctl stop cbs-parts-system
systemctl restart cbs-parts-system

# View logs
journalctl -u cbs-parts-system -f
tail -f /opt/cbs-parts-system/logs/*.log
```

### **Container Management**
```bash
# View running containers
docker ps

# Restart specific service
docker restart cbs-parts-api
docker restart cbs-form-api
docker restart cbs-quotation-generator

# View container logs
docker logs cbs-parts-api -f
docker logs cbs-form-api -f
```

### **System Performance**
```bash
# Check system resources
htop
df -h                    # Disk space
free -h                  # Memory usage
docker stats             # Container resources
```

## 🔧 **Maintenance Tasks**

### **Daily Monitoring**
- ✅ Check service status
- ✅ Review error logs
- ✅ Monitor resource usage
- ✅ Verify alert system

### **Weekly Tasks**
- 🔄 Review system performance
- 📊 Check log sizes
- 🧹 Clean old backups
- 🔍 Security audit

### **Monthly Tasks**
- 🆙 System updates
- 📝 Review configurations
- 🔐 SSL certificate renewal
- 📊 Performance analysis

## 💾 **Backup & Recovery**

### **Automated Backups**
```bash
# Daily automated backups at 2 AM
/opt/cbs-parts-system/backup.sh

# Manual backup
sudo -u cbsuser /opt/cbs-parts-system/backup.sh

# Backup location
ls -la /opt/cbs-backups/
```

### **Disaster Recovery**
```bash
# 1. Stop services
systemctl stop cbs-parts-system

# 2. Restore from backup
cd /opt/cbs-backups
tar -xzf cbs-backup-YYYYMMDD_HHMMSS.tar.gz

# 3. Copy files back
cp -r config/* /opt/cbs-parts-system/config/
cp .env /opt/cbs-parts-system/

# 4. Restart services
systemctl start cbs-parts-system
```

## 🔒 **Security Features**

### **✅ Built-in Security**
- 🔐 **Firewall**: UFW with restricted ports
- 🛡️ **Fail2ban**: Intrusion prevention
- 🔒 **SSL/TLS**: HTTPS encryption
- 👤 **User Isolation**: Non-root containers
- 📝 **Audit Logs**: Complete access logging

### **Security Monitoring**
```bash
# Check failed login attempts
sudo fail2ban-client status sshd

# Review firewall status
sudo ufw status verbose

# Check security logs
tail -f /var/log/auth.log
tail -f /var/log/nginx/access.log
```

## 📈 **Scaling Options**

### **Vertical Scaling (Single Server)**
- Increase CPU/RAM on existing server
- Add SSD storage for better performance
- Optimize container resource limits

### **Horizontal Scaling (Multiple Servers)**
- Load balancer with multiple backend servers
- Database replication for high availability
- CDN for static content delivery

### **Cloud Auto-Scaling**
- AWS Auto Scaling Groups
- Google Cloud Instance Groups
- Azure Scale Sets

## 🚨 **Troubleshooting**

### **Common Issues**

**❌ Service Won't Start**
```bash
# Check logs
journalctl -u cbs-parts-system -f
docker logs cbs-parts-api

# Check configuration
cat /opt/cbs-parts-system/.env
```

**❌ High Memory Usage**
```bash
# Check container usage
docker stats
# Restart heavy containers
docker restart cbs-quotation-generator
```

**❌ SSL Certificate Issues**
```bash
# Renew certificate
sudo certbot renew
sudo systemctl reload nginx
```

**❌ Database Connection Errors**
```bash
# Check Smartsheet connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.smartsheet.com/2.0/sheets
```

### **Emergency Procedures**

**🚨 Complete System Failure**
```bash
# 1. Check system resources
df -h && free -h && top

# 2. Restart all services
systemctl restart cbs-parts-system

# 3. If still failing, restore from backup
# (Follow disaster recovery steps above)
```

**🚨 High Load/Traffic Spike**
```bash
# 1. Check current load
htop

# 2. Scale containers temporarily
docker-compose -f deployment/docker-compose.yml up --scale parts-api=3

# 3. Monitor performance
docker stats
```

## 📞 **Support Contacts**

### **System Administrator**
- **Name**: Your IT Team
- **Email**: admin@yourcompany.com
- **Phone**: +1-XXX-XXX-XXXX

### **Application Support**
- **Smartsheet Issues**: Smartsheet Support
- **Server Issues**: Your hosting provider
- **Application Bugs**: Development team

## 🎯 **SLA Targets**

### **Availability Targets**
- ✅ **Uptime**: 99.9% (8.77 hours downtime/year)
- ✅ **Response Time**: < 2 seconds for API calls
- ✅ **Recovery Time**: < 5 minutes for automatic restart
- ✅ **Backup Frequency**: Daily with 30-day retention

### **Performance Metrics**
- **Parts Search**: < 500ms response time
- **Order Submission**: < 3 seconds end-to-end
- **PDF Generation**: < 10 seconds per quotation
- **Concurrent Users**: Support for 50+ simultaneous users

---

## 🏆 **Production Checklist**

**Before Going Live:**
- ✅ Configure real Smartsheet API tokens
- ✅ Set up SSL certificate with your domain
- ✅ Configure email/Slack alerts
- ✅ Test complete order workflow
- ✅ Verify backup system
- ✅ Set up monitoring dashboard
- ✅ Train support team
- ✅ Document emergency procedures

**🚀 Your CBS Parts System is ready for 24/7 production operation!**
