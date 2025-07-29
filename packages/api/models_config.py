"""Models configuration endpoint for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import os

# Import model configurations
try:
    from ai_models import MODEL_CONFIGS, get_available_models
except ImportError:
    # Fallback configurations if import fails
    MODEL_CONFIGS = {
        "openai": {
            "models": {
                "gpt-4-turbo-preview": {"name": "GPT-4 Turbo Preview", "supports_functions": True, "supportsTools": True},
                "gpt-4": {"name": "GPT-4", "supports_functions": True, "supportsTools": True},
                "gpt-4o": {"name": "GPT-4o", "supports_functions": True, "supportsTools": True},
                "gpt-4o-mini": {"name": "GPT-4o Mini", "supports_functions": True, "supportsTools": True},
                "gpt-3.5-turbo": {"name": "GPT-3.5 Turbo", "supports_functions": True, "supportsTools": True},
                "o1-preview": {"name": "o1 Preview (Reasoning)", "supports_functions": False, "reasoning_model": True, "supportsTools": False},
                "o1-mini": {"name": "o1 Mini (Reasoning)", "supports_functions": False, "reasoning_model": True, "supportsTools": False},
                "o3-mini": {"name": "o3 Mini", "supports_functions": True, "supportsTools": True}
            }
        },
        "anthropic": {
            "models": {
                "claude-3-5-sonnet-20241022": {"name": "Claude 3.5 Sonnet", "supports_functions": True, "supportsTools": True},
                "claude-3-opus-20240229": {"name": "Claude 3 Opus", "supports_functions": True, "supportsTools": True},
                "claude-3-sonnet-20240229": {"name": "Claude 3 Sonnet", "supports_functions": True, "supportsTools": True},
                "claude-3-haiku-20240307": {"name": "Claude 3 Haiku", "supports_functions": True, "supportsTools": True},
                "claude-4-sonnet-20250514": {"name": "Claude 4 Sonnet", "supports_functions": True, "supportsTools": True}
            }
        }
    }
    
    def get_available_models(provider):
        return MODEL_CONFIGS.get(provider, {}).get("models", {})


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[MODELS_CONFIG] Received GET request: {self.path}")
        path_parts = self.path.split('/')
        print(f"[MODELS_CONFIG] Path parts: {path_parts}")
        
        if len(path_parts) >= 3 and path_parts[2] == 'models':
            if len(path_parts) == 3:
                # List all providers and their models
                result = {
                    "providers": {}
                }
                
                for provider, config in MODEL_CONFIGS.items():
                    result["providers"][provider] = {
                        "name": provider.capitalize(),
                        "models": list(config["models"].keys()),
                        "requires_api_key": f"{provider.upper()}_API_KEY"
                    }
                
                self.send_json_response(result)
                
            elif len(path_parts) == 4:
                # Get models for specific provider
                provider = path_parts[3]
                models = get_available_models(provider)
                
                if models:
                    # Check if API key is configured
                    api_key_env = f"{provider.upper()}_API_KEY"
                    has_api_key = bool(os.environ.get(api_key_env))
                    
                    result = {
                        "provider": provider,
                        "has_api_key": has_api_key,
                        "models": {}
                    }
                    
                    for model_id, model_info in models.items():
                        result["models"][model_id] = {
                            "id": model_id,
                            "name": model_info.get("name", model_id),
                            "supports_functions": model_info.get("supports_functions", True),
                            "supports_vision": model_info.get("supports_vision", False),
                            "max_tokens": model_info.get("max_tokens", 4096),
                            "reasoning_model": model_info.get("reasoning_model", False)
                        }
                    
                    self.send_json_response(result)
                else:
                    print(f"[MODELS_CONFIG] Unknown provider: {provider}")
                    self.send_error(404, f"Unknown provider: {provider}")
                    
        else:
            print(f"[MODELS_CONFIG] Invalid path format: {self.path}")
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())