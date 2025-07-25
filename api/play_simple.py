"""Play endpoint - simplified for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from datetime import datetime

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/play/games':
            # List available games
            games = [
                {
                    "id": "minesweeper",
                    "name": "Minesweeper", 
                    "description": "Classic mine detection game",
                    "difficulties": ["easy", "medium", "hard", "expert"]
                },
                {
                    "id": "risk",
                    "name": "Risk",
                    "description": "Strategic territory control",
                    "difficulties": ["easy", "medium", "hard"]
                }
            ]
            self.send_json_response({"games": games})
            
        elif path.startswith('/api/play/games/') and len(path.split('/')) == 5:
            # Get job status
            job_id = path.split('/')[-1]
            
            # Return demo in-progress status
            self.send_json_response({
                "job_id": job_id,
                "status": "in_progress",
                "total_games": 1,
                "completed_games": 0,
                "games": [{
                    "id": f"game-{job_id}-1",
                    "status": "in_progress",
                    "total_moves": 5,
                    "game_type": "minesweeper"
                }]
            })
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path
        
        if path == '/api/play':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            play_config = json.loads(post_data)
            
            # Validate required fields
            required = ['game', 'model', 'provider']
            for field in required:
                if field not in play_config:
                    self.send_error(400, f"Missing required field: {field}")
                    return
            
            # Create job ID
            job_id = "play_" + str(uuid.uuid4())[:8]
            
            # Create game records
            num_games = play_config.get("num_games", 1)
            games_created = []
            
            for i in range(num_games):
                game_id = str(uuid.uuid4())
                game_data = {
                    "id": game_id,
                    "job_id": job_id,
                    "game_type": play_config.get("game", "minesweeper"),
                    "difficulty": play_config.get("difficulty", "medium"),
                    "scenario": play_config.get("scenario"),
                    "model_name": play_config.get("model", "gpt-4"),
                    "model_provider": play_config.get("provider", "openai"),
                    "status": "queued",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Try to save to Supabase
                if SUPABASE_URL and SUPABASE_ANON_KEY:
                    try:
                        from supabase import create_client
                        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                        supabase.table('games').insert(game_data).execute()
                    except:
                        pass
                
                games_created.append({
                    "game_id": game_id,
                    "game_number": i + 1
                })
            
            # Start first game immediately (simplified approach)
            # In production, this would be handled by a queue worker
            if games_created:
                self.run_single_game(games_created[0]['game_id'], play_config)
            
            self.send_json_response({
                "job_id": job_id,
                "status": "started",
                "message": f"Started {num_games} game(s)",
                "games": games_created
            })
            
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def run_single_game(self, game_id, config):
        """Run a single game (simplified for demo)."""
        # This would normally call the game_runner endpoint
        # For now, just update status to in_progress
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            try:
                from supabase import create_client
                supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                supabase.table('games').update({
                    'status': 'in_progress',
                    'started_at': datetime.utcnow().isoformat()
                }).eq('id', game_id).execute()
            except:
                pass
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())