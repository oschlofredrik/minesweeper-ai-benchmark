# Plugin Development Guide

The Minesweeper AI Benchmark supports a plugin architecture that allows you to extend the platform with custom functionality.

## Overview

The plugin system supports four types of plugins:

1. **Model Plugins** - Add support for new LLM providers
2. **Metric Plugins** - Create custom evaluation metrics
3. **Game Plugins** - Implement Minesweeper variants
4. **Prompt Strategy Plugins** - Add advanced prompting techniques (future)

## Quick Start

### 1. Create Example Plugins

```bash
python -m src.cli.main plugin create-example
```

This creates example plugin files in the `plugins/` directory.

### 2. List Available Plugins

```bash
python -m src.cli.main plugin list
```

### 3. View Plugin Information

```bash
python -m src.cli.main plugin info <plugin_name>
```

### 4. Load a Plugin

```bash
python -m src.cli.main plugin load <plugin_name>
```

## Creating a Model Plugin

Model plugins allow you to integrate new LLM providers or custom models.

### Basic Structure

```python
from src.plugins import ModelPlugin, PluginMetadata, PluginType
from src.models.base import ModelResponse
from src.core.types import Action
from typing import Optional

class MyCustomModel(ModelPlugin):
    """Custom model implementation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_custom_model",
            version="1.0.0",
            description="Integration with My Custom LLM",
            author="Your Name",
            plugin_type=PluginType.MODEL,
            config_schema={
                "api_key": {"type": "string", "required": True},
                "endpoint": {"type": "string", "required": True},
                "model_name": {"type": "string", "required": False},
            }
        )
    
    async def initialize(self) -> None:
        """Initialize your model client."""
        # Set up API client
        self.client = MyAPIClient(
            api_key=self.config["api_key"],
            endpoint=self.config["endpoint"]
        )
        self._initialized = True
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response from your model."""
        # Call your API
        response = await self.client.complete(
            prompt=prompt,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 500)
        )
        
        return ModelResponse(
            content=response.text,
            raw_response=response.raw,
            model=self.config.get("model_name", "custom"),
            usage={
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
            }
        )
    
    def parse_action(self, response: str) -> Optional[Action]:
        """Parse game action from response."""
        # Use base class parser or implement custom
        return self._parse_action_from_response(response)
    
    def format_prompt(self, board_state: str, prompt_style: str = "standard", **kwargs) -> str:
        """Format prompt for your model."""
        if prompt_style == "json":
            return f'''{{
                "task": "minesweeper",
                "board": "{board_state}",
                "instruction": "Provide next move as: reveal (row, col) or flag (row, col)"
            }}'''
        else:
            return f"Board:\n{board_state}\n\nYour move:"
```

### Using Your Model Plugin

```bash
# Create config file
cat > model_config.json << EOF
{
    "api_key": "your-api-key",
    "endpoint": "https://api.example.com/v1",
    "model_name": "custom-v1"
}
EOF

# Load and test plugin
python -m src.cli.main plugin load my_custom_model -c model_config.json

# Evaluate with plugin
python -m src.cli.main evaluate --model my_custom_model --provider plugin --num-games 10
```

## Creating a Metric Plugin

Metric plugins add new ways to evaluate model performance.

### Basic Structure

```python
from src.plugins import MetricPlugin, PluginMetadata, PluginType, MetricResult
from src.core.types import GameResult
from typing import List

class StrategyMetric(MetricPlugin):
    """Measures strategic gameplay patterns."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="strategy_metrics",
            version="1.0.0",
            description="Advanced strategy analysis metrics",
            author="Your Name",
            plugin_type=PluginType.METRIC,
        )
    
    def calculate(self, game_results: List[GameResult], **kwargs) -> List[MetricResult]:
        """Calculate metrics across all games."""
        metrics = []
        
        # Corner preference metric
        corner_moves = 0
        total_first_moves = 0
        
        for game in game_results:
            if game.moves:
                first_move = game.moves[0]
                if self._is_corner(first_move.position, game.board_size):
                    corner_moves += 1
                total_first_moves += 1
        
        if total_first_moves > 0:
            metrics.append(MetricResult(
                name="corner_preference",
                value=corner_moves / total_first_moves,
                description="Preference for corner moves as first move",
                metadata={"total_games": len(game_results)}
            ))
        
        # Add more metrics...
        
        return metrics
    
    def calculate_single_game(self, game_result: GameResult, **kwargs) -> List[MetricResult]:
        """Calculate metrics for one game."""
        metrics = []
        
        # Pattern detection count
        patterns_found = self._count_patterns(game_result)
        metrics.append(MetricResult(
            name="patterns_utilized",
            value=patterns_found,
            description="Number of Minesweeper patterns identified",
        ))
        
        return metrics
    
    def _is_corner(self, position, board_size):
        """Check if position is a corner."""
        row, col = position.row, position.col
        max_row, max_col = board_size[0] - 1, board_size[1] - 1
        return (row, col) in [(0, 0), (0, max_col), (max_row, 0), (max_row, max_col)]
    
    def _count_patterns(self, game_result):
        """Count recognized patterns in gameplay."""
        # Implementation details...
        return 0
```

