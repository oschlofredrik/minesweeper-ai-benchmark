"""Direct synchronous test of OpenAI API - no threading."""
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test OpenAI API directly."""
        try:
            api_key = os.environ.get('OPENAI_API_KEY', '')
            
            response_data = {
                "has_openai_key": bool(api_key),
                "key_prefix": api_key[:10] + "..." if api_key else "NO_KEY",
                "env_vars": sorted([k for k in os.environ.keys() if 'OPENAI' in k or 'SUPABASE' in k])
            }
            
            if api_key:
                # Try a direct API call
                import urllib.request
                import urllib.error
                
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Say 'API works!'"}],
                    "max_tokens": 10
                }
                
                req = urllib.request.Request(url, 
                    data=json.dumps(payload).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        result = json.loads(resp.read().decode('utf-8'))
                        response_data["api_call_success"] = True
                        response_data["api_response"] = result['choices'][0]['message']['content']
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode('utf-8')
                    response_data["api_call_success"] = False
                    response_data["api_error"] = f"{e.code}: {error_body}"
                except Exception as e:
                    response_data["api_call_success"] = False
                    response_data["api_error"] = str(e)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()