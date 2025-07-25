"""Play endpoint - simplified for Vercel."""
print("[PLAY_SIMPLE] Module loading...")

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import uuid
from datetime import datetime

print(f"[PLAY_SIMPLE] Python version: {sys.version}")
print(f"[PLAY_SIMPLE] __file__ = {__file__}")

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

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
        
        elif path.startswith('/api/benchmark/jobs/'):
            # Get benchmark job status
            job_id = path.split('/')[-1]
            print(f"[BENCHMARK] Job status request for {job_id}")
            
            # For now, return completed status
            self.send_json_response({
                "job_id": job_id,
                "status": "completed",
                "games": [],
                "summary": {
                    "games_completed": 1,
                    "wins": 0,
                    "win_rate": 0.0,
                    "avg_moves": 1
                }
            })
            
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
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
        
        elif path == '/api/benchmark/run':
            print(f"[BENCHMARK] Received POST to {path}")
            # Handle benchmark run here
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                config = json.loads(post_data)
                
                # Log the benchmark request
                print(f"[BENCHMARK] Config received: {json.dumps(config)}")
                print(f"[BENCHMARK] Environment check - OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
                print(f"[BENCHMARK] Environment check - ANTHROPIC_API_KEY exists: {'ANTHROPIC_API_KEY' in os.environ}")
            except Exception as e:
                print(f"[BENCHMARK] Error parsing request: {e}")
                self.send_json_response({"error": str(e)}, 400)
                return
            
            job_id = "bench_" + str(uuid.uuid4())[:8]
            
            # Try to run a simple game
            try:
                result = self.run_benchmark_game(config)
                print(f"[BENCHMARK] Game completed: won={result.get('won')}, moves={result.get('total_moves')}")
                
                response = {
                    "job_id": job_id,
                    "status": "completed",
                    "config": config,
                    "games": [{
                        "game_id": result['game_id'],
                        "game_number": 1,
                        "status": "completed",
                        "won": result.get('won', False),
                        "total_moves": result.get('total_moves', 0),
                        "duration": result.get('duration', 0),
                        "final_state": result.get('final_state'),
                        "moves": result.get('moves', [])
                    }],
                    "summary": {
                        "games_completed": 1,
                        "wins": 1 if result.get('won') else 0,
                        "win_rate": 1.0 if result.get('won') else 0.0,
                        "avg_moves": result.get('total_moves', 0)
                    }
                }
            except Exception as e:
                print(f"[BENCHMARK] Error running game: {str(e)}")
                import traceback
                traceback.print_exc()
                
                response = {
                    "job_id": job_id,
                    "status": "error",
                    "config": config,
                    "games": [],
                    "error": str(e)
                }
            
            self.send_json_response(response)
            
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
    
    def run_benchmark_game(self, config):
        """Run a single benchmark game with AI."""
        print(f"[GAME] Starting game with model={config.get('model')} provider={config.get('provider')}")
        
        game_id = str(uuid.uuid4())
        game_type = config.get('game', 'minesweeper')
        model_name = config.get('model', 'gpt-4')
        provider = config.get('provider', 'openai')
        difficulty = config.get('difficulty', 'medium')
        
        # Try to import required modules
        try:
            from ai_models import call_ai_model, format_game_messages, extract_function_call
            print(f"[GAME] Successfully imported ai_models")
            
            from game_runner import (
                SimpleMinesweeper, SimpleRisk,
                get_minesweeper_prompt, get_risk_prompt,
                get_function_schema, execute_minesweeper_move, execute_risk_move
            )
            print(f"[GAME] Successfully imported game_runner")
        except ImportError as e:
            print(f"[GAME] Failed to import: {e}")
            raise
        
        # Initialize game
        try:
            if game_type == 'minesweeper':
                print(f"[GAME] Creating Minesweeper game with difficulty={difficulty}")
                difficulty_configs = {
                    'easy': {'rows': 9, 'cols': 9, 'mines': 10},
                    'medium': {'rows': 16, 'cols': 16, 'mines': 40},
                    'hard': {'rows': 16, 'cols': 30, 'mines': 99}
                }
                cfg = difficulty_configs.get(difficulty, difficulty_configs['medium'])
                game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
                get_prompt = get_minesweeper_prompt
                execute_move = execute_minesweeper_move
            else:
                print(f"[GAME] Creating Risk game")
                game = SimpleRisk(scenario=config.get('scenario'))
                get_prompt = get_risk_prompt
                execute_move = execute_risk_move
            
            # Get function schema
            function_schema = get_function_schema(game_type)
            print(f"[GAME] Got function schema for {game_type}")
            
        except Exception as e:
            print(f"[GAME] Error initializing game: {str(e)}")
            raise
        
        # Run game
        moves = []
        max_moves = 30
        start_time = datetime.utcnow()
        
        try:
            for move_num in range(max_moves):
                print(f"[GAME] Move {move_num + 1}")
                
                # Get prompt
                prompt = get_prompt(game)
                messages = format_game_messages(game_type, prompt)
                
                # Call AI
                print(f"[GAME] Calling AI with {len(messages)} messages")
                response = call_ai_model(
                    provider=provider,
                    model=model_name,
                    messages=messages,
                    functions=[function_schema],
                    temperature=0.7
                )
                
                print(f"[GAME] AI response: {json.dumps(response)[:200]}...")
                
                # Extract move
                ai_move = extract_function_call(response)
                if not ai_move:
                    print(f"[GAME] Could not extract move from response")
                    # Return with what we have
                    break
                
                print(f"[GAME] AI move: {ai_move}")
                
                # Execute move
                valid, message = execute_move(game, ai_move)
                print(f"[GAME] Move valid={valid}, message={message}")
                
                # Record move
                moves.append({
                    'move_number': move_num + 1,
                    'action': ai_move,
                    'valid': valid,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Check game over
                if game.game_over:
                    print(f"[GAME] Game over! Won={getattr(game, 'won', False)}")
                    break
                    
        except Exception as e:
            print(f"[GAME] Error during game: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'game_id': game_id,
            'game_type': game_type,
            'status': 'completed',
            'won': getattr(game, 'won', False),
            'total_moves': len(moves),
            'moves': moves,
            'final_state': game.to_json_state() if hasattr(game, 'to_json_state') else {},
            'duration': duration
        }
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())