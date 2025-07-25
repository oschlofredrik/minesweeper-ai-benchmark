"""Play game endpoints."""
from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse
from . import supabase_db as db
import uuid

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # List available games
        if path == '/api/play/games':
            games = [
                {
                    "id": "minesweeper",
                    "name": "Minesweeper", 
                    "description": "Classic mine detection game",
                    "difficulties": ["easy", "medium", "hard", "expert"],
                    "modes": ["classic", "no-guess", "density"]
                },
                {
                    "id": "risk",
                    "name": "Risk",
                    "description": "Strategic territory control",
                    "difficulties": ["easy", "medium", "hard"],
                    "modes": ["conquest", "mission", "capitals"]
                },
                {
                    "id": "sudoku",
                    "name": "Sudoku",
                    "description": "Number placement puzzle",
                    "difficulties": ["easy", "medium", "hard", "expert"],
                    "modes": ["classic", "killer", "samurai"]
                }
            ]
            self.send_json_response({"games": games})
            
        # Get game status
        elif path.startswith('/api/play/games/') and len(path.split('/')) == 5:
            job_id = path.split('/')[-1]
            games = db.list_games()
            
            # Find games for this job
            job_games = [g for g in games if g.get("job_id") == job_id]
            
            if job_games:
                status = {
                    "job_id": job_id,
                    "status": "completed" if all(g.get("status") != "in_progress" for g in job_games) else "in_progress",
                    "total_games": len(job_games),
                    "completed_games": sum(1 for g in job_games if g.get("status") != "in_progress"),
                    "games": job_games
                }
                self.send_json_response(status)
            else:
                self.send_error(404, "Job not found")
                
        # Get game results
        elif path.startswith('/api/play/games/') and path.endswith('/results'):
            job_id = path.split('/')[-2]
            games = db.list_games()
            job_games = [g for g in games if g.get("job_id") == job_id]
            
            if job_games:
                results = {
                    "job_id": job_id,
                    "summary": {
                        "total_games": len(job_games),
                        "wins": sum(1 for g in job_games if g.get("won")),
                        "losses": sum(1 for g in job_games if not g.get("won")),
                        "avg_moves": sum(g.get("total_moves", 0) for g in job_games) / len(job_games) if job_games else 0
                    },
                    "games": job_games
                }
                self.send_json_response(results)
            else:
                self.send_error(404, "Job not found")
                
        # Get game summary
        elif path.startswith('/api/play/games/') and path.endswith('/summary'):
            job_id = path.split('/')[-2]
            games = db.list_games()
            job_games = [g for g in games if g.get("job_id") == job_id]
            
            if job_games:
                # Calculate summary statistics
                total_games = len(job_games)
                wins = sum(1 for g in job_games if g.get("won"))
                
                summary = {
                    "job_id": job_id,
                    "model": job_games[0].get("model_name", "Unknown"),
                    "game_type": job_games[0].get("game_type", "minesweeper"),
                    "total_games": total_games,
                    "wins": wins,
                    "losses": total_games - wins,
                    "win_rate": wins / total_games if total_games > 0 else 0,
                    "avg_moves": sum(g.get("total_moves", 0) for g in job_games) / total_games if total_games > 0 else 0,
                    "avg_duration": sum(g.get("duration", 0) for g in job_games) / total_games if total_games > 0 else 0,
                    "created_at": min(g.get("created_at", "") for g in job_games),
                    "completed_at": max(g.get("updated_at", "") for g in job_games)
                }
                self.send_json_response(summary)
            else:
                self.send_error(404, "Job not found")
                
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path
        
        # Start new game(s)
        if path == '/api/play':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            play_config = json.loads(post_data)
            
            # Create job ID
            job_id = "play_" + str(uuid.uuid4())[:8]
            
            # Create game records
            num_games = play_config.get("num_games", 1)
            games_created = []
            
            for i in range(num_games):
                game_data = {
                    "job_id": job_id,
                    "game_type": play_config.get("game", "minesweeper"),
                    "difficulty": play_config.get("difficulty", "medium"),
                    "model_name": play_config.get("model", "gpt-4"),
                    "model_provider": play_config.get("provider", "openai"),
                    "game_number": i + 1,
                    "total_games": num_games,
                    "status": "in_progress",
                    "moves": [],
                    "config": play_config
                }
                
                game_id = db.create_game(game_data)
                games_created.append({
                    "game_id": game_id,
                    "game_number": i + 1
                })
            
            # For Vercel, we need to trigger games separately due to timeout
            # Mark all games as queued
            for game_info in games_created:
                db.update_game(game_info["game_id"], {"status": "queued"})
            
            # Trigger the first game immediately
            if games_created:
                import httpx
                try:
                    # Call our run_game endpoint asynchronously
                    # In production, use the actual Vercel URL
                    base_url = os.environ.get("VERCEL_URL", "https://tilts.vercel.app")
                    httpx.post(
                        f"{base_url}/api/run_game",
                        json={"game_id": games_created[0]["game_id"]},
                        timeout=1.0  # Don't wait for response
                    )
                except:
                    pass  # Fire and forget
            
            self.send_json_response({
                "job_id": job_id,
                "status": "started",
                "message": f"Started {num_games} game(s)",
                "games": games_created
            })
            
        else:
            self.send_error(404)
    
    def _run_game_async(self, game_id: str, play_config: dict):
        """Run a game asynchronously (in practice, synchronously for Vercel)."""
        from .runner import runner
        
        # Get game details
        game = db.get_game(game_id)
        if not game:
            return
        
        # Run the actual game
        result = runner.run_game(
            game_type=game["game_type"],
            model_name=game["model_name"],
            model_provider=game["model_provider"],
            difficulty=game["difficulty"],
            job_id=game["job_id"]
        )
        
        # The runner already updates the database, but we need to update our specific game_id
        if result.get("game_id") != game_id:
            # Copy results to our game record
            source_game = db.get_game(result["game_id"])
            if source_game:
                db.update_game(game_id, {
                    "status": source_game["status"],
                    "won": source_game.get("won"),
                    "total_moves": source_game.get("total_moves"),
                    "valid_moves": source_game.get("valid_moves"),
                    "mines_identified": source_game.get("mines_identified"),
                    "mines_total": source_game.get("mines_total"),
                    "duration": source_game.get("duration"),
                    "moves": source_game.get("moves", []),
                    "final_board_state": source_game.get("final_board_state"),
                    "error_message": source_game.get("error_message")
                })
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())