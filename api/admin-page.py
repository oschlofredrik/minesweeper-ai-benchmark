"""Admin page endpoint."""
from http.server import BaseHTTPRequestHandler
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve the admin HTML
        base_path = Path(__file__).parent.parent
        
        # Try to find the admin.html file
        possible_paths = [
            base_path / 'serverless-migration' / 'src' / 'api' / 'static' / 'admin.html',
            base_path / 'src' / 'api' / 'static' / 'admin.html',
            base_path / 'vercel' / 'static' / 'admin.html'
        ]
        
        for file_path in possible_paths:
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        
        # If no admin.html found, return 404
        self.send_error(404, "Admin page not found")