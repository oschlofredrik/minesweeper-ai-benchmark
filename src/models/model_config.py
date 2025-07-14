"""Model-specific configurations for different AI models."""

import os
from typing import Dict, Any

# Model-specific configurations
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    # Standard OpenAI models
    "gpt-4": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "cot"
    },
    "gpt-4-turbo": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "cot"
    },
    "gpt-4o": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "cot"
    },
    "gpt-4o-mini": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "standard"
    },
    "gpt-3.5-turbo": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "standard"
    },
    
    # o1 reasoning models
    "o1-preview": {
        "timeout": 120,  # 2 minutes for complex reasoning
        "supports_functions": False,
        "optimal_prompt_format": "reasoning",
        "uses_responses_api": False
    },
    "o1-mini": {
        "timeout": 60,  # 1 minute
        "supports_functions": False,
        "optimal_prompt_format": "reasoning",
        "uses_responses_api": False
    },
    
    # o3 models (new reasoning models with responses API)
    "o3": {
        "timeout": 300,  # 5 minutes for deep reasoning
        "supports_functions": False,
        "optimal_prompt_format": "reasoning",
        "uses_responses_api": True
    },
    "o3-mini": {
        "timeout": 120,  # 2 minutes
        "supports_functions": False,
        "optimal_prompt_format": "reasoning",
        "uses_responses_api": True
    },
    
    # o4 models (future)
    "o4": {
        "timeout": 300,  # 5 minutes
        "supports_functions": False,
        "optimal_prompt_format": "reasoning",
        "uses_responses_api": True
    },
    "o4-mini": {
        "timeout": 120,  # 2 minutes
        "supports_functions": False,
        "optimal_prompt_format": "reasoning",
        "uses_responses_api": True
    },
    
    # Anthropic models
    "claude-3-opus-20240229": {
        "timeout": 60,
        "supports_functions": True,
        "optimal_prompt_format": "cot"
    },
    "claude-3-sonnet-20240229": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "cot"
    },
    "claude-3-haiku-20240307": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "standard"
    },
    "claude-3-5-sonnet-20241022": {
        "timeout": 60,
        "supports_functions": True,
        "optimal_prompt_format": "cot"
    },
    "claude-3-5-haiku-20241022": {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "standard"
    },
}

def get_model_config(model_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Model configuration dict with defaults
    """
    # Get base config or use defaults
    config = MODEL_CONFIGS.get(model_name, {
        "timeout": 30,
        "supports_functions": True,
        "optimal_prompt_format": "standard",
        "uses_responses_api": False
    })
    
    # Check if it's an o3/o4 model by prefix
    if model_name.startswith("o3") or model_name.startswith("o4"):
        config.setdefault("uses_responses_api", True)
        config.setdefault("supports_functions", False)
        config.setdefault("timeout", 120)  # Default 2 minutes for unknown o3/o4 models
    
    return config.copy()  # Return a copy to avoid mutations

def get_model_timeout(model_name: str) -> int:
    """Get timeout for a specific model."""
    # Check for environment variable override
    env_timeout = os.getenv(f"MODEL_TIMEOUT_{model_name.upper().replace('-', '_')}")
    if env_timeout:
        try:
            return int(env_timeout)
        except ValueError:
            pass
    
    # Check for general timeout override
    general_timeout = os.getenv("MODEL_TIMEOUT")
    if general_timeout:
        try:
            return int(general_timeout)
        except ValueError:
            pass
    
    return get_model_config(model_name).get("timeout", 30)

def uses_responses_api(model_name: str) -> bool:
    """Check if model uses the responses.create API."""
    return get_model_config(model_name).get("uses_responses_api", False)

def supports_functions(model_name: str) -> bool:
    """Check if model supports function calling."""
    return get_model_config(model_name).get("supports_functions", True)