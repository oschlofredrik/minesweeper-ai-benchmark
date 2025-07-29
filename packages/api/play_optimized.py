"""Optimized play endpoint with batch leaderboard updates."""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from db_optimized import (
        create_game, update_game, batch_update_leaderboard,
        get_game, list_games, HAS_SUPABASE
    )
    from cache_service import cache
    USE_OPTIMIZED = True
except ImportError:
    USE_OPTIMIZED = False
    HAS_SUPABASE = False

# Import game runner
try:
    from game_runner import SimpleMinesweeper, run_ai_turn
    from ai_models_http import call_ai_model, format_game_messages, extract_function_call
except ImportError:
    SimpleMinesweeper = None
    run_ai_turn = None
    call_ai_model = None

# Batch processing configuration
BATCH_SIZE = int(os.environ.get('LEADERBOARD_BATCH_SIZE', '10'))
UPDATE_INTERVAL = int(os.environ.get('LEADERBOARD_UPDATE_INTERVAL', '30'))  # seconds

# Global batch queue
leaderboard_batch_queue = []
last_batch_update = time.time()

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
            # Get job status with optimized queries
            job_id = path.split('/')[-1]
            
            if USE_OPTIMIZED:
                # Use optimized list_games with pagination
                games, total = list_games(job_id=job_id, limit=100)
                
                # Calculate summary statistics
                completed_games = [g for g in games if g['status'] in ['won', 'lost', 'error']]
                wins = sum(1 for g in completed_games if g.get('won', False))
                total_moves = sum(g.get('total_moves', 0) for g in completed_games)
                
                response = {
                    "job_id": job_id,
                    "status": "completed" if len(completed_games) == total else "in_progress",
                    "total_games": total,
                    "completed_games": len(completed_games),
                    "games": games[:10],  # Only return first 10 for performance
                    "summary": {
                        "wins": wins,
                        "losses": len(completed_games) - wins,
                        "win_rate": wins / len(completed_games) if completed_games else 0,
                        "avg_moves": total_moves / len(completed_games) if completed_games else 0
                    }
                }
            else:
                # Fallback response
                response = {
                    "job_id": job_id,
                    "status": "in_progress",
                    "total_games": 1,
                    "completed_games": 0,
                    "games": []
                }
            
            self.send_json_response(response)
            
        elif path == '/api/play/batch-status':
            # Return batch processing status
            self.send_json_response({
                "queue_size": len(leaderboard_batch_queue),
                "batch_size": BATCH_SIZE,
                "update_interval": UPDATE_INTERVAL,
                "time_until_next_update": max(0, UPDATE_INTERVAL - (time.time() - last_batch_update))
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
            
            # Create game records using optimized module
            num_games = play_config.get("num_games", 1)
            games_created = []
            
            for i in range(num_games):
                game_data = {
                    "job_id": job_id,
                    "game_type": play_config.get("game", "minesweeper"),
                    "difficulty": play_config.get("difficulty", "medium"),
                    "scenario": play_config.get("scenario"),
                    "model_name": play_config.get("model", "gpt-4"),
                    "model_provider": play_config.get("provider", "openai"),
                    "status": "queued"
                }
                
                if USE_OPTIMIZED:
                    game_id = create_game(game_data)
                else:
                    game_id = str(uuid.uuid4())
                
                games_created.append({
                    "game_id": game_id,
                    "game_number": i + 1
                })
            
            # Start processing games asynchronously
            # In production, this would be handled by a queue worker
            if games_created:
                self.queue_games_for_processing(games_created, play_config)
            
            self.send_json_response({
                "job_id": job_id,
                "status": "started",
                "message": f"Started {num_games} game(s)",
                "games": games_created
            })
            
        elif path == '/api/play/force-batch-update':
            # Force immediate batch update (admin endpoint)
            if leaderboard_batch_queue:
                self.process_leaderboard_batch()
                self.send_json_response({
                    "message": "Batch update processed",
                    "items_processed": len(leaderboard_batch_queue)
                })
            else:
                self.send_json_response({
                    "message": "No items in batch queue"
                })
                
        else:
            self.send_error(404)
    
    def queue_games_for_processing(self, games: List[Dict], config: Dict):
        """Queue games for processing - actually run them."""
        if not games:
            return
            
        # For Vercel, we need to run games synchronously within the request
        # In production, this would be handled by a background worker
        for game_info in games[:1]:  # Run first game only to avoid timeout
            game_id = game_info['game_id']
            
            try:
                # Mark as in_progress
                if USE_OPTIMIZED:
                    update_game(game_id, {
                        'status': 'in_progress',
                        'started_at': datetime.utcnow().isoformat()
                    })
                
                # Actually run the game
                print(f"[PLAY] Running game {game_id}")
                result = self.run_single_game(game_id, config)
                
                # Handle completion
                self.handle_game_completion(game_id, result)
                
            except Exception as e:
                print(f"[PLAY] Error running game {game_id}: {e}")
                if USE_OPTIMIZED:
                    update_game(game_id, {
                        'status': 'error',
                        'error': str(e)
                    })
    
    def run_single_game(self, game_id: str, config: Dict) -> Dict[str, Any]:
        """Run a single game with AI."""
        print(f"[GAME] Starting game {game_id}")
        
        game_type = config.get('game', 'minesweeper')
        model_name = config.get('model', 'gpt-4')
        provider = config.get('provider', 'openai')
        difficulty = config.get('difficulty', 'medium')
        
        if not SimpleMinesweeper or not call_ai_model:
            raise ImportError("Game runner or AI models not available")
        
        # Initialize game
        if game_type == 'minesweeper':
            difficulty_configs = {
                'easy': {'rows': 9, 'cols': 9, 'mines': 10},
                'medium': {'rows': 16, 'cols': 16, 'mines': 40},
                'hard': {'rows': 16, 'cols': 30, 'mines': 99}
            }
            cfg = difficulty_configs.get(difficulty, difficulty_configs['medium'])
            game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
        else:
            raise ValueError(f"Unsupported game type: {game_type}")
        
        # Run game
        moves = []
        max_moves = 50
        start_time = datetime.utcnow()
        
        for move_num in range(max_moves):
            # Get game state
            board_state = game.get_board_state()
            prompt = f"Current Minesweeper board:\n{board_state}\n\nMake your next move (reveal row col or flag row col):"
            
            # Call AI
            messages = format_game_messages(game_type, prompt)
            
            try:
                response = call_ai_model(
                    provider=provider,
                    model=model_name,
                    messages=messages,
                    temperature=0.7
                )
                
                # Extract move
                ai_move = extract_function_call(response)
                if not ai_move:
                    print(f"[GAME] Could not extract move from AI response")
                    break
                
                # Execute move
                action = ai_move.get('action', 'reveal')
                row = ai_move.get('row', 0)
                col = ai_move.get('col', 0)
                
                if action == 'reveal':
                    valid, message = game.reveal(row, col)
                elif action == 'flag':
                    valid, message = game.flag(row, col)
                else:
                    valid, message = False, "Invalid action"
                
                moves.append({
                    'move_number': move_num + 1,
                    'action': ai_move,
                    'valid': valid,
                    'message': message
                })
                
                if game.game_over:
                    break
                    
            except Exception as e:
                print(f"[GAME] Error during move {move_num + 1}: {e}")
                break
        
        # Calculate results
        duration = (datetime.utcnow() - start_time).total_seconds()
        valid_moves = sum(1 for m in moves if m['valid'])
        
        return {
            'game_id': game_id,
            'model_name': model_name,
            'won': game.won if hasattr(game, 'won') else False,
            'total_moves': len(moves),
            'valid_moves': valid_moves,
            'mines_identified': sum(1 for r in range(game.rows) for c in range(game.cols) if game.flags[r][c] and (r, c) in game.mines),
            'mines_total': game.num_mines,
            'duration': duration,
            'moves': moves
        }
    
    def queue_leaderboard_update(self, game_result: Dict[str, Any]):
        """Queue a game result for batch leaderboard update."""
        global leaderboard_batch_queue, last_batch_update
        
        # Add to queue
        leaderboard_batch_queue.append(game_result)
        
        # Check if we should process the batch
        should_process = False
        
        # Process if batch size reached
        if len(leaderboard_batch_queue) >= BATCH_SIZE:
            should_process = True
        
        # Process if time interval exceeded
        elif time.time() - last_batch_update >= UPDATE_INTERVAL:
            should_process = True
        
        if should_process:
            self.process_leaderboard_batch()
    
    def process_leaderboard_batch(self):
        """Process the batch of leaderboard updates."""
        global leaderboard_batch_queue, last_batch_update
        
        if not leaderboard_batch_queue:
            return
        
        # Copy current batch and clear queue
        batch_to_process = leaderboard_batch_queue[:]
        leaderboard_batch_queue = []
        
        # Update last batch time
        last_batch_update = time.time()
        
        # Process batch update
        if USE_OPTIMIZED:
            try:
                batch_update_leaderboard(batch_to_process)
                print(f"[BATCH] Processed {len(batch_to_process)} leaderboard updates")
            except Exception as e:
                print(f"[BATCH] Error processing batch: {e}")
                # Re-queue failed items
                leaderboard_batch_queue.extend(batch_to_process)
    
    def handle_game_completion(self, game_id: str, result: Dict[str, Any]):
        """Handle game completion with optimized updates."""
        # Update game record
        if USE_OPTIMIZED:
            update_game(game_id, {
                'status': 'won' if result.get('won') else 'lost',
                'won': result.get('won', False),
                'total_moves': result.get('total_moves', 0),
                'valid_moves': result.get('valid_moves', 0),
                'mines_identified': result.get('mines_identified', 0),
                'mines_total': result.get('mines_total', 0),
                'duration': result.get('duration', 0),
                'final_board_state': result.get('final_state'),
                'moves': result.get('moves', [])
            })
        
        # Queue leaderboard update
        self.queue_leaderboard_update({
            'model_name': result.get('model_name'),
            'won': result.get('won', False),
            'total_moves': result.get('total_moves', 0),
            'valid_moves': result.get('valid_moves', 0),
            'mines_identified': result.get('mines_identified', 0),
            'mines_total': result.get('mines_total', 0)
        })
    
    def send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response with proper headers."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# Background task to process batch updates periodically
# In production, this would be a separate worker or scheduled function
def ensure_batch_processing():
    """Ensure batch updates are processed periodically."""
    global last_batch_update
    
    if leaderboard_batch_queue and time.time() - last_batch_update >= UPDATE_INTERVAL:
        # Create a dummy handler to process the batch
        class DummyHandler:
            def process_leaderboard_batch(self):
                global leaderboard_batch_queue, last_batch_update
                
                if not leaderboard_batch_queue:
                    return
                
                batch_to_process = leaderboard_batch_queue[:]
                leaderboard_batch_queue = []
                last_batch_update = time.time()
                
                if USE_OPTIMIZED:
                    try:
                        batch_update_leaderboard(batch_to_process)
                        print(f"[BATCH-WORKER] Processed {len(batch_to_process)} leaderboard updates")
                    except Exception as e:
                        print(f"[BATCH-WORKER] Error: {e}")
                        leaderboard_batch_queue.extend(batch_to_process)
        
        handler = DummyHandler()
        handler.process_leaderboard_batch()