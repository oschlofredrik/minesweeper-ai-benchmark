"""Base classes for game plugins in the AI competition platform."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Type
from enum import Enum
import json
from datetime import datetime


class GameMode(Enum):
    """Available game modes for competitions."""
    SPEED = "speed"  # Fastest completion wins
    ACCURACY = "accuracy"  # Highest accuracy wins
    EFFICIENCY = "efficiency"  # Fewest moves wins
    CREATIVE = "creative"  # Most creative solution wins
    REASONING = "reasoning"  # Best explanation wins
    MIXED = "mixed"  # Custom weighted combination


@dataclass
class GameAction:
    """Generic action for any game."""
    action_type: str  # Game-specific action identifier
    parameters: Dict[str, Any]  # Action-specific parameters
    reasoning: Optional[str] = None  # AI's reasoning for this action


@dataclass
class GameState:
    """Generic game state representation."""
    state_data: Dict[str, Any]  # Game-specific state data
    is_terminal: bool  # Whether the game has ended
    is_victory: bool  # Whether the current state is a victory
    possible_actions: List[GameAction]  # Valid actions from this state
    
    def to_prompt_format(self) -> str:
        """Convert state to AI-friendly text representation."""
        return json.dumps(self.state_data, indent=2)


@dataclass
class GameResult:
    """Result of a completed game."""
    final_state: GameState
    moves_made: int
    time_taken: float  # seconds
    victory: bool
    score_components: Dict[str, float]  # Component scores for flexible scoring
    move_history: List[GameAction]
    error_message: Optional[str] = None


@dataclass
class ScoringComponent:
    """Definition of a scoring component."""
    name: str
    description: str
    min_value: float = 0.0
    max_value: float = 1.0
    higher_is_better: bool = True


@dataclass
class GameConfig:
    """Configuration for a game instance."""
    difficulty: str = "medium"  # easy, medium, hard, expert
    mode: GameMode = GameMode.MIXED
    custom_settings: Dict[str, Any] = None  # Game-specific settings
    time_limit: Optional[int] = None  # seconds
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}


class BaseGame(ABC):
    """Abstract base class for all games."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the game."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for the game."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the game."""
        pass
    
    @property
    @abstractmethod
    def supported_modes(self) -> List[GameMode]:
        """List of supported game modes."""
        pass
    
    @abstractmethod
    def get_scoring_components(self) -> List[ScoringComponent]:
        """Get available scoring components for this game."""
        pass
    
    @abstractmethod
    def create_instance(self, config: GameConfig) -> 'GameInstance':
        """Create a new game instance with given configuration."""
        pass
    
    @abstractmethod
    def get_ai_prompt_template(self) -> str:
        """Get the prompt template for AI players."""
        pass
    
    @abstractmethod
    def get_move_format_description(self) -> str:
        """Describe the expected move format for AI responses."""
        pass
    
    @abstractmethod
    def get_visualization_data(self, state: GameState) -> Dict[str, Any]:
        """Get data needed for frontend visualization."""
        pass


class GameInstance(ABC):
    """Abstract base class for game instances."""
    
    def __init__(self, config: GameConfig, instance_id: str):
        self.config = config
        self.instance_id = instance_id
        self.start_time = datetime.utcnow()
        self.move_count = 0
        self.move_history: List[GameAction] = []
    
    @abstractmethod
    def get_initial_state(self) -> GameState:
        """Get the initial game state."""
        pass
    
    @abstractmethod
    def apply_action(self, state: GameState, action: GameAction) -> Tuple[GameState, bool, str]:
        """
        Apply an action to the current state.
        
        Returns:
            - New game state
            - Whether the action was valid
            - Error message if invalid
        """
        pass
    
    @abstractmethod
    def calculate_score_components(self, result: GameResult) -> Dict[str, float]:
        """Calculate individual scoring components for the game result."""
        pass
    
    @abstractmethod
    def get_optimal_moves(self, state: GameState) -> int:
        """Get the optimal number of moves from this state (for efficiency scoring)."""
        pass
    
    def make_move(self, current_state: GameState, action: GameAction) -> Tuple[GameState, bool, str]:
        """
        Make a move in the game, updating internal state.
        
        Returns:
            - New game state
            - Whether the action was valid
            - Error message if invalid
        """
        new_state, valid, error = self.apply_action(current_state, action)
        
        if valid:
            self.move_count += 1
            self.move_history.append(action)
        
        return new_state, valid, error
    
    def get_result(self, final_state: GameState) -> GameResult:
        """Get the final game result."""
        time_taken = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Calculate base score components
        score_components = self.calculate_score_components(
            GameResult(
                final_state=final_state,
                moves_made=self.move_count,
                time_taken=time_taken,
                victory=final_state.is_victory,
                score_components={},  # Will be filled
                move_history=self.move_history
            )
        )
        
        return GameResult(
            final_state=final_state,
            moves_made=self.move_count,
            time_taken=time_taken,
            victory=final_state.is_victory,
            score_components=score_components,
            move_history=self.move_history
        )


class AIGameInterface(ABC):
    """Interface for AI models to interact with games."""
    
    @abstractmethod
    def get_function_calling_schema(self) -> Dict[str, Any]:
        """Get the function calling schema for structured AI responses."""
        pass
    
    @abstractmethod
    def parse_ai_response(self, response: Dict[str, Any]) -> GameAction:
        """Parse AI response into a game action."""
        pass
    
    @abstractmethod
    def format_state_for_ai(self, state: GameState, config: GameConfig) -> str:
        """Format game state for AI consumption based on mode and config."""
        pass