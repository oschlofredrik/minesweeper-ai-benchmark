"""Test plugin base functionality without external dependencies."""

import asyncio
from datetime import datetime
from src.plugins.base import Plugin, PluginType, PluginMetadata


class TestPlugin(Plugin):
    """Test implementation of a plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.MODEL,
            config_schema={
                "required_field": {"type": "string", "required": True},
                "optional_field": {"type": "integer", "required": False},
            }
        )
    
    async def initialize(self) -> None:
        """Initialize test plugin."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup test plugin."""
        self._initialized = False


def test_plugin_metadata():
    """Test plugin metadata creation."""
    metadata = PluginMetadata(
        name="example",
        version="1.0.0",
        description="Example plugin",
        author="Author",
        plugin_type=PluginType.METRIC,
    )
    
    assert metadata.name == "example"
    assert metadata.plugin_type == PluginType.METRIC
    assert metadata.dependencies == []  # Default empty list
    assert isinstance(metadata.created_at, datetime)
    print("✓ Plugin metadata test passed")


def test_plugin_config_validation():
    """Test plugin configuration validation."""
    # Test with valid config
    plugin = TestPlugin({"required_field": "value", "optional_field": 42})
    assert plugin.validate_config() == True
    
    # Test with missing required field
    plugin = TestPlugin({"optional_field": 42})
    assert plugin.validate_config() == False
    
    # Test with empty config (missing required)
    plugin = TestPlugin({})
    assert plugin.validate_config() == False
    
    print("✓ Plugin config validation test passed")


def test_plugin_info():
    """Test plugin info retrieval."""
    plugin = TestPlugin({"required_field": "test"})
    info = plugin.get_info()
    
    assert info["name"] == "test_plugin"
    assert info["version"] == "1.0.0"
    assert info["type"] == "model"
    assert info["initialized"] == False
    
    print("✓ Plugin info test passed")


async def test_plugin_lifecycle():
    """Test plugin initialization and cleanup."""
    plugin = TestPlugin({"required_field": "test"})
    
    # Check initial state
    assert plugin._initialized == False
    
    # Initialize
    await plugin.initialize()
    assert plugin._initialized == True
    
    # Cleanup
    await plugin.cleanup()
    assert plugin._initialized == False
    
    print("✓ Plugin lifecycle test passed")


def run_tests():
    """Run all tests."""
    print("Testing Plugin Base Functionality...\n")
    
    test_plugin_metadata()
    test_plugin_config_validation()
    test_plugin_info()
    asyncio.run(test_plugin_lifecycle())
    
    print("\n✅ All plugin base tests passed!")


if __name__ == "__main__":
    run_tests()