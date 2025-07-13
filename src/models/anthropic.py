"""Anthropic model interface implementation."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import anthropic
from anthropic import AsyncAnthropic

from src.core.config import settings
from src.core.exceptions import ModelAPIError, ModelTimeoutError
from .base import BaseModel, ModelResponse


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
        
        try:
            # Create completion with timeout
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=self.model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    system="You are an expert Minesweeper player. Analyze the board carefully and make logical deductions. Always provide clear reasoning for your moves.",
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=self.timeout
            )
            
            # Extract response
            content = response.content[0].text if response.content else ""
            
            # Calculate tokens (Anthropic uses different token counting)
            tokens_used = None
            if hasattr(response, 'usage'):
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return ModelResponse(
                content=content,
                raw_response=response,
                model_name=f"Anthropic/{self.model_id}",
                timestamp=datetime.utcnow(),
                tokens_used=tokens_used,
            )
            
        except asyncio.TimeoutError:
            raise ModelTimeoutError(
                f"Anthropic API call timed out after {self.timeout} seconds"
            )
        except anthropic.APIError as e:
            raise ModelAPIError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            raise ModelAPIError(f"Unexpected error calling Anthropic API: {str(e)}")
    
    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response with retry logic.
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
        
        Returns:
            ModelResponse object
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, **kwargs)
            except ModelAPIError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                continue
        
        raise last_error