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
from .model_capabilities import get_model_capabilities
from .model_config import get_model_config, get_model_timeout

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
        
        # Get model-specific configuration
        model_cfg = get_model_config(self.model_id)
        self.timeout = model_config.get("timeout", model_cfg.get("timeout", settings.model_timeout))
        
        # Log the timeout being used
        logger.info(f"Initialized {self.model_id} with timeout: {self.timeout}s")
        
        # Get model capabilities
        self.capabilities = get_model_capabilities(self.model_id)
        
        # Set convenience properties
        self.is_reasoning_model = self.capabilities.get("is_reasoning_model", False)
        self.uses_responses_api = self.capabilities.get("api_type") == "responses"
        self.supports_streaming = self.capabilities.get("supports_streaming", True)
        self.supports_function_calling = self.capabilities.get("supports_function_calling", True)
    
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
    
    async def _generate_with_responses_api(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response using the new responses.create API for o3/o4 models."""
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        logger.info(
            f"Generating response using responses API",
            extra={
                "model_id": self.model_id,
                "prompt_length": len(prompt),
                "timeout": self.timeout
            }
        )
        
        try:
            # Get appropriate system prompt
            prompts = prompt_manager.get_prompt_for_model("openai", "", use_function_calling=False)
            
            # Combine system and user prompts
            full_prompt = f"{prompts['system']}\n\n{prompt}"
            
            # Create request with reasoning effort
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model_id,
                    reasoning={"effort": kwargs.get("reasoning_effort", "medium")},
                    input=[
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ]
                ),
                timeout=self.timeout
            )
            
            # Extract content from response
            content = response.output_text if hasattr(response, 'output_text') else str(response)
            
            # Log the response
            logger.info(
                f"Received response from reasoning API",
                extra={
                    "model_id": self.model_id,
                    "response_length": len(content),
                    "has_reasoning": hasattr(response, 'reasoning_text')
                }
            )
            
            # Extract reasoning if available
            reasoning_text = None
            if hasattr(response, 'reasoning_text'):
                reasoning_text = response.reasoning_text
            
            return ModelResponse(
                content=content,
                raw_response=response,
                model_name=self.model_id,
                timestamp=datetime.now(timezone.utc),
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
                reasoning=reasoning_text
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout generating response for model {self.model_id} after {self.timeout}s")
            raise ModelAPIError(f"Timeout after {self.timeout}s. Consider increasing timeout for {self.model_id} models.")
        except Exception as e:
            logger.error(
                f"Error generating response",
                extra={
                    "model_id": self.model_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise ModelAPIError(f"OpenAI API error: {str(e)}")
    
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
        
        # Route to appropriate API based on model type
        if self.uses_responses_api:
            # Use new responses API for o3/o4 models
            return await self._generate_with_responses_api(prompt, **kwargs)
        
        # Check if we should use function calling
        use_functions = kwargs.get("use_functions", True)
        
        try:
            # Get appropriate system prompt
            if use_functions and not self.is_reasoning_model:
                prompts = prompt_manager.get_prompt_for_model("openai", "", use_function_calling=True)
            else:
                prompts = prompt_manager.get_prompt_for_model("openai", "", use_function_calling=False)
            
            # Build the request parameters
            # Check if model supports system messages
            supports_system = self.capabilities.get("supports_system_messages", True)
            
            if supports_system and prompts.get("system"):
                messages = [
                    {
                        "role": "system",
                        "content": prompts["system"]
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            else:
                # For models that don't support system messages, combine system and user prompts
                combined_prompt = prompt
                if prompts.get("system"):
                    combined_prompt = f"{prompts['system']}\n\n{prompt}"
                messages = [
                    {
                        "role": "user",
                        "content": combined_prompt
                    }
                ]
            
            # Build request parameters
            request_params = {
                "model": self.model_id,
                "messages": messages,
                "n": 1,
            }
            
            # o1 models only support default temperature (1)
            if not self.model_id.startswith("o1"):
                request_params["temperature"] = temperature
            
            # Use max_completion_tokens for o1 models, max_tokens for others
            if self.model_id.startswith("o1"):
                request_params["max_completion_tokens"] = max_tokens
            else:
                request_params["max_tokens"] = max_tokens
            
            # Add tools if requested and model supports it
            if use_functions and self.supports_function_calling:
                request_params["tools"] = self._get_minesweeper_tools()
                # Use auto tool_choice to allow reasoning in content field
                # Can be overridden with force_tool_choice kwarg if needed
                if kwargs.get('force_tool_choice', False):
                    request_params["tool_choice"] = {
                        "type": "function",
                        "function": {"name": "make_move"}
                    }
                    logger.info(f"Using function calling for model {self.model_id} with forced tool_choice")
                else:
                    # Default is auto - allows content alongside tool calls
                    logger.info(f"Using function calling for model {self.model_id} with auto tool_choice")
            else:
                logger.info(f"NOT using function calling for model {self.model_id}: use_functions={use_functions}, is_reasoning_model={self.is_reasoning_model}")
            
            # Create completion with timeout and streaming if supported
            stream_callback = kwargs.get('stream_callback')
            
            if stream_callback and not use_functions:  # Can't stream with function calling
                # Stream the response
                stream = await asyncio.wait_for(
                    self.client.chat.completions.create(**request_params, stream=True),
                    timeout=self.timeout
                )
                
                content = ""
                message = None
                tokens_used = None
                
                async for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            content += delta.content
                            # Stream reasoning as it comes
                            await stream_callback(delta.content)
                        
                        # Get final message from last chunk
                        if chunk.choices[0].finish_reason:
                            message = chunk.choices[0].message if hasattr(chunk.choices[0], 'message') else None
                            if hasattr(chunk, 'usage'):
                                tokens_used = chunk.usage.total_tokens
            else:
                # Non-streaming request
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(**request_params),
                    timeout=self.timeout
                )
                
                message = response.choices[0].message
                content = message.content or ""
                tokens_used = response.usage.total_tokens if response.usage else None
            
            reasoning_text = None
            function_call = None
            
            # With auto tool_choice, content field may contain detailed reasoning
            if content:
                # Content field contains the detailed step-by-step analysis
                reasoning_text = content
                logger.info(f"Captured reasoning from content field: {len(content)} chars")
            
            # Check for function calls
            if message and hasattr(message, 'tool_calls') and message.tool_calls:
                logger.info(
                    f"OpenAI function call received",
                    extra={
                        "model_id": self.model_id,
                        "num_tool_calls": len(message.tool_calls),
                        "tool_names": [tc.function.name for tc in message.tool_calls] if message.tool_calls else [],
                        "has_content": bool(content)
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
                            "reasoning_in_function": bool(function_call.get('reasoning')),
                            "reasoning_in_content": bool(content)
                        }
                    )
                    # Preserve the action for parsing
                    action_str = f"Action: {function_call['action']} ({function_call['row']}, {function_call['col']})"
                    
                    # If we have detailed reasoning in content, use that as primary reasoning
                    # Otherwise fall back to reasoning from function call
                    if not reasoning_text:
                        reasoning_text = function_call.get('reasoning', '')
                    
                    # Append action to content for backward compatibility
                    if content:
                        content = f"{content}\n\n{action_str}"
                    else:
                        content = action_str
            else:
                if message:
                    logger.warning(f"No function call in response from {self.model_id}, content length: {len(content)}")
                # For o1 models or when functions not used, check for reasoning
                if hasattr(response, 'choices') and response.choices and hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'reasoning'):
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
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else None,
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else None,
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