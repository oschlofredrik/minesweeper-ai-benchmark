"""Models API endpoint for fetching available AI models."""
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        path_parts = path.strip('/').split('/')
        
        if path == '/api/models':
            # Return available providers
            providers = []
            if os.environ.get('OPENAI_API_KEY'):
                providers.append('openai')
            if os.environ.get('ANTHROPIC_API_KEY'):
                providers.append('anthropic')
            
            self.send_json_response({
                'providers': providers
            })
            
        elif len(path_parts) == 3 and path_parts[0] == 'api' and path_parts[1] == 'models':
            # Return models for specific provider
            provider = path_parts[2]
            
            if provider == 'openai':
                models = {
                    'gpt-4': {
                        'name': 'GPT-4',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'gpt-4-turbo-preview': {
                        'name': 'GPT-4 Turbo',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'gpt-3.5-turbo': {
                        'name': 'GPT-3.5 Turbo',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'gpt-4o': {
                        'name': 'GPT-4o',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'gpt-4o-mini': {
                        'name': 'GPT-4o Mini',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'o1-preview': {
                        'name': 'o1 Preview',
                        'supports_functions': False,
                        'reasoning_model': True
                    },
                    'o1-mini': {
                        'name': 'o1 Mini',
                        'supports_functions': False,
                        'reasoning_model': True
                    }
                }
                
                self.send_json_response({
                    'models': models,
                    'has_api_key': bool(os.environ.get('OPENAI_API_KEY'))
                })
                
            elif provider == 'anthropic':
                models = {
                    'claude-3-5-sonnet-20241022': {
                        'name': 'Claude 3.5 Sonnet',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'claude-3-opus-20240229': {
                        'name': 'Claude 3 Opus',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'claude-3-sonnet-20240229': {
                        'name': 'Claude 3 Sonnet',
                        'supports_functions': True,
                        'reasoning_model': False
                    },
                    'claude-3-haiku-20240307': {
                        'name': 'Claude 3 Haiku',
                        'supports_functions': True,
                        'reasoning_model': False
                    }
                }
                
                self.send_json_response({
                    'models': models,
                    'has_api_key': bool(os.environ.get('ANTHROPIC_API_KEY'))
                })
                
            else:
                self.send_error(404, 'Provider not found')
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())