### Using Metric Plugins

Metric plugins are automatically used during evaluation when loaded:

```bash
# Load metric plugin
python -m src.cli.main plugin load strategy_metrics

# Run evaluation - metrics will be included
python -m src.cli.main evaluate --model gpt-4 --num-games 20
```

## Creating a Game Plugin

Game plugins allow you to create Minesweeper variants.

### Basic Structure

```python
from src.plugins import GamePlugin, PluginMetadata, PluginType, GameState
from src.core.types import Action, GameStatus, Position
from typing import Tuple, Dict, Any

class TriangularMinesweeper(GamePlugin):
    """Minesweeper on a triangular grid."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="triangular_minesweeper",
            version="1.0.0",
            description="Minesweeper variant with triangular cells",
            author="Your Name",
            plugin_type=PluginType.GAME,
            config_schema={
                "size": {"type": "integer", "required": False, "default": 9},
                "mine_density": {"type": "float", "required": False, "default": 0.15},
            }
        )
    
    def create_game(self, difficulty: str = "medium", **kwargs) -> GameState:
        """Create new triangular Minesweeper game."""
        size = self.config.get("size", 9)
        mine_density = self.config.get("mine_density", 0.15)
        
        # Create triangular grid
        board = self._create_triangular_board(size, mine_density)
        
        return GameState(
            board=board,
            status=GameStatus.IN_PROGRESS,
            moves=[],
            metadata={
                "difficulty": difficulty,
                "size": size,
                "total_mines": int(size * (size + 1) / 2 * mine_density),
                "variant": "triangular",
            }
        )
    
    def make_move(self, game_state: GameState, action: Action) -> Tuple[bool, str, GameState]:
        """Process a move in triangular Minesweeper."""
        # Validate move
        if not self.is_valid_move(game_state, action):
            return False, "Invalid position for triangular grid", game_state
        
        # Process move...
        # Update board, check for win/loss, etc.
        
        new_state = GameState(
            board=updated_board,
            status=new_status,
            moves=game_state.moves + [action],
            metadata=game_state.metadata,
        )
        
        return True, "Move successful", new_state
    
    def get_board_representation(self, game_state: GameState, format: str = "ascii") -> str:
        """Get triangular board as string."""
        if format == "ascii":
            return self._triangular_to_ascii(game_state.board)
        else:
            return str(game_state.board)
    
    def _create_triangular_board(self, size: int, mine_density: float):
        """Create triangular game board."""
        # Implementation...
        pass
    
    def _triangular_to_ascii(self, board):
        """Convert to ASCII art triangular display."""
        # Implementation...
        pass
```

## Plugin Configuration

### Configuration Schema

Define required and optional configuration parameters:

```python
config_schema={
    "api_key": {
        "type": "string",
        "required": True,
        "description": "API authentication key"
    },
    "timeout": {
        "type": "integer", 
        "required": False,
        "default": 30,
        "description": "Request timeout in seconds"
    },
    "retry_count": {
        "type": "integer",
        "required": False, 
        "default": 3,
        "description": "Number of retries on failure"
    }
}
```

### Loading with Configuration

```bash
# Via JSON file
python -m src.cli.main plugin load my_plugin -c config.json

# Or programmatically
from src.plugins import PluginManager

manager = PluginManager()
plugin = await manager.load_plugin("my_plugin", {
    "api_key": "xxx",
    "timeout": 60
})
```

## Plugin Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def generate(self, prompt: str, **kwargs) -> ModelResponse:
    try:
        response = await self.client.complete(prompt)
        return ModelResponse(...)
    except ApiError as e:
        # Log error and return meaningful message
        logger.error(f"API error: {e}")
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}")
        raise
```

### 2. Resource Management

Clean up resources properly:

```python
async def initialize(self) -> None:
    """Initialize resources."""
    self.client = await create_client(self.config)
    self.session = aiohttp.ClientSession()
    self._initialized = True

