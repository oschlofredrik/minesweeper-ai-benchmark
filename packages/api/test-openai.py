"""Direct OpenAI test endpoint to debug API calls."""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test OpenAI API directly."""
        try:
            api_key = os.environ.get('OPENAI_API_KEY', '')
            
            if not api_key:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "OPENAI_API_KEY not set",
                    "env_vars": list(os.environ.keys())
                }).encode())
                return
            
            # Make a simple test call to OpenAI
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello from Tilts!' in exactly 5 words."}
                ],
                "temperature": 0.7,
                "max_tokens": 50
            }
            
            print(f"[TEST] Making OpenAI API call with key: {api_key[:10]}...")
            
            req = urllib.request.Request(url, 
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"[TEST] OpenAI response received: {result}")
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "response": result,
                        "message": result['choices'][0]['message']['content'],
                        "api_key_prefix": api_key[:10] + "..."
                    }).encode())
                    
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"[TEST] OpenAI API error: {e.code} - {error_body}")
                
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": f"OpenAI API error: {e.code}",
                    "details": error_body,
                    "api_key_prefix": api_key[:10] + "..."
                }).encode())
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[TEST] Error: {str(e)}")
            print(f"[TEST] Traceback: {error_trace}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "traceback": error_trace
            }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()