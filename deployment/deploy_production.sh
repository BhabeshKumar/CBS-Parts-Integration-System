#!/bin/bash
# CBS Parts System - Production Deployment Script
# Ensures 24/7 availability with proper setup

set -e

echo "🏭 CBS Parts System - Production Deployment"
echo "==========================================="

# Configuration
INSTALL_DIR="/opt/cbs-parts-system"
SERVICE_USER="cbsuser"
BACKUP_DIR="/opt/cbs-backups"
DOMAIN=${1:-"localhost"}
USE_SSL="true"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
fi

log "Starting production deployment..."

# Install required packages
log "Installing system dependencies..."
apt-get update
apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    fail2ban \
    ufw \
    htop \
    curl \
    git \
    logrotate

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Create service user
log "Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d $INSTALL_DIR $SERVICE_USER
fi

# Create directories
log "Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $BACKUP_DIR
mkdir -p $INSTALL_DIR/logs
mkdir -p /var/log/cbs-parts

# Set permissions
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chown -R $SERVICE_USER:$SERVICE_USER $BACKUP_DIR
chmod 755 $INSTALL_DIR

# Copy application files
log "Copying application files..."
if [ -d "$(pwd)" ]; then
    cp -r * $INSTALL_DIR/
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
fi

# Configure production URLs
log "Configuring production URLs for domain: $DOMAIN"
cd $INSTALL_DIR
python3 scripts/configure_production_urls.py $DOMAIN --ssl

# Setup environment file
log "Setting up environment..."
cat > $INSTALL_DIR/.env << EOF
# CBS Parts System Production Environment
SMARTSHEET_API_TOKEN=7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB
SLACK_WEBHOOK_URL=your_slack_webhook
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_USERNAME=your_email@company.com
EMAIL_PASSWORD=your_app_password
ALERT_EMAIL=admin@company.com
NODE_ENV=production
PYTHONUNBUFFERED=1

# CBS Configuration
CBS_ENVIRONMENT=production
CBS_DOMAIN=$DOMAIN
CBS_USE_SSL=true
CBS_BASE_URL=https://$DOMAIN

# CBS Director
CBS_DIRECTOR_EMAIL=bhabesh.kumar@sheaney.ie

# Smartsheet Sheet IDs
ORDERS_INTAKE_SHEET_ID=p3G494hxj7PMRR54xFH4vFV4gf2g94vqM4V9Q7H1
SALES_WORKS_ORDERS_SHEET_ID=G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391
CBS_PARTS_SHEET_ID=4695255724019588
CBS_DISCOUNTS_SHEET_ID=8920011042148228

# Company Information
COMPANY_NAME=Concrete Batching Systems
COMPANY_PHONE=+1 234 567 8900
COMPANY_EMAIL=info@cbs.com
COMPANY_WEBSITE=www.cbs.com
EOF

chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.env
chmod 600 $INSTALL_DIR/.env

# Setup systemd service
log "Installing systemd service..."
cp $INSTALL_DIR/deployment/systemd/cbs-parts-system.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable cbs-parts-system

# Setup log rotation
log "Setting up log rotation..."
cat > /etc/logrotate.d/cbs-parts << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload cbs-parts-system || true
    endscript
}
EOF

# Setup firewall
log "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000:8003/tcp  # CBS API ports

# Setup fail2ban for security
log "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Setup SSL with Let's Encrypt (if domain provided)
if [ ! -z "$1" ]; then
    DOMAIN=$1
    log "Setting up SSL certificate for $DOMAIN..."
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    # Setup auto-renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
fi

# Setup monitoring cron job
log "Setting up monitoring..."
cat > /etc/cron.d/cbs-monitor << EOF
# CBS Parts System Monitoring
*/5 * * * * $SERVICE_USER cd $INSTALL_DIR && python3 deployment/system_monitor.py >> /var/log/cbs-parts/monitor.log 2>&1
EOF

# Setup backup script
log "Setting up backup system..."
cat > $INSTALL_DIR/backup.sh << 'EOF'
#!/bin/bash
# CBS Parts System Backup

BACKUP_DIR="/opt/cbs-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
mkdir -p $BACKUP_DIR/$DATE

# Backup configuration
cp -r /opt/cbs-parts-system/config $BACKUP_DIR/$DATE/
cp /opt/cbs-parts-system/.env $BACKUP_DIR/$DATE/

# Backup database file
cp "/opt/cbs-parts-system/CBS Parts from Sage.xlsx" $BACKUP_DIR/$DATE/

# Backup logs (last 7 days)
find /opt/cbs-parts-system/logs -name "*.log" -mtime -7 -exec cp {} $BACKUP_DIR/$DATE/ \;

# Create archive
tar -czf $BACKUP_DIR/cbs-backup-$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

# Keep only last 30 backups
ls -t $BACKUP_DIR/cbs-backup-*.tar.gz | tail -n +31 | xargs -r rm

echo "Backup completed: cbs-backup-$DATE.tar.gz"
EOF

chmod +x $INSTALL_DIR/backup.sh
chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/backup.sh

# Setup backup cron
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh") | crontab -u $SERVICE_USER -

# Build and start services
log "Building and starting services..."
cd $INSTALL_DIR
sudo -u $SERVICE_USER docker-compose -f deployment/docker-compose-production.yml build
systemctl start cbs-parts-system

# Wait for services to start
log "Waiting for services to start..."
sleep 60

# Health check
log "Performing health check..."
HEALTH_CHECK_PASSED=true

for port in 8000 8002 8003 5173; do
    if ! curl -f http://localhost:$port/health >/dev/null 2>&1; then
        warn "Service on port $port is not responding"
        HEALTH_CHECK_PASSED=false
    fi
done

if $HEALTH_CHECK_PASSED; then
    log "✅ All services are healthy!"
else
    warn "Some services may not be fully started yet. Check logs with: journalctl -u cbs-parts-system -f"
fi

# Final instructions
log "Deployment completed!"
echo ""
echo "🎉 CBS Parts System is now running 24/7!"
echo ""
echo "📊 System Status:"
echo "   • View logs: journalctl -u cbs-parts-system -f"
echo "   • Service status: systemctl status cbs-parts-system"
echo "   • Restart system: systemctl restart cbs-parts-system"
echo "   • Stop system: systemctl stop cbs-parts-system"
echo ""
echo "🌐 URLs:"
echo "   • Customer Orders: http://localhost:8000/templates/enhanced_order_form.html"
echo "   • CBS Review: http://localhost:8000/templates/parts_review_interface.html"
echo "   • API Health: http://localhost:8002/api/health"
echo ""
echo "⚙️ Configuration:"
echo "   • Edit settings: $INSTALL_DIR/.env"
echo "   • View logs: $INSTALL_DIR/logs/"
echo "   • Backups: $BACKUP_DIR/"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update $INSTALL_DIR/.env with your actual API tokens"
echo "   2. Configure SSL if you have a domain"
echo "   3. Test the system with real orders"
echo ""

log "Production deployment completed successfully! 🚀"
