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
            
        # Serve static files
        elif path.startswith('/static/'):
            filename = path[8:]  # Remove /static/ prefix
            self.serve_static_file(filename)
            
        # API endpoints
        elif path == '/health':
            self.send_json({"status": "healthy", "service": "tilts"})
            
        # Route to specific endpoint handlers based on path
        elif path.startswith('/api/'):
            # Import db module to ensure it's initialized
            from . import supabase_db as db
            
            # Use dynamic imports to get leaderboard from db
            if path == '/api/leaderboard':
                leaderboard = db.get_leaderboard()
                self.send_json({"entries": leaderboard})
                
            elif path == '/api/overview/stats':
                sessions = db.list_sessions()
                games = db.list_games()
                leaderboard = db.get_leaderboard()
                best_model = leaderboard[0] if leaderboard else None
                
                self.send_json({
                    "total_games": len(games),
                    "total_models": len(leaderboard),
                    "best_model": best_model.get("model_name") if best_model else "N/A",
                    "best_win_rate": best_model.get("win_rate", 0) if best_model else 0
                })
                
            elif path == '/api/games/active':
                games = db.list_games()
                active_games = [g for g in games if g.get("status") == "in_progress"]
                self.send_json({"games": active_games})
                
            elif path == '/api/stats':
                sessions = db.list_sessions()
                active_sessions = db.list_sessions(active_only=True)
                
                self.send_json({
                    "total_sessions": len(sessions),
                    "active_sessions": len(active_sessions),
                    "total_players": sum(len(s.get("players", [])) for s in sessions)
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