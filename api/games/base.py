"""Base game interface for Vercel deployment."""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class GameMove:
    """Represents a move in a game."""
    action: str  # 'reveal', 'flag', 'unflag' for Minesweeper
    position: Tuple[int, int]  # (row, col)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "position": list(self.position),
            "reasoning": self.reasoning
        }

@dataclass
class GameState:
    """Current state of a game."""
    board: Any  # Game-specific board representation
    status: str  # 'in_progress', 'won', 'lost'
    moves: List[GameMove]
    turn_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "turn_count": self.turn_count,
            "moves": [m.to_dict() for m in self.moves]
        }

class BaseGame(ABC):
    """Abstract base class for games."""
    
    def __init__(self, difficulty: str = "medium", **kwargs):
        self.difficulty = difficulty
        self.state = None
        self.config = kwargs
    
    @abstractmethod
    def new_game(self) -> GameState:
        """Start a new game."""
        pass
    
    @abstractmethod
    def make_move(self, move: GameMove) -> Tuple[bool, str]:
        """
        Make a move in the game.
        Returns: (is_valid, message)
        """
        pass
    
    @abstractmethod
    def get_board_state_for_ai(self) -> str:
        """Get board state formatted for AI understanding."""
        pass
    
    @abstractmethod
    def get_valid_moves(self) -> List[Dict[str, Any]]:
        """Get list of valid moves in current state."""
        pass
    
    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if game is finished."""
        pass
    
    @abstractmethod
    def get_function_schema(self) -> Dict[str, Any]:
        """Get function calling schema for this game."""
        pass
    
    def get_state_dict(self) -> Dict[str, Any]:
        """Get complete game state as dictionary."""
        return {
            "game_type": self.__class__.__name__.lower().replace("game", ""),
            "difficulty": self.difficulty,
            "state": self.state.to_dict() if self.state else None,
            "config": self.config
        }