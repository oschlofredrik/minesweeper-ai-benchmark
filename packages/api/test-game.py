"""Test single game move execution."""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import random

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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test game execution with AI."""
        try:
            api_key = os.environ.get('OPENAI_API_KEY', '')
            
            # Create a new game
            game = SimpleMinesweeper(rows=9, cols=9, mines=10)  # Easy mode for testing
            
            # Get the prompt
            prompt = get_minesweeper_prompt(game)
            
            response_data = {
                "has_openai_key": bool(api_key),
                "game_created": True,
                "board_size": f"{game.rows}x{game.cols}",
                "mines": game.num_mines,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt
            }
            
            if api_key:
                # Try calling OpenAI
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert Minesweeper player. Analyze the game state and make optimal moves."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 200
                }
                
                response_data["messages_sent"] = messages
                response_data["payload"] = payload
                
                req = urllib.request.Request(url, 
                    data=json.dumps(payload).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        result = json.loads(resp.read().decode('utf-8'))
                        response_data["api_call_success"] = True
                        response_data["api_response"] = result
                        response_data["ai_move"] = result['choices'][0]['message']['content']
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode('utf-8')
                    response_data["api_call_success"] = False
                    response_data["api_error"] = f"{e.code}: {error_body}"
                except Exception as e:
                    response_data["api_call_success"] = False
                    response_data["api_error"] = str(e)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()