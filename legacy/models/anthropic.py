"""Anthropic model interface implementation."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import anthropic
from anthropic import AsyncAnthropic

from src.core.config import settings
from src.core.exceptions import ModelAPIError, ModelTimeoutError
from src.core.logging_config import get_logger
from src.core.prompts import prompt_manager
from .base import BaseModel, ModelResponse

# Initialize logger
logger = get_logger("models.anthropic")


class AnthropicModel(BaseModel):
    """Anthropic model interface (Claude 3, etc.)."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize Anthropic model.
        
        Args:
            model_config: Configuration with model_id, temperature, etc.
        """
        super().__init__(model_config)
        
        # Get API key from config or environment
        api_key = model_config.get("api_key") or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.model_id = model_config.get("model_id", "claude-3-opus-20240229")
        self.timeout = model_config.get("timeout", settings.model_timeout)
        
        # Check if this is a model with thinking/reasoning capabilities
        self.supports_thinking = 'claude-4' in self.model_id.lower() or model_config.get("enable_thinking", False)
    
    def _get_minesweeper_tools(self):
        """Get the Minesweeper tool definitions for Anthropic."""
        return [
            {
                "name": "make_move",
                "description": "Make a move in Minesweeper by revealing, flagging, or unflagging a cell",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["reveal", "flag", "unflag"],
                            "description": "The action to perform on the cell"
                        },
                        "row": {
                            "type": "integer",
                            "description": "The row index of the cell (0-based)",
                            "minimum": 0
                        },
                        "col": {
                            "type": "integer",
                            "description": "The column index of the cell (0-based)",
                            "minimum": 0
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed explanation for why this move is being made, including logical deductions"
                        }
                    },
                    "required": ["action", "row", "col", "reasoning"]
                }
            }
        ]
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate response from Anthropic model.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            ModelResponse object
        """
        # Merge kwargs with defaults
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        # Log the API call
        logger.info(
            f"Calling Anthropic API",
            extra={
                "model_id": self.model_id,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "prompt_length": len(prompt)
            }
        )
        
        # Check if we should use tools
        use_tools = kwargs.get("use_tools", True)
        
        try:
            # Get appropriate system prompt
            if use_tools and not self.supports_thinking:
                prompts = prompt_manager.get_prompt_for_model("anthropic", "", use_function_calling=True)
            else:
                prompts = prompt_manager.get_prompt_for_model("anthropic", "", use_function_calling=False)
            
            # Build the request parameters
            request_params = {
                "model": self.model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "system": prompts["system"],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add tools if requested and not using thinking mode
            if kwargs.get('use_game_functions') and kwargs.get('game_tools') and not self.supports_thinking:
                # Use game-specific tools
                request_params["tools"] = [kwargs['game_tools']]
            elif use_tools and not self.supports_thinking:
                request_params["tools"] = self._get_minesweeper_tools()
            
            # Create completion with timeout
            response = await asyncio.wait_for(
                self.client.messages.create(**request_params),
                timeout=self.timeout
            )
            
            # Extract response based on content type
            content = ""
            reasoning_text = None
            tool_use = None
            
            # Process content blocks
            if hasattr(response, 'content'):
                for block in response.content:
                    if hasattr(block, 'type'):
                        if block.type == 'text':
                            content += block.text
                        elif block.type == 'thinking':
                            reasoning_text = block.text
                        elif block.type == 'tool_use' and block.name == 'make_move':
                            tool_use = block.input
            
            # With auto tool use, content contains detailed reasoning
            if content and not reasoning_text:
                reasoning_text = content
                logger.info(f"Captured reasoning from text content: {len(content)} chars")
            
            # If we have a tool use, append the action to content
            if tool_use:
                action_str = f"Action: {tool_use['action']} ({tool_use['row']}, {tool_use['col']})"
                if content:
                    content = f"{content}\n\n{action_str}"
                else:
                    content = action_str
                    # Fall back to reasoning from tool use if no text content
                    if not reasoning_text and 'reasoning' in tool_use:
                        reasoning_text = tool_use['reasoning']
            
            # If no content was extracted, try the old way
            if not content and response.content:
                content = response.content[0].text if response.content else ""
            
            # Calculate tokens (Anthropic uses different token counting)
            tokens_used = None
            if hasattr(response, 'usage'):
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Log successful response
            logger.info(
                f"Anthropic API response received",
                extra={
                    "model_id": self.model_id,
                    "response_length": len(content) if content else 0,
                    "tokens_used": tokens_used,
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else None,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else None,
                    "has_tool_use": tool_use is not None,
                    "has_reasoning": bool(reasoning_text)
                }
            )
            
            # Log the full prompt and response for debugging
            logger.debug(
                f"Anthropic API interaction details",
                extra={
                    "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "response": content[:500] + "..." if content and len(content) > 500 else content,
                    "tool_use_details": tool_use if tool_use else None,
                    "reasoning_extracted": reasoning_text if reasoning_text else None
                }
            )
            
            model_response = ModelResponse(
                content=content,
                raw_response=response,
                model_name=f"Anthropic/{self.model_id}",
                timestamp=datetime.now(timezone.utc),
                tokens_used=tokens_used,
            )
            
            # If we found reasoning, use it
            if reasoning_text:
                model_response.reasoning = reasoning_text
            
            # If we have a tool use, add it to the response
            if tool_use:
                model_response.function_call = tool_use
            
            return model_response
            
        except asyncio.TimeoutError:
            logger.error(
                f"Anthropic API timeout",
                extra={"model_id": self.model_id, "timeout": self.timeout}
            )
            raise ModelTimeoutError(
                f"Anthropic API call timed out after {self.timeout} seconds"
            )
        except anthropic.APIError as e:
            logger.error(
                f"Anthropic API error",
                extra={"model_id": self.model_id, "error": str(e)},
                exc_info=True
            )
            raise ModelAPIError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected Anthropic error",
                extra={"model_id": self.model_id, "error": str(e)},
                exc_info=True
            )
            raise ModelAPIError(f"Unexpected error calling Anthropic API: {str(e)}")