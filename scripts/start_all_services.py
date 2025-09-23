#!/usr/bin/env python3
"""
Start all CBS services together
"""

import subprocess
import time
import signal
import sys
from pathlib import Path

# Change to project directory
project_root = Path(__file__).parent.parent
print(f"Starting services from: {project_root}")

# Store process IDs for cleanup
processes = []

def signal_handler(sig, frame):
    print('\n🛑 Stopping all services...')
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    print('✅ All services stopped')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    print("🚀 Starting CBS Services...")
    
    # Start Parts API (port 8002)
    print("📦 Starting Parts API...")
    parts_api = subprocess.Popen([
        sys.executable, "scripts/start_cbs_parts_api.py"
    ], cwd=project_root)
    processes.append(parts_api)
    time.sleep(3)
    
    # Start Form API (port 8003)
    print("📋 Starting Form Submission API...")
    form_api = subprocess.Popen([
        sys.executable, "src/api/smartsheet_form_api.py"
    ], cwd=project_root)
    processes.append(form_api)
    time.sleep(2)
    
    # Start Review Server (port 8000)
    print("🔍 Starting Review Interface Server...")
    review_server = subprocess.Popen([
        sys.executable, "scripts/start_review_server.py"
    ], cwd=project_root)
    processes.append(review_server)
    time.sleep(2)
    
    print("\n✅ All services started!")
    print("=" * 50)
    print("🌐 Available Services:")
    print("   • Parts API: http://localhost:8002")
    print("   • Parts API Docs: http://localhost:8002/docs")
    print("   • Form API: http://localhost:8003")
    print("   • Form API Health: http://localhost:8003/api/health")
    print("   • Review Server: http://localhost:8000")
    print("=" * 50)
    print("📋 Customer Interface:")
    print(f"   • Order Form: http://localhost:8000/templates/enhanced_order_form.html")
    print("=" * 50)
    print("🔍 CBS Management Interface:")
    print(f"   • Parts Review: http://localhost:8000/templates/parts_review_interface.html?review_id=QUOTE_ID")
    print(f"   • Parts Database: http://localhost:8000/templates/parts_selection_interface.html")
    print("=" * 50)
    print("📄 Quotation Generator:")
    print("   • To start quotation generator: python3 scripts/start_quotation_generator.py")
    print("   • Quotation Generator URL: http://localhost:5173")
    print("=" * 50)
    print("Press Ctrl+C to stop all services")
    
    # Keep running
    while True:
        time.sleep(1)
        
except Exception as e:
    print(f"❌ Error starting services: {e}")
    signal_handler(None, None)
