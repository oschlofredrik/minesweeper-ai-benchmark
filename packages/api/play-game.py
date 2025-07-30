"""Simple game playing endpoint - just game + AI, no complexity."""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import random
import time

class SimpleMinesweeper:
    """Basic Minesweeper game implementation."""
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
        """Get what the player/AI can see."""
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
    
    def reveal(self, row, col):
        """Reveal a cell."""
        if self.game_over or self.revealed[row][col] or self.flags[row][col]:
            return False, "Invalid move"
        
        self.revealed[row][col] = True
        
        if self.board[row][col] == -1:
            self.game_over = True
            return True, "Hit mine - game over"
        
        # Auto-reveal zeros
        if self.board[row][col] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.revealed[nr][nc] and not self.flags[nr][nc]:
                            self.reveal(nr, nc)
        
        # Check win
        revealed_count = sum(sum(row) for row in self.revealed)
        if revealed_count == self.rows * self.cols - self.num_mines:
            self.won = True
            self.game_over = True
            return True, "All safe cells revealed - you won!"
        
        return True, "Cell revealed"
    
    def flag(self, row, col):
        """Flag/unflag a cell."""
        if self.game_over or self.revealed[row][col]:
            return False, "Invalid flag"
        
        self.flags[row][col] = not self.flags[row][col]
        return True, f"Cell {'flagged' if self.flags[row][col] else 'unflagged'}"


def get_ai_move(game_state, model='gpt-4o-mini'):
    """Get a move from the AI for the current game state."""
    
    # Build prompt
    rows = len(game_state)
    cols = len(game_state[0]) if rows > 0 else 0
    
    prompt = f"Minesweeper board ({rows}x{cols}):\n\n"
    
    # Add column numbers
    prompt += "   "
    for c in range(cols):
        prompt += f"{c:2} "
    prompt += "\n"
    
    # Add board
    for r in range(rows):
        prompt += f"{r:2} "
        for c in range(cols):
            prompt += f"{game_state[r][c]:2} "
        prompt += "\n"
    
    prompt += "\n? = unrevealed, F = flagged, numbers = adjacent mines\n"
    prompt += "Choose ONE move. Reply with just: action row col\n"
    prompt += "Example: reveal 3 5\n"
    prompt += "Example: flag 7 2\n"
    
    # Call OpenAI
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError("No OpenAI API key")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert Minesweeper player. Give concise move commands."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "store": True  # Enable storing completions in OpenAI dashboard
    }
    
    req = urllib.request.Request(url, 
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    print(f"[AI] Calling OpenAI API with model {model}")
    print(f"[AI] API Key: {api_key[:20]}...")
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        ai_text = result['choices'][0]['message']['content'].strip()
        print(f"[AI] OpenAI response: {ai_text}")
        print(f"[AI] Usage: {result.get('usage', {})}")
        
    # Parse move - no fallbacks
    parts = ai_text.lower().split()
    if len(parts) >= 3 and parts[0] in ['reveal', 'flag']:
        action = parts[0]
        row = int(parts[1])
        col = int(parts[2])
        return {
            'action': action,
            'row': row,
            'col': col,
            'raw_response': ai_text
        }
    else:
        raise ValueError(f"Could not parse AI response: {ai_text}")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Play a game with AI."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            data = json.loads(post_data.decode('utf-8'))
            
            # Game config
            difficulty = data.get('difficulty', 'easy')
            model = data.get('model', 'gpt-4o-mini')
            max_moves = data.get('max_moves', 50)
            
            difficulties = {
                'easy': {'rows': 9, 'cols': 9, 'mines': 10},
                'medium': {'rows': 16, 'cols': 16, 'mines': 40},
                'hard': {'rows': 16, 'cols': 30, 'mines': 99}
            }
            
            cfg = difficulties.get(difficulty, difficulties['easy'])
            game = SimpleMinesweeper(cfg['rows'], cfg['cols'], cfg['mines'])
            
            # Play the game
            moves = []
            start_time = time.time()
            
            while not game.game_over and len(moves) < max_moves:
                # Get current state
                board_state = game.get_visible_state()
                
                # Get AI move
                move_start = time.time()
                ai_move = get_ai_move(board_state, model)
                move_duration = time.time() - move_start
                print(f"[GAME] AI response time: {move_duration:.2f}s")
                
                # Execute move
                if ai_move['action'] == 'flag':
                    valid, message = game.flag(ai_move['row'], ai_move['col'])
                else:
                    valid, message = game.reveal(ai_move['row'], ai_move['col'])
                
                # Record move
                moves.append({
                    'move_number': len(moves) + 1,
                    'action': ai_move['action'],
                    'row': ai_move['row'],
                    'col': ai_move['col'],
                    'valid': valid,
                    'message': message,
                    'board_state': game.get_visible_state()
                })
                
                print(f"[GAME] Move {len(moves)}: {ai_move['action']} ({ai_move['row']}, {ai_move['col']}) - {message}")
            
            # Game complete
            duration = time.time() - start_time
            
            result = {
                'game_id': f"game_{int(time.time())}",
                'status': 'completed',
                'won': game.won,
                'total_moves': len(moves),
                'duration': duration,
                'final_board': game.get_visible_state(),
                'moves': moves,
                'api_key_used': os.environ.get('OPENAI_API_KEY', '')[:20] + '...' if os.environ.get('OPENAI_API_KEY') else 'NO_KEY',
                'endpoint_version': 'play-game-v2'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }).encode())
    
    def do_GET(self):
        """Test endpoint."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "endpoint": "play-game",
            "description": "Simple game playing with AI",
            "method": "POST",
            "params": {
                "difficulty": "easy|medium|hard",
                "model": "gpt-4o-mini|gpt-4",
                "max_moves": "number"
            }
        }).encode())
    
    def do_OPTIONS(self):
        """CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()