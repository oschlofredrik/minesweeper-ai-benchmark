"""Bridge endpoint to use Vercel AI SDK for evaluations."""
from http.server import BaseHTTPRequestHandler
import json
import subprocess
import os
import uuid
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Start an AI SDK evaluation."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Extract evaluation parameters
            game_type = data.get('game', 'minesweeper')
            provider = data.get('provider', 'openai')
            model_name = data.get('model', 'gpt-4')
            num_games = data.get('num_games', 10)
            difficulty = data.get('difficulty', 'medium')
            use_sdk = data.get('use_sdk', True)
            
            if not use_sdk:
                # Fallback to Python implementation
                self.send_error(400, "This endpoint requires use_sdk=true")
                return
            
            # Create evaluation ID
            evaluation_id = str(uuid.uuid4())
            
            # Prepare games configuration
            games = []
            for i in range(num_games):
                games.append({
                    "id": f"game_{i+1}",
                    "type": game_type,
                    "provider": provider,
                    "model": model_name,
                    "difficulty": difficulty,
                    "initialState": self._create_initial_state(game_type, difficulty)
                })
            
            # Store evaluation request
            evaluation_data = {
                "id": evaluation_id,
                "games": games,
                "status": "queued",
                "created_at": datetime.utcnow().isoformat(),
                "config": {
                    "game_type": game_type,
                    "provider": provider,
                    "model_name": model_name,
                    "num_games": num_games,
                    "difficulty": difficulty
                }
            }
            
            # For now, return the evaluation setup
            # In production, this would trigger the TypeScript evaluation
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "evaluation_id": evaluation_id,
                "status": "queued",
                "message": "Evaluation queued for processing",
                "config": evaluation_data["config"],
                "endpoint": f"/api/evaluation/{evaluation_id}"
            }).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def _create_initial_state(self, game_type, difficulty):
        """Create initial game state based on type and difficulty."""
        if game_type == "minesweeper":
            difficulties = {
                "easy": {"rows": 9, "cols": 9, "mines": 10},
                "medium": {"rows": 16, "cols": 16, "mines": 40},
                "hard": {"rows": 16, "cols": 30, "mines": 99}
            }
            config = difficulties.get(difficulty, difficulties["medium"])
            return {
                "board": [[0 for _ in range(config["cols"])] for _ in range(config["rows"])],
                "config": config,
                "moves": []
            }
        elif game_type == "risk":
            return {
                "territories": {},
                "players": ["ai", "opponent"],
                "currentPlayer": "ai",
                "phase": "reinforce"
            }
        else:
            return {}
    
    def do_GET(self):
        """Check SDK availability."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "sdk_available": True,
            "version": "2.0.0",
            "supported_games": ["minesweeper", "risk"],
            "supported_providers": ["openai", "anthropic"],
            "features": [
                "streaming",
                "multi-step",
                "tool-calling",
                "real-time-updates",
                "fluid-compute"
            ]
        }).encode())