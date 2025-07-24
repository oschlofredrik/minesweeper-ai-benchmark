"""Simple Number Puzzle game plugin to demonstrate the system."""

import random
from typing import Dict, Any, List, Tuple, Optional
import uuid

from src.games.base import (
    BaseGame, GameInstance, GameState, GameAction, GameResult,
    GameConfig, GameMode, ScoringComponent, AIGameInterface
)


class NumberPuzzleGame(BaseGame):
    """
    Simple number guessing puzzle for demonstration.
    AI must guess a target number using higher/lower feedback.
    """
    
    @property
    def name(self) -> str:
        return "number_puzzle"
    
    @property
    def display_name(self) -> str:
        return "Number Puzzle"
    
    @property
    def description(self) -> str:
        return "Guess the target number using binary search strategy"
    
    @property
    def supported_modes(self) -> List[GameMode]:
        return [GameMode.SPEED, GameMode.EFFICIENCY, GameMode.REASONING, GameMode.MIXED]
    
    def get_scoring_components(self) -> List[ScoringComponent]:
        return [
            ScoringComponent(
                name="completion",
                description="Whether the number was found",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="speed",
                description="Time taken to find the number",
                min_value=0.0,
                max_value=float('inf'),
                higher_is_better=False
            ),
            ScoringComponent(
                name="efficiency",
                description="How close to optimal binary search",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="reasoning",
                description="Quality of strategy explanation",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            )
        ]
    
    def create_instance(self, config: GameConfig) -> GameInstance:
        return NumberPuzzleInstance(config, str(uuid.uuid4()))
    
    def get_ai_prompt_template(self) -> str:
        return """You are playing a number guessing game.

Target: A number between {min_value} and {max_value}
Guesses made: {guesses_made}
Feedback history:
{feedback_history}

Your last guess: {last_guess}
Last feedback: {last_feedback}

Make your next guess strategically."""
    
    def get_move_format_description(self) -> str:
        return """Guess a number:
- action_type: "guess"
- parameters: {"value": <your guess>}
- reasoning: Explain your strategy"""
    
    def get_visualization_data(self, state: GameState) -> Dict[str, Any]:
        return {
            "type": "number_line",
            "min": state.state_data.get("min_value", 1),
            "max": state.state_data.get("max_value", 100),
            "guesses": state.state_data.get("guess_history", []),
            "found": state.is_victory
        }


