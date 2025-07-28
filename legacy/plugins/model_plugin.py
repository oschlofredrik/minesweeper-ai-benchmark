"""Plugin interface for custom model providers."""

from abc import abstractmethod
from typing import Dict, Any, Optional

from src.models.base import BaseModel, ModelResponse
from src.core.types import Action
from .base import Plugin, PluginType, PluginMetadata


class ModelPlugin(Plugin, BaseModel):
    """Base class for model provider plugins."""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Default metadata for model plugins."""
        return PluginMetadata(
            name="custom_model",
            version="1.0.0",
            description="Custom model plugin",
            author="Unknown",
            plugin_type=PluginType.MODEL,
        )
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional model-specific parameters
        
        Returns:
            Model response
        """
        pass
    
    @abstractmethod
    def parse_action(self, response: str) -> Optional[Action]:
        """
        Parse an action from model response.
        
        Args:
            response: Model response text
        
        Returns:
            Parsed action or None
        """
        pass
    
    @abstractmethod
    def format_prompt(
        self,
        board_state: str,
        prompt_style: str = "standard",
        **kwargs
    ) -> str:
        """
        Format a prompt for the model.
        
        Args:
            board_state: Current game board state
            prompt_style: Style of prompt formatting
            **kwargs: Additional formatting parameters
        
        Returns:
            Formatted prompt
        """
        pass
    
    async def initialize(self) -> None:
        """Initialize the model plugin."""
        # Validate API keys or connection
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup model resources."""
        # Close connections, cleanup resources
        self._initialized = False


class ExampleModelPlugin(ModelPlugin):
    """Example implementation of a model plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example_llm",
            version="1.0.0",
            description="Example LLM integration",
            author="Example Author",
            plugin_type=PluginType.MODEL,
            config_schema={
                "api_key": {"type": "string", "required": True},
                "endpoint": {"type": "string", "required": False},
                "model_name": {"type": "string", "required": True},
            }
        )
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response from example model."""
        # This is where you'd call your custom model API
        # For example:
        # response = await self.client.generate(prompt, **kwargs)
        
        return ModelResponse(
            content="Example response: reveal (2, 3)",
            raw_response={"text": "Example response: reveal (2, 3)"},
            model="example_llm",
            usage={"prompt_tokens": 100, "completion_tokens": 20},
        )
    
    def parse_action(self, response: str) -> Optional[Action]:
        """Parse action from response."""
        # Use the base class parser or implement custom logic
        return self._parse_action_from_response(response)
    
    def format_prompt(
        self,
        board_state: str,
        prompt_style: str = "standard",
        **kwargs
    ) -> str:
        """Format prompt for example model."""
        return f"""You are playing Minesweeper.

Current board state:
{board_state}

Please provide your next move in the format: 'reveal (row, col)' or 'flag (row, col)'
"""