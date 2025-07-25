"""Minesweeper game implementation for Vercel."""
import random
from typing import Dict, List, Tuple, Optional, Set
from .base import BaseGame, GameMove, GameState

class MinesweeperGame(BaseGame):
    """Minesweeper game implementation."""
    
    DIFFICULTY_SETTINGS = {
        "easy": {"rows": 9, "cols": 9, "mines": 10},
        "medium": {"rows": 16, "cols": 16, "mines": 40},
        "hard": {"rows": 16, "cols": 30, "mines": 99}
    }
    
    def __init__(self, difficulty: str = "medium", **kwargs):
        super().__init__(difficulty, **kwargs)
        settings = self.DIFFICULTY_SETTINGS.get(difficulty, self.DIFFICULTY_SETTINGS["medium"])
        self.rows = kwargs.get("rows", settings["rows"])
        self.cols = kwargs.get("cols", settings["cols"])
        self.num_mines = kwargs.get("mines", settings["mines"])
        self.board = None
        self.visible = None
        self.flags = None
        self.mines = None
        self.first_move = True
    
    def new_game(self) -> GameState:
        """Start a new Minesweeper game."""
        # Initialize empty board
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.visible = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.flags = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.mines = set()
        self.first_move = True
        
        self.state = GameState(
            board=self._get_visible_board(),
            status="in_progress",
            moves=[],
            turn_count=0
        )
        return self.state
    
    def _place_mines(self, avoid_row: int, avoid_col: int):
        """Place mines on the board, avoiding the first click position."""
        # Get all valid positions
        positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                # Avoid 3x3 area around first click
                if abs(r - avoid_row) <= 1 and abs(c - avoid_col) <= 1:
                    continue
                positions.append((r, c))
        
        # Randomly select mine positions
        mine_positions = random.sample(positions, min(self.num_mines, len(positions)))
        self.mines = set(mine_positions)
        
        # Place mines on board
        for r, c in mine_positions:
            self.board[r][c] = -1
        
        # Calculate numbers
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
    
    def _get_visible_board(self) -> List[List[str]]:
        """Get the board as seen by the player."""
        visible_board = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if self.flags[r][c]:
                    row.append("F")  # Flag
                elif not self.visible[r][c]:
                    row.append("?")  # Unknown
                elif self.board[r][c] == -1:
                    row.append("*")  # Mine (game over)
                else:
                    row.append(str(self.board[r][c]))  # Number
            visible_board.append(row)
        return visible_board
    
    def _reveal_cell(self, row: int, col: int) -> bool:
        """Reveal a cell and return if it was safe."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False
        
        if self.visible[row][col] or self.flags[row][col]:
            return False
        
        self.visible[row][col] = True
        
        # Hit a mine
        if self.board[row][col] == -1:
            return False
        
        # Auto-reveal empty cells
        if self.board[row][col] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.visible[nr][nc] and not self.flags[nr][nc]:
                            self._reveal_cell(nr, nc)
        
        return True
    
    def make_move(self, move: GameMove) -> Tuple[bool, str]:
        """Make a move in Minesweeper."""
        if self.state.status != "in_progress":
            return False, "Game is already over"
        
        row, col = move.position
        
        # Validate position
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return False, f"Invalid position: ({row}, {col})"
        
        # Place mines on first move
        if self.first_move and move.action == "reveal":
            self._place_mines(row, col)
            self.first_move = False
        
        # Execute move
        if move.action == "reveal":
            if self.visible[row][col]:
                return False, f"Cell ({row}, {col}) is already revealed"
            if self.flags[row][col]:
                return False, f"Cannot reveal flagged cell ({row}, {col})"
            
            safe = self._reveal_cell(row, col)
            if not safe:
                self.state.status = "lost"
                # Reveal all mines
                for r, c in self.mines:
                    self.visible[r][c] = True
            else:
                # Check for win
                if self._check_win():
                    self.state.status = "won"
        
        elif move.action == "flag":
            if self.visible[row][col]:
                return False, f"Cannot flag revealed cell ({row}, {col})"
            if self.flags[row][col]:
                return False, f"Cell ({row}, {col}) is already flagged"
            self.flags[row][col] = True
        
        elif move.action == "unflag":
            if not self.flags[row][col]:
                return False, f"Cell ({row}, {col}) is not flagged"
            self.flags[row][col] = False
        
        else:
            return False, f"Invalid action: {move.action}"
        
        # Update state
        self.state.moves.append(move)
        self.state.turn_count += 1
        self.state.board = self._get_visible_board()
        
        return True, "Move successful"
    
    def _check_win(self) -> bool:
        """Check if the game is won."""
        for r in range(self.rows):
            for c in range(self.cols):
                # All non-mine cells must be revealed
                if self.board[r][c] != -1 and not self.visible[r][c]:
                    return False
        return True
    
    def get_board_state_for_ai(self) -> str:
        """Get board state formatted for AI."""
        visible_board = self._get_visible_board()
        board_str = "Current Minesweeper board:\n"
        
        # Add column headers
        board_str += "   "
        for c in range(self.cols):
            board_str += f"{c:2} "
        board_str += "\n"
        
        # Add rows
        for r in range(self.rows):
            board_str += f"{r:2} "
            for c in range(self.cols):
                board_str += f" {visible_board[r][c]} "
            board_str += "\n"
        
        # Add game info
        total_mines = self.num_mines
        flagged = sum(row.count(True) for row in self.flags)
        board_str += f"\nTotal mines: {total_mines}"
        board_str += f"\nFlagged cells: {flagged}"
        board_str += f"\nRemaining mines: {total_mines - flagged}"
        
        return board_str
    
    def get_valid_moves(self) -> List[Dict[str, Any]]:
        """Get all valid moves in current state."""
        moves = []
        
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.visible[r][c]:
                    if not self.flags[r][c]:
                        moves.append({
                            "action": "reveal",
                            "position": [r, c]
                        })
                        moves.append({
                            "action": "flag",
                            "position": [r, c]
                        })
                    else:
                        moves.append({
                            "action": "unflag",
                            "position": [r, c]
                        })
        
        return moves
    
    def is_game_over(self) -> bool:
        """Check if game is finished."""
        return self.state.status != "in_progress"
    
    def get_function_schema(self) -> Dict[str, Any]:
        """Get function calling schema for Minesweeper."""
        return {
            "name": "make_move",
            "description": "Make a move in Minesweeper",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reveal", "flag", "unflag"],
                        "description": "The action to perform"
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
                        "description": "Explanation for this move"
                    }
                },
                "required": ["action", "row", "col", "reasoning"]
            }
        }