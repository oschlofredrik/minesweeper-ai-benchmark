"""Status endpoint for SDK evaluations."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_optimized import list_games, HAS_SUPABASE

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get evaluation status."""
        # Extract evaluation ID from path
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) < 3:
            self.send_error(400, "Invalid path")
            return
        
        evaluation_id = path_parts[2]  # /api/evaluation/{id}/status
        
        try:
            if HAS_SUPABASE:
                # Get games for this evaluation
                games, total = list_games(job_id=evaluation_id, limit=100)
                
                # Calculate statistics
                completed = [g for g in games if g['status'] in ['won', 'lost', 'error']]
                in_progress = [g for g in games if g['status'] in ['running', 'in_progress']]
                
                response = {
                    "evaluation_id": evaluation_id,
                    "status": "completed" if len(completed) == total else 
                             "running" if len(in_progress) > 0 else "queued",
                    "progress": len(completed) / total if total > 0 else 0,
                    "games_total": total,
                    "games_completed": len(completed),
                    "games": games[:10]  # Return first 10
                }
            else:
                # Fallback response
                response = {
                    "evaluation_id": evaluation_id,
                    "status": "running",
                    "progress": 0.5,
                    "games_total": 1,
                    "games_completed": 0
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()