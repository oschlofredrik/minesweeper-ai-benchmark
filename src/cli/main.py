"""Main CLI entry point for the Minesweeper benchmark."""

import click
import asyncio
from pathlib import Path
from typing import Optional
import json

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.types import ModelConfig, Difficulty, TaskType, Action, ActionType, Position, GameStatus
from src.core.config import settings
from src.evaluation import EvaluationEngine
from src.tasks import TaskRepository, TaskGenerator
from src.games.minesweeper import MinesweeperGame
from src.models import list_providers

console = Console()


@click.group()
def cli():
    """Minesweeper AI Benchmark - Evaluate LLMs on logic-based reasoning."""
    pass


@cli.command()
@click.option(
    "--model", "-m",
    required=True,
    help="Model to evaluate (e.g., gpt-4, claude-3)"
)
@click.option(
    "--provider", "-p",
    type=click.Choice(["openai", "anthropic"]),
    help="Model provider (auto-detected if not specified)"
)
@click.option(
    "--num-games", "-n",
    default=10,
    help="Number of games to play"
)
@click.option(
    "--difficulty", "-d",
    type=click.Choice(["beginner", "intermediate", "expert"]),
    default="expert",
    help="Game difficulty"
)
@click.option(
    "--task-type", "-t",
    type=click.Choice(["interactive", "static"]),
    default="interactive",
    help="Type of tasks to run"
)
@click.option(
    "--prompt-format",
    type=click.Choice(["standard", "json", "cot"]),
    default="standard",
    help="Prompt format to use"
)
@click.option(
    "--parallel", "-j",
    default=1,
    help="Number of games to run in parallel"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed progress"
)
@click.option(
    "--temperature",
    default=0.7,
    help="Model temperature"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file for results (JSON)"
)
def evaluate(
    model: str,
    provider: Optional[str],
    num_games: int,
    difficulty: str,
    task_type: str,
    prompt_format: str,
    parallel: int,
    verbose: bool,
    temperature: float,
    output: Optional[str],
):
    """Evaluate a model on Minesweeper tasks."""
    # Auto-detect provider if not specified
    if not provider:
        if "gpt" in model.lower():
            provider = "openai"
        elif "claude" in model.lower():
            provider = "anthropic"
        else:
            console.print(
                "[red]Could not auto-detect provider. Please specify with --provider[/red]"
            )
            return
    
    # Create model config
    model_config = ModelConfig(
        name=f"{provider}/{model}",
        provider=provider,
        model_id=model,
        temperature=temperature,
    )
    
    # Load or generate tasks
    console.print(f"Loading {num_games} {difficulty} {task_type} tasks...")
    
    repo = TaskRepository()
    tasks = repo.load_tasks(
        task_type=TaskType(task_type),
        difficulty=Difficulty(difficulty.upper()),
        limit=num_games,
    )
    
    if len(tasks) < num_games:
        console.print(
            f"Only found {len(tasks)} tasks. Generating {num_games - len(tasks)} more..."
        )
        generator = TaskGenerator()
        new_tasks = generator.generate_task_batch(
            num_tasks=num_games - len(tasks),
            task_type=TaskType(task_type),
            difficulty=Difficulty(difficulty.upper()),
        )
        repo.save_tasks(new_tasks)
        tasks.extend(new_tasks)
    
    # Run evaluation
    console.print(f"\n[bold]Evaluating {model} on {len(tasks)} tasks[/bold]")
    
    engine = EvaluationEngine()
    
    # Run async evaluation
    results = asyncio.run(
        engine.evaluate_model(
            model_config=model_config,
            tasks=tasks,
            prompt_format=prompt_format,
            parallel_games=parallel,
            verbose=verbose,
        )
    )
    
    # Save results if requested
    if output:
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Results saved to {output}[/green]")


