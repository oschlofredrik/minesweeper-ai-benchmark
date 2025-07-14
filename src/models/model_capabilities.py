"""Model capabilities configuration for different AI models."""

from typing import Dict, Any

# Model capabilities mapping
MODEL_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    # OpenAI Models
    "gpt-4": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
    },
    "gpt-4o": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
    },
    "gpt-4o-mini": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
    },
    "gpt-3.5-turbo": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
    },
    # o1 series - older reasoning models
    "o1-preview": {
        "supports_function_calling": False,
        "supports_streaming": False,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
        "is_reasoning_model": True,
    },
    "o1-mini": {
        "supports_function_calling": False,
        "supports_streaming": False,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
        "is_reasoning_model": True,
    },
    # o3/o4 series - new reasoning models with responses API
    "o3-mini": {
        "supports_function_calling": False,
        "supports_streaming": False,
        "supports_system_messages": False,
        "api_type": "responses",
        "max_tokens": 4096,
        "is_reasoning_model": True,
        "reasoning_efforts": ["low", "medium", "high"],
    },
    "o4-mini": {
        "supports_function_calling": False,
        "supports_streaming": False,
        "supports_system_messages": False,
        "api_type": "responses",
        "max_tokens": 4096,
        "is_reasoning_model": True,
        "reasoning_efforts": ["low", "medium", "high"],
    },
    
    # Anthropic Models
    "claude-3-opus-20240229": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "messages",
        "max_tokens": 4096,
    },
    "claude-3-5-sonnet-20241022": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "messages",
        "max_tokens": 4096,
    },
    "claude-3-5-haiku-20241022": {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "messages",
        "max_tokens": 4096,
    },
}

def get_model_capabilities(model_id: str) -> Dict[str, Any]:
    """Get capabilities for a specific model."""
    # Check exact match first
    if model_id in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_id]
    
    # Check prefixes for versioned models
    for model_prefix, capabilities in MODEL_CAPABILITIES.items():
        if model_id.startswith(model_prefix):
            return capabilities
    
    # Default capabilities for unknown models
    return {
        "supports_function_calling": True,
        "supports_streaming": True,
        "supports_system_messages": True,
        "api_type": "chat_completions",
        "max_tokens": 4096,
    }