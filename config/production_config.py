#!/usr/bin/env python3
"""
CBS Parts System - Production Configuration
Automatically configures URLs for live deployment
"""

import os
from typing import Dict, Optional

class ProductionConfig:
    """Production configuration for CBS Parts System"""
    
    def __init__(self):
        self.environment = os.getenv('CBS_ENVIRONMENT', 'development')
        self.domain = os.getenv('CBS_DOMAIN', 'localhost')
        self.use_ssl = os.getenv('CBS_USE_SSL', 'false').lower() == 'true'
        self.port_mapping = self._get_port_mapping()
        
    def _get_port_mapping(self) -> Dict[str, int]:
        """Get port mapping based on environment"""
        if self.environment == 'production':
            # In production, nginx handles all routing
            return {
                'parts_api': 80 if not self.use_ssl else 443,
                'form_api': 80 if not self.use_ssl else 443,
                'web_server': 80 if not self.use_ssl else 443,
                'quotation_generator': 80 if not self.use_ssl else 443
            }
        else:
            # Development ports
            return {
                'parts_api': 8002,
                'form_api': 8003,
                'web_server': 8000,
                'quotation_generator': 5173
            }
    
    def get_base_url(self) -> str:
        """Get base URL for the application"""
        protocol = 'https' if self.use_ssl else 'http'
        
        if self.environment == 'production':
            return f"{protocol}://{self.domain}"
        else:
            return f"http://{self.domain}"
    
    def get_service_url(self, service: str, path: str = "") -> str:
        """Get full URL for a specific service"""
        base_url = self.get_base_url()
        
        if self.environment == 'production':
            # In production, all services are behind nginx proxy
            service_paths = {
                'parts_api': '/api/parts',
                'form_api': '/api',
                'web_server': '',
                'quotation_generator': '/quotation'
            }
            service_path = service_paths.get(service, '')
            return f"{base_url}{service_path}{path}"
        else:
            # Development - direct service ports
            port = self.port_mapping[service]
            return f"http://{self.domain}:{port}{path}"
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get all API endpoints"""
        return {
            'parts_search': self.get_service_url('parts_api', '/search'),
            'parts_health': self.get_service_url('parts_api', '/health'),
            'submit_order': self.get_service_url('form_api', '/submit-order'),
            'get_order': self.get_service_url('form_api', '/order'),
            'update_order': self.get_service_url('form_api', '/order'),
            'generate_quotation': self.get_service_url('form_api', '/generate-quotation'),
            'quotation_template': self.get_service_url('form_api', '/quotation-template')
        }
    
    def get_frontend_urls(self) -> Dict[str, str]:
        """Get frontend URLs"""
        return {
            'order_form': self.get_service_url('web_server', '/templates/enhanced_order_form.html'),
            'review_interface': self.get_service_url('web_server', '/templates/parts_review_interface.html'),
            'quotation_generator': self.get_service_url('quotation_generator', '/')
        }
    
    def export_javascript_config(self) -> str:
        """Export configuration as JavaScript for frontend use"""
        api_endpoints = self.get_api_endpoints()
        frontend_urls = self.get_frontend_urls()
        
        js_config = f"""
// CBS Parts System - Production Configuration
window.CBS_CONFIG = {{
    environment: '{self.environment}',
    domain: '{self.domain}',
    baseUrl: '{self.get_base_url()}',
    
    // API Endpoints
    api: {{
        partsSearch: '{api_endpoints["parts_search"]}',
        partsHealth: '{api_endpoints["parts_health"]}',
        submitOrder: '{api_endpoints["submit_order"]}',
        getOrder: '{api_endpoints["get_order"]}',
        updateOrder: '{api_endpoints["update_order"]}',
        generateQuotation: '{api_endpoints["generate_quotation"]}',
        quotationTemplate: '{api_endpoints["quotation_template"]}'
    }},
    
    // Frontend URLs
    urls: {{
        orderForm: '{frontend_urls["order_form"]}',
        reviewInterface: '{frontend_urls["review_interface"]}',
        quotationGenerator: '{frontend_urls["quotation_generator"]}'
    }}
}};

