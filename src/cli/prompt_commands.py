"""CLI commands for prompt engineering."""

import click
import asyncio
from pathlib import Path
from typing import Optional
import json

from rich.console import Console
from rich.table import Table

from src.core.types import ModelConfig
from src.prompt_engineering import PromptManager, PromptTemplate

console = Console()


def add_prompt_commands(cli_group):
    """Add prompt engineering commands to CLI."""
    
    @cli_group.group()
    def prompt():
        """Prompt engineering and optimization commands."""
        pass
    
    @prompt.command()
    def list():
        """List available prompt templates."""
        manager = PromptManager()
        templates = manager.list_templates()
        
        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return
        
        table = Table(title="Prompt Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Tags", style="yellow")
        table.add_column("Version", style="blue")
        
        for template in templates:
            table.add_row(
                template.name,
                template.description,
                ", ".join(template.tags),
                template.version,
            )
        
        console.print(table)
    
    @prompt.command()
    @click.argument("template_name")
    def show(template_name: str):
        """Show details of a specific template."""
        manager = PromptManager()
        template = manager.get_template(template_name)
        
        if not template:
            console.print(f"[red]Template '{template_name}' not found[/red]")
            return
        
        console.print(f"\n[bold]Template: {template.name}[/bold]")
        console.print(f"Description: {template.description}")
        console.print(f"Version: {template.version}")
        console.print(f"Tags: {', '.join(template.tags)}")
        
        if template.parameters:
            console.print(f"\n[cyan]Parameters:[/cyan]")
            for key, value in template.parameters.items():
                console.print(f"  {key}: {value}")
        
        console.print(f"\n[cyan]Template:[/cyan]")
        console.print(template.template)
        
        if template.few_shot_examples:
            console.print(f"\n[cyan]Few-shot examples: {len(template.few_shot_examples)}[/cyan]")
        
        if template.performance_metrics:
            console.print(f"\n[cyan]Performance metrics:[/cyan]")
            for metric, value in template.performance_metrics.items():
                console.print(f"  {metric}: {value:.3f}")
    
    @prompt.command()
    @click.option("--name", "-n", required=True, help="Template name")
    @click.option("--template-file", "-f", type=click.Path(exists=True), help="File containing template text")
    @click.option("--description", "-d", default="Custom prompt template", help="Template description")
    @click.option("--tags", "-t", multiple=True, help="Template tags")
    def create(name: str, template_file: Optional[str], description: str, tags: tuple):
        """Create a new prompt template."""
        manager = PromptManager()
        
        # Check if template already exists
        if manager.get_template(name):
            console.print(f"[red]Template '{name}' already exists[/red]")
            return
        
        # Get template text
        if template_file:
            with open(template_file, "r") as f:
                template_text = f.read()
        else:
            console.print("[cyan]Enter template text (end with Ctrl+D):[/cyan]")
            lines = []
            try:
                while True:
                    lines.append(input())
            except EOFError:
                pass
            template_text = "\n".join(lines)
        
        # Create template
        template = PromptTemplate(
            name=name,
            template=template_text,
            description=description,
            tags=list(tags) if tags else [],
        )
        
        manager.save_template(template)
        console.print(f"\n[green]Template '{name}' created successfully[/green]")
    
    @prompt.command()
    @click.argument("base_template")
    @click.argument("new_name")
    @click.option("--template-file", "-f", type=click.Path(exists=True), help="File with new template text")
    @click.option("--description", "-d", help="New description")
    @click.option("--tags", "-t", multiple=True, help="Additional tags")
    def variation(base_template: str, new_name: str, template_file: Optional[str], description: Optional[str], tags: tuple):
        """Create a variation of an existing template."""
        manager = PromptManager()
        
        # Check base template exists
        base = manager.get_template(base_template)
        if not base:
            console.print(f"[red]Base template '{base_template}' not found[/red]")
            return
        
        # Prepare modifications
        modifications = {}
        
        if template_file:
            with open(template_file, "r") as f:
                modifications["template"] = f.read()
        
        if description:
            modifications["description"] = description
        else:
            modifications["description"] = f"Variation of {base_template}"
        
        if tags:
            modifications["tags"] = list(base.tags) + list(tags)
        
        # Create variation
        new_template = manager.create_variation(
            base_template=base_template,
            name=new_name,
            modifications=modifications,
        )
        
        console.print(f"\n[green]Variation '{new_name}' created successfully[/green]")
    
    @prompt.command()
    @click.option("--model", "-m", required=True, help="Model to use for testing")
    @click.option("--provider", "-p", type=click.Choice(["openai", "anthropic"]), help="Model provider")
    def test(model: str, provider: Optional[str]):
        """Interactive prompt testing session."""
        # Import here to avoid circular imports
        from src.prompt_engineering.prompt_tester import PromptTester
        
        # Auto-detect provider if not specified
        if not provider:
            if "gpt" in model.lower():
                provider = "openai"
            elif "claude" in model.lower():
                provider = "anthropic"
            else:
                console.print("[red]Could not auto-detect provider. Please specify with --provider[/red]")
                return
        
        # Create model config
        model_config = ModelConfig(
            name=f"{provider}/{model}",
            provider=provider,
            model_id=model,
        )
        
        # Run interactive tester
        manager = PromptManager()
        tester = PromptTester(manager)
        tester.interactive_test(model_config)
    
    @prompt.command()
    @click.option("--base-template", "-b", required=True, help="Base template to optimize")
    @click.option("--model", "-m", required=True, help="Model to use")
    @click.option("--provider", "-p", type=click.Choice(["openai", "anthropic"]), help="Model provider")
    @click.option("--num-games", "-n", default=20, help="Games per variation")
    @click.option("--output", "-o", type=click.Path(), help="Output file for results")
    def optimize(base_template: str, model: str, provider: Optional[str], num_games: int, output: Optional[str]):
        """Optimize a prompt template."""
        # Import here to avoid circular imports
        from src.prompt_engineering.prompt_optimizer import PromptOptimizer
        from src.core.types import TaskType, Difficulty
        
        # Auto-detect provider
        if not provider:
            if "gpt" in model.lower():
                provider = "openai"
            elif "claude" in model.lower():
                provider = "anthropic"
            else:
                console.print("[red]Could not auto-detect provider[/red]")
                return
        
        model_config = ModelConfig(
            name=f"{provider}/{model}",
            provider=provider,
            model_id=model,
        )
        
        # Define variations to test
        variations = [
            {
                "template": "You are an expert Minesweeper player. {board_state}\n\nAnalyze carefully and provide your move as: Action: [reveal/flag] (row, col)",
                "description": "Expert player emphasis",
            },
            {
                "parameters": {"pattern_hints": "Pay special attention to 1-2-1 patterns and corner constraints."},
                "description": "Pattern hints",
            },
            {
                "template": "{board_state}\n\nReason step by step:\n1. Identify all revealed numbers\n2. Count adjacent mines vs flags\n3. Find guaranteed safe/mine cells\n4. Make your move\n\nAction: [reveal/flag] (row, col)",
                "description": "Structured reasoning",
            },
        ]
        
        # Run optimization
        console.print(f"\n[bold]Optimizing template: {base_template}[/bold]")
        
        manager = PromptManager()
        optimizer = PromptOptimizer(manager)
        
        results = asyncio.run(
            optimizer.optimize_prompt(
                base_template=base_template,
                model_config=model_config,
                variations=variations,
                num_games=num_games,
            )
        )
        
        # Display results
        console.print(f"\n[green]Optimization complete![/green]")
        console.print(f"Best template: {results['best_template']}")
        console.print(f"Best win rate: {results['best_metrics']['win_rate']:.1%}")
        
        # Save results
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"\nResults saved to: {output}")
    
    @prompt.command()
    @click.argument("template_a")
    @click.argument("template_b")
    @click.option("--model", "-m", required=True, help="Model to use")
    @click.option("--provider", "-p", type=click.Choice(["openai", "anthropic"]), help="Model provider")
    @click.option("--num-games", "-n", default=50, help="Games per template")
    def compare(template_a: str, template_b: str, model: str, provider: Optional[str], num_games: int):
        """A/B test two prompt templates."""
        # Import here to avoid circular imports
        from src.prompt_engineering.prompt_optimizer import PromptOptimizer
        
        # Auto-detect provider
        if not provider:
            if "gpt" in model.lower():
                provider = "openai"
            elif "claude" in model.lower():
                provider = "anthropic"
            else:
                console.print("[red]Could not auto-detect provider[/red]")
                return
        
        model_config = ModelConfig(
            name=f"{provider}/{model}",
            provider=provider,
            model_id=model,
        )
        
        # Run A/B test
        console.print(f"\n[bold]A/B Testing: {template_a} vs {template_b}[/bold]")
        
        manager = PromptManager()
        optimizer = PromptOptimizer(manager)
        
        result = asyncio.run(
            optimizer.ab_test(
                template_a=template_a,
                template_b=template_b,
                model_config=model_config,
                num_games=num_games,
            )
        )
        
        # Display results
        table = Table(title="A/B Test Results")
        table.add_column("Template", style="cyan")
        table.add_column("Win Rate", style="green")
        table.add_column("Valid Moves", style="yellow")
        
        table.add_row(
            template_a,
            f"{result.metrics_a['win_rate']:.1%}",
            f"{result.metrics_a.get('valid_move_rate', 0):.1%}",
        )
        
        table.add_row(
            template_b,
            f"{result.metrics_b['win_rate']:.1%}",
            f"{result.metrics_b.get('valid_move_rate', 0):.1%}",
        )
        
        console.print("\n")
        console.print(table)
        
        if result.winner:
            console.print(f"\n[green]Winner: {result.winner}[/green]")
            console.print(f"Statistical significance: p = {result.p_values.get('win_rate', 1.0):.4f}")
        else:
            console.print("\n[yellow]No statistically significant difference[/yellow]")
    
    return prompt