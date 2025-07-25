"""Benchmark page endpoint"""
from http.server import BaseHTTPRequestHandler
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve the benchmark page
        page_path = Path(__file__).parent / 'pages' / 'benchmark.html'
        
        if page_path.exists():
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open(page_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Benchmark page not found")