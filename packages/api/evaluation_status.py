"""Status endpoint for SDK evaluations."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Try to import database functions
try:
    from db_optimized import list_games, HAS_SUPABASE
except:
    HAS_SUPABASE = False
    def list_games(**kwargs):
        return [], 0

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get evaluation status."""
        try:
            # Extract evaluation ID from path
            path_parts = self.path.strip('/').split('/')
            if len(path_parts) < 3:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
                return
            
            evaluation_id = path_parts[2]  # /api/evaluation/{id}/status
            
            # Try to get real game data
            if HAS_SUPABASE:
                try:
                    # Get games for this evaluation
                    games, total = list_games(job_id=evaluation_id, limit=100)
                    
                    # Calculate statistics
                    completed = [g for g in games if g['status'] in ['won', 'lost', 'error']]
                    in_progress = [g for g in games if g['status'] in ['running', 'in_progress']]
                    queued = [g for g in games if g['status'] == 'queued']
                    
                    # Determine overall status
                    if len(completed) == total and total > 0:
                        status = "completed"
                    elif len(in_progress) > 0:
                        status = "running"
                    elif len(queued) > 0:
                        status = "queued"
                    else:
                        status = "unknown"
                    
                    response = {
                        "evaluation_id": evaluation_id,
                        "status": status,
                        "progress": len(completed) / total if total > 0 else 0,
                        "games_total": total,
                        "games_completed": len(completed),
                        "games_in_progress": len(in_progress),
                        "games_queued": len(queued),
                        "games": games[:10]  # Return first 10
                    }
                except Exception as e:
                    print(f"[Status] Database error: {e}")
                    # Fallback to mock data if database fails
                    response = {
                        "evaluation_id": evaluation_id,
                        "status": "running",
                        "progress": 0.5,
                        "games_total": 1,
                        "games_completed": 0,
                        "message": "Database unavailable, showing placeholder data"
                    }
            else:
                # No database - return mock data
                response = {
                    "evaluation_id": evaluation_id,
                    "status": "running",
                    "progress": 0.5,
                    "games_total": 1,
                    "games_completed": 0,
                    "message": "Database not configured, showing placeholder data"
                }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": f"Error in evaluation_status: {str(e)}",
                "type": type(e).__name__
            }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()