"""Bridge endpoint to use Vercel AI SDK for evaluations."""
from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Start an AI SDK evaluation."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract evaluation parameters
            game_type = data.get('game', 'minesweeper')
            provider = data.get('provider', 'openai')
            model_name = data.get('model', 'gpt-4')
            num_games = data.get('num_games', 10)
            difficulty = data.get('difficulty', 'medium')
            use_sdk = data.get('use_sdk', True)
            
            # Check for required environment variables
            if provider == 'openai' and not os.environ.get('OPENAI_API_KEY'):
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "OPENAI_API_KEY environment variable not set"
                }).encode())
                return
            elif provider == 'anthropic' and not os.environ.get('ANTHROPIC_API_KEY'):
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "ANTHROPIC_API_KEY environment variable not set"
                }).encode())
                return
            
            if not use_sdk:
                # Fallback to Python implementation
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "This endpoint requires use_sdk=true"
                }).encode())
                return
            
            # Create evaluation ID
            evaluation_id = str(uuid.uuid4())
            
            # For now, return a simple response without complex processing
            # The actual game execution would need to be implemented separately
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "evaluation_id": evaluation_id,
                "status": "started",
                "message": "SDK evaluation started (simplified version)",
                "config": {
                    "game_type": game_type,
                    "provider": provider,
                    "model_name": model_name,
                    "num_games": num_games,
                    "difficulty": difficulty
                },
                "endpoint": f"/api/evaluation/{evaluation_id}",
                "note": "This is a simplified endpoint - full game execution not implemented"
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": f"Error in evaluate-sdk: {str(e)}",
                "type": type(e).__name__
            }).encode())
    
    def do_GET(self):
        """Check SDK availability."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "sdk_available": True,
            "version": "2.0.0-simplified",
            "supported_games": ["minesweeper", "risk"],
            "supported_providers": ["openai", "anthropic"],
            "note": "This is a simplified version without game execution"
        }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()