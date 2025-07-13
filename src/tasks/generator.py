"""Task generation for creating benchmark tasks."""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.types import Task, TaskType, Difficulty, Position, Action, ActionType
from src.games.minesweeper import MinesweeperGame, MinesweeperSolver


class TaskGenerator:
    """Generate Minesweeper benchmark tasks."""
    
    # Board configurations by difficulty
    DIFFICULTY_CONFIGS = {
        Difficulty.BEGINNER: {"rows": 9, "cols": 9, "mines": 10},
        Difficulty.INTERMEDIATE: {"rows": 16, "cols": 16, "mines": 40},
        Difficulty.EXPERT: {"rows": 16, "cols": 30, "mines": 99},
    }
    
    def generate_interactive_task(
        self,
        difficulty: Difficulty = Difficulty.EXPERT,
        seed: Optional[int] = None,
        ensure_solvable: bool = False,
    ) -> Task:
        """
        Generate an interactive (full game) task.
        
        Args:
            difficulty: Difficulty level
            seed: Random seed for reproducibility
            ensure_solvable: Whether to ensure the board is solvable without guessing
        
        Returns:
            Generated task
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        
        config = self.DIFFICULTY_CONFIGS[difficulty].copy()
        config["seed"] = seed
        
        if ensure_solvable:
            # Generate boards until we find one that's solvable
            # (This is a simplified check - full solvability is complex)
            config = self._find_solvable_config(config)
        
        description = (
            f"Play a complete game of Minesweeper at {difficulty.value} difficulty. "
            f"Board size: {config['rows']}x{config['cols']} with {config['mines']} mines."
        )
        
        return Task.create(
            task_type=TaskType.INTERACTIVE,
            difficulty=difficulty,
            board_config=config,
            description=description,
            metadata={
                "seed": seed,
                "ensure_solvable": ensure_solvable,
            }
        )
    
    def generate_static_task(
        self,
        difficulty: Difficulty = Difficulty.INTERMEDIATE,
        reveal_percentage: float = 0.3,
        seed: Optional[int] = None,
    ) -> Task:
        """
        Generate a static (single-move) task from a partially revealed board.
        
        Args:
            difficulty: Difficulty level  
            reveal_percentage: Percentage of safe cells to reveal
            seed: Random seed
        
        Returns:
            Generated task
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        
        # Create a game and reveal some cells
        config = self.DIFFICULTY_CONFIGS[difficulty].copy()
        game = MinesweeperGame(
            rows=config["rows"],
            cols=config["cols"],
            mines=config["mines"],
            seed=seed,
        )
        
        # Reveal a portion of the board
        board_state = self._create_partial_board_state(game, reveal_percentage)
        
        # Find safe moves using solver
        solver = MinesweeperSolver(game.board)
        safe_moves = solver.find_safe_moves()
        
        description = (
            f"Given a partially revealed Minesweeper board, identify the next safe move. "
            f"Board has {len(safe_moves)} guaranteed safe moves available."
        )
        
        task_config = config.copy()
        task_config["seed"] = seed
        task_config["initial_state"] = board_state
        task_config["solution"] = {
            "safe_moves": [
                {"row": move.position.row, "col": move.position.col}
                for move in safe_moves
            ]
        }
        
        return Task.create(
            task_type=TaskType.STATIC,
            difficulty=difficulty,
            board_config=task_config,
            description=description,
            metadata={
                "reveal_percentage": reveal_percentage,
                "num_safe_moves": len(safe_moves),
            }
        )
    
    def generate_task_batch(
        self,
        num_tasks: int,
        task_type: TaskType = TaskType.INTERACTIVE,
        difficulty: Difficulty = Difficulty.EXPERT,
        **kwargs
    ) -> List[Task]:
        """
        Generate a batch of tasks.
        
        Args:
            num_tasks: Number of tasks to generate
            task_type: Type of tasks
            difficulty: Difficulty level
            **kwargs: Additional arguments for task generation
        
        Returns:
            List of generated tasks
        """
        tasks = []
        
        for i in range(num_tasks):
            if task_type == TaskType.INTERACTIVE:
                task = self.generate_interactive_task(difficulty, **kwargs)
            else:
                task = self.generate_static_task(difficulty, **kwargs)
            
            tasks.append(task)
        
        return tasks
    
    def _find_solvable_config(
        self, base_config: Dict[str, Any], max_attempts: int = 100
    ) -> Dict[str, Any]:
        """
        Find a board configuration that's solvable without guessing.
        
        This is a simplified version - perfect solvability checking is complex.
        """
        for attempt in range(max_attempts):
            seed = random.randint(0, 2**31 - 1)
            config = base_config.copy()
            config["seed"] = seed
            
            # Create game and check if it has safe moves available
            game = MinesweeperGame(
                rows=config["rows"],
                cols=config["cols"],
                mines=config["mines"],
                seed=seed,
            )
            
            # Start with a corner reveal (common strategy)
            corners = [
                Position(0, 0),
                Position(0, config["cols"] - 1),
                Position(config["rows"] - 1, 0),
                Position(config["rows"] - 1, config["cols"] - 1),
            ]
            
            for corner in corners:
                if not game.board.get_cell(corner).has_mine:
                    game.make_move(Action(ActionType.REVEAL, corner))
                    break
            
            # Check if solver can find moves
            solver = MinesweeperSolver(game.board)
            if solver.find_safe_moves():
                return config
        
        # Fallback to base config if no solvable board found
        return base_config
    
    def _create_partial_board_state(
        self, game: MinesweeperGame, reveal_percentage: float
    ) -> Dict[str, Any]:
        """Create a partially revealed board state."""
        total_cells = game.board.rows * game.board.cols
        non_mine_cells = total_cells - game.board.total_mines
        cells_to_reveal = int(non_mine_cells * reveal_percentage)
        
        # Find safe starting position
        safe_positions = []
        for row in range(game.board.rows):
            for col in range(game.board.cols):
                pos = Position(row, col)
                if not game.board.get_cell(pos).has_mine:
                    safe_positions.append(pos)
        
        # Reveal random safe cells
        positions_to_reveal = random.sample(safe_positions, 
                                          min(cells_to_reveal, len(safe_positions)))
        
        # Prefer revealing cells with low numbers for better gameplay
        positions_to_reveal.sort(
            key=lambda p: game.board.get_cell(p).adjacent_mines
        )
        
        for pos in positions_to_reveal[:cells_to_reveal]:
            game.make_move(Action(ActionType.REVEAL, pos))
        
        # Return board state
        return {
            "revealed_cells": [
                {
                    "row": pos.row,
                    "col": pos.col,
                    "value": game.board.get_cell(pos).adjacent_mines
                }
                for pos, _ in game.get_current_state().revealed_cells.items()
            ],
            "flagged_cells": [
                {"row": pos.row, "col": pos.col}
                for pos in game.get_current_state().flagged_cells
            ],
        }