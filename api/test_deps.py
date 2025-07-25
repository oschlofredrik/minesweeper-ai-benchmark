"""Test if dependencies are installed."""
from http.server import BaseHTTPRequestHandler
import json
import sys
import subprocess

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # List installed packages
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True)
            packages = result.stdout
        except:
            packages = "Could not list packages"
        
        # Check specific imports
        imports = {}
        for module in ['openai', 'anthropic', 'httpx', 'supabase']:
            try:
                __import__(module)
                imports[module] = "✓ Installed"
            except ImportError:
                imports[module] = "✗ Not found"
        
        response = {
            "python_version": sys.version,
            "python_path": sys.path,
            "imports": imports,
            "pip_list": packages
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())