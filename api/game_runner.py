"""Simplified game runner for Vercel with AI integration."""
from http.server import BaseHTTPRequestHandler
import json
import os
import random
import time
from datetime import datetime
import uuid
import sys

# Import game implementations inline to avoid complex imports
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
    
    def to_json_state(self):
        """Convert to JSON-serializable state."""
        return {
            'board': self.get_board_state(),
            'game_over': self.game_over,
            'won': self.won,
            'revealed_count': sum(1 for r in range(self.rows) for c in range(self.cols) if self.visible[r][c]),
            'flag_count': sum(1 for r in range(self.rows) for c in range(self.cols) if self.flags[r][c])
        }


class SimpleRisk:
    """Simplified Risk game."""
    def __init__(self, scenario=None):
        self.territories = {}
        self.players = {}
        self.current_player = 'player_0'
        self.phase = 'reinforce'
        self.game_over = False
        self.winner = None
        self.turn = 1
        self.reinforcements = 5
        
        # Initialize a simple map
        self._initialize_territories()
        
        if scenario:
            self._load_scenario(scenario)
        else:
            self._default_setup()
    
    def _initialize_territories(self):
        """Initialize territory connections (simplified)."""
        # Just a few territories for demo
        territories = [
            ('north_america', 'alaska'),
            ('north_america', 'northwest_territory'),
            ('north_america', 'alberta'),
            ('north_america', 'ontario'),
            ('north_america', 'greenland'),
            ('north_america', 'eastern_us'),
            ('north_america', 'western_us'),
            ('south_america', 'venezuela'),
            ('south_america', 'brazil'),
            ('south_america', 'argentina'),
            ('europe', 'great_britain'),
            ('europe', 'scandinavia'),
            ('europe', 'ukraine'),
            ('europe', 'southern_europe'),
            ('asia', 'ural'),
            ('asia', 'siberia'),
            ('asia', 'china'),
            ('asia', 'india'),
            ('africa', 'north_africa'),
            ('africa', 'egypt'),
            ('africa', 'south_africa'),
            ('australia', 'indonesia'),
            ('australia', 'eastern_australia')
        ]
        
        for continent, territory in territories:
            self.territories[territory] = {
                'continent': continent,
                'owner': None,
                'armies': 0
            }
    
    def _default_setup(self):
        """Default game setup."""
        # Randomly assign territories
        territory_list = list(self.territories.keys())
        random.shuffle(territory_list)
        
        # Two players
        self.players = {
            'player_0': {'territories': [], 'color': 'Red'},
            'player_1': {'territories': [], 'color': 'Blue'}
        }
        
        # Distribute territories
        for i, territory in enumerate(territory_list):
            player = 'player_0' if i % 2 == 0 else 'player_1'
            self.territories[territory]['owner'] = player
            self.territories[territory]['armies'] = random.randint(1, 3)
            self.players[player]['territories'].append(territory)
    
    def _load_scenario(self, scenario_name):
        """Load a predefined scenario."""
        # Simplified scenario loading
        if scenario_name == 'north_america_conquest':
            # Player 0 owns most of North America
            for territory in ['alaska', 'northwest_territory', 'alberta', 'ontario', 'eastern_us', 'western_us']:
                self.territories[territory]['owner'] = 'player_0'
                self.territories[territory]['armies'] = random.randint(3, 7)
            
            # Player 1 holds out
            for territory in ['greenland', 'venezuela', 'brazil']:
                self.territories[territory]['owner'] = 'player_1'
                self.territories[territory]['armies'] = random.randint(4, 8)
            
            # Rest to player 1
            for tid, tdata in self.territories.items():
                if tdata['owner'] is None:
                    tdata['owner'] = 'player_1'
                    tdata['armies'] = random.randint(2, 4)
            
            self._update_player_territories()
    
    def _update_player_territories(self):
        """Update player territory lists."""
        self.players = {
            'player_0': {'territories': [], 'color': 'Red'},
            'player_1': {'territories': [], 'color': 'Blue'}
        }
        
        for tid, tdata in self.territories.items():
            owner = tdata['owner']
            if owner in self.players:
                self.players[owner]['territories'].append(tid)
    
    def reinforce(self, territory, armies):
        """Place reinforcements."""
        if self.phase != 'reinforce':
            return False, "Not in reinforce phase"
        
        if territory not in self.territories:
            return False, "Invalid territory"
        
        if self.territories[territory]['owner'] != self.current_player:
            return False, "You don't own this territory"
        
        if armies > self.reinforcements:
            return False, "Not enough reinforcements"
        
        self.territories[territory]['armies'] += armies
        self.reinforcements -= armies
        
        if self.reinforcements == 0:
            self.phase = 'attack'
        
        return True, f"Placed {armies} armies in {territory}"
    
    def attack(self, from_territory, to_territory, armies):
        """Simplified attack."""
        if self.phase != 'attack':
            return False, "Not in attack phase"
        
        # Validate territories
        if from_territory not in self.territories or to_territory not in self.territories:
            return False, "Invalid territory"
        
        if self.territories[from_territory]['owner'] != self.current_player:
            return False, "You don't own the attacking territory"
        
        if self.territories[to_territory]['owner'] == self.current_player:
            return False, "Can't attack your own territory"
        
        if self.territories[from_territory]['armies'] <= armies:
            return False, "Not enough armies"
        
        # Simplified combat - just random outcome
        attacker_dice = min(armies, 3)
        defender_dice = min(self.territories[to_territory]['armies'], 2)
        
        # Roll dice
        attacker_rolls = sorted([random.randint(1, 6) for _ in range(attacker_dice)], reverse=True)
        defender_rolls = sorted([random.randint(1, 6) for _ in range(defender_dice)], reverse=True)
        
        # Compare rolls
        attacker_losses = 0
        defender_losses = 0
        
        for i in range(min(len(attacker_rolls), len(defender_rolls))):
            if attacker_rolls[i] > defender_rolls[i]:
                defender_losses += 1
            else:
                attacker_losses += 1
        
        # Apply losses
        self.territories[from_territory]['armies'] -= attacker_losses
        self.territories[to_territory]['armies'] -= defender_losses
        
        # Check if territory conquered
        if self.territories[to_territory]['armies'] == 0:
            old_owner = self.territories[to_territory]['owner']
            self.territories[to_territory]['owner'] = self.current_player
            self.territories[to_territory]['armies'] = armies - attacker_losses
            self.territories[from_territory]['armies'] -= (armies - attacker_losses)
            
            # Update player territories
            self.players[self.current_player]['territories'].append(to_territory)
            self.players[old_owner]['territories'].remove(to_territory)
            
            # Check if player eliminated
            if len(self.players[old_owner]['territories']) == 0:
                self.game_over = True
                self.winner = self.current_player
                return True, f"Conquered {to_territory} and eliminated {old_owner}!"
            
            return True, f"Conquered {to_territory}!"
        
        return True, f"Attack resulted in {attacker_losses} attacker losses, {defender_losses} defender losses"
    
    def end_attack(self):
        """End attack phase."""
        if self.phase != 'attack':
            return False, "Not in attack phase"
        self.phase = 'fortify'
        return True, "Attack phase ended"
    
    def fortify(self, from_territory, to_territory, armies):
        """Move armies between territories."""
        # Simplified - allow any movement between owned territories
        if self.phase != 'fortify':
            return False, "Not in fortify phase"
        
        if from_territory not in self.territories or to_territory not in self.territories:
            return False, "Invalid territory"
        
        if self.territories[from_territory]['owner'] != self.current_player:
            return False, "You don't own the source territory"
        
        if self.territories[to_territory]['owner'] != self.current_player:
            return False, "You don't own the destination territory"
        
        if self.territories[from_territory]['armies'] <= armies:
            return False, "Must leave at least 1 army"
        
        self.territories[from_territory]['armies'] -= armies
        self.territories[to_territory]['armies'] += armies
        
        # End turn
        self._next_turn()
        
        return True, f"Moved {armies} armies from {from_territory} to {to_territory}"
    
    def skip_fortify(self):
        """Skip fortify phase."""
        if self.phase != 'fortify':
            return False, "Not in fortify phase"
        self._next_turn()
        return True, "Skipped fortify phase"
    
    def _next_turn(self):
        """Move to next turn."""
        self.turn += 1
        self.phase = 'reinforce'
        self.current_player = 'player_1' if self.current_player == 'player_0' else 'player_0'
        
        # Calculate reinforcements (simplified)
        territory_count = len(self.players[self.current_player]['territories'])
        self.reinforcements = max(3, territory_count // 3)
    
    def to_json_state(self):
        """Convert to JSON-serializable state."""
        return {
            'territories': self.territories,
            'players': self.players,
            'current_player': self.current_player,
            'phase': self.phase,
            'turn': self.turn,
            'game_over': self.game_over,
            'winner': self.winner,
            'reinforcements': self.reinforcements if self.phase == 'reinforce' else 0
        }
    
    def get_board_state(self):
        """Get text representation for AI."""
        lines = [f"=== RISK - Turn {self.turn} - {self.phase.upper()} Phase ==="]
        lines.append(f"Current Player: {self.current_player}")
        
        if self.phase == 'reinforce':
            lines.append(f"Reinforcements Available: {self.reinforcements}")
        
        lines.append("\nYour Territories:")
        for tid in self.players[self.current_player]['territories']:
            tdata = self.territories[tid]
            lines.append(f"- {tid}: {tdata['armies']} armies ({tdata['continent']})")
        
        lines.append("\nEnemy Territories:")
        enemy = 'player_1' if self.current_player == 'player_0' else 'player_0'
        for tid in self.players[enemy]['territories']:
            tdata = self.territories[tid]
            lines.append(f"- {tid}: {tdata['armies']} armies ({tdata['continent']})")
        
        return '\n'.join(lines)


# AI integration functions
def get_minesweeper_prompt(game):
    """Generate prompt for Minesweeper AI."""
    return f"""You are playing Minesweeper. The board uses these symbols:
- ?: Hidden cell
- F: Flagged cell
- 0-8: Revealed cell with number of adjacent mines
- *: Mine (game over)

Current board state:
{game.get_board_state()}

Make your next move. Think step by step about which cell to reveal or flag based on the numbers shown."""


def get_risk_prompt(game):
    """Generate prompt for Risk AI."""
    return f"""You are playing Risk, a strategic territory conquest game.

{game.get_board_state()}

Available actions based on current phase:
- reinforce: Place armies on your territories
- attack: Attack enemy territories
- end_attack: End attack phase and move to fortify
- fortify: Move armies between your territories
- skip_fortify: Skip fortify and end turn

Make your next move. Consider your strategic position and objectives."""


def get_function_schema(game_type):
    """Get function calling schema for each game."""
    if game_type == 'minesweeper':
        return {
            "name": "make_move",
            "description": "Make a move in Minesweeper",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reveal", "flag"],
                        "description": "Action to take"
                    },
                    "row": {
                        "type": "integer",
                        "description": "Row index (0-based)"
                    },
                    "col": {
                        "type": "integer",
                        "description": "Column index (0-based)"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of your reasoning"
                    }
                },
                "required": ["action", "row", "col", "reasoning"]
            }
        }
    else:  # risk
        return {
            "name": "make_move",
            "description": "Make a move in Risk",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reinforce", "attack", "end_attack", "fortify", "skip_fortify"],
                        "description": "Action to take"
                    },
                    "territory": {
                        "type": "string",
                        "description": "Territory for reinforce action"
                    },
                    "from": {
                        "type": "string",
                        "description": "Source territory for attack/fortify"
                    },
                    "to": {
                        "type": "string",
                        "description": "Target territory for attack/fortify"
                    },
                    "armies": {
                        "type": "integer",
                        "description": "Number of armies",
                        "minimum": 1
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Strategic reasoning"
                    }
                },
                "required": ["action", "reasoning"]
            }
        }


