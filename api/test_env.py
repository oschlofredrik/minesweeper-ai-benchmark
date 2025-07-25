"""Test environment variables and API keys."""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get API keys
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        response = {
            "openai_key": {
                "exists": bool(openai_key),
                "length": len(openai_key),
                "prefix": openai_key[:10] if openai_key else "N/A",
                "suffix": openai_key[-4:] if openai_key else "N/A",
                "has_whitespace": openai_key != openai_key.strip() if openai_key else False,
                "char_codes_first_10": [ord(c) for c in openai_key[:10]] if openai_key else []
            },
            "anthropic_key": {
                "exists": bool(anthropic_key),
                "length": len(anthropic_key),
                "prefix": anthropic_key[:10] if anthropic_key else "N/A",
                "suffix": anthropic_key[-4:] if anthropic_key else "N/A"
            }
        }
        
        # Test API call
        if openai_key:
            test_url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {openai_key}"}
            
            try:
                req = urllib.request.Request(test_url, headers=headers)
                with urllib.request.urlopen(req) as resp:
                    response["openai_test"] = "SUCCESS"
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                response["openai_test"] = f"FAILED: {e.code}"
                response["error_details"] = error_body[:200]
            except Exception as e:
                response["openai_test"] = f"ERROR: {str(e)}"
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())