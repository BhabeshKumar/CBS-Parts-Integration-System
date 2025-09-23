#!/usr/bin/env python3
"""
Simple HTTP server to serve the review interface
"""

import http.server
import socketserver
import os
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

PORT = 8000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(project_root), **kwargs)

try:
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🌐 HTTP Server running at http://localhost:{PORT}")
        print(f"📋 Order Form: http://localhost:{PORT}/templates/enhanced_order_form.html")
        print(f"🔍 Review Interface: http://localhost:{PORT}/templates/parts_review_interface.html")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Server stopped")
except Exception as e:
    print(f"❌ Error starting server: {e}")
