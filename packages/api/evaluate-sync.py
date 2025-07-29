"""Synchronous SDK evaluation endpoint for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from datetime import datetime
import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from db_optimized import create_game, update_game, HAS_SUPABASE
    print("[SYNC] Database imports successful")
except Exception as e:
    print(f"[SYNC] Database import error: {e}")
    HAS_SUPABASE = False
    def create_game(data): return str(uuid.uuid4())
    def update_game(id, data): pass

# Copy the necessary functions and classes inline
import random
import re
import urllib.request
import urllib.error

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
    try:
        if 'choices' in response and response['choices']:
            choice = response['choices'][0]
            content = choice.get('message', {}).get('content', '')
            
            # Try to extract JSON from content
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback parsing
            if 'reveal' in content.lower():
                numbers = re.findall(r'\d+', content)
                if len(numbers) >= 2:
                    return {'action': 'reveal', 'row': int(numbers[0]), 'col': int(numbers[1])}
        
        return None
    except Exception as e:
        print(f"[SYNC] Error extracting move: {e}")
        return None

def execute_move(game, move):
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

def call_ai_model(provider, model, messages, functions=None, temperature=0.7):
    """Direct OpenAI API call."""
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
        
        req = urllib.request.Request(url, 
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    else:
        raise ValueError(f"Provider {provider} not implemented")

def format_game_messages(game_type, prompt):
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

def run_single_move(game, provider, model_name):
    """Run a single move in the game."""
    prompt = get_minesweeper_prompt(game)
    messages = format_game_messages('minesweeper', prompt)
    
    print(f"[SYNC] Calling {provider} {model_name}")
    response = call_ai_model(
        provider=provider,
        model=model_name,
        messages=messages,
        temperature=0.7
    )
    
    ai_move = extract_move_from_response(response)
    if not ai_move:
        raise ValueError("Could not extract move from AI response")
    
    valid, message = execute_move(game, ai_move)
    
    return {
        'move': ai_move,
        'valid': valid,
        'message': message,
        'response': response
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Run a synchronous evaluation."""
        try:
            # Set a timeout for the entire request
            start_time = time.time()
            max_duration = 25  # seconds (Vercel limit is 30)
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"[SYNC] Received request: {data}")
            
            # Extract parameters
            game_type = data.get('game', 'minesweeper')
            provider = data.get('provider', 'openai')
            model_name = data.get('model', 'gpt-4o-mini')
            difficulty = data.get('difficulty', 'medium')
            max_moves = data.get('max_moves', 10)  # Limit moves for sync execution
            
            # Check API key
            if provider == 'openai' and not os.environ.get('OPENAI_API_KEY'):
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "OPENAI_API_KEY environment variable not set"
                }).encode())
                return
            
            # Create evaluation ID
            evaluation_id = str(uuid.uuid4())
            game_id = str(uuid.uuid4())
            
            # Initialize game
            difficulties = {
                'easy': {'rows': 9, 'cols': 9, 'mines': 10},
                'medium': {'rows': 16, 'cols': 16, 'mines': 40},
                'hard': {'rows': 16, 'cols': 30, 'mines': 99}
            }
            cfg = difficulties.get(difficulty, difficulties['medium'])
            
            game = SimpleMinesweeper(rows=cfg['rows'], cols=cfg['cols'], mines=cfg['mines'])
            
            # Run game moves
            moves = []
            move_count = 0
            
            while not game.game_over and move_count < max_moves:
                # Check timeout
                if time.time() - start_time > max_duration:
                    print(f"[SYNC] Timeout after {move_count} moves")
                    break
                
                try:
                    move_result = run_single_move(game, provider, model_name)
                    moves.append({
                        'move_number': move_count + 1,
                        'action': move_result['move'],
                        'valid': move_result['valid'],
                        'message': move_result['message']
                    })
                    move_count += 1
                    print(f"[SYNC] Move {move_count}: {move_result['move']} - {move_result['message']}")
                    
                except Exception as e:
                    print(f"[SYNC] Error during move {move_count + 1}: {e}")
                    moves.append({
                        'move_number': move_count + 1,
                        'error': str(e)
                    })
                    break
            
            # Calculate results
            duration = time.time() - start_time
            valid_moves = sum(1 for m in moves if m.get('valid', False))
            
            result = {
                "evaluation_id": evaluation_id,
                "game_id": game_id,
                "status": "completed",
                "game_over": game.game_over,
                "won": game.won,
                "total_moves": len(moves),
                "valid_moves": valid_moves,
                "duration": duration,
                "moves": moves,
                "final_board_preview": str(game.get_visible_state()[:5])  # Show first 5 rows
            }
            
            # Save to database if available
            if HAS_SUPABASE:
                db_id = create_game({
                    "job_id": evaluation_id,
                    "game_type": game_type,
                    "difficulty": difficulty,
                    "model_name": model_name,
                    "model_provider": provider,
                    "status": "completed",
                    "won": game.won,
                    "total_moves": len(moves),
                    "valid_moves": valid_moves,
                    "duration": duration,
                    "moves": moves
                })
                result["db_id"] = db_id
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            import traceback
            error_message = f"Error in evaluate-sync: {str(e)}"
            print(f"[SYNC] Error: {error_message}")
            print(f"[SYNC] Traceback: {traceback.format_exc()}")
            
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
        """Check endpoint availability."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "endpoint": "evaluate-sync",
            "description": "Synchronous game evaluation (no threading)",
            "max_moves": 10,
            "timeout": "25 seconds",
            "has_openai_key": bool(os.environ.get('OPENAI_API_KEY'))
        }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()