"""Game runner for model evaluation."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.core.types import (
    Action, ActionType, GameTranscript, ModelConfig, Task, Position, Move
)
from src.core.exceptions import (
    InvalidModelResponseError, GameAlreadyFinishedError,
    ModelTimeoutError
)
from src.games.minesweeper import MinesweeperGame
from src.models import create_model, BaseModel
from src.core.logging_config import get_logger

# Initialize logger
logger = get_logger("evaluation.runner")


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
            
            # Debug logging
            logger.debug(
                f"Game loop iteration {move_count}",
                extra={
                    "game_id": game.game_id,
                    "game_status": game.status.value,
                    "move_count": move_count,
                    "max_moves": max_moves,
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "move_num": move_count
                }
            )
            
            # Get current board state
            board_state = game.get_board_representation("ascii")
            
            # Log board state for debugging
            logger.debug(
                f"Move {move_count} - Current board state",
                extra={
                    "game_id": game.game_id,
                    "move_count": move_count,
                    "board_preview": board_state[:200] + "..." if len(board_state) > 200 else board_state,
                    "cells_revealed": game.cells_revealed,
                    "flags_placed": game.flags_placed,
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "move_num": move_count
                }
            )
            
            try:
                # Log the move attempt
                logger.info(
                    f"Move {move_count} - Sending prompt to model",
                    extra={
                        "game_id": game.game_id,
                        "move_count": move_count,
                        "model": self.model_config.name,
                        "prompt_format": prompt_format,
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "move_num": move_count
                    }
                )
                
                # Get model's move (play_move handles prompt formatting internally)
                # Use function calling by default
                response = await self.model.play_move(board_state, prompt_format, use_functions=True)
                
                # Log the model response
                logger.info(
                    f"Move {move_count} - Model response received",
                    extra={
                        "game_id": game.game_id,
                        "move_count": move_count,
                        "has_action": response.action is not None,
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "move_num": move_count,
                        "has_reasoning": response.reasoning is not None,
                        "tokens_used": response.tokens_used
                    }
                )
                
                if verbose:
                    print(f"\nMove {move_count}:")
                    if response.reasoning:
                        print(f"Reasoning: {response.reasoning[:100]}...")
                
                # Parse action
                if not response.action:
                    raise InvalidModelResponseError("No action found in response")
                
                action = response.action
                
                # Store AI interaction details for the move
                # Get the actual prompt that was sent (play_move formats it internally)
                actual_prompt = self.model.format_prompt(board_state, prompt_format if prompt_format != "auto" else self.model.get_optimal_prompt_format())
                
                ai_details = {
                    'prompt_sent': actual_prompt,
                    'full_response': response.content,
                    'model_reasoning': response.reasoning,
                    'tokens_used': response.tokens_used,
                    'function_call': response.function_call
                }
                
                # Log the AI details being stored
                logger.debug(
                    f"Move {move_count} - AI details to store",
                    extra={
                        "game_id": game.game_id,
                        "move_count": move_count,
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "move_num": move_count,
                        "has_prompt": bool(ai_details['prompt_sent']),
                        "prompt_length": len(ai_details['prompt_sent']) if ai_details['prompt_sent'] else 0,
                        "has_response": bool(ai_details['full_response']),
                        "response_length": len(ai_details['full_response']) if ai_details['full_response'] else 0,
                        "has_reasoning": bool(ai_details['model_reasoning']),
                        "reasoning_length": len(ai_details['model_reasoning']) if ai_details['model_reasoning'] else 0,
                        "has_function_call": bool(ai_details['function_call'])
                    }
                )
                
                # Make the move
                success, message, info = game.make_move(action, ai_details=ai_details)
                
                # Log the move result
                logger.info(
                    f"Move {move_count} - Action executed",
                    extra={
                        "game_id": game.game_id,
                        "move_count": move_count,
                        "action": action.to_string(),
                        "success": success,
                        "message": message,
                        "game_status": info.get("game_status"),
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "move_num": move_count
                    }
                )
                
                if verbose:
                    print(f"Action: {action.to_string()}")
                    print(f"Result: {message}")
                
                if success:
                    # Reset error counter on successful move
                    consecutive_errors = 0
                    
                    # Debug: Log end of successful move
                    logger.debug(
                        f"Move {move_count} completed successfully",
                        extra={
                            "game_id": game.game_id,
                            "game_status_after_move": game.status.value,
                            "will_continue": game.status.value == "in_progress" and move_count < max_moves,
                            "total_cells_revealed": game.cells_revealed,
                            "total_flags_placed": game.flags_placed,
                            "model_name": self.model_config.name,
                            "model_provider": self.model_config.provider,
                            "move_num": move_count
                        }
                    )
                else:
                    # Handle invalid moves
                    consecutive_errors += 1
                    logger.warning(
                        f"Move {move_count} - Invalid move attempted",
                        extra={
                            "game_id": game.game_id,
                            "move_count": move_count,
                            "action": action.to_string(),
                            "message": message,
                            "consecutive_errors": consecutive_errors,
                            "model_name": self.model_config.name,
                            "model_provider": self.model_config.provider,
                            "move_num": move_count
                        }
                    )
                    
                    if consecutive_errors >= 3:
                        logger.error(
                            f"Too many consecutive invalid moves, ending game",
                            extra={
                                "game_id": game.game_id,
                                "consecutive_errors": consecutive_errors,
                                "model_name": self.model_config.name,
                                "model_provider": self.model_config.provider
                            }
                        )
                        # Mark game as error
                        game.mark_as_error("Too many consecutive invalid moves")
                        break
                
            except InvalidModelResponseError as e:
                consecutive_errors += 1
                
                logger.warning(
                    f"Move {move_count} - Failed to parse model response",
                    extra={
                        "game_id": game.game_id,
                        "move_count": move_count,
                        "error": str(e),
                        "consecutive_errors": consecutive_errors,
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "move_num": move_count,
                        "error_type": "InvalidModelResponseError"
                    }
                )
                
                if verbose:
                    print(f"Error parsing model response: {e}")
                
                # Create a dummy action for the failed move
                dummy_action = Action(ActionType.REVEAL, Position(0, 0))
                
                # Try to get the prompt that would have been sent
                try:
                    actual_prompt = self.model.format_prompt(board_state, prompt_format if prompt_format != "auto" else self.model.get_optimal_prompt_format())
                except:
                    actual_prompt = None
                    
                ai_details = {
                    'prompt_sent': actual_prompt,
                    'full_response': response.content if 'response' in locals() else None,
                    'model_reasoning': response.reasoning if 'response' in locals() else None,
                    'tokens_used': response.tokens_used if 'response' in locals() else None
                }
                
                # Record the failed attempt
                try:
                    game.make_move(dummy_action, ai_details=ai_details)
                except:
                    pass  # Ignore errors when recording failed moves
                
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
        
        # Debug: Log why loop exited
        logger.debug(
            f"Game loop exited",
            extra={
                "game_id": game.game_id,
                "final_status": game.status.value,
                "total_moves": move_count,
                "max_moves": max_moves,
                "loop_condition": game.status.value == "in_progress" and move_count < max_moves,
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider
            }
        )
        
        # Ensure game has end time
        if not game.end_time:
            game.end_time = datetime.now(timezone.utc)
        
        transcript = game.get_transcript()
        
        # Log game completion
        stats = game.get_statistics()
        logger.info(
            f"Game completed",
            extra={
                "game_id": game.game_id,
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider,
                "status": stats['status'],
                "moves_made": stats['moves_made'],
                "board_coverage": stats['board_coverage'],
                "duration": (game.end_time - game.start_time).total_seconds() if game.end_time else None
            }
        )
        
        if verbose:
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