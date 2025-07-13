"""Base model interface for all LLM integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import re
from datetime import datetime
import asyncio

from src.core.types import Action, ActionType, Position
from src.core.exceptions import InvalidModelResponseError, ModelAPIError
from src.core.logging_config import get_logger

logger = get_logger("models.base")


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
    function_call: Optional[Dict[str, Any]] = None  # For function calling responses
    
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
    
    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response with retry logic.
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
        
        Returns:
            ModelResponse object
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, **kwargs)
            except ModelAPIError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                continue
        
        raise last_error

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
        # For reasoning models, the entire response before the action might be reasoning
        # Check if this looks like a reasoning-first response
        action_indicators = ['action:', 'move:', 'reveal', 'flag', 'unflag']
        
        # Find where the action starts
        action_start = len(response)
        for indicator in action_indicators:
            pos = response.lower().find(indicator.lower())
            if pos != -1 and pos < action_start:
                action_start = pos
        
        # If we found an action and there's substantial text before it, that's likely reasoning
        if action_start > 50 and action_start < len(response):
            reasoning = response[:action_start].strip()
            # Clean up common endings
            reasoning = re.sub(r'(Therefore|So|Thus|Hence|Now)[,:]?\s*$', '', reasoning, flags=re.IGNORECASE).strip()
            if reasoning:
                return reasoning
        
        # Otherwise, look for explicit reasoning sections
        reasoning_patterns = [
            r'reasoning:\s*(.*?)(?=action:|move:|$)',
            r'explanation:\s*(.*?)(?=action:|move:|$)',
            r'because\s+(.*?)(?=therefore|so|thus|action:|move:|$)',
            r'analysis:\s*(.*?)(?=action:|move:|$)',
            r'thinking:\s*(.*?)(?=action:|move:|$)',
            r'thought process:\s*(.*?)(?=action:|move:|$)',
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

Based on logical deduction, what is your next move?

Think step by step about which cells are definitely safe or definitely mines based on the numbers shown. Then use the make_move function to specify your action."""
        
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
        
        elif format_type == "reasoning":  # For reasoning models
            return f"""You are an expert Minesweeper player. Here is the current board state:

{board_state}

Legend:
- ?: Hidden cell
- F: Flagged cell
- .: Empty cell (0 adjacent mines)
- 1-8: Number of adjacent mines

Analyze the board carefully. Think through all the logical deductions you can make based on the revealed numbers and their adjacent cells. Consider which cells must be mines and which must be safe.

After your analysis, provide your next move in this format:
Action: [reveal/flag] (row, col)"""
        
        else:
            raise ValueError(f"Unknown prompt format type: {format_type}")
    
    def get_optimal_prompt_format(self) -> str:
        """
        Get the optimal prompt format for this model.
        
        Returns:
            Best prompt format type for the model
        """
        # Check if model implementation suggests a format
        if hasattr(self, 'is_reasoning_model') and self.is_reasoning_model:
            return "reasoning"
        elif hasattr(self, 'supports_thinking') and self.supports_thinking:
            return "reasoning"
        elif 'gpt-4' in self.name.lower() or 'claude' in self.name.lower():
            return "cot"  # Chain of thought works well for these
        else:
            return "standard"
    
    async def play_move(self, board_state: str, prompt_format: str = "auto", use_functions: bool = True) -> ModelResponse:
        """
        High-level method to get a move from the model.
        
        Args:
            board_state: Current board state
            prompt_format: Format type for the prompt ("auto" to auto-detect)
        
        Returns:
            ModelResponse with parsed action
        """
        # Auto-detect best format if requested
        if prompt_format == "auto":
            prompt_format = self.get_optimal_prompt_format()
            
        prompt = self.format_prompt(board_state, prompt_format)
        
        # Pass use_functions to generate method
        kwargs = {}
        if hasattr(self, '_get_minesweeper_tools'):  # Check if model supports functions
            kwargs['use_functions'] = use_functions
            if hasattr(self, 'client') and hasattr(self.client, 'messages'):  # Anthropic
                kwargs['use_tools'] = use_functions
        
        response = await self.generate(prompt, **kwargs)
        
        # Try to parse action from function call first, then from content
        if response.function_call:
            # Parse action from function call
            try:
                action_type = ActionType(response.function_call.get('action', '').lower())
                position = Position(
                    row=response.function_call.get('row', 0),
                    col=response.function_call.get('col', 0)
                )
                response.action = Action(action_type, position)
                # Use reasoning from function call if not already set
                if not response.reasoning and 'reasoning' in response.function_call:
                    response.reasoning = response.function_call['reasoning']
            except (ValueError, KeyError) as e:
                # Function call parsing failed
                logger.warning(f"Failed to parse function call: {e}")
        else:
            # Try to parse action from content
            try:
                response.action = self.parse_action(response.content)
            except InvalidModelResponseError:
                # Action parsing failed, will be handled by caller
                pass
        
        # Extract reasoning if not already set
        if not response.reasoning:
            response.reasoning = self.extract_reasoning(response.content)
        
        return response