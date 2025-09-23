#!/usr/bin/env python3
"""
CBS Parts System - Production Startup Script
Starts all required services for the complete system.
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path

def signal_handler(sig, frame):
    print('\n🛑 Stopping CBS Parts System...')
    print('✅ All services stopped')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_production_system():
    """Start the complete CBS Parts production system."""
    
    print("🏭 CBS Parts System - Production Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Error: Please run this script from the CBS_Parts_System_Production directory")
        sys.exit(1)
    
    try:
        print("🔧 Starting system services...")
        
        # Start all backend services
        print("📊 Starting backend services...")
        backend_process = subprocess.Popen([
            sys.executable, "scripts/start_all_services.py"
        ])
        
        print("⏳ Waiting for services to initialize...")
        time.sleep(5)
        
        print("\n✅ CBS Parts System Started Successfully!")
        print("=" * 50)
        print("🌐 System URLs:")
        print("   • Customer Order Form: http://localhost:8000/templates/enhanced_order_form.html")
        print("   • CBS Review Interface: http://localhost:8000/templates/parts_review_interface.html?review_id=QUOTE_ID")
        print("   • Parts Database API: http://localhost:8002/docs")
        print("=" * 50)
        print("📋 Next Steps:")
        print("   1. Start quotation generator: cd cbs_pdf_generator && npm run dev")
        print("   2. Test customer order form")
        print("   3. Review orders in Smartsheet")
        print("=" * 50)
        print("Press Ctrl+C to stop all services")
        
        # Keep running
        backend_process.wait()
        
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_production_system()
