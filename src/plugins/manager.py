"""Plugin manager for loading and managing plugins."""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import json
import asyncio

from .base import Plugin, PluginType, PluginMetadata
from .model_plugin import ModelPlugin
from .metric_plugin import MetricPlugin
from .game_plugin import GamePlugin


class PluginManager:
    """Manages loading, initialization, and access to plugins."""
    
    def __init__(self, plugin_dir: Optional[Path] = None):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dir: Directory containing plugins
        """
        self.plugin_dir = plugin_dir or Path("plugins")
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_classes: Dict[PluginType, Type[Plugin]] = {
            PluginType.MODEL: ModelPlugin,
            PluginType.METRIC: MetricPlugin,
            PluginType.GAME: GamePlugin,
        }
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover available plugins in the plugin directory.
        
        Returns:
            List of plugin metadata
        """
        discovered = []
        
        # Look for Python files in plugin directory
        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                # Load module dynamically
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(
                    f"custom_plugins.{module_name}",
                    file_path
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"custom_plugins.{module_name}"] = module
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes in module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Plugin) and 
                            obj not in [Plugin, ModelPlugin, MetricPlugin, GamePlugin]):
                            
                            # Create temporary instance to get metadata
                            try:
                                temp_instance = obj()
                                discovered.append(temp_instance.metadata)
                            except Exception as e:
                                print(f"Error getting metadata for {name}: {e}")
                
            except Exception as e:
                print(f"Error loading plugin from {file_path}: {e}")
        
        # Also check for plugin manifests (JSON files)
        for manifest_path in self.plugin_dir.glob("*.json"):
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                
                if "plugin" in manifest:
                    metadata = PluginMetadata(
                        name=manifest["plugin"]["name"],
                        version=manifest["plugin"]["version"],
                        description=manifest["plugin"]["description"],
                        author=manifest["plugin"]["author"],
                        plugin_type=PluginType(manifest["plugin"]["type"]),
                        dependencies=manifest["plugin"].get("dependencies", []),
                        config_schema=manifest["plugin"].get("config_schema"),
                    )
                    discovered.append(metadata)
            
            except Exception as e:
                print(f"Error loading manifest from {manifest_path}: {e}")
        
        return discovered
    
    async def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Plugin:
        """
        Load and initialize a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            config: Plugin configuration
        
        Returns:
            Initialized plugin instance
        """
        # Check if already loaded
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        
        # Find plugin class
        plugin_class = self._find_plugin_class(plugin_name)
        if not plugin_class:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        # Create instance
        plugin = plugin_class(config)
        
        # Validate configuration
        if not plugin.validate_config():
            raise ValueError(f"Invalid configuration for plugin '{plugin_name}'")
        
        # Initialize plugin
        await plugin.initialize()
        
        # Store plugin
        self.plugins[plugin_name] = plugin
        
        return plugin
    
    async def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload and cleanup a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
        """
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            await plugin.cleanup()
            del self.plugins[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        Get a loaded plugin by name.
        
        Args:
            plugin_name: Plugin name
        
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        Get all loaded plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
        
        Returns:
            List of plugins of the specified type
        """
        return [
            plugin for plugin in self.plugins.values()
            if plugin.metadata.plugin_type == plugin_type
        ]
    
    def list_loaded_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins.
        
        Returns:
            List of plugin information
        """
        return [plugin.get_info() for plugin in self.plugins.values()]
    
    async def reload_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Plugin:
        """
        Reload a plugin (unload and load again).
        
        Args:
            plugin_name: Plugin to reload
            config: New configuration
        
        Returns:
            Reloaded plugin instance
        """
        await self.unload_plugin(plugin_name)
        return await self.load_plugin(plugin_name, config)
    
    def _find_plugin_class(self, plugin_name: str) -> Optional[Type[Plugin]]:
        """Find plugin class by name."""
        # First check built-in example plugins
        for module_name in ["model_plugin", "metric_plugin", "game_plugin"]:
            try:
                module = importlib.import_module(f"src.plugins.{module_name}")
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Plugin) and
                        hasattr(obj, 'metadata')):
                        
                        # Create temp instance to check name
                        try:
                            temp = obj()
                            if temp.metadata.name == plugin_name:
                                return obj
                        except:
                            pass
            except:
                pass
        
        # Then check custom plugins in plugin directory
        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(
                    f"custom_plugins.{module_name}",
                    file_path
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Plugin) and
                            hasattr(obj, 'metadata')):
                            
                            try:
                                temp = obj()
                                if temp.metadata.name == plugin_name:
                                    return obj
                            except:
                                pass
            except:
                pass
        
        return None
    
    def install_plugin_from_file(
        self,
        file_path: Path,
        plugin_name: Optional[str] = None,
    ) -> bool:
        """
        Install a plugin from a file.
        
        Args:
            file_path: Path to plugin file
            plugin_name: Optional name for the plugin file
        
        Returns:
            True if successful
        """
        try:
            # Copy file to plugin directory
            dest_name = plugin_name or file_path.name
            dest_path = self.plugin_dir / dest_name
            
            with open(file_path, 'r') as src:
                content = src.read()
            
            with open(dest_path, 'w') as dst:
                dst.write(content)
            
            return True
        
        except Exception as e:
            print(f"Error installing plugin: {e}")
            return False
    
    async def validate_all_plugins(self) -> Dict[str, bool]:
        """
        Validate all discovered plugins.
        
        Returns:
            Dictionary of plugin names to validation status
        """
        results = {}
        discovered = self.discover_plugins()
        
        for metadata in discovered:
            try:
                # Try to load plugin
                plugin = await self.load_plugin(metadata.name)
                results[metadata.name] = True
                
                # Unload after validation
                await self.unload_plugin(metadata.name)
                
            except Exception as e:
                results[metadata.name] = False
                print(f"Plugin {metadata.name} validation failed: {e}")
        
        return results