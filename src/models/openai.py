"""OpenAI model interface implementation."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import openai
from openai import AsyncOpenAI
import json

from src.core.config import settings
from src.core.exceptions import ModelAPIError, ModelTimeoutError
from src.core.logging_config import get_logger
from src.core.prompts import prompt_manager
from .base import BaseModel, ModelResponse

# Initialize logger
logger = get_logger("models.openai")


class OpenAIModel(BaseModel):
    """OpenAI model interface (GPT-4, GPT-3.5, etc.)."""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize OpenAI model.
        
        Args:
            model_config: Configuration with model_id, temperature, etc.
        """
        super().__init__(model_config)
        
        # Get API key from config or environment
        api_key = model_config.get("api_key") or settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_id = model_config.get("model_id", "gpt-4")
        self.timeout = model_config.get("timeout", settings.model_timeout)
        
        # Check if this is a reasoning model
        self.is_reasoning_model = any(x in self.model_id.lower() for x in ['o1', 'reasoning'])
    
    def _get_minesweeper_tools(self):
        """Get the Minesweeper function definitions for OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "make_move",
                    "description": "Make a move in Minesweeper by revealing, flagging, or unflagging a cell",
                    "parameters": {
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
            }
        ]
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate response from OpenAI model.
        
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
            f"Calling OpenAI API",
            extra={
                "model_id": self.model_id,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "prompt_length": len(prompt)
            }
        )
        
        # Check if we should use function calling
        use_functions = kwargs.get("use_functions", True)
        
        try:
            # Get appropriate system prompt
            if use_functions and not self.is_reasoning_model:
                prompts = prompt_manager.get_prompt_for_model("openai", "", use_function_calling=True)
            else:
                prompts = prompt_manager.get_prompt_for_model("openai", "", use_function_calling=False)
            
            # Build the request parameters
            request_params = {
                "model": self.model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": prompts["system"]
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "n": 1,
            }
            
            # Add tools if requested and not using a reasoning model
            if use_functions and not self.is_reasoning_model:
                request_params["tools"] = self._get_minesweeper_tools()
                request_params["tool_choice"] = "auto"
            
            # Create completion with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**request_params),
                timeout=self.timeout
            )
            
            # Extract response based on whether functions were used
            message = response.choices[0].message
            content = message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else None
            reasoning_text = None
            function_call = None
            
            # Check for function calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                logger.info(
                    f"OpenAI function call received",
                    extra={
                        "model_id": self.model_id,
                        "num_tool_calls": len(message.tool_calls),
                        "tool_names": [tc.function.name for tc in message.tool_calls] if message.tool_calls else []
                    }
                )
                tool_call = message.tool_calls[0]
                if tool_call.function.name == "make_move":
                    function_call = json.loads(tool_call.function.arguments)
                    logger.debug(
                        f"Function call parsed",
                        extra={
                            "action": function_call.get('action'),
                            "position": f"({function_call.get('row')}, {function_call.get('col')})",
                            "reasoning_length": len(function_call.get('reasoning', '')),
                            "reasoning_preview": function_call.get('reasoning', '')[:100] + '...' if len(function_call.get('reasoning', '')) > 100 else function_call.get('reasoning', '')
                        }
                    )
                    # Extract reasoning from function call
                    reasoning_text = function_call.get('reasoning', '')
                    # Format content to include the action
                    content = f"Action: {function_call['action']} ({function_call['row']}, {function_call['col']})"
                    if reasoning_text:
                        content = f"{reasoning_text}\n\n{content}"
            else:
                # For o1 models or when functions not used, check for reasoning
                if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'reasoning'):
                    reasoning_text = response.choices[0].message.reasoning
                elif 'o1' in self.model_id.lower() or 'reasoning' in self.model_id.lower():
                    # For o1 models, the response often starts with reasoning
                    # We'll extract it in the base class
                    pass
            
            # Log successful response
            logger.info(
                f"OpenAI API response received",
                extra={
                    "model_id": self.model_id,
                    "response_length": len(content) if content else 0,
                    "tokens_used": tokens_used,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "has_function_call": function_call is not None,
                    "has_reasoning": bool(reasoning_text)
                }
            )
            
            # Log the full prompt and response for debugging
            logger.debug(
                f"OpenAI API interaction details",
                extra={
                    "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "response": content[:500] + "..." if content and len(content) > 500 else content,
                    "function_call_details": function_call if function_call else None,
                    "reasoning_extracted": reasoning_text if reasoning_text else None
                }
            )
            
            model_response = ModelResponse(
                content=content,
                raw_response=response,
                model_name=f"OpenAI/{self.model_id}",
                timestamp=datetime.now(timezone.utc),
                tokens_used=tokens_used,
            )
            
            # If we found reasoning, use it
            if reasoning_text:
                model_response.reasoning = reasoning_text
            
            # If we have a function call, add it to the response
            if function_call:
                model_response.function_call = function_call
            
            return model_response
            
        except asyncio.TimeoutError:
            logger.error(
                f"OpenAI API timeout",
                extra={"model_id": self.model_id, "timeout": self.timeout}
            )
            raise ModelTimeoutError(
                f"OpenAI API call timed out after {self.timeout} seconds"
            )
        except openai.APIError as e:
            logger.error(
                f"OpenAI API error",
                extra={"model_id": self.model_id, "error": str(e)},
                exc_info=True
            )
            raise ModelAPIError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected OpenAI error",
                extra={"model_id": self.model_id, "error": str(e)},
                exc_info=True
            )
            raise ModelAPIError(f"Unexpected error calling OpenAI API: {str(e)}")