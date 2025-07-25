"""Authentication and API key validation for Vercel."""
import os
import json
from http.server import BaseHTTPRequestHandler
from typing import Optional, Dict, Any
from .lib import supabase_db as db

# Environment variables for API keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', '')

def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are configured."""
    return {
        'openai': bool(OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-')),
        'anthropic': bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY.startswith('sk-ant-')),
        'admin': bool(ADMIN_API_KEY)
    }

def check_model_access(model_name: str, provider: str) -> bool:
    """Check if we have API access for the requested model."""
    api_status = validate_api_keys()
    
    if provider == 'openai':
        return api_status['openai']
    elif provider == 'anthropic':
        return api_status['anthropic']
    
    return False

def require_admin(handler: BaseHTTPRequestHandler) -> bool:
    """Check if request has valid admin authorization."""
    if not ADMIN_API_KEY:
        # No admin key configured, allow access in development
        return True
    
    # Check Authorization header
    auth_header = handler.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return token == ADMIN_API_KEY
    
    # Check X-API-Key header
    api_key = handler.headers.get('X-API-Key', '')
    return api_key == ADMIN_API_KEY

class handler(BaseHTTPRequestHandler):
    """API key validation endpoint."""
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/auth/status':
            self.handle_auth_status()
        elif path == '/api/auth/validate':
            self.handle_validate_keys()
        else:
            self.send_error(404)
    
    def handle_auth_status(self):
        """Get current authentication status."""
        status = validate_api_keys()
        
        # Don't expose actual keys, just status
        response = {
            'configured': {
                'openai': status['openai'],
                'anthropic': status['anthropic'],
                'admin': status['admin']
            },
            'models_available': {
                'openai': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] if status['openai'] else [],
                'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] if status['anthropic'] else []
            }
        }
        
        self.send_json_response(response)
    
    def handle_validate_keys(self):
        """Validate API keys by making test requests."""
        results = {}
        
        # Test OpenAI
        if OPENAI_API_KEY:
            try:
                import httpx
                response = httpx.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
                    timeout=5.0
                )
                results['openai'] = {
                    'valid': response.status_code == 200,
                    'status_code': response.status_code
                }
            except Exception as e:
                results['openai'] = {
                    'valid': False,
                    'error': str(e)
                }
        else:
            results['openai'] = {'valid': False, 'error': 'Not configured'}
        
        # Test Anthropic
        if ANTHROPIC_API_KEY:
            try:
                import httpx
                response = httpx.get(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': ANTHROPIC_API_KEY,
                        'anthropic-version': '2023-06-01'
                    },
                    timeout=5.0
                )
                # Anthropic returns 401 for GET requests, which is expected
                results['anthropic'] = {
                    'valid': response.status_code in [401, 405],
                    'status_code': response.status_code
                }
            except Exception as e:
                results['anthropic'] = {
                    'valid': False,
                    'error': str(e)
                }
        else:
            results['anthropic'] = {'valid': False, 'error': 'Not configured'}
        
        self.send_json_response({'validation_results': results})
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())