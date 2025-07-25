"""Minimal Vercel handler for Tilts platform."""
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        # Serve overview page for root
        if path == '/' or path == '/index.html':
            self.serve_page('overview.html')
            
        # Serve other pages
        elif path == '/leaderboard':
            self.serve_page('leaderboard.html')
        elif path == '/compete':
            self.serve_page('compete.html')
        elif path == '/compete-wizard':
            self.serve_page('compete-wizard.html')
        elif path == '/benchmark':
            self.serve_page('benchmark.html')
        elif path == '/host':
            self.serve_page('host.html')
        elif path == '/admin':
            self.serve_page('admin.html')
        elif path == '/summary':
            self.serve_page('summary.html')
        elif path == '/replay':
            self.serve_page('replay.html')
        elif path == '/test-game':
            self.serve_page('test-game.html')
        elif path == '/sessions':
            # Redirect to compete page which shows active sessions
            self.send_response(302)
            self.send_header('Location', '/compete')
            self.end_headers()
        elif path == '/prompts':
            # Prompts page doesn't exist yet, redirect to overview
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        # Serve static files
        elif path.startswith('/static/'):
            filename = path[8:]  # Remove /static/ prefix
            self.serve_static_file(filename)
            
        # API endpoints
        elif path == '/health':
            self.send_json({"status": "healthy", "service": "tilts"})
            
        # Route to specific endpoint handlers based on path
        elif path.startswith('/api/'):
            # Temporary: Return demo data without complex imports
            if path == '/api/leaderboard':
                # This is now handled by leaderboard_simple.py
                self.send_error(404)
                
            elif path == '/api/overview/stats':
                # Return demo stats
                self.send_json({
                    "total_games": 25,
                    "total_models": 3,
                    "best_model": "gpt-4",
                    "best_win_rate": 0.7
                })
                
            elif path == '/api/games/active':
                # Return empty active games
                self.send_json({"games": []})
                
            elif path == '/api/stats':
                # Return demo stats
                self.send_json({
                    "total_sessions": 5,
                    "active_sessions": 1,
                    "total_players": 12
                })
                
            else:
                # For other API endpoints, return 404 (they should have their own handlers)
                self.send_error(404)
                
        elif path == '/robots.txt':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"User-agent: *\nAllow: /")
            
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
    
    def serve_page(self, filename):
        """Serve HTML pages from the pages directory."""
        page_path = Path(__file__).parent / 'pages' / filename
        
        if page_path.exists():
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open(page_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"Page not found: {filename}")
    
    def serve_file(self, filename, content_type):
        """Serve static files."""
        static_path = Path(__file__).parent / 'static' / filename
        
        if static_path.exists():
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            
            with open(static_path, 'rb') as f:
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