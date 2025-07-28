"""Simple game runner endpoint for Vercel."""
from http.server import BaseHTTPRequestHandler
import json
import os
import random
import time
from datetime import datetime
import uuid

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

class SimpleMinesweeper:
    """Simplified Minesweeper game."""
    def __init__(self, rows=9, cols=9, mines=10):
        self.rows = rows
        self.cols = cols
        self.num_mines = mines
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]
        self.visible = [[False for _ in range(cols)] for _ in range(rows)]
        self.flags = [[False for _ in range(cols)] for _ in range(rows)]
        self.mines = set()
        self.game_over = False
        self.won = False
        self._place_mines()
        self._calculate_numbers()
    
    def _place_mines(self):
        """Place mines randomly."""
        while len(self.mines) < self.num_mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            self.mines.add((r, c))
    
    def _calculate_numbers(self):
        """Calculate mine counts."""
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in self.mines:
                    count = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if (nr, nc) in self.mines:
                                    count += 1
                    self.board[r][c] = count
                else:
                    self.board[r][c] = -1
    
    def reveal(self, row, col):
        """Reveal a cell."""
        if self.game_over or self.visible[row][col] or self.flags[row][col]:
            return False, "Invalid move"
        
        self.visible[row][col] = True
        
        if (row, col) in self.mines:
            self.game_over = True
            self.won = False
            return True, "Hit mine - game over"
        
        # Auto-reveal neighbors if cell is 0
        if self.board[row][col] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.visible[nr][nc]:
                            self.reveal(nr, nc)
        
        # Check win condition
        safe_cells = self.rows * self.cols - self.num_mines
        revealed = sum(1 for r in range(self.rows) for c in range(self.cols) if self.visible[r][c])
        if revealed == safe_cells:
            self.game_over = True
            self.won = True
            return True, "All safe cells revealed - you won!"
        
        return True, "Cell revealed"
    
    def flag(self, row, col):
        """Flag/unflag a cell."""
        if self.game_over or self.visible[row][col]:
            return False, "Cannot flag this cell"
        self.flags[row][col] = not self.flags[row][col]
        return True, "Cell flagged" if self.flags[row][col] else "Cell unflagged"
    
    def get_board_state(self):
        """Get current board state for AI."""
        lines = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if self.flags[r][c]:
                    row.append('F')
                elif not self.visible[r][c]:
                    row.append('?')
                elif self.board[r][c] == -1:
                    row.append('*')
                else:
                    row.append(str(self.board[r][c]))
            lines.append(' '.join(row))
        return '\n'.join(lines)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/run_game':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            game_id = data.get('game_id')
            if not game_id:
                self.send_error(400, "Missing game_id")
                return
            
            # Run a simple demo game
            result = self.run_demo_game(game_id)
            
            self.send_json_response(result)
        else:
            self.send_error(404)
    
    def run_demo_game(self, game_id):
        """Run a demo Minesweeper game."""
        start_time = time.time()
        
        # Create game
        game = SimpleMinesweeper(9, 9, 10)
        moves = []
        move_count = 0
        
        # Make some demo moves
        demo_moves = [
            ('reveal', 4, 4),
            ('reveal', 0, 0),
            ('flag', 2, 3),
            ('reveal', 6, 7),
            ('reveal', 8, 8)
        ]
        
        for action, row, col in demo_moves:
            move_count += 1
            
            if action == 'reveal':
                valid, message = game.reveal(row, col)
            else:
                valid, message = game.flag(row, col)
            
            moves.append({
                "move_number": move_count,
                "action": action,
                "position": [row, col],
                "valid": valid,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if game.game_over:
                break
        
        duration = time.time() - start_time
        
        return {
            "game_id": game_id,
            "status": "completed",
            "won": game.won,
            "total_moves": move_count,
            "valid_moves": sum(1 for m in moves if m["valid"]),
            "duration": duration,
            "moves": moves,
            "final_board": game.get_board_state()
        }
    
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