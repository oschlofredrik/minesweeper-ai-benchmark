"""Game runner for model evaluation."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from src.core.types import (
    Action, ActionType, GameTranscript, ModelConfig, Task, Position
)
from src.core.exceptions import (
    InvalidModelResponseError, GameAlreadyFinishedError,
    ModelTimeoutError
)
from src.games.minesweeper import MinesweeperGame
from src.models import create_model, BaseModel


class GameRunner:
    """Runs individual games with models."""
    
    def __init__(self, model_config: ModelConfig):
        """
        Initialize game runner with a model.
        
        Args:
            model_config: Model configuration
        """
        self.model = create_model(model_config)
        self.model_config = model_config
    
    async def run_game(
        self,
        task: Task,
        max_moves: int = 500,
        prompt_format: str = "standard",
        verbose: bool = False,
    ) -> GameTranscript:
        """
        Run a single game with the model.
        
        Args:
            task: Task defining the game parameters
            max_moves: Maximum moves allowed
            prompt_format: Format for model prompts
            verbose: Whether to print progress
        
        Returns:
            Game transcript
        """
        # Extract board configuration
        board_config = task.board_config
        game = MinesweeperGame(
            rows=board_config.get("rows", 16),
            cols=board_config.get("cols", 30),
            mines=board_config.get("mines", 99),
            seed=board_config.get("seed"),
            task_id=task.task_id,
            model_name=self.model_config.name,
        )
        
        if verbose:
            print(f"Starting game {game.game_id} with {self.model_config.name}")
            print(f"Board: {game.board.rows}x{game.board.cols}, {game.board.total_mines} mines")
        
        # Make first move if specified
        if "first_move" in board_config:
            first_pos = board_config["first_move"]
            first_action = Action(
                ActionType.REVEAL,
                Position(first_pos["row"], first_pos["col"])
            )
            game.make_move(first_action)
        
        # Game loop
        move_count = 0
        consecutive_errors = 0
        
        while game.status.value == "in_progress" and move_count < max_moves:
            move_count += 1
            
            # Get current board state
            board_state = game.get_board_representation("ascii")
            
            try:
                # Get model's move
                response = await self.model.play_move(board_state, prompt_format)
                
                if verbose:
                    print(f"\nMove {move_count}:")
                    if response.reasoning:
                        print(f"Reasoning: {response.reasoning[:100]}...")
                
                # Parse action
                if not response.action:
                    raise InvalidModelResponseError("No action found in response")
                
                action = response.action
                
                # Update move with reasoning
                if game.moves:
                    game.moves[-1].model_reasoning = response.reasoning
                
                # Make the move
                success, message, info = game.make_move(action)
                
                if verbose:
                    print(f"Action: {action.to_string()}")
                    print(f"Result: {message}")
                
                # Reset error counter on successful move
                consecutive_errors = 0
                
            except InvalidModelResponseError as e:
                consecutive_errors += 1
                if verbose:
                    print(f"Error parsing model response: {e}")
                
                # Add failed move to transcript
                if game.moves:
                    game.moves[-1].was_valid = False
                    game.moves[-1].error_message = str(e)
                
                if consecutive_errors >= 3:
                    if verbose:
                        print("Too many consecutive errors, ending game")
                    break
                
            except ModelTimeoutError as e:
                if verbose:
                    print(f"Model timeout: {e}")
                break
                
            except GameAlreadyFinishedError:
                break
                
            except Exception as e:
                if verbose:
                    print(f"Unexpected error: {e}")
                break
        
        # Ensure game has end time
        if not game.end_time:
            game.end_time = datetime.utcnow()
        
        transcript = game.get_transcript()
        
        if verbose:
            stats = game.get_statistics()
            print(f"\nGame finished: {stats['status']}")
            print(f"Moves: {stats['moves_made']}")
            print(f"Board coverage: {stats['board_coverage']:.1%}")
        
        return transcript
    
    async def run_multiple_games(
        self,
        tasks: list[Task],
        max_moves: int = 500,
        prompt_format: str = "standard",
        parallel: int = 1,
        verbose: bool = False,
    ) -> list[GameTranscript]:
        """
        Run multiple games.
        
        Args:
            tasks: List of tasks to run
            max_moves: Maximum moves per game
            prompt_format: Format for model prompts
            parallel: Number of games to run in parallel
            verbose: Whether to print progress
        
        Returns:
            List of game transcripts
        """
        if parallel <= 1:
            # Run sequentially
            transcripts = []
            for i, task in enumerate(tasks):
                if verbose:
                    print(f"\nGame {i + 1}/{len(tasks)}")
                transcript = await self.run_game(
                    task, max_moves, prompt_format, verbose
                )
                transcripts.append(transcript)
            return transcripts
        
        # Run in parallel batches
        transcripts = []
        for i in range(0, len(tasks), parallel):
            batch = tasks[i:i + parallel]
            if verbose:
                print(f"\nRunning batch {i // parallel + 1}/{(len(tasks) + parallel - 1) // parallel}")
            
            batch_tasks = [
                self.run_game(task, max_moves, prompt_format, False)
                for task in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            transcripts.extend(batch_results)
        
        return transcripts