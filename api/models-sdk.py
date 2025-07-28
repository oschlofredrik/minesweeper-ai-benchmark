"""API endpoint to get available models from Vercel AI SDK configuration."""
from http.server import BaseHTTPRequestHandler
import json
import os

# Model configurations matching the TypeScript SDK
MODEL_CONFIGS = {
    "openai": {
        "gpt-4-turbo-preview": {"name": "GPT-4 Turbo Preview", "supportsTools": True},
        "gpt-4": {"name": "GPT-4", "supportsTools": True},
        "gpt-4o": {"name": "GPT-4o", "supportsTools": True},
        "gpt-4o-mini": {"name": "GPT-4o Mini", "supportsTools": True},
        "gpt-3.5-turbo": {"name": "GPT-3.5 Turbo", "supportsTools": True},
        "o1-preview": {"name": "o1 Preview (Reasoning)", "supportsTools": False},
        "o1-mini": {"name": "o1 Mini (Reasoning)", "supportsTools": False},
        "o3-mini": {"name": "o3 Mini", "supportsTools": True}
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"name": "Claude 3.5 Sonnet", "supportsTools": True},
        "claude-3-opus-20240229": {"name": "Claude 3 Opus", "supportsTools": True},
        "claude-3-sonnet-20240229": {"name": "Claude 3 Sonnet", "supportsTools": True},
        "claude-3-haiku-20240307": {"name": "Claude 3 Haiku", "supportsTools": True},
        "claude-4-sonnet-20250514": {"name": "Claude 4 Sonnet", "supportsTools": True}
    }
}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        try:
            # Parse provider from path: /api/models-sdk/{provider}
            path_parts = self.path.strip('/').split('/')
            
            if len(path_parts) == 3 and path_parts[0] == 'api' and path_parts[1] == 'models-sdk':
                provider = path_parts[2]
                
                if provider in MODEL_CONFIGS:
                    # Check if API key is configured
                    api_key_var = f"{provider.upper()}_API_KEY"
                    has_api_key = bool(os.environ.get(api_key_var))
                    
                    response = {
                        "provider": provider,
                        "models": MODEL_CONFIGS[provider],
                        "has_api_key": has_api_key
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_error(404, f"Unknown provider: {provider}")
            
            elif len(path_parts) == 2 and path_parts[0] == 'api' and path_parts[1] == 'models-sdk':
                # Return all providers and their models
                response = {
                    "providers": list(MODEL_CONFIGS.keys()),
                    "models": MODEL_CONFIGS
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_error(404, "Not found")
                
        except Exception as e:
            print(f"[models-sdk] Error: {str(e)}")
            self.send_error(500, str(e))