class NumberPuzzleInstance(GameInstance):
    """Instance of the number puzzle game."""
    
    def __init__(self, config: GameConfig, instance_id: str):
        super().__init__(config, instance_id)
        
        # Set range based on difficulty
        ranges = {
            "easy": (1, 50),
            "medium": (1, 100),
            "hard": (1, 1000),
            "expert": (1, 10000)
        }
        
        self.min_value, self.max_value = ranges.get(config.difficulty, (1, 100))
        
        # Allow custom range
        if "min_value" in config.custom_settings:
            self.min_value = config.custom_settings["min_value"]
        if "max_value" in config.custom_settings:
            self.max_value = config.custom_settings["max_value"]
        
        # Generate target
        self.target = random.randint(self.min_value, self.max_value)
        
        # Track game state
        self.found = False
        self.guess_history: List[Tuple[int, str]] = []  # (guess, feedback)
        self.last_guess: Optional[int] = None
        self.last_feedback: str = "Make your first guess"
    
    def get_initial_state(self) -> GameState:
        return self._create_game_state()
    
    def _create_game_state(self) -> GameState:
        # Only one possible action type in this game
        possible_actions = []
        if not self.found:
            # Suggest some strategic guesses
            if not self.guess_history:
                # First guess: middle
                mid = (self.min_value + self.max_value) // 2
                possible_actions.append(GameAction(
                    action_type="guess",
                    parameters={"value": mid}
                ))
            else:
                # Suggest any valid number (AI should pick strategically)
                for i in range(min(5, self.max_value - self.min_value + 1)):
                    possible_actions.append(GameAction(
                        action_type="guess",
                        parameters={"value": self.min_value + i}
                    ))
        
        feedback_history = "\n".join([
            f"Guess {i+1}: {guess} - {feedback}"
            for i, (guess, feedback) in enumerate(self.guess_history)
        ])
        
        return GameState(
            state_data={
                "min_value": self.min_value,
                "max_value": self.max_value,
                "guesses_made": len(self.guess_history),
                "guess_history": self.guess_history,
                "feedback_history": feedback_history,
                "last_guess": self.last_guess,
                "last_feedback": self.last_feedback,
                "found": self.found
            },
            is_terminal=self.found,
            is_victory=self.found,
            possible_actions=possible_actions
        )
    
    def apply_action(self, state: GameState, action: GameAction) -> Tuple[GameState, bool, str]:
        if self.found:
            return state, False, "Number already found"
        
        if action.action_type != "guess":
            return state, False, f"Unknown action: {action.action_type}"
        
        guess = action.parameters.get("value")
        if guess is None:
            return state, False, "No value provided"
        
        try:
            guess = int(guess)
        except:
            return state, False, "Value must be an integer"
        
        if not (self.min_value <= guess <= self.max_value):
            return state, False, f"Guess must be between {self.min_value} and {self.max_value}"
        
        # Check guess
        self.last_guess = guess
        
        if guess == self.target:
            self.last_feedback = "Correct! You found it!"
            self.found = True
        elif guess < self.target:
            self.last_feedback = "Too low"
        else:
            self.last_feedback = "Too high"
        
        self.guess_history.append((guess, self.last_feedback))
        
        return self._create_game_state(), True, ""
    
    def calculate_score_components(self, result: GameResult) -> Dict[str, float]:
        components = {}
        
        # Completion
        components["completion"] = 1.0 if result.victory else 0.0
        
        # Speed
        components["speed"] = result.time_taken
        
        # Efficiency - compare to optimal binary search
        if result.moves_made > 0:
            import math
            optimal_moves = math.ceil(math.log2(self.max_value - self.min_value + 1))
            components["efficiency"] = min(1.0, optimal_moves / result.moves_made)
        else:
            components["efficiency"] = 0.0
        
        # Reasoning - would need LLM judge in practice
        # For now, give points for any reasoning
        has_reasoning = any(
            move.reasoning and len(move.reasoning) > 10
            for move in result.move_history
        )
        components["reasoning"] = 0.8 if has_reasoning else 0.2
        
        return components
    
    def get_optimal_moves(self, state: GameState) -> int:
        """Calculate optimal moves remaining using binary search."""
        import math
        
        if state.is_terminal:
            return 0
        
        # Get current search space from history
        current_min = self.min_value
        current_max = self.max_value
        
        for guess, feedback in self.guess_history:
            if feedback == "Too low":
                current_min = max(current_min, guess + 1)
            elif feedback == "Too high":
                current_max = min(current_max, guess - 1)
        
        # Optimal moves for remaining space
        remaining_space = current_max - current_min + 1
        return max(1, math.ceil(math.log2(remaining_space)))


class NumberPuzzleAIInterface(AIGameInterface):
    """AI interface for Number Puzzle."""
    
    def get_function_calling_schema(self) -> Dict[str, Any]:
        return {
            "name": "make_guess",
            "description": "Guess a number in the number puzzle",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "integer",
                        "description": "Your guess"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explain your guessing strategy"
                    }
                },
                "required": ["value", "reasoning"]
            }
        }
    
    def parse_ai_response(self, response: Dict[str, Any]) -> GameAction:
        return GameAction(
            action_type="guess",
            parameters={"value": response.get("value", 0)},
            reasoning=response.get("reasoning", "")
        )
    
    def format_state_for_ai(self, state: GameState, config: GameConfig) -> str:
        template = NumberPuzzleGame().get_ai_prompt_template()
        
        mode_hints = {
            GameMode.SPEED: "\nGuess quickly but strategically!",
            GameMode.EFFICIENCY: "\nUse optimal binary search strategy!",
            GameMode.REASONING: "\nExplain your strategy in detail!"
        }
        
        hint = mode_hints.get(config.mode, "")
        
        return template.format(**state.state_data) + hint