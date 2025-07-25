"""Run a single game - separate endpoint for Vercel function timeout management."""
from http.server import BaseHTTPRequestHandler
import json
from . import supabase_db as db
from .runner import runner

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Run a single game."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        game_id = data.get("game_id")
        if not game_id:
            self.send_error(400, "game_id required")
            return
        
        # Get game details
        game = db.get_game(game_id)
        if not game:
            self.send_error(404, "Game not found")
            return
        
        # Check if already running/completed
        if game.get("status") not in ["queued", "in_progress"]:
            self.send_json_response({
                "game_id": game_id,
                "status": game["status"],
                "message": "Game already processed"
            })
            return
        
        # Run the game
        try:
            result = runner.run_game(
                game_type=game["game_type"],
                model_name=game["model_name"],
                model_provider=game["model_provider"],
                difficulty=game.get("difficulty", "medium"),
                job_id=game.get("job_id")
            )
            
            # Update our game record with the results
            game_data = db.get_game(result["game_id"])
            if game_data and result["game_id"] != game_id:
                # Copy data from runner's game to our game
                db.update_game(game_id, {
                    "status": game_data["status"],
                    "won": game_data.get("won"),
                    "total_moves": game_data.get("total_moves"),
                    "valid_moves": game_data.get("valid_moves"),
                    "duration": game_data.get("duration"),
                    "moves": game_data.get("moves", []),
                    "final_board_state": game_data.get("final_board_state"),
                    "mines_identified": game_data.get("mines_identified"),
                    "mines_total": game_data.get("mines_total"),
                    "total_tokens": result.get("tokens_used", 0)
                })
            
            self.send_json_response({
                "game_id": game_id,
                "status": "completed",
                "result": result
            })
            
            # Check if there are more games in the same job to run
            if game.get("job_id"):
                all_games = db.list_games()
                job_games = [g for g in all_games if g.get("job_id") == game["job_id"] and g.get("status") == "queued"]
                
                if job_games:
                    # Trigger the next game
                    import os
                    import httpx
                    try:
                        base_url = os.environ.get("VERCEL_URL", "https://tilts.vercel.app")
                        httpx.post(
                            f"{base_url}/api/run_game",
                            json={"game_id": job_games[0]["id"]},
                            timeout=1.0
                        )
                    except:
                        pass
            
        except Exception as e:
            # Update game with error
            db.update_game(game_id, {
                "status": "error",
                "error_message": str(e)
            })
            
            self.send_json_response({
                "game_id": game_id,
                "status": "error",
                "error": str(e)
            })
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())