@cli.command()
@click.option(
    "--models", "-m",
    multiple=True,
    required=True,
    help="Models to compare (can specify multiple)"
)
@click.option(
    "--num-games", "-n",
    default=10,
    help="Number of games per model"
)
@click.option(
    "--difficulty", "-d",
    type=click.Choice(["beginner", "intermediate", "expert"]),
    default="expert",
    help="Game difficulty"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file for comparison results"
)
def compare(
    models: tuple,
    num_games: int,
    difficulty: str,
    output: Optional[str],
):
    """Compare multiple models on the same tasks."""
    # Parse model specifications
    model_configs = []
    for model_spec in models:
        if "/" in model_spec:
            provider, model = model_spec.split("/", 1)
        else:
            # Auto-detect
            if "gpt" in model_spec.lower():
                provider = "openai"
                model = model_spec
            elif "claude" in model_spec.lower():
                provider = "anthropic"
                model = model_spec
            else:
                console.print(f"[red]Cannot parse model: {model_spec}[/red]")
                return
        
        model_configs.append(
            ModelConfig(
                name=f"{provider}/{model}",
                provider=provider,
                model_id=model,
            )
        )
    
    # Load tasks
    repo = TaskRepository()
    tasks = repo.load_tasks(
        task_type=TaskType.INTERACTIVE,
        difficulty=Difficulty(difficulty.upper()),
        limit=num_games,
    )
    
    if len(tasks) < num_games:
        generator = TaskGenerator()
        new_tasks = generator.generate_task_batch(
            num_tasks=num_games - len(tasks),
            task_type=TaskType.INTERACTIVE,
            difficulty=Difficulty(difficulty.upper()),
        )
        repo.save_tasks(new_tasks)
        tasks.extend(new_tasks)
    
    # Run comparison
    console.print(f"\n[bold]Comparing {len(model_configs)} models on {len(tasks)} tasks[/bold]")
    
    engine = EvaluationEngine()
    results = asyncio.run(
        engine.compare_models(
            model_configs=model_configs,
            tasks=tasks,
        )
    )
    
    # Display comparison table
    table = Table(title="Model Comparison")
    table.add_column("Model", style="cyan")
    table.add_column("Win Rate", style="green")
    table.add_column("Valid Moves", style="yellow")
    table.add_column("Mine Precision", style="blue")
    table.add_column("Board Coverage", style="magenta")
    
    for model_name, model_results in results["model_results"].items():
        metrics = model_results["metrics"]
        table.add_row(
            model_name,
            f"{metrics['win_rate']:.1%}",
            f"{metrics['valid_move_rate']:.1%}",
            f"{metrics['mine_identification_precision']:.1%}",
            f"{metrics['board_coverage_on_loss']:.1%}",
        )
    
    console.print("\n")
    console.print(table)
    
    # Save if requested
    if output:
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Results saved to {output}[/green]")


