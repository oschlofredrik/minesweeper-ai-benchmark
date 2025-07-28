"""Plugin system for extending the Minesweeper benchmark."""

from .base import Plugin, PluginType, PluginMetadata
from .manager import PluginManager
from .metric_plugin import MetricPlugin, MetricResult, GameResult

__all__ = [
    "Plugin",
    "PluginType", 
    "PluginMetadata",
    "PluginManager",
    "MetricPlugin",
    "MetricResult",
    "GameResult",
]