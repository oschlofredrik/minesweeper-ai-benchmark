"""Test database endpoint."""
from http.server import BaseHTTPRequestHandler
import json
import simple_db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Test getting leaderboard
            leaderboard = simple_db.get_leaderboard()
            
            response = {
                "status": "ok",
                "has_supabase": simple_db.HAS_SUPABASE,
                "leaderboard_count": len(leaderboard),
                "sample_entry": leaderboard[0] if leaderboard else None
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": str(e), "type": type(e).__name__}
            self.wfile.write(json.dumps(error_response).encode())