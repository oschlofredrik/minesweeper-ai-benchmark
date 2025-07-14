"""Interactive prompt testing and development tools."""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.panel import Panel

from src.core.types import ModelConfig, Action, ActionType, Position
from src.games.tilts import TiltsGame, TiltsBoard
from src.models import create_model
from .prompt_manager import PromptManager, PromptTemplate


console = Console()


class PromptTester:
    """Interactive prompt testing and refinement."""
    
    def __init__(
        self,
        prompt_manager: PromptManager,
        test_results_dir: Optional[Path] = None,
    ):
        """
        Initialize prompt tester.
        
        Args:
            prompt_manager: Manager for prompt templates
            test_results_dir: Directory for storing test results
        """
        self.prompt_manager = prompt_manager
        self.test_results_dir = test_results_dir or Path("data/prompt_tests")
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_game: Optional[TiltsGame] = None
        self.current_template: Optional[PromptTemplate] = None
        self.test_history: List[Dict[str, Any]] = []
    
    def interactive_test(self, model_config: ModelConfig) -> None:
        """
        Run interactive prompt testing session.
        
        Args:
            model_config: Model configuration to use
        """
        console.print("\n[bold]Interactive Prompt Testing[/bold]")
        console.print("Test and refine prompts with real game scenarios\n")
        
        while True:
            # Main menu
            console.print("\n[cyan]Options:[/cyan]")
            console.print("1. Select prompt template")
            console.print("2. Create new game scenario")
            console.print("3. Test current prompt")
            console.print("4. Compare prompts")
            console.print("5. Edit prompt")
            console.print("6. View test history")
            console.print("7. Save test session")
            console.print("8. Exit")
            
            choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                self._select_template()
            elif choice == "2":
                self._create_game_scenario()
            elif choice == "3":
                asyncio.run(self._test_current_prompt(model_config))
            elif choice == "4":
                asyncio.run(self._compare_prompts(model_config))
            elif choice == "5":
                self._edit_prompt()
            elif choice == "6":
                self._view_test_history()
            elif choice == "7":
                self._save_test_session()
            elif choice == "8":
                if Confirm.ask("Exit prompt tester?"):
                    break
    
    def _select_template(self) -> None:
        """Select a prompt template."""
        templates = self.prompt_manager.list_templates()
        
        if not templates:
            console.print("[red]No templates available[/red]")
            return
        
        # Display templates
        table = Table(title="Available Templates")
        table.add_column("Index", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="yellow")
        table.add_column("Tags", style="blue")
        
        for i, template in enumerate(templates):
            table.add_row(
                str(i + 1),
                template.name,
                template.description,
                ", ".join(template.tags),
            )
        
        console.print(table)
        
        # Select template
        idx = Prompt.ask(
            "Select template",
            choices=[str(i + 1) for i in range(len(templates))],
        )
        
        self.current_template = templates[int(idx) - 1]
        console.print(f"\n[green]Selected: {self.current_template.name}[/green]")
    
    def _create_game_scenario(self) -> None:
        """Create a new game scenario."""
        # Game configuration
        rows = int(Prompt.ask("Rows", default="9"))
        cols = int(Prompt.ask("Columns", default="9"))
        mines = int(Prompt.ask("Mines", default="10"))
        
        seed_input = Prompt.ask("Random seed (optional)", default="")
        seed = int(seed_input) if seed_input else None
        
        # Create game
        self.current_game = TiltsGame(rows=rows, cols=cols, mines=mines, seed=seed)
        
        # Option to make some moves
        if Confirm.ask("Make some initial moves?"):
            self._make_manual_moves()
        
        console.print("\n[green]Game scenario created[/green]")
        self._display_current_game()
    
    def _make_manual_moves(self) -> None:
        """Make manual moves in the current game."""
        while True:
            self._display_current_game()
            
            move = Prompt.ask(
                "\nEnter move (r/f row col) or 'done'",
                default="done",
            )
            
            if move.lower() == "done":
                break
            
            try:
                parts = move.split()
                action_type = parts[0].lower()
                row = int(parts[1])
                col = int(parts[2])
                
                if action_type == "r":
                    action = Action(ActionType.REVEAL, Position(row, col))
                elif action_type == "f":
                    action = Action(ActionType.FLAG, Position(row, col))
                else:
                    console.print("[red]Invalid action type[/red]")
                    continue
                
                success, message, _ = self.current_game.make_move(action)
                console.print(f"[yellow]{message}[/yellow]")
                
                if self.current_game.status.value != "in_progress":
                    console.print("[red]Game ended![/red]")
                    break
                    
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    async def _test_current_prompt(self, model_config: ModelConfig) -> None:
        """Test current prompt on current game."""
        if not self.current_template:
            console.print("[red]No template selected[/red]")
            return
        
        if not self.current_game:
            console.print("[red]No game scenario created[/red]")
            return
        
        # Format prompt
        board_state = self.current_game.get_board_representation("ascii")
        prompt = self.current_template.format(board_state=board_state)
        
        # Display prompt
        console.print("\n[bold]Generated Prompt:[/bold]")
        console.print(Panel(prompt, title="Prompt", border_style="blue"))
        
        # Get model response
        console.print("\n[yellow]Getting model response...[/yellow]")
        
        model = create_model(model_config)
        
        start_time = datetime.utcnow()
        response = await model.generate(prompt)
        end_time = datetime.utcnow()
        
        # Display response
        console.print("\n[bold]Model Response:[/bold]")
        console.print(Panel(response.content, title="Response", border_style="green"))
        
        # Parse action
        action = model.parse_action(response.content)
        
        if action:
            console.print(f"\n[green]Parsed Action: {action.type.value} {action.position}[/green]")
            
            # Option to apply move
            if Confirm.ask("Apply this move to the game?"):
                success, message, _ = self.current_game.make_move(action)
                console.print(f"[yellow]{message}[/yellow]")
                self._display_current_game()
        else:
            console.print("\n[red]Could not parse action from response[/red]")
        
        # Record test
        self.test_history.append({
            "timestamp": start_time.isoformat(),
            "template": self.current_template.name,
            "prompt": prompt,
            "response": response.content,
            "parsed_action": str(action) if action else None,
            "response_time": (end_time - start_time).total_seconds(),
            "board_state": board_state,
        })
    
    async def _compare_prompts(self, model_config: ModelConfig) -> None:
        """Compare multiple prompts on the same scenario."""
        if not self.current_game:
            console.print("[red]No game scenario created[/red]")
            return
        
        # Select templates to compare
        templates = self.prompt_manager.list_templates()
        selected = []
        
        console.print("\n[cyan]Select templates to compare (enter indices separated by spaces):[/cyan]")
        for i, template in enumerate(templates):
            console.print(f"{i + 1}. {template.name}")
        
        indices = Prompt.ask("Template indices").split()
        
        for idx in indices:
            try:
                selected.append(templates[int(idx) - 1])
            except (ValueError, IndexError):
                console.print(f"[red]Invalid index: {idx}[/red]")
        
        if len(selected) < 2:
            console.print("[red]Need at least 2 templates to compare[/red]")
            return
        
        # Test each template
        board_state = self.current_game.get_board_representation("ascii")
        model = create_model(model_config)
        
        results = []
        
        for template in selected:
            console.print(f"\n[yellow]Testing {template.name}...[/yellow]")
            
            prompt = template.format(board_state=board_state)
            
            start_time = datetime.utcnow()
            response = await model.generate(prompt)
            end_time = datetime.utcnow()
            
            action = model.parse_action(response.content)
            
            results.append({
                "template": template.name,
                "response": response.content,
                "action": str(action) if action else "None",
                "time": (end_time - start_time).total_seconds(),
            })
        
        # Display comparison
        table = Table(title="Prompt Comparison Results")
        table.add_column("Template", style="cyan")
        table.add_column("Action", style="green")
        table.add_column("Response Time", style="yellow")
        
        for result in results:
            table.add_row(
                result["template"],
                result["action"],
                f"{result['time']:.2f}s",
            )
        
        console.print("\n")
        console.print(table)
        
        # Show full responses
        if Confirm.ask("\nShow full responses?"):
            for result in results:
                console.print(f"\n[bold]{result['template']}:[/bold]")
                console.print(Panel(result["response"], border_style="blue"))
    
    def _edit_prompt(self) -> None:
        """Edit current prompt template."""
        if not self.current_template:
            console.print("[red]No template selected[/red]")
            return
        
        console.print("\n[bold]Current Template:[/bold]")
        console.print(Syntax(
            self.current_template.template,
            "text",
            theme="monokai",
            line_numbers=True,
        ))
        
        if Confirm.ask("\nEdit template?"):
            # Simple text input (in practice, might open editor)
            console.print("\n[yellow]Enter new template (end with empty line):[/yellow]")
            
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            
            new_template = "\n".join(lines)
            
            if new_template and Confirm.ask("Save changes?"):
                # Create new version
                new_name = f"{self.current_template.name}_edited"
                
                new_prompt = PromptTemplate(
                    name=new_name,
                    template=new_template,
                    description=f"Edited version of {self.current_template.name}",
                    parameters=self.current_template.parameters.copy(),
                    tags=self.current_template.tags + ["edited"],
                )
                
                self.prompt_manager.save_template(new_prompt)
                self.current_template = new_prompt
                
                console.print(f"\n[green]Saved as: {new_name}[/green]")
    
    def _view_test_history(self) -> None:
        """View test history."""
        if not self.test_history:
            console.print("[yellow]No test history yet[/yellow]")
            return
        
        table = Table(title="Test History")
        table.add_column("Time", style="cyan")
        table.add_column("Template", style="green")
        table.add_column("Action", style="yellow")
        table.add_column("Response Time", style="blue")
        
        for test in self.test_history[-10:]:  # Show last 10
            table.add_row(
                test["timestamp"].split("T")[1][:8],
                test["template"],
                test["parsed_action"] or "None",
                f"{test['response_time']:.2f}s",
            )
        
        console.print(table)
        
        if Confirm.ask("\nView full test details?"):
            idx = Prompt.ask(
                "Test index",
                choices=[str(i + 1) for i in range(len(self.test_history))],
            )
            
            test = self.test_history[int(idx) - 1]
            
            console.print(f"\n[bold]Test Details:[/bold]")
            console.print(f"Template: {test['template']}")
            console.print(f"Time: {test['timestamp']}")
            console.print(f"\n[bold]Board State:[/bold]")
            console.print(test["board_state"])
            console.print(f"\n[bold]Response:[/bold]")
            console.print(Panel(test["response"], border_style="green"))
    
    def _save_test_session(self) -> None:
        """Save current test session."""
        if not self.test_history:
            console.print("[yellow]No tests to save[/yellow]")
            return
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"test_session_{timestamp}.json"
        filepath = self.test_results_dir / filename
        
        session_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": self.test_history,
            "current_template": self.current_template.name if self.current_template else None,
        }
        
        with open(filepath, "w") as f:
            json.dump(session_data, f, indent=2)
        
        console.print(f"\n[green]Session saved to: {filepath}[/green]")
    
    def _display_current_game(self) -> None:
        """Display current game state."""
        if not self.current_game:
            return
        
        console.print("\n[bold]Current Game State:[/bold]")
        console.print(self.current_game.get_board_representation("ascii"))
        console.print(f"Status: {self.current_game.status.value}")
        console.print(f"Moves: {len(self.current_game.moves)}")
        console.print(f"Flags: {self.current_game.flags_placed}")
    
    def test_single_scenario(
        self,
        template_name: str,
        game_state: str,
        model_config: ModelConfig,
    ) -> Dict[str, Any]:
        """
        Test a template on a specific game state.
        
        Args:
            template_name: Name of template to test
            game_state: ASCII representation of game board
            model_config: Model configuration
        
        Returns:
            Test results
        """
        template = self.prompt_manager.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Format prompt
        prompt = template.format(board_state=game_state)
        
        # Get response synchronously
        model = create_model(model_config)
        response = asyncio.run(model.generate(prompt))
        
        # Parse action
        action = model.parse_action(response.content)
        
        return {
            "template": template_name,
            "prompt": prompt,
            "response": response.content,
            "parsed_action": str(action) if action else None,
            "success": action is not None,
        }