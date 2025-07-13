"""Model interfaces for the benchmark platform."""

from .base import BaseModel, ModelResponse
from .openai import OpenAIModel
from .anthropic import AnthropicModel
from .factory import create_model, register_model, list_providers
from src.core.types import ModelConfig

__all__ = [
    "BaseModel",
    "ModelResponse", 
    "OpenAIModel",
    "AnthropicModel",
    "create_model",
    "register_model",
    "list_providers",
    "ModelConfig",
]