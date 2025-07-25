"""AI Model integration using HTTP requests instead of SDK libraries."""
import os
import json
import time
from typing import Dict, Any, Optional, List
import urllib.request
import urllib.error

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


def make_http_request(url: str, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
    """Make HTTP request to API."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {
            "error": f"HTTP {e.code}: {e.reason}",
            "details": error_body
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def call_openai_model(
    model: str,
    messages: List[Dict[str, str]],
    functions: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Call OpenAI API with function calling support using HTTP."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {
            "error": "OpenAI API key not found",
            "content": "Please set OPENAI_API_KEY environment variable"
        }
    
    # Check if this is a reasoning model
    model_config = MODEL_CONFIGS["openai"]["models"].get(model, {})
    is_reasoning_model = model_config.get("reasoning_model", False)
    
    # Prepare request
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0 if is_reasoning_model else temperature,
    }
    
    # Add function calling for supported models
    if functions and model_config.get("supports_functions", False):
        data["tools"] = [{"type": "function", "function": func} for func in functions]
        data["tool_choice"] = "auto"
    
    print(f"[HTTP] Making OpenAI API call with model={model}")
    response = make_http_request(url, headers, data)
    
    if "error" in response:
        return {
            "error": f"OpenAI API error: {response['error']}",
            "content": ""
        }
    
    try:
        # Extract response
        choice = response["choices"][0]
        message = choice["message"]
        
        # Handle function calls
        if "tool_calls" in message and message["tool_calls"]:
            tool_call = message["tool_calls"][0]
            function_args = json.loads(tool_call["function"]["arguments"])
            return {
                "function_call": {
                    "name": tool_call["function"]["name"],
                    "arguments": function_args
                },
                "content": message.get("content", ""),
                "usage": response.get("usage", {})
            }
        
        # Regular response
        return {
            "content": message["content"],
            "usage": response.get("usage", {})
        }
        
    except Exception as e:
        return {
            "error": f"Error parsing OpenAI response: {str(e)}",
            "content": ""
        }


def call_anthropic_model(
    model: str,
    messages: List[Dict[str, str]],
    functions: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Call Anthropic API with tool use support using HTTP."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return {
            "error": "Anthropic API key not found",
            "content": "Please set ANTHROPIC_API_KEY environment variable"
        }
    
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
    
    # Prepare request
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": anthropic_messages,
        "temperature": temperature,
        "max_tokens": 4096
    }
    
    if system_message:
        data["system"] = system_message
    
    # Add tool use for supported models
    if functions:
        tools = []
        for func in functions:
            tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"]
            })
        data["tools"] = tools
    
    print(f"[HTTP] Making Anthropic API call with model={model}")
    response = make_http_request(url, headers, data)
    
    if "error" in response:
        return {
            "error": f"Anthropic API error: {response['error']}",
            "content": ""
        }
    
    try:
        # Handle tool use
        for content in response["content"]:
            if content["type"] == "tool_use":
                return {
                    "function_call": {
                        "name": content["name"],
                        "arguments": content["input"]
                    },
                    "content": "",
                    "usage": {
                        "prompt_tokens": response["usage"]["input_tokens"],
                        "completion_tokens": response["usage"]["output_tokens"],
                        "total_tokens": response["usage"]["input_tokens"] + response["usage"]["output_tokens"]
                    }
                }
        
        # Regular text response
        text_content = ""
        for content in response["content"]:
            if content["type"] == "text":
                text_content += content["text"]
        
        return {
            "content": text_content,
            "usage": {
                "prompt_tokens": response["usage"]["input_tokens"],
                "completion_tokens": response["usage"]["output_tokens"],
                "total_tokens": response["usage"]["input_tokens"] + response["usage"]["output_tokens"]
            }
        }
        
    except Exception as e:
        return {
            "error": f"Error parsing Anthropic response: {str(e)}",
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
    print(f"[HTTP] call_ai_model called with provider={provider}, model={model}")
    
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