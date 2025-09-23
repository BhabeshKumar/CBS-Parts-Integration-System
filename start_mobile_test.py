#!/usr/bin/env python3
"""
CBS Parts System - Simple Mobile Test
"""

import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

# Set environment variables with your actual tokens
os.environ['SMARTSHEET_API_TOKEN'] = '7R7hgaXfL3J2pBrk757P73G4umegsLkWgRSgB'
os.environ['ORDERS_INTAKE_SHEET_ID'] = 'GxQx8H833G8rQrh7hX88fX4cJMVmqvFMRmq83c71'
os.environ['SALES_WORKS_ORDERS_SHEET_ID'] = 'G7Wm6pV3rQ6p8PpJg4WQ8R2MP29PPW25WrpjQ391'
os.environ['CBS_PARTS_SHEET_ID'] = '4695255724019588'
os.environ['CBS_DISCOUNTS_SHEET_ID'] = '8920011042148228'
os.environ['CBS_DIRECTOR_EMAIL'] = 'bhabesh.kumar@sheaney.ie'

# Add src to path
sys.path.append('src')

processes = []

def get_local_ip():
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line and '192.168' in line:
                return line.split()[1]
    except:
        pass
    return '192.168.0.11'

def cleanup():
    print("\n🛑 Stopping services...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
        except:
            try:
                p.kill()
            except:
                pass

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

def start_parts_api():
    print("🔧 Starting Parts API...")
    cmd = [sys.executable, 'scripts/start_cbs_parts_api.py']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(p)
    return p

def start_web_server():
    print("🌐 Starting Web Server...")
    cmd = [sys.executable, '-c', '''
import http.server
import socketserver
import os
os.chdir("templates")
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"OK")
            return
        super().do_GET()
with socketserver.TCPServer(("0.0.0.0", 8000), Handler) as httpd:
    httpd.serve_forever()
''']
    p = subprocess.Popen(cmd)
    processes.append(p)
    return p

def start_quotation_generator():
    print("📄 Starting Quotation Generator...")
    cmd = ['npm', 'run', 'dev', '--', '--host', '0.0.0.0']
    p = subprocess.Popen(cmd, cwd='cbs_pdf_generator')
    processes.append(p)
    return p

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    local_ip = get_local_ip()
    
    print("�� CBS Parts System - Mobile Test")
    print("=" * 40)
    print(f"📱 Local IP: {local_ip}")
    print("=" * 40)
    
    # Start services
    start_parts_api()
    time.sleep(3)
    
    start_web_server()
    time.sleep(2)
    
    start_quotation_generator()
    time.sleep(8)
    
    print("\n🎉 Services Started!")
    print("=" * 50)
    print("📱 Test these URLs on your mobile:")
    print("=" * 50)
    print(f"🔗 Customer Form:")
    print(f"   http://{local_ip}:8000/enhanced_order_form.html")
    print(f"🔗 Parts Review:")
    print(f"   http://{local_ip}:8000/parts_review_interface.html")
    print(f"🔗 Parts Search API:")
    print(f"   http://{local_ip}:8002/api/parts/search?q=mixer")
    print(f"🔗 Quotation Generator:")
    print(f"   http://{local_ip}:5173")
    print("=" * 50)
    print("📋 Instructions:")
    print("1. Connect mobile to same WiFi")
    print("2. Open browser on mobile")
    print("3. Try the URLs above")
    print("4. Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(30)
            print(f"🔄 Services running on {local_ip}...")
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
