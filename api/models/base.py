"""Base model interface for Vercel."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

@dataclass
class ModelResponse:
    """Response from a model."""
    action: str
    parameters: Dict[str, Any]
    reasoning: str
    raw_response: str
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "parameters": self.parameters,
            "reasoning": self.reasoning,
            "tokens_used": self.tokens_used
        }

class BaseModel(ABC):
    """Abstract base class for AI models."""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 1000)
    
    @abstractmethod
    def get_move(self, game_state: str, function_schema: Dict[str, Any], 
                 move_history: List[Dict[str, Any]] = None) -> ModelResponse:
        """Get a move from the model given game state."""
        pass
    
    @abstractmethod
    def supports_function_calling(self) -> bool:
        """Check if model supports function calling."""
        pass