#!/usr/bin/env python3
import http.server
import socketserver
import os
import socket

# Change to templates directory (works both locally and in Docker)
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
templates_dir = os.path.join(project_root, 'templates')
os.chdir(templates_dir)

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'CBS Web Server OK - Mobile Ready')
            return
        
        # Serve enhanced_smartsheet_review.html as the default page
        if self.path == '/' or self.path == '/index.html':
            self.path = '/enhanced_smartsheet_review.html'
        
        super().do_GET()

class MobileCompatibleTCPServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        super().server_bind()

if __name__ == "__main__":
    with MobileCompatibleTCPServer(('0.0.0.0', 8000), Handler) as httpd:
        print("🌐 Starting CBS Web Server on port 8000...")
        httpd.serve_forever()