# Import AI models module
sys.path.append(os.path.dirname(__file__))
try:
    from ai_models import call_ai_model as call_ai_api, format_game_messages, extract_function_call
except ImportError:
    # Fallback if import fails
    def call_ai_api(*args, **kwargs):
        return {"error": "AI models module not available"}
    def format_game_messages(*args, **kwargs):
        return []
    def extract_function_call(*args, **kwargs):
        return None


def call_ai_model(prompt, function_schema, model_name, provider, game_type):
    """Call AI model with function calling."""
    # Format messages
    messages = format_game_messages(game_type, prompt)
    
    # Call AI API
    response = call_ai_api(
        provider=provider,
        model=model_name,
        messages=messages,
        functions=[function_schema],
        temperature=0.7
    )
    
    # Check for errors
    if "error" in response:
        print(f"AI API Error: {response['error']}")
        # Fallback to demo move
        if game_type == 'minesweeper':
            return {
                "action": "reveal",
                "row": random.randint(0, 8),
                "col": random.randint(0, 8),
                "reasoning": "Demo move due to API error"
            }
        else:
            return {
                "action": "reinforce",
                "territory": "alaska",
                "armies": 3,
                "reasoning": "Demo move due to API error"
            }
    
    # Extract function call
    function_args = extract_function_call(response)
    if function_args:
        return function_args
    
    # Try to parse from content if no function call
    # This handles models that don't support function calling
    content = response.get("content", "")
    if content:
        # Simple parsing logic for non-function-calling models
        if game_type == 'minesweeper':
            # Look for patterns like "reveal (3, 4)" or "flag at row 3, col 4"
            import re
            reveal_match = re.search(r"reveal.*?(\d+).*?(\d+)", content.lower())
            flag_match = re.search(r"flag.*?(\d+).*?(\d+)", content.lower())
            
            if reveal_match:
                return {
                    "action": "reveal",
                    "row": int(reveal_match.group(1)),
                    "col": int(reveal_match.group(2)),
                    "reasoning": content
                }
            elif flag_match:
                return {
                    "action": "flag",
                    "row": int(flag_match.group(1)),
                    "col": int(flag_match.group(2)),
                    "reasoning": content
                }
    
    # Final fallback
    if game_type == 'minesweeper':
        return {
            "action": "reveal",
            "row": random.randint(0, 8),
            "col": random.randint(0, 8),
            "reasoning": "Could not parse AI response, using random move"
        }
    else:
        return {
            "action": "reinforce",
            "territory": "alaska",
            "armies": 3,
            "reasoning": "Could not parse AI response, using default move"
        }


