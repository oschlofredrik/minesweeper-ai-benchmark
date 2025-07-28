"""Supabase configuration endpoint."""
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Return Supabase configuration for frontend."""
        # Only return public values
        config = {
            "url": os.environ.get('SUPABASE_URL', ''),
            "anonKey": os.environ.get('SUPABASE_ANON_KEY', '')
        }
        
        # Check if configured
        if not config["url"] or not config["anonKey"]:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Supabase not configured"}).encode())
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(config).encode())