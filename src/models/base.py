"""Base model interface for all LLM integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import re
from datetime import datetime

from src.core.types import Action, ActionType, Position
from src.core.exceptions import InvalidModelResponseError


@dataclass
class ModelResponse:
    """Response from a model."""
    content: str
    raw_response: Any
    model_name: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    reasoning: Optional[str] = None
    action: Optional[Action] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseModel(ABC):
    """Abstract base class for all model interfaces."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize model with configuration.
        
        Args:
            model_config: Model-specific configuration
        """
        self.config = model_config
        self.name = model_config.get("name", "unknown")
        self.temperature = model_config.get("temperature", 0.7)
        self.max_tokens = model_config.get("max_tokens", 1000)
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional model-specific parameters
        
        Returns:
            ModelResponse object
        """
        pass
    
    def parse_action(self, response: str) -> Action:
        """
        Parse an action from model response.
        
        Args:
            response: Model response text
        
        Returns:
            Parsed Action object
        
        Raises:
            InvalidModelResponseError: If action cannot be parsed
        """
        # Try multiple parsing patterns
        patterns = [
            # Format: "reveal (2, 3)" or "flag (1, 2)"
            r'(reveal|flag|unflag)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)',
            # Format: "reveal 2,3" or "flag 1,2"
            r'(reveal|flag|unflag)\s+(\d+)\s*,\s*(\d+)',
            # Format: "reveal [2][3]" or "flag [1][2]"
            r'(reveal|flag|unflag)\s*\[\s*(\d+)\s*\]\s*\[\s*(\d+)\s*\]',
            # Format: "Action: reveal Position: (2,3)"
            r'action:\s*(reveal|flag|unflag).*position:\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)',
            # Format: "R(2,3)" or "F(1,2)"
            r'([RFU])\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)',
        ]
        
        response_lower = response.lower()
        
        for pattern in patterns:
            match = re.search(pattern, response_lower, re.IGNORECASE)
            if match:
                action_str = match.group(1).lower()
                row = int(match.group(2))
                col = int(match.group(3))
                
                # Handle single letter abbreviations
                if action_str == 'r':
                    action_type = ActionType.REVEAL
                elif action_str == 'f':
                    action_type = ActionType.FLAG
                elif action_str == 'u':
                    action_type = ActionType.UNFLAG
                else:
                    action_type = ActionType(action_str)
                
                return Action(action_type, Position(row, col))
        
        # Try to find JSON format
        json_pattern = r'\{[^}]*"action"[^}]*\}'
        json_match = re.search(json_pattern, response, re.DOTALL)
        if json_match:
            import json
            try:
                data = json.loads(json_match.group(0))
                action_type = ActionType(data.get("action", "").lower())
                
                # Handle different position formats in JSON
                if "position" in data:
                    if isinstance(data["position"], dict):
                        row = data["position"].get("row")
                        col = data["position"].get("col", data["position"].get("column"))
                    elif isinstance(data["position"], list) and len(data["position"]) >= 2:
                        row, col = data["position"][:2]
                    else:
                        raise ValueError("Invalid position format in JSON")
                elif "row" in data and ("col" in data or "column" in data):
                    row = data["row"]
                    col = data.get("col", data.get("column"))
                else:
                    raise ValueError("No position found in JSON")
                
                return Action(action_type, Position(int(row), int(col)))
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
        
        raise InvalidModelResponseError(
            f"Could not parse action from response: {response[:200]}..."
        )
    
    def extract_reasoning(self, response: str) -> Optional[str]:
        """
        Extract reasoning/explanation from model response.
        
        Args:
            response: Model response text
        
        Returns:
            Extracted reasoning text or None
        """
        # Look for common reasoning indicators
        reasoning_patterns = [
            r'reasoning:\s*(.*?)(?=action:|$)',
            r'explanation:\s*(.*?)(?=action:|$)',
            r'because\s+(.*?)(?=therefore|so|thus|action:|$)',
            r'analysis:\s*(.*?)(?=action:|move:|$)',
            r'thinking:\s*(.*?)(?=action:|move:|$)',
        ]
        
        for pattern in reasoning_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                # Clean up the reasoning text
                reasoning = re.sub(r'\s+', ' ', reasoning)  # Normalize whitespace
                return reasoning[:500]  # Limit length
        
        # If no explicit reasoning section, try to extract from the beginning
        # if it looks like an explanation
        if any(word in response.lower()[:100] for word in ['because', 'since', 'the cell', 'adjacent']):
            # Take first few sentences as reasoning
            sentences = response.split('.')[:3]
            reasoning = '. '.join(sentences).strip()
            if reasoning:
                return reasoning
        
        return None
    
    def format_prompt(self, board_state: str, format_type: str = "standard") -> str:
        """
        Format the prompt for the model.
        
        Args:
            board_state: The current board state
            format_type: Type of prompt format to use
        
        Returns:
            Formatted prompt string
        """
        if format_type == "standard":
            return f"""You are playing Minesweeper. Here is the current board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines
- *: Mine (only shown when game is over)

Based on logical deduction, what is your next move? Please provide:
1. Your reasoning for the move
2. Your action in the format: "Action: [reveal/flag/unflag] (row, col)"

Think step by step about which cells are definitely safe or definitely mines based on the numbers shown."""
        
        elif format_type == "json":
            return f"""You are playing Minesweeper. Here is the current board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell  
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines

Analyze the board and provide your next move as JSON:
{{
    "reasoning": "Your logical deduction explaining why this move is safe",
    "action": "reveal",
    "position": {{"row": 0, "col": 0}}
}}

Use logical deduction based on the numbers to find guaranteed safe cells or mines."""
        
        elif format_type == "cot":  # Chain of thought
            return f"""You are an expert Minesweeper player. Analyze this board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)  
- 1-8: Number of adjacent mines

Let's think step by step:
1. First, identify all revealed numbers and their adjacent hidden cells
2. Count how many mines are already flagged around each number
3. Determine which cells must be mines or must be safe
4. Choose the best move based on certainty

Provide your analysis and then state your move as: Action: [reveal/flag] (row, col)"""
        
        else:
            raise ValueError(f"Unknown prompt format type: {format_type}")
    
    async def play_move(self, board_state: str, prompt_format: str = "standard") -> ModelResponse:
        """
        High-level method to get a move from the model.
        
        Args:
            board_state: Current board state
            prompt_format: Format type for the prompt
        
        Returns:
            ModelResponse with parsed action
        """
        prompt = self.format_prompt(board_state, prompt_format)
        response = await self.generate(prompt)
        
        # Try to parse action and reasoning
        try:
            response.action = self.parse_action(response.content)
        except InvalidModelResponseError:
            # Action parsing failed, will be handled by caller
            pass
        
        response.reasoning = self.extract_reasoning(response.content)
        
        return response