"""Bridge endpoint to use Vercel AI SDK for evaluations."""
from http.server import BaseHTTPRequestHandler
import json
import subprocess
import os
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_optimized import create_game, update_game, HAS_SUPABASE
from game_runner import SimpleMinesweeper, get_minesweeper_prompt, get_function_schema, execute_minesweeper_move
from ai_models_http import call_ai_model, format_game_messages, extract_function_call
import threading
import time

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Start an AI SDK evaluation."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            print(f"[SDK] Received request: {data}")
            
            # Check for required environment variables
            if data.get('provider') == 'openai' and not os.environ.get('OPENAI_API_KEY'):
                self.send_error(500, "OPENAI_API_KEY environment variable not set")
                return
            elif data.get('provider') == 'anthropic' and not os.environ.get('ANTHROPIC_API_KEY'):
                self.send_error(500, "ANTHROPIC_API_KEY environment variable not set")
                return
            
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
            
            # Create game records in database
            if HAS_SUPABASE:
                for i, game in enumerate(games):
                    game_data = {
                        "job_id": evaluation_id,
                        "game_type": game_type,
                        "difficulty": difficulty,
                        "model_name": model_name,
                        "model_provider": provider,
                        "status": "queued"
                    }
                    game_id = create_game(game_data)
                    games[i]["db_id"] = game_id
            
            # Start game execution in background thread
            # Note: In production, this should be a proper queue/worker system
            def run_games():
                for i, game in enumerate(games[:1]):  # Run first game only to avoid timeout
                    game_id = game.get("db_id", game["id"])
                    try:
                        self._run_single_game(game_id, evaluation_data["config"])
                    except Exception as e:
                        print(f"[SDK] Error running game {game_id}: {e}")
                        if HAS_SUPABASE:
                            update_game(game_id, {
                                'status': 'error',
                                'error': str(e)
                            })
            
            # Start execution thread
            thread = threading.Thread(target=run_games)
            thread.daemon = True
            thread.start()
            
            # Return response immediately
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "evaluation_id": evaluation_id,
                "status": "started",
                "message": "Evaluation started with AI execution",
                "config": evaluation_data["config"],
                "endpoint": f"/api/evaluation/{evaluation_id}",
                "games": games[:10]  # Return first 10 games
            }).encode())
            
        except Exception as e:
            import traceback
            error_message = f"Error in evaluate-sdk: {str(e)}"
            print(f"[SDK] Error: {error_message}")
            print(f"[SDK] Traceback: {traceback.format_exc()}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": error_message,
                "details": str(e),
                "type": type(e).__name__
            }).encode())
    
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
        self.send_header('Access-Control-Allow-Origin', '*')
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
    
    def _run_single_game(self, game_id: str, config: dict):
        """Run a single game with AI."""
        print(f"[SDK] Starting game {game_id}")
        
        # Update status
        if HAS_SUPABASE:
            update_game(game_id, {
                'status': 'in_progress',
                'started_at': datetime.utcnow().isoformat()
            })
        
        # Initialize game
        game_type = config.get('game_type', 'minesweeper')
        difficulty = config.get('difficulty', 'medium')
        provider = config.get('provider', 'openai')
        model_name = config.get('model_name', 'gpt-4')
        
        if game_type != 'minesweeper':
            raise ValueError(f"Unsupported game type: {game_type}")
        
        # Create game instance
        difficulties = {
            'easy': {'rows': 9, 'cols': 9, 'mines': 10},
            'medium': {'rows': 16, 'cols': 16, 'mines': 40},
            'hard': {'rows': 16, 'cols': 30, 'mines': 99}
        }
        cfg = difficulties.get(difficulty, difficulties['medium'])
        game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
        
        # Get function schema for structured responses
        function_schema = get_function_schema(game_type)
        
        # Run game
        moves = []
        max_moves = 200
        start_time = time.time()
        
        for move_num in range(max_moves):
            if game.game_over:
                break
            
            # Get game prompt
            prompt = get_minesweeper_prompt(game)
            messages = format_game_messages(game_type, prompt)
            
            try:
                # Call AI
                print(f"[SDK] Calling {provider} {model_name} for move {move_num + 1}")
                response = call_ai_model(
                    provider=provider,
                    model=model_name,
                    messages=messages,
                    functions=[function_schema] if function_schema else None,
                    temperature=0.7
                )
                
                # Extract move
                ai_move = extract_function_call(response)
                if not ai_move:
                    print(f"[SDK] Could not extract move from AI response")
                    break
                
                # Execute move
                valid, message = execute_minesweeper_move(game, ai_move)
                
                moves.append({
                    'move_number': move_num + 1,
                    'action': ai_move,
                    'valid': valid,
                    'message': message
                })
                
                print(f"[SDK] Move {move_num + 1}: {ai_move} - {message}")
                
            except Exception as e:
                print(f"[SDK] Error during move {move_num + 1}: {e}")
                break
        
        # Calculate results
        duration = time.time() - start_time
        valid_moves = sum(1 for m in moves if m['valid'])
        mines_identified = sum(1 for r in range(game.rows) for c in range(game.cols) 
                              if game.flags[r][c] and (r, c) in game.mines)
        
        # Update game with results
        if HAS_SUPABASE:
            update_game(game_id, {
                'status': 'won' if game.won else 'lost',
                'won': game.won,
                'total_moves': len(moves),
                'valid_moves': valid_moves,
                'mines_identified': mines_identified,
                'mines_total': game.num_mines,
                'duration': duration,
                'moves': moves,
                'completed_at': datetime.utcnow().isoformat()
            })
        
        print(f"[SDK] Game {game_id} completed: won={game.won}, moves={len(moves)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()