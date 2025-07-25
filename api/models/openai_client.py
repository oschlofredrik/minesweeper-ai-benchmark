"""OpenAI model client for Vercel."""
import os
import json
from typing import Dict, List, Optional, Any
import httpx
from .base import BaseModel, ModelResponse

class OpenAIModel(BaseModel):
    """OpenAI model implementation."""
    
    API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-4", **kwargs):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        super().__init__(api_key, model_name, **kwargs)
    
    def supports_function_calling(self) -> bool:
        """OpenAI models support function calling."""
        return True
    
    def get_move(self, game_state: str, function_schema: Dict[str, Any], 
                 move_history: List[Dict[str, Any]] = None) -> ModelResponse:
        """Get a move using OpenAI's function calling."""
        
        # Build messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert game player. Analyze the game state and make the best move. Always provide clear reasoning for your decisions."
            },
            {
                "role": "user",
                "content": game_state
            }
        ]
        
        # Add move history if provided
        if move_history:
            for move in move_history[-5:]:  # Last 5 moves for context
                messages.append({
                    "role": "assistant",
                    "content": f"I'll {move['action']} at position {move.get('position', 'N/A')}. {move.get('reasoning', '')}"
                })
                messages.append({
                    "role": "user", 
                    "content": "Good move. Here's the updated board. What's your next move?"
                })
                messages.append({
                    "role": "user",
                    "content": game_state
                })
        
        # Prepare request
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": [{
                "type": "function",
                "function": function_schema
            }],
            "tool_choice": {"type": "function", "function": {"name": function_schema["name"]}}
        }
        
        try:
            # Make API request
            response = httpx.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]
            
            # Extract function call
            if "tool_calls" in message and message["tool_calls"]:
                tool_call = message["tool_calls"][0]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                # Extract reasoning
                reasoning = function_args.get("reasoning", "")
                
                # Remove reasoning from parameters
                params = {k: v for k, v in function_args.items() if k != "reasoning"}
                
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
                
                return ModelResponse(
                    action=action,
                    parameters=parameters,
                    reasoning=reasoning,
                    raw_response=json.dumps(message),
                    tokens_used=data["usage"]["total_tokens"]
                )
            else:
                # Fallback if no function call
                content = message.get("content", "")
                return ModelResponse(
                    action="error",
                    parameters={},
                    reasoning=f"No function call made. Response: {content}",
                    raw_response=json.dumps(message),
                    tokens_used=data["usage"]["total_tokens"]
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