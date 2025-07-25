"""Host competition wizard endpoint."""
from http.server import BaseHTTPRequestHandler
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve the host wizard HTML
        base_path = Path(__file__).parent.parent
        
        # Try to find the host.html file
        possible_paths = [
            base_path / 'serverless-migration' / 'src' / 'api' / 'static' / 'host.html',
            base_path / 'src' / 'api' / 'static' / 'host.html',
            base_path / 'vercel' / 'static' / 'host.html',
            '/tmp/host_backup.html'  # The backup we created
        ]
        
        for file_path in possible_paths:
            file_path = Path(file_path)
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        
        # If no host.html found, redirect to compete as fallback
        self.send_response(301)
        self.send_header('Location', '/compete')
        self.end_headers()