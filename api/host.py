"""Host competition wizard endpoint."""
from http.server import BaseHTTPRequestHandler
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve the host wizard HTML
        # In Vercel, __file__ points to the deployed location
        static_path = Path(__file__).parent / 'static' / 'host.html'
        
        if static_path.exists():
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(static_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            # If file not found, show error
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Host page not found</h1><p>Looking for: {static_path}</p>".encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()