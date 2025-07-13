"""OpenAI model interface implementation."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import openai
from openai import AsyncOpenAI

from src.core.config import settings
from src.core.exceptions import ModelAPIError, ModelTimeoutError
from src.core.logging_config import get_logger
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
        
        try:
            # Create completion with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert Minesweeper player. Analyze the board carefully and make logical deductions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                ),
                timeout=self.timeout
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            # Log successful response
            logger.info(
                f"OpenAI API response received",
                extra={
                    "model_id": self.model_id,
                    "response_length": len(content) if content else 0,
                    "tokens_used": tokens_used,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None
                }
            )
            
            # Log the full prompt and response for debugging
            logger.debug(
                f"OpenAI API interaction details",
                extra={
                    "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "response": content[:500] + "..." if content and len(content) > 500 else content
                }
            )
            
            return ModelResponse(
                content=content,
                raw_response=response,
                model_name=f"OpenAI/{self.model_id}",
                timestamp=datetime.utcnow(),
                tokens_used=tokens_used,
            )
            
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