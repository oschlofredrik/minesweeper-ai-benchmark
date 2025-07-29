"""Optimized leaderboard endpoint with caching and connection pooling."""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from pathlib import Path

# Add the current directory to the path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from db_optimized import get_leaderboard, get_db_stats, HAS_SUPABASE
    from cache_service import cache, leaderboard_cache_key
    USE_OPTIMIZED = True
except ImportError:
    USE_OPTIMIZED = False
    HAS_SUPABASE = False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?')[1]
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            # Check if this is a stats request
            if query_params.get('stats') == 'true':
                self.handle_stats_request()
                return
            
            # Get leaderboard data
            if USE_OPTIMIZED:
                # Use optimized database module with caching
                entries = get_leaderboard()
            else:
                # Fallback to direct query or demo data
                entries = self.get_leaderboard_fallback()
            
            # Add cache headers for client-side caching
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=60')  # Cache for 1 minute
            self.send_header('ETag', str(hash(str(entries))))
            self.end_headers()
            
            # Send response
            response = {
                "entries": entries,
                "cached": USE_OPTIMIZED and cache.get(leaderboard_cache_key()) is not None,
                "total_entries": len(entries)
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, If-None-Match')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
    
    def handle_stats_request(self):
        """Return database performance statistics."""
        if USE_OPTIMIZED:
            stats = get_db_stats()
        else:
            stats = {"error": "Optimized database not available"}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
    
    def get_leaderboard_fallback(self):
        """Fallback method to get leaderboard data."""
        # Try direct Supabase query
        SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
        SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
        
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            try:
                from supabase import create_client
                supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                response = supabase.table('leaderboard_entries').select('*').order('win_rate', desc=True).execute()
                return response.data if response.data else self.get_demo_data()
            except:
                return self.get_demo_data()
        else:
            return self.get_demo_data()
    
    def get_demo_data(self):
        """Return demo leaderboard data."""
        return [
            {
                "model_name": "gpt-4",
                "games_played": 250,
                "wins": 213,
                "losses": 37,
                "win_rate": 0.852,
                "valid_move_rate": 0.98,
                "mine_identification_precision": 0.92,
                "mine_identification_recall": 0.88,
                "coverage_ratio": 0.85,
                "reasoning_score": 0.91,
                "composite_score": 0.875,
                "total_moves": 11250,
                "valid_moves": 11025,
                "mines_identified": 1840,
                "mines_total": 2000
            },
            {
                "model_name": "claude-3-opus",
                "games_played": 200,
                "wins": 164,
                "losses": 36,
                "win_rate": 0.82,
                "valid_move_rate": 0.97,
                "mine_identification_precision": 0.90,
                "mine_identification_recall": 0.86,
                "coverage_ratio": 0.83,
                "reasoning_score": 0.89,
                "composite_score": 0.855,
                "total_moves": 9200,
                "valid_moves": 8924,
                "mines_identified": 1440,
                "mines_total": 1600
            },
            {
                "model_name": "gpt-3.5-turbo",
                "games_played": 150,
                "wins": 98,
                "losses": 52,
                "win_rate": 0.653,
                "valid_move_rate": 0.94,
                "mine_identification_precision": 0.85,
                "mine_identification_recall": 0.78,
                "coverage_ratio": 0.75,
                "reasoning_score": 0.82,
                "composite_score": 0.763,
                "total_moves": 6750,
                "valid_moves": 6345,
                "mines_identified": 1020,
                "mines_total": 1200
            }
        ]
    
    def send_error_response(self, code, message):
        """Send error response."""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())