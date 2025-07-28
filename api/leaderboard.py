"""Leaderboard endpoint - self-contained for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import os

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Try to use Supabase if configured
            if SUPABASE_URL and SUPABASE_ANON_KEY:
                try:
                    from supabase import create_client
                    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                    response = supabase.table('leaderboard_entries').select('*').order('win_rate', desc=True).execute()
                    entries = response.data if response.data else []
                except:
                    # Fallback to demo data
                    entries = self.get_demo_data()
            else:
                entries = self.get_demo_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"entries": entries}).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def get_demo_data(self):
        """Return demo leaderboard data."""
        return [
            {
                "model_name": "gpt-4",
                "total_games": 10,
                "wins": 7,
                "losses": 3,
                "win_rate": 0.7,
                "avg_moves": 45.2,
                "avg_duration": 12.5,
                "ms_s_score": 0.752,
                "ms_i_score": 0.689
            },
            {
                "model_name": "claude-3-opus",
                "total_games": 8,
                "wins": 5,
                "losses": 3,
                "win_rate": 0.625,
                "avg_moves": 52.1,
                "avg_duration": 15.3,
                "ms_s_score": 0.698,
                "ms_i_score": 0.712
            },
            {
                "model_name": "gpt-3.5-turbo",
                "total_games": 15,
                "wins": 8,
                "losses": 7,
                "win_rate": 0.533,
                "avg_moves": 38.7,
                "avg_duration": 8.2,
                "ms_s_score": 0.612,
                "ms_i_score": 0.578
            }
        ]