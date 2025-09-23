#!/usr/bin/env python3
"""
CBS Parts System - 24/7 Production Monitor
Ensures system stays alive and alerts on failures
"""

import time
import requests
import logging
import smtplib
import json
import subprocess
import os
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """24/7 System Monitor for CBS Parts System"""
    
    def __init__(self):
        self.services = {
            'parts-api': 'http://localhost:8002/api/health',
            'form-api': 'http://localhost:8003/api/health', 
            'web-server': 'http://localhost:8000/health',
            'quotation-generator': 'http://localhost:5173'
        }
        
        self.alert_config = {
            'email_enabled': os.getenv('EMAIL_USERNAME') is not None,
            'slack_enabled': os.getenv('SLACK_WEBHOOK_URL') is not None,
            'email_smtp': os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com'),
            'email_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'email_username': os.getenv('EMAIL_USERNAME'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
            'alert_email': os.getenv('ALERT_EMAIL', 'admin@company.com')
        }
        
        self.failure_counts = {service: 0 for service in self.services}
        self.max_failures = 3
        self.check_interval = 60  # seconds
        self.restart_cooldown = 300  # 5 minutes
        self.last_restart = {service: 0 for service in self.services}
        
    def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.failure_counts[service_name] = 0
                return True
            else:
                logger.warning(f"{service_name} returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"{service_name} health check failed: {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a failed service using Docker"""
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_restart[service_name] < self.restart_cooldown:
            logger.info(f"Restart cooldown active for {service_name}")
            return False
        
        try:
            # Restart Docker container
            container_name = f"cbs-{service_name.replace('_', '-')}"
            subprocess.run(['docker', 'restart', container_name], check=True)
            
            self.last_restart[service_name] = current_time
            logger.info(f"Successfully restarted {service_name}")
            
            # Wait for service to start
            time.sleep(30)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart {service_name}: {e}")
            return False
    
    def send_email_alert(self, subject: str, body: str):
        """Send email alert"""
        if not self.alert_config['email_enabled']:
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.alert_config['email_username']
            msg['To'] = self.alert_config['alert_email']
            msg['Subject'] = f"CBS Parts System Alert: {subject}"
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.alert_config['email_smtp'], self.alert_config['email_port'])
            server.starttls()
            server.login(self.alert_config['email_username'], self.alert_config['email_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def send_slack_alert(self, message: str):
        """Send Slack alert"""
        if not self.alert_config['slack_enabled']:
            return
        
        try:
            payload = {
                'text': f"🚨 CBS Parts System Alert",
                'attachments': [{
                    'color': 'danger',
                    'fields': [{
                        'title': 'System Status',
                        'value': message,
                        'short': False
                    }],
                    'footer': 'CBS Parts Monitor',
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(
                self.alert_config['slack_webhook'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def send_alert(self, service_name: str, status: str, details: str = ""):
        """Send alerts via all configured channels"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = f"{service_name.upper()} {status}"
        
        body = f"""
CBS Parts System Alert

Service: {service_name}
Status: {status}
Time: {timestamp}
Details: {details}

System Status:
{self.get_system_status_summary()}

Please check the system immediately.
        """
        
        slack_message = f"*{service_name}* is {status}\nTime: {timestamp}\n{details}"
        
        # Send alerts
        self.send_email_alert(subject, body)
        self.send_slack_alert(slack_message)
    
    def get_system_status_summary(self) -> str:
        """Get current system status summary"""
        status_lines = []
        for service_name, url in self.services.items():
            is_healthy = self.check_service_health(service_name, url)
            status = "✅ HEALTHY" if is_healthy else "❌ FAILED"
            failures = self.failure_counts[service_name]
            status_lines.append(f"• {service_name}: {status} (failures: {failures})")
        
        return "\n".join(status_lines)
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting CBS Parts System Monitor...")
        logger.info(f"Monitoring {len(self.services)} services every {self.check_interval} seconds")
        
        while True:
            try:
                all_healthy = True
                
                for service_name, url in self.services.items():
                    is_healthy = self.check_service_health(service_name, url)
                    
                    if not is_healthy:
                        all_healthy = False
                        self.failure_counts[service_name] += 1
                        
                        logger.warning(f"{service_name} failed health check (failure #{self.failure_counts[service_name]})")
                        
                        # Attempt restart after max failures
                        if self.failure_counts[service_name] >= self.max_failures:
                            logger.error(f"{service_name} exceeded max failures, attempting restart...")
                            
                            restart_success = self.restart_service(service_name)
                            
                            if restart_success:
                                self.send_alert(service_name, "RESTARTED", "Service was automatically restarted due to health check failures")
                                self.failure_counts[service_name] = 0
                            else:
                                self.send_alert(service_name, "FAILED", f"Service failed and could not be restarted (failures: {self.failure_counts[service_name]})")
                    
                    else:
                        # Service is healthy
                        if self.failure_counts[service_name] > 0:
                            logger.info(f"{service_name} recovered from {self.failure_counts[service_name]} failures")
                            self.failure_counts[service_name] = 0
                
                # Log system status every hour
                if int(time.time()) % 3600 < self.check_interval:
                    logger.info(f"System Status Summary:\n{self.get_system_status_summary()}")
                
                # Check disk space
                self.check_disk_space()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(self.check_interval)
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    usage_percent = int(parts[4].rstrip('%'))
                    if usage_percent > 90:
                        self.send_alert("DISK_SPACE", "WARNING", f"Disk usage at {usage_percent}%")
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")

def main():
    """Main function"""
    monitor = SystemMonitor()
    monitor.monitor_loop()

if __name__ == "__main__":
    main()