console.log('CBS Config loaded for environment:', window.CBS_CONFIG.environment);
"""
        return js_config
    
    def update_html_templates(self, template_dir: str):
        """Update HTML templates with production URLs"""
        import glob
        import re
        
        template_files = glob.glob(f"{template_dir}/*.html")
        
        for template_file in template_files:
            print(f"Updating template: {template_file}")
            
            with open(template_file, 'r') as f:
                content = f.read()
            
            # Replace localhost URLs with production URLs
            api_endpoints = self.get_api_endpoints()
            frontend_urls = self.get_frontend_urls()
            
            # API endpoint replacements
            replacements = [
                (r'http://localhost:8002/api/', api_endpoints['parts_search'].replace('/search', '/') + '/'),
                (r'http://localhost:8003/api/', api_endpoints['submit_order'].replace('/submit-order', '/') + '/'),
                (r'http://localhost:8000/', self.get_service_url('web_server', '/') + '/'),
                (r'http://localhost:5173/', frontend_urls['quotation_generator']),
                
                # Specific endpoint replacements
                (r'http://localhost:8002/api/search', api_endpoints['parts_search']),
                (r'http://localhost:8003/api/submit-order', api_endpoints['submit_order']),
                (r'http://localhost:8003/api/order/', api_endpoints['get_order'] + '/'),
                (r'http://localhost:5173/\?', frontend_urls['quotation_generator'] + '?'),
            ]
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Add configuration script at the beginning of <body>
            config_script = f"<script>{self.export_javascript_config()}</script>"
            content = re.sub(r'(<body[^>]*>)', r'\1\n' + config_script, content)
            
            with open(template_file, 'w') as f:
                f.write(content)
    
    def create_environment_file(self, output_path: str):
        """Create environment file for deployment"""
        env_content = f"""# CBS Parts System - Production Environment Configuration

# Environment Settings
CBS_ENVIRONMENT={self.environment}
CBS_DOMAIN={self.domain}
CBS_USE_SSL={str(self.use_ssl).lower()}

# Service URLs (auto-generated)
CBS_BASE_URL={self.get_base_url()}
CBS_PARTS_API_URL={self.get_service_url('parts_api')}
CBS_FORM_API_URL={self.get_service_url('form_api')}
CBS_WEB_SERVER_URL={self.get_service_url('web_server')}
CBS_QUOTATION_URL={self.get_service_url('quotation_generator')}

# Smartsheet Configuration (update these)
SMARTSHEET_API_TOKEN=your_token_here

# Alert Configuration
SLACK_WEBHOOK_URL=your_slack_webhook
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_USERNAME=your_email@company.com
EMAIL_PASSWORD=your_app_password
ALERT_EMAIL=admin@company.com

# Node.js Environment
NODE_ENV=production
"""
        
        with open(output_path, 'w') as f:
            f.write(env_content)
        
        print(f"Environment file created: {output_path}")

def main():
    """Configure system for production deployment"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Configure CBS Parts System for production')
    parser.add_argument('--domain', required=True, help='Production domain (e.g., cbsparts.yourdomain.com)')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL/HTTPS')
    parser.add_argument('--template-dir', default='../templates', help='Templates directory')
    parser.add_argument('--output-env', default='../.env.production', help='Output environment file')
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ['CBS_ENVIRONMENT'] = 'production'
    os.environ['CBS_DOMAIN'] = args.domain
    os.environ['CBS_USE_SSL'] = str(args.ssl).lower()
    
    # Create production config
    config = ProductionConfig()
    
    print(f"🌍 Configuring CBS Parts System for production...")
    print(f"   Domain: {args.domain}")
    print(f"   SSL: {'Enabled' if args.ssl else 'Disabled'}")
    print(f"   Base URL: {config.get_base_url()}")
    
    # Update templates
    print(f"\n📝 Updating HTML templates...")
    config.update_html_templates(args.template_dir)
    
    # Create environment file
    print(f"\n⚙️ Creating environment configuration...")
    config.create_environment_file(args.output_env)
    
    # Show configuration summary
    print(f"\n✅ Production configuration complete!")
    print(f"\n🌐 Your URLs will be:")
    
    frontend_urls = config.get_frontend_urls()
    for name, url in frontend_urls.items():
        print(f"   • {name}: {url}")
    
    api_endpoints = config.get_api_endpoints()
    print(f"\n🔌 API Endpoints:")
    for name, url in api_endpoints.items():
        print(f"   • {name}: {url}")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Update {args.output_env} with your actual API tokens")
    print(f"   2. Deploy using: ./deployment/deploy_production.sh {args.domain}")
    print(f"   3. Configure DNS to point {args.domain} to your server")
    print(f"   4. Test all URLs after deployment")

if __name__ == "__main__":
    main()
