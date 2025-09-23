#!/usr/bin/env python3
"""
CBS Parts System - Local Mobile Test
Start services accessible from mobile devices on local network
"""

import os
import sys
import time
import subprocess
import signal
import requests
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Set environment variables
os.environ['SMARTSHEET_API_TOKEN'] = '7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB'
os.environ['ORDERS_INTAKE_SHEET_ID'] = 'GxQx8H833G8rQrh7hX88fX4cJMVmqvFMRmq83c71'
os.environ['SALES_WORKS_ORDERS_SHEET_ID'] = 'G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391'
os.environ['CBS_PARTS_SHEET_ID'] = '4695255724019588'
os.environ['CBS_DISCOUNTS_SHEET_ID'] = '8920011042148228'
os.environ['CBS_DIRECTOR_EMAIL'] = 'bhabesh.kumar@sheaney.ie'

# Global list to track processes
processes = []

def get_local_ip():
    """Get local IP address"""
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'inet ' in line and '127.0.0.1' not in line and 'inet 192.168' in line:
                return line.split()[1]
    except:
        pass
    return '192.168.0.11'  # fallback

def cleanup_ports():
    """Kill any existing services on our ports"""
    ports = [8002, 8003, 8000, 5173]
    for port in ports:
        try:
            subprocess.run(f'lsof -ti:{port} | xargs kill -9', shell=True, capture_output=True)
        except:
            pass

def start_parts_api():
    """Start Parts API"""
    print("🔧 Starting Parts API (Port 8002)...")
    
    cmd = [
        sys.executable, '-c',
        '''
import sys, os
sys.path.append("src")
import uvicorn
from api.cbs_parts_api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
'''
    ]
    
    process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
    processes.append(process)
    return process

def start_form_api():
    """Start Form API"""
    print("📋 Starting Form API (Port 8003)...")
    
    cmd = [
        sys.executable, '-c',
        '''
import sys, os
sys.path.append("src")
import uvicorn
from api.smartsheet_form_api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
'''
    ]
    
    process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
    processes.append(process)
    return process

def start_web_server():
    """Start Web Server"""
    print("🌐 Starting Web Server (Port 8000)...")
    
    cmd = [
        sys.executable, '-c',
        '''
import http.server
import socketserver
import os

os.chdir("templates")

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>CBS Web Server OK</h1>")
            return
        super().do_GET()

with socketserver.TCPServer(("0.0.0.0", 8000), MyHTTPRequestHandler) as httpd:
    print("Web server running on port 8000")
    httpd.serve_forever()
'''
    ]
    
    process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
    processes.append(process)
    return process

def start_quotation_generator():
    """Start Quotation Generator"""
    print("📄 Starting Quotation Generator (Port 5173)...")
    
    cmd = ['npm', 'run', 'dev', '--', '--host', '0.0.0.0', '--port', '5173']
    
    process = subprocess.Popen(cmd, cwd=Path(__file__).parent / 'cbs_pdf_generator')
    processes.append(process)
    return process

def check_service_health(url):
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down services...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
    sys.exit(0)

def main():
    """Main function"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get local IP
    local_ip = get_local_ip()
    
    print("🚀 CBS Parts System - Mobile Test Deployment")
    print("=" * 50)
    print(f"📱 Your Local IP: {local_ip}")
    print("=" * 50)
    
    # Clean up any existing services
    cleanup_ports()
    time.sleep(2)
    
    # Start all services
    print("\n🔄 Starting all services...")
    
    # Start services in order
    start_parts_api()
    time.sleep(3)
    
    start_form_api()
    time.sleep(3)
    
    start_web_server()
    time.sleep(3)
    
    start_quotation_generator()
    time.sleep(5)
    
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(10)
    
    # Check service health
    print("\n🔍 Checking service health...")
    
    services = [
        ("Parts API", f"http://{local_ip}:8002/api/health"),
        ("Form API", f"http://{local_ip}:8003/api/health"),
        ("Web Server", f"http://{local_ip}:8000/health"),
        ("Quotation Generator", f"http://{local_ip}:5173")
    ]
    
    healthy_services = 0
    for name, url in services:
        if check_service_health(url):
            print(f"   ✅ {name}: {url}")
            healthy_services += 1
        else:
            print(f"   ❌ {name}: {url}")
    
    print(f"\n📊 {healthy_services}/{len(services)} services are healthy")
    
    if healthy_services >= 3:  # At least 3 services working
        print("\n🎉 System is ready for mobile testing!")
        print("=" * 60)
        print("📱 Mobile URLs (use these on your phone):")
        print("=" * 60)
        
        print(f"\n🔗 Customer Order Form:")
        print(f"   http://{local_ip}:8000/templates/enhanced_order_form.html")
        
        print(f"\n🔗 CBS Review Interface:")
        print(f"   http://{local_ip}:8000/templates/parts_review_interface.html")
        
        print(f"\n🔗 Parts Search API:")
        print(f"   http://{local_ip}:8002/api/parts/search?q=mixer")
        
        print(f"\n🔗 Quotation Generator:")
        print(f"   http://{local_ip}:5173")
        
        print("\n📋 Testing Instructions:")
        print("1. Connect your mobile to the same WiFi network")
        print("2. Open any browser on your mobile")
        print("3. Enter the URLs above")
        print("4. Test the customer order form")
        print("5. Test parts selection and search")
        
        print("\n⌨️  Press Ctrl+C to stop all services")
        print("=" * 60)
    else:
        print("\n❌ Not enough services are running. Check errors above.")
        signal_handler(None, None)
        return
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(60)
            print(f"🔄 Services running... (Local IP: {local_ip})")
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
