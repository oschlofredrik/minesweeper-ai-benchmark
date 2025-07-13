"""Base plugin infrastructure."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class PluginType(Enum):
    """Types of plugins supported."""
    MODEL = "model"
    METRIC = "metric"
    GAME = "game"
    PROMPT_STRATEGY = "prompt_strategy"


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin-specific configuration
        """
        self.config = config or {}
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin (async setup)."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def validate_config(self) -> bool:
        """
        Validate plugin configuration against schema.
        
        Returns:
            True if config is valid
        """
        if not self.metadata.config_schema:
            return True
        
        # Simple validation - can be extended with jsonschema
        required_keys = [
            key for key, spec in self.metadata.config_schema.items()
            if spec.get("required", False)
        ]
        
        for key in required_keys:
            if key not in self.config:
                return False
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information.
        
        Returns:
            Plugin info dictionary
        """
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "type": self.metadata.plugin_type.value,
            "description": self.metadata.description,
            "author": self.metadata.author,
            "initialized": self._initialized,
        }