"""Test OpenAI import directly."""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        response = {
            "test": "OpenAI import test",
            "status": "failed",
            "error": None
        }
        
        try:
            import openai
            response["status"] = "success"
            response["version"] = openai.__version__
            response["message"] = "OpenAI imported successfully"
        except ImportError as e:
            response["error"] = str(e)
            response["message"] = "Failed to import openai"
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())