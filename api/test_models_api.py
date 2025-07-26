"""Test the models API endpoint."""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Simple test response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "test": "Models API test endpoint",
            "status": "working",
            "path": self.path
        }
        
        self.wfile.write(json.dumps(response).encode())