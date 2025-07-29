"""SDK-powered evaluation endpoint that actually runs games."""
from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from datetime import datetime
import sys
from pathlib import Path
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from db_optimized import create_game, update_game, HAS_SUPABASE
    print("[SDK] Database imports successful")
except Exception as e:
    print(f"[SDK] Database import error: {e}")
    HAS_SUPABASE = False
    def create_game(data): return str(uuid.uuid4())
    def update_game(id, data): pass

# Import AI models handler
try:
    from ai_models_http import call_ai_model, format_game_messages
    print("[SDK] AI models import successful")
except Exception as e:
    print(f"[SDK] AI models import error: {e}")
    # Fallback implementation
    def call_ai_model(provider, model, messages, functions=None, temperature=0.7):
        """Fallback AI caller using direct HTTP."""
        import urllib.request
        import urllib.error
        
        if provider == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY', '')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if functions:
                payload["functions"] = functions
                payload["function_call"] = "auto"
            
            print(f"[SDK] Calling OpenAI API with model {model}")
            
            req = urllib.request.Request(url, 
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"[SDK] OpenAI response received")
                    return result
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"[SDK] OpenAI API error: {e.code} - {error_body}")
                raise ValueError(f"OpenAI API error: {error_body}")
        else:
            raise ValueError(f"Provider {provider} not implemented in fallback")
    
    def format_game_messages(game_type, prompt):
        """Format messages for AI."""
        return [
            {
                "role": "system",
                "content": "You are an expert Minesweeper player. Analyze the game state and make optimal moves."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

# Simple Minesweeper implementation
class SimpleMinesweeper:
    def __init__(self, rows=16, cols=16, mines=40):
        self.rows = rows
        self.cols = cols
        self.num_mines = mines
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]
        self.revealed = [[False for _ in range(cols)] for _ in range(rows)]
        self.flags = [[False for _ in range(cols)] for _ in range(rows)]
        self.mines = set()
        self.game_over = False
        self.won = False
        self._place_mines()
        self._calculate_numbers()
    
    def _place_mines(self):
        import random
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        self.mines = set(random.sample(positions, self.num_mines))
        for r, c in self.mines:
            self.board[r][c] = -1
    
    def _calculate_numbers(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1:
                    count = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.board[nr][nc] == -1:
                                    count += 1
                    self.board[r][c] = count
    
    def reveal(self, row, col):
        if self.game_over or self.revealed[row][col] or self.flags[row][col]:
            return False, "Invalid move"
        
        self.revealed[row][col] = True
        
        if self.board[row][col] == -1:
            self.game_over = True
            return True, "Hit mine - game over"
        
        # Auto-reveal neighbors if cell is 0
        if self.board[row][col] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.revealed[nr][nc] and not self.flags[nr][nc]:
                            self.reveal(nr, nc)
        
        # Check win condition
        revealed_count = sum(sum(row) for row in self.revealed)
        if revealed_count == self.rows * self.cols - self.num_mines:
            self.won = True
            self.game_over = True
            return True, "All safe cells revealed - you won!"
        
        return True, "Cell revealed"
    
    def flag(self, row, col):
        if self.game_over or self.revealed[row][col]:
            return False, "Invalid flag"
        
        self.flags[row][col] = not self.flags[row][col]
        return True, f"Cell {'flagged' if self.flags[row][col] else 'unflagged'}"
    
    def get_visible_state(self):
        """Get the game state as the AI would see it."""
        visible = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if self.flags[r][c]:
                    row.append('F')
                elif not self.revealed[r][c]:
                    row.append('?')
                else:
                    row.append(str(self.board[r][c]))
            visible.append(row)
        return visible

def get_minesweeper_prompt(game):
    """Generate prompt for Minesweeper AI."""
    state = game.get_visible_state()
    
    prompt = f"""Current Minesweeper game state ({game.rows}x{game.cols} with {game.num_mines} mines):

Board (? = unrevealed, F = flagged, numbers = revealed):
"""
    
    # Add column numbers
    prompt += "   "
    for c in range(game.cols):
        prompt += f"{c:2} "
    prompt += "\n"
    
    # Add board with row numbers
    for r in range(game.rows):
        prompt += f"{r:2} "
        for c in range(game.cols):
            prompt += f"{state[r][c]:2} "
        prompt += "\n"
    
    prompt += "\nAnalyze the board and make the best move. Respond with a JSON object containing:\n"
    prompt += '{"action": "reveal" or "flag", "row": number, "col": number, "reasoning": "explanation"}'
    
    return prompt

def extract_move_from_response(response):
    """Extract move from AI response."""
    try:
        # Handle function calls
        if 'choices' in response and response['choices']:
            choice = response['choices'][0]
            
            # Check for function call
            if 'function_call' in choice.get('message', {}):
                args = json.loads(choice['message']['function_call']['arguments'])
                return args
            
            # Otherwise try to parse content
            content = choice.get('message', {}).get('content', '')
            
            # Try to extract JSON from content
            import re
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback parsing
            if 'reveal' in content.lower():
                # Try to extract coordinates
                numbers = re.findall(r'\d+', content)
                if len(numbers) >= 2:
                    return {'action': 'reveal', 'row': int(numbers[0]), 'col': int(numbers[1])}
            
        return None
    except Exception as e:
        print(f"[SDK] Error extracting move: {e}")
        return None

def execute_move(game, move):
    """Execute a move on the game."""
    try:
        action = move.get('action', '').lower()
        row = int(move.get('row', -1))
        col = int(move.get('col', -1))
        
        if row < 0 or row >= game.rows or col < 0 or col >= game.cols:
            return False, f"Invalid coordinates: ({row}, {col})"
        
        if action == 'reveal':
            return game.reveal(row, col)
        elif action == 'flag':
            return game.flag(row, col)
        else:
            return False, f"Invalid action: {action}"
    except Exception as e:
        return False, f"Error executing move: {e}"

def run_single_game(game_id, config):
    """Run a single game with AI."""
    print(f"[SDK] Starting game {game_id}")
    
    # Update status
    if HAS_SUPABASE:
        update_game(game_id, {
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat()
        })
    
    # Initialize game
    difficulty = config.get('difficulty', 'medium')
    provider = config.get('provider', 'openai')
    model_name = config.get('model', 'gpt-4o-mini')
    
    difficulties = {
        'easy': {'rows': 9, 'cols': 9, 'mines': 10},
        'medium': {'rows': 16, 'cols': 16, 'mines': 40},
        'hard': {'rows': 16, 'cols': 30, 'mines': 99}
    }
    cfg = difficulties.get(difficulty, difficulties['medium'])
    
    game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
    
    # Run game
    moves = []
    max_moves = 200
    start_time = time.time()
    
    for move_num in range(max_moves):
        if game.game_over:
            break
        
        # Get game prompt
        prompt = get_minesweeper_prompt(game)
        messages = format_game_messages('minesweeper', prompt)
        
        try:
            # Call AI
            print(f"[SDK] Move {move_num + 1}: Calling {provider} {model_name}")
            response = call_ai_model(
                provider=provider,
                model=model_name,
                messages=messages,
                temperature=0.7
            )
            
            # Extract move
            ai_move = extract_move_from_response(response)
            if not ai_move:
                print(f"[SDK] Could not extract move from AI response")
                break
            
            # Execute move
            valid, message = execute_move(game, ai_move)
            
            moves.append({
                'move_number': move_num + 1,
                'action': ai_move,
                'valid': valid,
                'message': message
            })
            
            print(f"[SDK] Move {move_num + 1}: {ai_move.get('action')} ({ai_move.get('row')}, {ai_move.get('col')}) - {message}")
            
        except Exception as e:
            print(f"[SDK] Error during move {move_num + 1}: {e}")
            moves.append({
                'move_number': move_num + 1,
                'error': str(e)
            })
            break
    
    # Calculate results
    duration = time.time() - start_time
    valid_moves = sum(1 for m in moves if m.get('valid', False))
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
    
    print(f"[SDK] Game {game_id} completed: won={game.won}, moves={len(moves)}, duration={duration:.1f}s")
    
    return {
        'game_id': game_id,
        'won': game.won,
        'total_moves': len(moves),
        'valid_moves': valid_moves,
        'duration': duration
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Start an AI SDK evaluation."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"[SDK] Received request: {data}")
            
            # Extract evaluation parameters
            game_type = data.get('game', 'minesweeper')
            provider = data.get('provider', 'openai')
            model_name = data.get('model', 'gpt-4o-mini')
            num_games = data.get('num_games', 1)
            difficulty = data.get('difficulty', 'medium')
            use_sdk = data.get('use_sdk', True)
            
            # Check for required environment variables
            if provider == 'openai' and not os.environ.get('OPENAI_API_KEY'):
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "OPENAI_API_KEY environment variable not set"
                }).encode())
                return
            elif provider == 'anthropic' and not os.environ.get('ANTHROPIC_API_KEY'):
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "ANTHROPIC_API_KEY environment variable not set"
                }).encode())
                return
            
            # Create evaluation ID
            evaluation_id = str(uuid.uuid4())
            
            # Prepare games configuration
            games = []
            for i in range(num_games):
                game_id = str(uuid.uuid4())
                games.append({
                    "id": game_id,
                    "type": game_type,
                    "provider": provider,
                    "model": model_name,
                    "difficulty": difficulty
                })
                
                # Create game record in database
                if HAS_SUPABASE:
                    db_id = create_game({
                        "job_id": evaluation_id,
                        "game_type": game_type,
                        "difficulty": difficulty,
                        "model_name": model_name,
                        "model_provider": provider,
                        "status": "queued"
                    })
                    games[i]["db_id"] = db_id
            
            # Start game execution in background thread
            def run_games():
                results = []
                for game in games:
                    game_id = game.get("db_id", game["id"])
                    try:
                        result = run_single_game(game_id, {
                            'game_type': game_type,
                            'provider': provider,
                            'model': model_name,
                            'difficulty': difficulty
                        })
                        results.append(result)
                    except Exception as e:
                        print(f"[SDK] Error running game {game_id}: {e}")
                        if HAS_SUPABASE:
                            update_game(game_id, {
                                'status': 'error',
                                'error': str(e)
                            })
                print(f"[SDK] Evaluation {evaluation_id} complete: {len(results)} games")
            
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
                "message": "SDK evaluation started",
                "config": {
                    "game_type": game_type,
                    "provider": provider,
                    "model_name": model_name,
                    "num_games": num_games,
                    "difficulty": difficulty
                },
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
    
    def do_GET(self):
        """Check SDK availability."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "sdk_available": True,
            "version": "2.1.0",
            "supported_games": ["minesweeper"],
            "supported_providers": ["openai", "anthropic"],
            "has_openai_key": bool(os.environ.get('OPENAI_API_KEY')),
            "has_anthropic_key": bool(os.environ.get('ANTHROPIC_API_KEY'))
        }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()