def execute_minesweeper_move(game, move):
    """Execute a Minesweeper move."""
    action = move.get('action')
    row = move.get('row', 0)
    col = move.get('col', 0)
    
    if action == 'reveal':
        return game.reveal(row, col)
    elif action == 'flag':
        return game.flag(row, col)
    else:
        return False, "Invalid action"


def execute_risk_move(game, move):
    """Execute a Risk move."""
    action = move.get('action')
    
    if action == 'reinforce':
        return game.reinforce(move.get('territory'), move.get('armies', 1))
    elif action == 'attack':
        return game.attack(move.get('from'), move.get('to'), move.get('armies', 1))
    elif action == 'end_attack':
        return game.end_attack()
    elif action == 'fortify':
        return game.fortify(move.get('from'), move.get('to'), move.get('armies', 1))
    elif action == 'skip_fortify':
        return game.skip_fortify()
    else:
        return False, "Invalid action"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/game_runner/play':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            game_type = data.get('game_type', 'minesweeper')
            config = data.get('config', {})
            model_name = data.get('model', 'gpt-4')
            provider = data.get('provider', 'openai')
            
            # Create game instance
            if game_type == 'minesweeper':
                game = SimpleMinesweeper(
                    rows=config.get('rows', 9),
                    cols=config.get('cols', 9),
                    mines=config.get('mines', 10)
                )
                get_prompt = get_minesweeper_prompt
                execute_move = execute_minesweeper_move
            else:  # risk
                game = SimpleRisk(scenario=config.get('scenario'))
                get_prompt = get_risk_prompt
                execute_move = execute_risk_move
            
            # Get function schema
            function_schema = get_function_schema(game_type)
            
            # Run game with AI
            moves = []
            max_moves = 50
            
            for move_num in range(max_moves):
                # Get current state
                game_state = game.to_json_state()
                
                # Generate prompt
                prompt = get_prompt(game)
                
                # Call AI with game type
                ai_response = call_ai_model(prompt, function_schema, model_name, provider, game_type)
                
                # Store token usage if available
                token_usage = None
                if isinstance(ai_response, dict) and 'usage' in ai_response:
                    token_usage = ai_response.get('usage')
                
                # Execute move
                valid, message = execute_move(game, ai_response)
                
                # Record move
                move_record = {
                    'move_number': move_num + 1,
                    'action': ai_response,
                    'valid': valid,
                    'message': message,
                    'game_state': game_state,
                    'timestamp': datetime.utcnow().isoformat(),
                    'prompt': prompt
                }
                
                if token_usage:
                    move_record['token_usage'] = token_usage
                
                moves.append(move_record)
                
                # Check game over
                if game.game_over:
                    break
            
            # Return result
            result = {
                'game_id': str(uuid.uuid4()),
                'game_type': game_type,
                'status': 'completed',
                'won': getattr(game, 'won', False) or getattr(game, 'winner', None) == 'player_0',
                'total_moves': len(moves),
                'moves': moves,
                'final_state': game.to_json_state()
            }
            
            self.send_json_response(result)
        else:
            self.send_error(404)
    
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