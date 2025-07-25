"""AI Model configurations and integration for Vercel."""
import os
import sys
import json
import time
from typing import Dict, Any, Optional, List

# Model configurations
MODEL_CONFIGS = {
    "openai": {
        "models": {
            "gpt-4-turbo-preview": {
                "name": "GPT-4 Turbo",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": True
            },
            "gpt-4": {
                "name": "GPT-4",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": False
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": False
            },
            "gpt-4o": {
                "name": "GPT-4o",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": True
            },
            "gpt-4o-mini": {
                "name": "GPT-4o Mini",
                "max_tokens": 16384,
                "supports_functions": True,
                "supports_vision": True
            },
            "o1-preview": {
                "name": "o1 Preview",
                "max_tokens": 128000,
                "supports_functions": False,
                "supports_vision": False,
                "reasoning_model": True
            },
            "o1-mini": {
                "name": "o1 Mini",
                "max_tokens": 65536,
                "supports_functions": False,
                "supports_vision": False,
                "reasoning_model": True
            }
        }
    },
    "anthropic": {
        "models": {
            "claude-3-opus-20240229": {
                "name": "Claude 3 Opus",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": True
            },
            "claude-3-sonnet-20240229": {
                "name": "Claude 3 Sonnet",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": True
            },
            "claude-3-haiku-20240307": {
                "name": "Claude 3 Haiku",
                "max_tokens": 4096,
                "supports_functions": True,
                "supports_vision": True
            },
            "claude-3-5-sonnet-20241022": {
                "name": "Claude 3.5 Sonnet",
                "max_tokens": 8192,
                "supports_functions": True,
                "supports_vision": True
            }
        }
    }
}


def get_available_models(provider: str) -> Dict[str, Any]:
    """Get available models for a provider."""
    return MODEL_CONFIGS.get(provider, {}).get("models", {})


def call_openai_model(
    model: str,
    messages: List[Dict[str, str]],
    functions: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Call OpenAI API with function calling support."""
    # Debug import issues
    print(f"[AI_MODELS] Python path: {sys.path}")
    print(f"[AI_MODELS] Current directory: {os.getcwd()}")
    print(f"[AI_MODELS] Directory contents: {os.listdir('.')}")
    
    try:
        import openai
        print(f"[AI_MODELS] OpenAI library version: {openai.__version__}")
    except ImportError as e:
        # Check if openai is in site-packages
        import site
        print(f"[AI_MODELS] Site packages: {site.getsitepackages() if hasattr(site, 'getsitepackages') else 'N/A'}")
        
        return {
            "error": f"OpenAI library not installed: {str(e)}",
            "content": "OpenAI library is required but not available in Vercel environment"
        }
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        # Debug: print all env vars that start with OPENAI
        env_vars = [k for k in os.environ.keys() if 'OPENAI' in k or 'API' in k]
        print(f"Available env vars with OPENAI/API: {env_vars}")
        return {
            "error": "OpenAI API key not found",
            "content": f"Please set OPENAI_API_KEY environment variable. Found vars: {env_vars}"
        }
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Check if this is a reasoning model (o1 series)
        model_config = MODEL_CONFIGS["openai"]["models"].get(model, {})
        is_reasoning_model = model_config.get("reasoning_model", False)
        
        # Prepare request parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": 0 if is_reasoning_model else temperature,
        }
        
        # Add function calling for supported models
        if functions and model_config.get("supports_functions", False):
            params["tools"] = [{"type": "function", "function": func} for func in functions]
            params["tool_choice"] = "auto"
        
        # Make API call
        print(f"Making OpenAI API call with model={model}")
        response = client.chat.completions.create(**params)
        
        # Extract response
        message = response.choices[0].message
        print(f"Got response from OpenAI: {message}")
        
        # Handle function calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_call = message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)
            return {
                "function_call": {
                    "name": tool_call.function.name,
                    "arguments": function_args
                },
                "content": message.content or "",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        
        # Regular response
        return {
            "content": message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
    except Exception as e:
        return {
            "error": f"OpenAI API error: {str(e)}",
            "content": ""
        }


def call_anthropic_model(
    model: str,
    messages: List[Dict[str, str]],
    functions: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Call Anthropic API with tool use support."""
    try:
        import anthropic
    except ImportError:
        return {
            "error": "Anthropic library not installed",
            "content": "Please install anthropic: pip install anthropic"
        }
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return {
            "error": "Anthropic API key not found",
            "content": "Please set ANTHROPIC_API_KEY environment variable"
        }
    
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        # Convert OpenAI-style messages to Anthropic format
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Prepare request parameters
        params = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        
        if system_message:
            params["system"] = system_message
        
        # Add tool use for supported models
        if functions:
            tools = []
            for func in functions:
                tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
            params["tools"] = tools
        
        # Make API call
        response = client.messages.create(**params)
        
        # Handle tool use
        for content in response.content:
            if content.type == "tool_use":
                return {
                    "function_call": {
                        "name": content.name,
                        "arguments": content.input
                    },
                    "content": "",
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    }
                }
        
        # Regular text response
        text_content = ""
        for content in response.content:
            if content.type == "text":
                text_content += content.text
        
        return {
            "content": text_content,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        }
        
    except Exception as e:
        return {
            "error": f"Anthropic API error: {str(e)}",
            "content": ""
        }


def call_ai_model(
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    functions: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Call appropriate AI model based on provider."""
    print(f"call_ai_model called with provider={provider}, model={model}")
    
    if provider == "openai":
        return call_openai_model(model, messages, functions, temperature)
    elif provider == "anthropic":
        return call_anthropic_model(model, messages, functions, temperature)
    else:
        return {
            "error": f"Unknown provider: {provider}",
            "content": ""
        }


def extract_function_call(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract function call from AI response."""
    if "function_call" in response:
        return response["function_call"]["arguments"]
    return None


def format_game_messages(game_type: str, prompt: str, include_system: bool = True) -> List[Dict[str, str]]:
    """Format messages for AI model based on game type."""
    messages = []
    
    if include_system:
        if game_type == "minesweeper":
            system_prompt = """You are an expert Minesweeper player. Analyze the board carefully and make logical moves based on the numbers shown. Always explain your reasoning before making a move.

When you see a number, it indicates how many mines are in the 8 adjacent cells. Use this information to deduce safe cells and mine locations."""
        else:  # risk
            system_prompt = """You are an expert Risk player. Think strategically about territory control, continent bonuses, and defensive positions. Always explain your strategic reasoning before making a move.

Consider factors like:
- Continent control for bonus armies
- Defensive positions and choke points
- Weakening opponents while maintaining your strength
- Long-term strategic goals"""
        
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    return messages