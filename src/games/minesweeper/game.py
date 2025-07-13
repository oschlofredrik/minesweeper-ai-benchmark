"""Minesweeper game implementation with full game flow."""

from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import uuid

from src.core.types import (
    GameState, GameStatus, Action, ActionType, Position,
    Move, GameTranscript
)
from src.core.exceptions import (
    InvalidMoveError, GameAlreadyFinishedError, InvalidBoardConfigError
)
from .board import MinesweeperBoard


class MinesweeperGame:
    """Main Minesweeper game class managing game flow and state."""
    
    def __init__(
        self,
        rows: int = 16,
        cols: int = 30,
        mines: int = 99,
        seed: Optional[int] = None,
        game_id: Optional[str] = None,
        task_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize a new Minesweeper game.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            mines: Number of mines
            seed: Random seed for reproducibility
            game_id: Unique game identifier
            task_id: Task identifier for benchmarking
            model_name: Name of the model playing the game
        """
        self.game_id = game_id or str(uuid.uuid4())
        self.task_id = task_id or "unknown"
        self.model_name = model_name or "unknown"
        
        # Initialize board
        self.board = MinesweeperBoard(rows, cols, mines, seed)
        
        # Game state
        self.status = GameStatus.IN_PROGRESS
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.moves: List[Move] = []
        self.first_move_safe = True  # Common Minesweeper rule
        
        # Statistics
        self.cells_revealed = 0
        self.flags_placed = 0
        self.correct_flags = 0
    
    def make_move(self, action: Action, ai_details: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Execute a move in the game.
        
        Args:
            action: The action to perform
            ai_details: Optional dict with AI interaction details (prompt, response, etc.)
        
        Returns:
            Tuple of (success, message, game_info)
        """
        if self.status != GameStatus.IN_PROGRESS:
            raise GameAlreadyFinishedError(
                f"Game is already {self.status.value}. No more moves allowed."
            )
        
        # Get current board state for the move record
        board_before = self.board.to_ascii()
        timestamp = datetime.utcnow()
        
        try:
            # Validate position
            if not self._is_valid_position(action.position):
                raise InvalidMoveError(
                    f"Position ({action.position.row}, {action.position.col}) is out of bounds"
                )
            
            # Execute action based on type
            if action.action_type == ActionType.REVEAL:
                success, message, info = self._handle_reveal(action.position)
            elif action.action_type == ActionType.FLAG:
                success, message, info = self._handle_flag(action.position)
            elif action.action_type == ActionType.UNFLAG:
                success, message, info = self._handle_unflag(action.position)
            else:
                raise InvalidMoveError(f"Unknown action type: {action.action_type}")
            
            # Get board state after move
            board_after = self.board.to_ascii()
            
            # Record move with AI details if provided
            move = Move(
                action=action,
                timestamp=timestamp,
                board_state_before=board_before,
                board_state_after=board_after,
                was_valid=success,
                error_message=None if success else message,
                prompt_sent=ai_details.get('prompt_sent') if ai_details else None,
                full_response=ai_details.get('full_response') if ai_details else None,
                model_reasoning=ai_details.get('model_reasoning') if ai_details else None,
                tokens_used=ai_details.get('tokens_used') if ai_details else None,
            )
            self.moves.append(move)
            
            # Check for game completion
            self._check_game_completion()
            
            # Add game status to info
            info["game_status"] = self.status.value
            info["moves_made"] = len(self.moves)
            
            return success, message, info
            
        except Exception as e:
            # Record failed move with AI details
            move = Move(
                action=action,
                timestamp=timestamp,
                board_state_before=board_before,
                board_state_after=None,
                was_valid=False,
                error_message=str(e),
                prompt_sent=ai_details.get('prompt_sent') if ai_details else None,
                full_response=ai_details.get('full_response') if ai_details else None,
                model_reasoning=ai_details.get('model_reasoning') if ai_details else None,
                tokens_used=ai_details.get('tokens_used') if ai_details else None,
            )
            self.moves.append(move)
            raise
    
    def _handle_reveal(self, pos: Position) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle reveal action."""
        cell = self.board.get_cell(pos)
        
        # Check if cell can be revealed
        if cell.is_revealed:
            return False, "Cell is already revealed", {"cells_revealed": 0}
        
        if cell.is_flagged:
            return False, "Cannot reveal flagged cell", {"cells_revealed": 0}
        
        # Special handling for first move
        if self.first_move_safe and len(self.moves) == 0 and cell.has_mine:
            # Move the mine to a different location
            self._relocate_mine_for_first_move(pos)
        
        # Reveal the cell
        hit_mine, revealed_positions = self.board.reveal_cell(pos)
        
        if hit_mine:
            self.status = GameStatus.LOST
            self.end_time = datetime.utcnow()
            return True, "Hit a mine! Game over.", {
                "hit_mine": True,
                "cells_revealed": len(revealed_positions),
                "mine_position": {"row": pos.row, "col": pos.col}
            }
        
        self.cells_revealed += len(revealed_positions)
        
        return True, f"Revealed {len(revealed_positions)} cells", {
            "cells_revealed": len(revealed_positions),
            "revealed_positions": [
                {"row": p.row, "col": p.col} for p in revealed_positions
            ]
        }
    
    def _handle_flag(self, pos: Position) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle flag action."""
        success = self.board.flag_cell(pos)
        
        if not success:
            return False, "Cannot flag this cell", {"flag_placed": False}
        
        self.flags_placed += 1
        if self.board.get_cell(pos).has_mine:
            self.correct_flags += 1
        
        return True, "Cell flagged", {
            "flag_placed": True,
            "total_flags": self.flags_placed
        }
    
    def _handle_unflag(self, pos: Position) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle unflag action."""
        cell = self.board.get_cell(pos)
        was_correct_flag = cell.is_flagged and cell.has_mine
        
        success = self.board.unflag_cell(pos)
        
        if not success:
            return False, "Cell is not flagged", {"flag_removed": False}
        
        self.flags_placed -= 1
        if was_correct_flag:
            self.correct_flags -= 1
        
        return True, "Flag removed", {
            "flag_removed": True,
            "total_flags": self.flags_placed
        }
    
    def _is_valid_position(self, pos: Position) -> bool:
        """Check if position is valid."""
        return 0 <= pos.row < self.board.rows and 0 <= pos.col < self.board.cols
    
    def _relocate_mine_for_first_move(self, pos: Position) -> None:
        """Relocate mine if first move would hit it."""
        # Find a safe position without a mine
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                new_pos = Position(row, col)
                if new_pos != pos and not self.board.get_cell(new_pos).has_mine:
                    # Move mine to new position
                    self.board.get_cell(pos).has_mine = False
                    self.board.get_cell(new_pos).has_mine = True
                    # Recalculate adjacent mines
                    self.board._calculate_adjacent_mines()
                    return
    
    def _check_game_completion(self) -> None:
        """Check if the game has been won."""
        if self.status != GameStatus.IN_PROGRESS:
            return
        
        game_state = self.board.get_game_state()
        
        if game_state["is_won"]:
            self.status = GameStatus.WON
            self.end_time = datetime.utcnow()
    
    def get_current_state(self) -> GameState:
        """Get current game state."""
        revealed_cells = {}
        flagged_cells = []
        
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                pos = Position(row, col)
                cell = self.board.get_cell(pos)
                
                if cell.is_revealed:
                    revealed_cells[pos] = cell.adjacent_mines
                elif cell.is_flagged:
                    flagged_cells.append(pos)
        
        return GameState(
            board_rows=self.board.rows,
            board_cols=self.board.cols,
            mine_positions=self.board.get_mine_positions(),
            revealed_cells=revealed_cells,
            flagged_cells=flagged_cells,
            status=self.status,
            moves_made=len(self.moves),
            start_time=self.start_time,
            end_time=self.end_time,
        )
    
    def get_board_representation(self, format_type: str = "ascii") -> str:
        """
        Get board representation in specified format.
        
        Args:
            format_type: "ascii" or "coordinate"
        
        Returns:
            String representation of the board
        """
        if format_type == "ascii":
            return self.board.to_ascii(show_mines=(self.status == GameStatus.LOST))
        elif format_type == "coordinate":
            import json
            return json.dumps(self.board.to_coordinate_list(), indent=2)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
    
    def get_valid_moves(self) -> List[Action]:
        """Get all valid moves in current state."""
        if self.status != GameStatus.IN_PROGRESS:
            return []
        
        valid_moves = []
        
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                pos = Position(row, col)
                cell = self.board.get_cell(pos)
                
                if cell.is_hidden:
                    # Can reveal or flag hidden cells
                    valid_moves.append(Action(ActionType.REVEAL, pos))
                    valid_moves.append(Action(ActionType.FLAG, pos))
                elif cell.is_flagged:
                    # Can unflag flagged cells
                    valid_moves.append(Action(ActionType.UNFLAG, pos))
        
        return valid_moves
    
    def get_transcript(self) -> GameTranscript:
        """Get complete game transcript."""
        return GameTranscript(
            game_id=self.game_id,
            task_id=self.task_id,
            model_name=self.model_name,
            moves=self.moves,
            final_state=self.get_current_state(),
            start_time=self.start_time,
            end_time=self.end_time or datetime.utcnow(),
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get game statistics."""
        total_cells = self.board.rows * self.board.cols
        non_mine_cells = total_cells - self.board.total_mines
        
        return {
            "game_id": self.game_id,
            "status": self.status.value,
            "moves_made": len(self.moves),
            "cells_revealed": self.cells_revealed,
            "cells_remaining": non_mine_cells - self.cells_revealed,
            "flags_placed": self.flags_placed,
            "correct_flags": self.correct_flags,
            "incorrect_flags": self.flags_placed - self.correct_flags,
            "board_coverage": self.cells_revealed / non_mine_cells if non_mine_cells > 0 else 0,
            "duration_seconds": (
                (self.end_time or datetime.utcnow()) - self.start_time
            ).total_seconds(),
        }