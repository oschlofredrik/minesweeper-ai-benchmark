"""Anthropic model client for Vercel."""
import os
import json
from typing import Dict, List, Optional, Any
import httpx
from .base import BaseModel, ModelResponse

class AnthropicModel(BaseModel):
    """Anthropic model implementation."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    
    def __init__(self, api_key: str = None, model_name: str = "claude-3-opus-20240229", **kwargs):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        super().__init__(api_key, model_name, **kwargs)
        self.anthropic_version = "2023-06-01"
    
    def supports_function_calling(self) -> bool:
        """Anthropic models support tool use (function calling)."""
        return True
    
    def get_move(self, game_state: str, function_schema: Dict[str, Any], 
                 move_history: List[Dict[str, Any]] = None) -> ModelResponse:
        """Get a move using Anthropic's tool use."""
        
        # Build messages
        system_prompt = "You are an expert game player. Analyze the game state and make the best move. Always provide clear reasoning for your decisions."
        
        messages = []
        
        # Add move history if provided
        if move_history:
            for move in move_history[-3:]:  # Last 3 moves for context
                messages.append({
                    "role": "assistant",
                    "content": f"I'll {move['action']} at position {move.get('position', 'N/A')}. {move.get('reasoning', '')}"
                })
                messages.append({
                    "role": "user",
                    "content": "Good move. Here's the updated board. What's your next move?"
                })
        
        # Add current game state
        messages.append({
            "role": "user",
            "content": game_state
        })
        
        # Convert function schema to Anthropic tool format
        tool = {
            "name": function_schema["name"],
            "description": function_schema["description"],
            "input_schema": {
                "type": "object",
                "properties": function_schema["parameters"]["properties"],
                "required": function_schema["parameters"]["required"]
            }
        }
        
        # Prepare request
        request_data = {
            "model": self.model_name,
            "system": system_prompt,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": tool["name"]}
        }
        
        try:
            # Make API request
            response = httpx.post(
                self.API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.anthropic_version,
                    "Content-Type": "application/json"
                },
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract tool use
            for content in data.get("content", []):
                if content["type"] == "tool_use":
                    tool_input = content["input"]
                    
                    # Extract reasoning
                    reasoning = tool_input.get("reasoning", "")
                    
                    # Remove reasoning from parameters
                    params = {k: v for k, v in tool_input.items() if k != "reasoning"}
                    
                    # Map parameters based on game type
                    if "row" in params and "col" in params:
                        # Minesweeper format
                        action = params.get("action", "reveal")
                        parameters = {
                            "position": [params["row"], params["col"]]
                        }
                    elif "territory" in params:
                        # Risk reinforcement
                        action = "reinforce"
                        parameters = params
                    elif "from_territory" in params:
                        # Risk attack/fortify
                        action = params.get("action", "attack")
                        parameters = params
                    else:
                        action = params.get("action", "unknown")
                        parameters = params
                    
                    # Also check for text content that might contain reasoning
                    text_content = ""
                    for c in data.get("content", []):
                        if c["type"] == "text":
                            text_content = c["text"]
                            break
                    
                    if text_content and not reasoning:
                        reasoning = text_content
                    
                    return ModelResponse(
                        action=action,
                        parameters=parameters,
                        reasoning=reasoning,
                        raw_response=json.dumps(data),
                        tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                    )
            
            # Fallback if no tool use
            text_content = ""
            for content in data.get("content", []):
                if content["type"] == "text":
                    text_content = content["text"]
                    break
            
            return ModelResponse(
                action="error",
                parameters={},
                reasoning=f"No tool use found. Response: {text_content}",
                raw_response=json.dumps(data),
                tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
            )
                
        except httpx.TimeoutException:
            return ModelResponse(
                action="error",
                parameters={},
                reasoning="Request timed out",
                raw_response="",
                tokens_used=0
            )
        except Exception as e:
            return ModelResponse(
                action="error",
                parameters={},
                reasoning=f"Error: {str(e)}",
                raw_response="",
                tokens_used=0
            )