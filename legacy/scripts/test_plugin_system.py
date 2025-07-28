#!/usr/bin/env python3
"""Test the plugin system functionality."""

import asyncio
from pathlib import Path
from src.plugins import PluginManager, PluginType

async def test_plugin_system():
    """Test basic plugin system functionality."""
    print("Testing Plugin System...")
    
    # Create plugin manager
    manager = PluginManager()
    print(f"\nPlugin directory: {manager.plugin_dir}")
    
    # Test 1: Discover plugins
    print("\n1. Discovering Plugins:")
    discovered = manager.discover_plugins()
    print(f"  Found {len(discovered)} plugins")
    
    for metadata in discovered:
        print(f"  - {metadata.name} v{metadata.version} ({metadata.plugin_type.value})")
    
    # Test 2: Get example plugins
    print("\n2. Built-in Example Plugins:")
    
    # Try to load example model plugin
    try:
        model_plugin = await manager.load_plugin("example_llm")
        print(f"  ✓ Loaded model plugin: {model_plugin.metadata.name}")
        
        # Test model plugin functionality
        response = await model_plugin.generate("Test prompt")
        print(f"    Response: {response.content[:50]}...")
        
    except Exception as e:
        print(f"  ✗ Error loading model plugin: {e}")
    
    # Try to load example metric plugin
    try:
        metric_plugin = await manager.load_plugin("efficiency_metrics")
        print(f"  ✓ Loaded metric plugin: {metric_plugin.metadata.name}")
        
    except Exception as e:
        print(f"  ✗ Error loading metric plugin: {e}")
    
    # Test 3: List loaded plugins
    print("\n3. Loaded Plugins:")
    loaded = manager.list_loaded_plugins()
    for plugin_info in loaded:
        print(f"  - {plugin_info['name']} ({plugin_info['type']})")
        print(f"    Initialized: {plugin_info['initialized']}")
    
    # Test 4: Get plugins by type
    print("\n4. Plugins by Type:")
    model_plugins = manager.get_plugins_by_type(PluginType.MODEL)
    print(f"  Model plugins: {len(model_plugins)}")
    
    metric_plugins = manager.get_plugins_by_type(PluginType.METRIC)
    print(f"  Metric plugins: {len(metric_plugins)}")
    
    # Test 5: Plugin validation
    print("\n5. Plugin Validation:")
    validation_results = await manager.validate_all_plugins()
    for plugin_name, is_valid in validation_results.items():
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {plugin_name}: {status}")
    
    # Cleanup
    print("\n6. Cleanup:")
    for plugin_name in list(manager.plugins.keys()):
        await manager.unload_plugin(plugin_name)
        print(f"  Unloaded {plugin_name}")
    
    print("\n✅ Plugin system test complete!")

if __name__ == "__main__":
    asyncio.run(test_plugin_system())