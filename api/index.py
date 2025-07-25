"""Minimal Vercel handler for Tilts platform."""
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        # Serve main page
        if path == '/' or path == '/index.html':
            self.serve_file('index-rams.html', 'text/html')
            
        # Serve static files
        elif path.startswith('/static/'):
            filename = path[8:]  # Remove /static/ prefix
            self.serve_static_file(filename)
            
        # API endpoints
        elif path == '/health':
            self.send_json({"status": "healthy", "service": "tilts"})
            
        elif path == '/api/leaderboard':
            self.send_json({
                "entries": [
                    {
                        "model_name": "gpt-4",
                        "games_played": 250,
                        "win_rate": 0.85,
                        "avg_moves": 45,
                        "valid_move_rate": 0.98,
                        "mine_identification_precision": 0.92,
                        "mine_identification_recall": 0.88,
                        "coverage_ratio": 0.75,
                        "reasoning_score": 0.90,
                        "composite_score": 0.86,
                        "last_updated": "2024-07-25T12:00:00Z"
                    },
                    {
                        "model_name": "claude-3-opus", 
                        "games_played": 200,
                        "win_rate": 0.82,
                        "avg_moves": 48,
                        "valid_move_rate": 0.97,
                        "mine_identification_precision": 0.90,
                        "mine_identification_recall": 0.85,
                        "coverage_ratio": 0.73,
                        "reasoning_score": 0.88,
                        "composite_score": 0.83,
                        "last_updated": "2024-07-25T11:00:00Z"
                    }
                ]
            })
            
        elif path == '/api/overview/stats':
            self.send_json({
                "total_games": 1000,
                "total_models": 5,
                "best_model": "gpt-4",
                "best_win_rate": 0.85
            })
            
        elif path == '/api/sessions':
            self.send_json({"sessions": []})
            
        elif path == '/api/games/active':
            self.send_json({"games": []})
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        if path == '/api/play':
            self.send_json({
                "job_id": "demo-job-123",
                "status": "started",
                "message": "Demo mode - evaluation started"
            })
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def serve_file(self, filename, content_type):
        base_path = Path(__file__).parent.parent
        file_path = base_path / 'serverless-migration' / 'src' / 'api' / 'static' / filename
        
        if file_path.exists():
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def serve_static_file(self, filename):
        # Determine content type
        content_type = 'text/plain'
        if filename.endswith('.css'):
            content_type = 'text/css'
        elif filename.endswith('.js'):
            content_type = 'application/javascript'
        elif filename.endswith('.html'):
            content_type = 'text/html'
        elif filename.endswith('.svg'):
            content_type = 'image/svg+xml'
        elif filename.endswith('.png'):
            content_type = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            content_type = 'image/jpeg'
        
        self.serve_file(filename, content_type)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())