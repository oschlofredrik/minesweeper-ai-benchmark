"""Factory for creating model instances."""

from typing import Dict, Any, Type, List
from src.core.types import ModelConfig
from .base import BaseModel
from .openai import OpenAIModel
from .anthropic import AnthropicModel


# Registry of available models
MODEL_REGISTRY: Dict[str, Type[BaseModel]] = {
    "openai": OpenAIModel,
    "anthropic": AnthropicModel,
}


def create_model(config: ModelConfig) -> BaseModel:
    """
    Create a model instance from configuration.
    
    Args:
        config: Model configuration
    
    Returns:
        Model instance
    
    Raises:
        ValueError: If provider is not supported
    """
    provider = config.provider.lower()
    
    if provider not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model provider: {provider}. "
            f"Available providers: {list(MODEL_REGISTRY.keys())}"
        )
    
    model_class = MODEL_REGISTRY[provider]
    
    # Convert ModelConfig to dict for the model class
    model_dict = {
        "name": config.name,
        "model_id": config.model_id,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        **config.additional_params,
    }
    
    return model_class(model_dict)


def register_model(provider: str, model_class: Type[BaseModel]) -> None:
    """
    Register a new model provider.
    
    Args:
        provider: Provider name
        model_class: Model class
    """
    MODEL_REGISTRY[provider.lower()] = model_class


def list_providers() -> List[str]:
    """Get list of available model providers."""
    return list(MODEL_REGISTRY.keys())