@cli.command()
@click.option(
    "--rows", "-r",
    default=9,
    help="Number of rows"
)
@click.option(
    "--cols", "-c", 
    default=9,
    help="Number of columns"
)
@click.option(
    "--mines", "-m",
    default=10,
    help="Number of mines"
)
@click.option(
    "--seed", "-s",
    type=int,
    help="Random seed for reproducibility"
)
def play(rows: int, cols: int, mines: int, seed: Optional[int]):
    """Play an interactive game of Minesweeper."""
    game = MinesweeperGame(rows=rows, cols=cols, mines=mines, seed=seed)
    
    console.print("[bold]Welcome to Minesweeper![/bold]")
    console.print(f"Board: {rows}x{cols} with {mines} mines\n")
    
    while game.status.value == "in_progress":
        # Display board
        console.print(game.get_board_representation("ascii"))
        console.print(f"\nMoves: {len(game.moves)} | Flags: {game.flags_placed}")
        
        # Get user input
        action_str = console.input("\nEnter action (r/f/u row col, or 'quit'): ").strip().lower()
        
        if action_str == "quit":
            break
        
        try:
            parts = action_str.split()
            if len(parts) != 3:
                console.print("[red]Invalid format. Use: r 2 3 (reveal row 2, col 3)[/red]")
                continue
            
            action_type = parts[0]
            row = int(parts[1])
            col = int(parts[2])
            
            if action_type == "r":
                action = Action(ActionType.REVEAL, Position(row, col))
            elif action_type == "f":
                action = Action(ActionType.FLAG, Position(row, col))
            elif action_type == "u":
                action = Action(ActionType.UNFLAG, Position(row, col))
            else:
                console.print(f"[red]Unknown action: {action_type}[/red]")
                continue
            
            success, message, info = game.make_move(action)
            console.print(f"[yellow]{message}[/yellow]")
            
        except (ValueError, IndexError) as e:
            console.print(f"[red]Invalid input: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    # Game over
    console.print("\n" + "="*50)
    if game.status == GameStatus.WON:
        console.print("[green][bold]Congratulations! You won![/bold][/green]")
    else:
        console.print("[red][bold]Game Over! You hit a mine.[/bold][/red]")
        console.print("\nFinal board:")
        console.print(game.get_board_representation("ascii"))
    
    stats = game.get_statistics()
    console.print(f"\nFinal statistics:")
    console.print(f"  Moves: {stats['moves_made']}")
    console.print(f"  Board coverage: {stats['board_coverage']:.1%}")
    console.print(f"  Duration: {stats['duration_seconds']:.1f}s")


@cli.command()
@click.option(
    "--num-tasks", "-n",
    default=30,
    help="Number of tasks to generate"
)
@click.option(
    "--task-type", "-t",
    type=click.Choice(["interactive", "static", "both"]),
    default="both",
    help="Type of tasks to generate"
)
@click.option(
    "--clear", "-c",
    is_flag=True,
    help="Clear existing tasks first"
)
def generate_tasks(num_tasks: int, task_type: str, clear: bool):
    """Generate benchmark tasks."""
    repo = TaskRepository()
    
    if clear:
        count = repo.clear_tasks()
        console.print(f"[yellow]Cleared {count} existing tasks[/yellow]")
    
    generator = TaskGenerator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        if task_type in ["interactive", "both"]:
            task_id = progress.add_task("Generating interactive tasks...", total=num_tasks)
            
            for difficulty in [Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.EXPERT]:
                tasks = generator.generate_task_batch(
                    num_tasks=num_tasks // 3,
                    task_type=TaskType.INTERACTIVE,
                    difficulty=difficulty,
                )
                repo.save_tasks(tasks)
                progress.advance(task_id, num_tasks // 3)
        
        if task_type in ["static", "both"]:
            task_id = progress.add_task("Generating static tasks...", total=num_tasks)
            
            for difficulty in [Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.EXPERT]:
                tasks = generator.generate_task_batch(
                    num_tasks=num_tasks // 3,
                    task_type=TaskType.STATIC,
                    difficulty=difficulty,
                )
                repo.save_tasks(tasks)
                progress.advance(task_id, num_tasks // 3)
    
    total_count = repo.get_task_count()
    console.print(f"\n[green]Total tasks in repository: {total_count}[/green]")


@cli.command()
@click.argument("results_file", type=click.Path(exists=True))
def show_results(results_file: str):
    """Display results from a previous evaluation."""
    with open(results_file, "r") as f:
        results = json.load(f)
    
    # Display summary
    console.print(f"\n[bold]Results for {results['model']['name']}[/bold]")
    console.print(f"Evaluated on {results['evaluation']['num_tasks']} tasks")
    console.print(f"Duration: {results['evaluation']['duration_seconds']:.1f}s")
    
    # Display metrics table
    metrics = results["metrics"]
    
    table = Table(title="Evaluation Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Win Rate", f"{metrics['win_rate']:.1%}")
    table.add_row("Valid Move Rate", f"{metrics['valid_move_rate']:.1%}")
    table.add_row("Mine Precision", f"{metrics['mine_identification_precision']:.1%}")
    table.add_row("Mine Recall", f"{metrics['mine_identification_recall']:.1%}")
    table.add_row("Board Coverage (losses)", f"{metrics['board_coverage_on_loss']:.1%}")
    
    if metrics.get('average_moves_to_win') is not None:
        table.add_row("Avg Moves to Win", f"{metrics['average_moves_to_win']:.1f}")
    if metrics.get('average_moves_to_loss') is not None:
        table.add_row("Avg Moves to Loss", f"{metrics['average_moves_to_loss']:.1f}")
    
    console.print("\n")
    console.print(table)


@cli.command()
def list_models():
    """List available model providers."""
    providers = list_providers()
    
    console.print("\n[bold]Available Model Providers:[/bold]")
    for provider in providers:
        console.print(f"  - {provider}")
    
    console.print("\n[bold]Example model specifications:[/bold]")
    console.print("  - openai/gpt-4")
    console.print("  - openai/gpt-3.5-turbo")
    console.print("  - anthropic/claude-3-opus-20240229")
    console.print("  - anthropic/claude-3-sonnet-20240229")


if __name__ == "__main__":
    cli()