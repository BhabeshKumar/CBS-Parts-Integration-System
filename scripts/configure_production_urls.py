#!/usr/bin/env python3
"""
CBS Parts System - Production URL Configuration
Automatically replaces localhost URLs with production URLs
"""

import os
import re
import glob
import json
import sys
from pathlib import Path

class ProductionURLUpdater:
    """Updates all localhost URLs to production URLs"""
    
    def __init__(self, domain: str, use_ssl: bool = True):
        self.domain = domain
        self.use_ssl = use_ssl
        self.protocol = 'https' if use_ssl else 'http'
        self.base_url = f"{self.protocol}://{domain}"
        
        # URL mappings for production
        self.url_mappings = {
            # API endpoints (behind nginx proxy)
            'http://localhost:8002/api/': f'{self.base_url}/api/parts/',
            'http://localhost:8003/api/': f'{self.base_url}/api/',
            'http://localhost:8000/': f'{self.base_url}/',
            'http://localhost:5173/': f'{self.base_url}/quotation/',
            
            # Specific endpoint mappings
            'http://localhost:8002/api/search': f'{self.base_url}/api/parts/search',
            'http://localhost:8002/api/health': f'{self.base_url}/api/parts/health',
            'http://localhost:8003/api/submit-order': f'{self.base_url}/api/submit-order',
            'http://localhost:8003/api/order/': f'{self.base_url}/api/order/',
            'http://localhost:8003/api/generate-quotation/': f'{self.base_url}/api/generate-quotation/',
            'http://localhost:8003/api/quotation-template/': f'{self.base_url}/api/quotation-template/',
            
            # Frontend URLs
            'http://localhost:8000/templates/enhanced_order_form.html': f'{self.base_url}/templates/enhanced_order_form.html',
            'http://localhost:8000/templates/parts_review_interface.html': f'{self.base_url}/templates/parts_review_interface.html',
            'http://localhost:5173/?': f'{self.base_url}/quotation/?',
        }
    
    def update_html_files(self, template_dir: str):
        """Update HTML template files"""
        print(f"🔧 Updating HTML templates in {template_dir}...")
        
        html_files = glob.glob(f"{template_dir}/*.html")
        
        for html_file in html_files:
            print(f"   📝 Updating {os.path.basename(html_file)}")
            
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply URL replacements
            for old_url, new_url in self.url_mappings.items():
                content = content.replace(old_url, new_url)
            
            # Add production configuration script
            config_script = self._generate_js_config()
            
            # Insert config script after <head> tag
            if '<head>' in content and 'window.CBS_CONFIG' not in content:
                content = content.replace('<head>', f'<head>\n    {config_script}')
            
            # Write back if changed
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"      ✅ Updated URLs in {os.path.basename(html_file)}")
            else:
                print(f"      ➖ No changes needed in {os.path.basename(html_file)}")
    
    def update_python_files(self, src_dir: str):
        """Update Python source files"""
        print(f"🔧 Updating Python files in {src_dir}...")
        
        python_files = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for py_file in python_files:
            print(f"   📝 Checking {os.path.relpath(py_file, src_dir)}")
            
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace localhost URLs in Python code
            for old_url, new_url in self.url_mappings.items():
                # Handle both single and double quotes
                content = content.replace(f'"{old_url}"', f'"{new_url}"')
                content = content.replace(f"'{old_url}'", f"'{new_url}'")
            
            # Replace localhost in f-strings and other patterns
            localhost_patterns = [
                (r'http://localhost:8002', f'{self.base_url}/api/parts'),
                (r'http://localhost:8003', f'{self.base_url}/api'),
                (r'http://localhost:8000', f'{self.base_url}'),
                (r'http://localhost:5173', f'{self.base_url}/quotation'),
            ]
            
            for pattern, replacement in localhost_patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"      ✅ Updated URLs in {os.path.relpath(py_file, src_dir)}")
    
    def update_docker_compose(self, docker_compose_path: str):
        """Update docker-compose.yml for production"""
        print(f"🐳 Updating Docker Compose configuration...")
        
        if not os.path.exists(docker_compose_path):
            print(f"   ⚠️  Docker Compose file not found: {docker_compose_path}")
            return
        
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        # Add environment variables for production
        env_vars = f"""
      - CBS_ENVIRONMENT=production
      - CBS_DOMAIN={self.domain}
      - CBS_USE_SSL={'true' if self.use_ssl else 'false'}
      - CBS_BASE_URL={self.base_url}"""
        
        # Add to each service that needs it
        services_to_update = ['parts-api', 'form-api', 'web-server']
        
        for service in services_to_update:
            # Find the service block and add environment variables
            service_pattern = f'(  {service}:.*?environment:)(.*?)(\n  [a-zA-Z]|\nvolumes:|\nnetworks:|\Z)'
            
            def add_env_vars(match):
                service_block = match.group(1)
                existing_env = match.group(2)
                after_env = match.group(3)
                
                if 'CBS_ENVIRONMENT' not in existing_env:
                    return service_block + existing_env + env_vars + after_env
                return match.group(0)
            
            content = re.sub(service_pattern, add_env_vars, content, flags=re.DOTALL)
        
        with open(docker_compose_path, 'w') as f:
            f.write(content)
        
        print(f"   ✅ Updated Docker Compose configuration")
    
    def _generate_js_config(self) -> str:
        """Generate JavaScript configuration"""
        config = {
            'environment': 'production',
            'domain': self.domain,
            'baseUrl': self.base_url,
            'api': {
                'partsSearch': f'{self.base_url}/api/parts/search',
                'partsHealth': f'{self.base_url}/api/parts/health',
                'submitOrder': f'{self.base_url}/api/submit-order',
                'getOrder': f'{self.base_url}/api/order',
                'updateOrder': f'{self.base_url}/api/order',
                'generateQuotation': f'{self.base_url}/api/generate-quotation',
                'quotationTemplate': f'{self.base_url}/api/quotation-template'
            },
            'urls': {
                'orderForm': f'{self.base_url}/templates/enhanced_order_form.html',
                'reviewInterface': f'{self.base_url}/templates/parts_review_interface.html',
                'quotationGenerator': f'{self.base_url}/quotation/'
            }
        }
        
        config_json = json.dumps(config, indent=8)
        return f"""<script>
    // CBS Parts System - Production Configuration
    window.CBS_CONFIG = {config_json};
    console.log('CBS Production Config loaded for:', window.CBS_CONFIG.domain);
</script>"""
    
    def create_nginx_config(self, output_path: str):
        """Create nginx configuration for production"""
        print(f"🌐 Creating Nginx configuration...")
        
        nginx_config = f"""# CBS Parts System - Production Nginx Configuration
server {{
    listen 80;
    server_name {self.domain};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain};
    
    # SSL Configuration (update with your certificate paths)
    ssl_certificate /etc/letsencrypt/live/{self.domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.domain}/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Parts API
    location /api/parts/ {{
        proxy_pass http://localhost:8002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Form API  
    location /api/ {{
        proxy_pass http://localhost:8003/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Quotation Generator
    location /quotation/ {{
        proxy_pass http://localhost:5173/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
    }}
    
    # Web Server (templates and static files)
    location / {{
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(nginx_config)
        
        print(f"   ✅ Nginx configuration created: {output_path}")
    
    def generate_summary(self):
        """Generate summary of URL changes"""
        print(f"\n🎯 Production URL Summary for {self.domain}")
        print(f"{'='*60}")
        
        print(f"\n🌐 Frontend URLs:")
        print(f"   • Customer Orders: {self.base_url}/templates/enhanced_order_form.html")
        print(f"   • CBS Review: {self.base_url}/templates/parts_review_interface.html")
        print(f"   • Quotation Generator: {self.base_url}/quotation/")
        
        print(f"\n🔌 API Endpoints:")
        print(f"   • Parts Search: {self.base_url}/api/parts/search")
        print(f"   • Submit Order: {self.base_url}/api/submit-order")
        print(f"   • Get Order: {self.base_url}/api/order/{{quote_id}}")
        print(f"   • Health Check: {self.base_url}/api/parts/health")
        
        print(f"\n📋 Deployment Steps:")
        print(f"   1. Configure DNS: Point {self.domain} to your server IP")
        print(f"   2. Deploy: ./deployment/deploy_production.sh {self.domain}")
        print(f"   3. SSL Setup: Automatic via Let's Encrypt")
        print(f"   4. Test: Visit {self.base_url}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python configure_production_urls.py <domain> [--ssl]")
        print("Example: python configure_production_urls.py cbsparts.yourcompany.com --ssl")
        sys.exit(1)
    
    domain = sys.argv[1]
    use_ssl = '--ssl' in sys.argv or '--https' in sys.argv
    
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print(f"🚀 Configuring CBS Parts System for production deployment")
    print(f"   Domain: {domain}")
    print(f"   SSL: {'Enabled' if use_ssl else 'Disabled'}")
    print(f"   Project Root: {project_root}")
    
    # Initialize updater
    updater = ProductionURLUpdater(domain, use_ssl)
    
    # Update all components
    updater.update_html_files(os.path.join(project_root, 'templates'))
    updater.update_python_files(os.path.join(project_root, 'src'))
    updater.update_docker_compose(os.path.join(project_root, 'deployment', 'docker-compose.yml'))
    updater.create_nginx_config(os.path.join(project_root, 'deployment', 'nginx-production.conf'))
    
    # Generate summary
    updater.generate_summary()
    
    print(f"\n✅ Production configuration completed!")
    print(f"🚀 Your system is ready for deployment to {domain}")

if __name__ == "__main__":
    main()
