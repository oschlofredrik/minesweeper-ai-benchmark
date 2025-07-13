"""Shared type definitions for the Minesweeper benchmark platform."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid


class CellState(Enum):
    """State of a cell in the Minesweeper grid."""
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"


class GameStatus(Enum):
    """Status of a Minesweeper game."""
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class ActionType(Enum):
    """Types of actions in Minesweeper."""
    REVEAL = "reveal"
    FLAG = "flag"
    UNFLAG = "unflag"


class TaskType(Enum):
    """Types of benchmark tasks."""
    STATIC = "static"  # Single-turn puzzle
    INTERACTIVE = "interactive"  # Full game


class Difficulty(Enum):
    """Difficulty levels for tasks."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


@dataclass
class Position:
    """Position on the board."""
    row: int
    col: int
    
    def __hash__(self) -> int:
        return hash((self.row, self.col))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col


@dataclass
class Action:
    """An action in the game."""
    action_type: ActionType
    position: Position
    
    def to_string(self) -> str:
        """Convert action to string representation."""
        return f"{self.action_type.value} ({self.position.row}, {self.position.col})"


@dataclass
class GameState:
    """Complete state of a Minesweeper game."""
    board_rows: int
    board_cols: int
    mine_positions: List[Position]
    revealed_cells: Dict[Position, int]  # Position -> adjacent mine count
    flagged_cells: List[Position]
    status: GameStatus
    moves_made: int
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def is_finished(self) -> bool:
        """Check if game is finished."""
        return self.status in [GameStatus.WON, GameStatus.LOST]


@dataclass
class Move:
    """A single move in the game with metadata."""
    action: Action
    timestamp: datetime
    board_state_before: str  # Text representation
    board_state_after: Optional[str] = None
    model_reasoning: Optional[str] = None
    was_valid: bool = True
    error_message: Optional[str] = None


@dataclass
class GameTranscript:
    """Complete transcript of a game."""
    game_id: str
    task_id: str
    model_name: str
    moves: List[Move]
    final_state: GameState
    start_time: datetime
    end_time: datetime
    
    @property
    def duration_seconds(self) -> float:
        """Calculate game duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def num_moves(self) -> int:
        """Get number of moves made."""
        return len(self.moves)


@dataclass
class EvaluationMetrics:
    """Metrics for evaluating model performance."""
    win_rate: float
    valid_move_rate: float
    mine_identification_precision: float
    mine_identification_recall: float
    average_moves_to_win: Optional[float]
    average_moves_to_loss: Optional[float]
    board_coverage_on_loss: float
    reasoning_quality_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "win_rate": self.win_rate,
            "valid_move_rate": self.valid_move_rate,
            "mine_identification_precision": self.mine_identification_precision,
            "mine_identification_recall": self.mine_identification_recall,
            "average_moves_to_win": self.average_moves_to_win,
            "average_moves_to_loss": self.average_moves_to_loss,
            "board_coverage_on_loss": self.board_coverage_on_loss,
            "reasoning_quality_score": self.reasoning_quality_score,
        }


@dataclass
class Task:
    """A benchmark task."""
    task_id: str
    task_type: TaskType
    difficulty: Difficulty
    board_config: Dict[str, Any]
    description: str
    metadata: Dict[str, Any]
    created_at: datetime
    
    @classmethod
    def create(
        cls,
        task_type: TaskType,
        difficulty: Difficulty,
        board_config: Dict[str, Any],
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Task":
        """Create a new task with generated ID."""
        return cls(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            difficulty=difficulty,
            board_config=board_config,
            description=description,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    provider: str  # "openai", "anthropic", "local"
    model_id: str  # e.g., "gpt-4", "claude-3"
    temperature: float = 0.7
    max_tokens: int = 1000
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        if self.additional_params is None:
            self.additional_params = {}