async def cleanup(self) -> None:
    """Clean up resources."""
    if hasattr(self, 'session'):
        await self.session.close()
    if hasattr(self, 'client'):
        await self.client.close()
    self._initialized = False
```

### 3. Configuration Validation

Validate configuration thoroughly:

```python
def validate_config(self) -> bool:
    """Validate plugin configuration."""
    if not super().validate_config():
        return False
    
    # Additional validation
    if "endpoint" in self.config:
        if not self.config["endpoint"].startswith("https://"):
            logger.warning("Endpoint should use HTTPS")
    
    return True
```

### 4. Documentation

Document your plugin well:

```python
class MyPlugin(ModelPlugin):
    """
    Integration with MyLLM API.
    
    This plugin provides access to MyLLM's language models through their
    REST API. It supports streaming responses and function calling.
    
    Configuration:
        api_key: Your MyLLM API key
        endpoint: API endpoint (default: https://api.myllm.com/v1)
        model: Model identifier (default: myllm-large)
    
    Example:
        plugin = MyPlugin({
            "api_key": "sk-...",
            "model": "myllm-large-v2"
        })
    """
```

## Testing Plugins

### Unit Testing

Create tests for your plugin:

```python
import pytest
from src.plugins import PluginManager

@pytest.mark.asyncio
async def test_my_plugin():
    manager = PluginManager()
    
    # Test loading
    plugin = await manager.load_plugin("my_plugin", {
        "api_key": "test_key"
    })
    assert plugin._initialized
    
    # Test functionality
    response = await plugin.generate("Test prompt")
    assert response.content
    
    # Test cleanup
    await manager.unload_plugin("my_plugin")
```

### Integration Testing

Test with the benchmark:

```bash
# Test model plugin
python -m src.cli.main plugin test-model my_custom_model --model test --num-games 3

# Run small evaluation
python -m src.cli.main evaluate --model my_custom_model --provider plugin --num-games 5
```

## Distribution

### Packaging Your Plugin

Create a plugin package:

```
my_plugin/
├── __init__.py
├── plugin.py
├── requirements.txt
├── README.md
└── config_example.json
```

### Plugin Manifest

Include a manifest for easy discovery:

```json
{
    "plugin": {
        "name": "my_custom_model",
        "version": "1.0.0",
        "description": "MyLLM integration for Minesweeper benchmark",
        "author": "Your Name",
        "type": "model",
        "dependencies": ["httpx>=0.25.0", "pydantic>=2.0"],
        "homepage": "https://github.com/yourname/my-plugin",
        "config_schema": {
            "api_key": {"type": "string", "required": true}
        }
    }
}
```

### Installation

Users can install your plugin:

```bash
# From file
python -m src.cli.main plugin install path/to/plugin.py

# From URL (future)
python -m src.cli.main plugin install https://example.com/plugin.py

# From package (future)
pip install minesweeper-plugin-mylllm
```

## Advanced Topics

### Async Operations

All plugin methods can be async:

```python
async def calculate(self, game_results: List[GameResult], **kwargs) -> List[MetricResult]:
    """Calculate metrics with async operations."""
    # Fetch additional data asynchronously
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/baseline") as resp:
            baseline = await resp.json()
    
    # Calculate metrics...
    return metrics
```

### Plugin Dependencies

Specify and check dependencies:

```python
@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="advanced_plugin",
        dependencies=["numpy>=1.20", "scipy>=1.7"],
        ...
    )

async def initialize(self) -> None:
    """Check dependencies before initialization."""
    try:
        import numpy as np
        import scipy
    except ImportError as e:
        raise RuntimeError(f"Missing dependency: {e}")
    
    self._initialized = True
```

### Inter-Plugin Communication

Plugins can interact through the manager:

```python
async def generate(self, prompt: str, **kwargs) -> ModelResponse:
    """Use another plugin for preprocessing."""
    manager = kwargs.get("plugin_manager")
    if manager:
        preprocessor = manager.get_plugin("prompt_enhancer")
        if preprocessor:
            prompt = await preprocessor.enhance(prompt)
    
    # Continue with generation...
```

## Troubleshooting

### Plugin Not Loading

1. Check file is in `plugins/` directory
2. Verify class inherits from correct base class
3. Ensure metadata property is implemented
4. Check for syntax errors

### Configuration Errors

1. Verify all required fields are provided
2. Check data types match schema
3. Look for validation errors in logs

### Performance Issues

1. Use async operations for I/O
2. Implement caching where appropriate
3. Profile your plugin code
4. Consider batching operations