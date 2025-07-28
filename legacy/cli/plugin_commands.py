"""CLI commands for plugin management."""

import click
import asyncio
from pathlib import Path
from typing import Optional
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.plugins import PluginManager, PluginType

console = Console()


def add_plugin_commands(cli_group):
    """Add plugin management commands to CLI."""
    
    @cli_group.group()
    def plugin():
        """Plugin management commands."""
        pass
    
    @plugin.command()
    def list():
        """List available plugins."""
        manager = PluginManager()
        discovered = manager.discover_plugins()
        
        if not discovered:
            console.print("[yellow]No plugins found[/yellow]")
            console.print("\nTo add plugins, place them in the 'plugins' directory")
            return
        
        # Group by type
        by_type = {}
        for metadata in discovered:
            plugin_type = metadata.plugin_type.value
            if plugin_type not in by_type:
                by_type[plugin_type] = []
            by_type[plugin_type].append(metadata)
        
        # Display each type
        for plugin_type, plugins in by_type.items():
            table = Table(title=f"{plugin_type.title()} Plugins")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Author", style="yellow")
            table.add_column("Description", style="white")
            
            for metadata in plugins:
                table.add_row(
                    metadata.name,
                    metadata.version,
                    metadata.author,
                    metadata.description,
                )
            
            console.print(table)
            console.print()
    
    @plugin.command()
    @click.argument("plugin_name")
    def info(plugin_name: str):
        """Show detailed information about a plugin."""
        manager = PluginManager()
        discovered = manager.discover_plugins()
        
        # Find plugin
        metadata = None
        for m in discovered:
            if m.name == plugin_name:
                metadata = m
                break
        
        if not metadata:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            return
        
        # Display info
        console.print(Panel.fit(
            f"[bold]{metadata.name}[/bold] v{metadata.version}\n"
            f"Type: {metadata.plugin_type.value}\n"
            f"Author: {metadata.author}\n"
            f"Description: {metadata.description}",
            title="Plugin Information",
        ))
        
        if metadata.dependencies:
            console.print("\n[cyan]Dependencies:[/cyan]")
            for dep in metadata.dependencies:
                console.print(f"  - {dep}")
        
        if metadata.config_schema:
            console.print("\n[cyan]Configuration Schema:[/cyan]")
            for key, spec in metadata.config_schema.items():
                required = "required" if spec.get("required") else "optional"
                console.print(f"  {key}: {spec.get('type', 'any')} ({required})")
    
    @plugin.command()
    @click.argument("plugin_name")
    @click.option("--config-file", "-c", type=click.Path(exists=True), help="Configuration file")
    def load(plugin_name: str, config_file: Optional[str]):
        """Load and initialize a plugin."""
        manager = PluginManager()
        
        # Load config if provided
        config = {}
        if config_file:
            with open(config_file) as f:
                config = json.load(f)
        
        # Load plugin
        console.print(f"Loading plugin '{plugin_name}'...")
        
        try:
            plugin = asyncio.run(manager.load_plugin(plugin_name, config))
            console.print(f"[green]✓ Plugin '{plugin_name}' loaded successfully[/green]")
            
            # Show plugin info
            info = plugin.get_info()
            console.print(f"  Type: {info['type']}")
            console.print(f"  Version: {info['version']}")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to load plugin: {e}[/red]")
    
    @plugin.command()
    def validate():
        """Validate all discovered plugins."""
        manager = PluginManager()
        
        console.print("Validating plugins...")
        results = asyncio.run(manager.validate_all_plugins())
        
        if not results:
            console.print("[yellow]No plugins to validate[/yellow]")
            return
        
        # Display results
        table = Table(title="Plugin Validation Results")
        table.add_column("Plugin", style="cyan")
        table.add_column("Status", style="green")
        
        for plugin_name, valid in results.items():
            status = "[green]✓ Valid[/green]" if valid else "[red]✗ Invalid[/red]"
            table.add_row(plugin_name, status)
        
        console.print(table)
        
        # Summary
        valid_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        console.print(f"\n{valid_count}/{total_count} plugins validated successfully")
    
    @plugin.command()
    @click.argument("file_path", type=click.Path(exists=True))
    @click.option("--name", "-n", help="Name for the plugin file")
    def install(file_path: str, name: Optional[str]):
        """Install a plugin from a file."""
        manager = PluginManager()
        file_path = Path(file_path)
        
        if not file_path.suffix == ".py":
            console.print("[red]Plugin file must be a Python file (.py)[/red]")
            return
        
        console.print(f"Installing plugin from {file_path}...")
        
        if manager.install_plugin_from_file(file_path, name):
            console.print("[green]✓ Plugin installed successfully[/green]")
            console.print(f"  Location: {manager.plugin_dir / (name or file_path.name)}")
        else:
            console.print("[red]✗ Failed to install plugin[/red]")
    
    @plugin.command()
    def create_example():
        """Create example plugin files."""
        examples = {
            "example_model_plugin.py": '''"""Example custom model plugin."""

from src.plugins import ModelPlugin, PluginMetadata, PluginType
from src.models.base import ModelResponse
from src.core.types import Action

class MyCustomModel(ModelPlugin):
    """Custom model implementation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_custom_model",
            version="1.0.0",
            description="My custom LLM integration",
            author="Your Name",
            plugin_type=PluginType.MODEL,
            config_schema={
                "api_key": {"type": "string", "required": True},
                "endpoint": {"type": "string", "required": True},
            }
        )
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response from custom model."""
        # Your API call here
        response_text = f"Example response for: {prompt[:50]}..."
        
        return ModelResponse(
            content=response_text,
            raw_response={"text": response_text},
            model=self.metadata.name,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )
    
    def parse_action(self, response: str) -> Optional[Action]:
        """Parse action from response."""
        return self._parse_action_from_response(response)
    
    def format_prompt(self, board_state: str, prompt_style: str = "standard", **kwargs) -> str:
        """Format prompt for model."""
        return f"Board:\\n{board_state}\\n\\nYour move:"
''',
            
            "example_metric_plugin.py": '''"""Example custom metric plugin."""

from src.plugins import MetricPlugin, PluginMetadata, PluginType, MetricResult, GameResult

class CustomMetric(MetricPlugin):
    """Custom evaluation metric."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom_metric",
            version="1.0.0",
            description="My custom evaluation metric",
            author="Your Name",
            plugin_type=PluginType.METRIC,
        )
    
    def calculate(self, game_results: List[GameResult], **kwargs) -> List[MetricResult]:
        """Calculate custom metrics."""
        # Your metric calculation here
        total_games = len(game_results)
        
        return [
            MetricResult(
                name="custom_score",
                value=0.75,  # Your calculation
                description="Custom scoring metric",
            )
        ]
    
    def calculate_single_game(self, game_result: GameResult, **kwargs) -> List[MetricResult]:
        """Calculate metrics for single game."""
        return [
            MetricResult(
                name="game_custom_score",
                value=0.8,
                description="Per-game custom score",
            )
        ]
''',
        }
        
        console.print("Creating example plugin files...")
        
        manager = PluginManager()
        for filename, content in examples.items():
            file_path = manager.plugin_dir / filename
            
            if file_path.exists():
                console.print(f"[yellow]Skipping {filename} (already exists)[/yellow]")
                continue
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            console.print(f"[green]✓ Created {filename}[/green]")
        
        console.print(f"\nExample plugins created in: {manager.plugin_dir}")
        console.print("Edit these files to create your own plugins!")
    
    @plugin.command()
    @click.argument("plugin_name")
    @click.option("--model", "-m", required=True, help="Model to test with")
    @click.option("--num-games", "-n", default=5, help="Number of test games")
    def test_model(plugin_name: str, model: str, num_games: int):
        """Test a model plugin."""
        from src.core.types import ModelConfig, TaskType, Difficulty
        from src.evaluation import EvaluationEngine
        from src.tasks import TaskRepository
        
        manager = PluginManager()
        
        # Load plugin
        console.print(f"Loading plugin '{plugin_name}'...")
        try:
            plugin = asyncio.run(manager.load_plugin(plugin_name))
        except Exception as e:
            console.print(f"[red]Failed to load plugin: {e}[/red]")
            return
        
        if plugin.metadata.plugin_type != PluginType.MODEL:
            console.print(f"[red]Plugin '{plugin_name}' is not a model plugin[/red]")
            return
        
        # Create model config using plugin
        model_config = ModelConfig(
            name=plugin_name,
            provider="plugin",
            model_id=plugin_name,
        )
        
        # Load test tasks
        repo = TaskRepository()
        tasks = repo.load_tasks(
            task_type=TaskType.INTERACTIVE,
            difficulty=Difficulty.BEGINNER,
            limit=num_games,
        )
        
        if len(tasks) < num_games:
            console.print(f"[yellow]Only {len(tasks)} tasks available[/yellow]")
        
        # Run evaluation
        console.print(f"\n[bold]Testing {plugin_name} on {len(tasks)} tasks[/bold]")
        
        engine = EvaluationEngine()
        results = asyncio.run(
            engine.evaluate_model(
                model_config=model_config,
                tasks=tasks,
                verbose=True,
            )
        )
        
        # Display results
        metrics = results["metrics"]
        console.print("\n[bold]Test Results:[/bold]")
        console.print(f"Win Rate: {metrics.get('win_rate', 0):.1%}")
        console.print(f"Valid Moves: {metrics.get('valid_move_rate', 0):.1%}")
        console.print(f"Games Played: {results['evaluation']['num_tasks']}")
    
    return plugin