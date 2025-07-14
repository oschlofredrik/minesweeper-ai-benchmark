"""Game runner with live event streaming support."""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from src.core.types import ModelConfig, Task, GameTranscript, Action
from src.core.exceptions import (
    InvalidModelResponseError, ModelTimeoutError, 
    GameAlreadyFinishedError
)
from src.core.logging_config import get_logger
from src.games.minesweeper import MinesweeperGame
from src.models import create_model
from src.api.event_streaming import (
    publish_game_started, publish_move_thinking, publish_move_reasoning,
    publish_move_completed, publish_game_completed, publish_metrics_update,
    publish_event, EventType
)

logger = get_logger("evaluation.streaming_runner")


class StreamingGameRunner:
    """Runs games with live event streaming."""
    
    def __init__(self, model_config: ModelConfig):
        """Initialize runner with a model configuration."""
        self.model_config = model_config
        self.model = create_model(model_config)
    
    async def run_single_game(
        self,
        task: Task,
        job_id: str,
        game_num: int,
        max_moves: int = 500,
        prompt_format: str = "auto",
        verbose: bool = False
    ) -> GameTranscript:
        """
        Run a single game with live streaming.
        
        Args:
            task: The task/game configuration
            job_id: Job ID for event streaming
            game_num: Game number in the session
            max_moves: Maximum moves allowed
            prompt_format: Prompt format to use
            verbose: Whether to print verbose output
            
        Returns:
            GameTranscript of the completed game
        """
        # Create game from task
        game = MinesweeperGame.from_task(task)
        
        # Publish game started event
        await publish_event(job_id, EventType.GAME_STARTED, {
            "game_num": game_num,
            "task_id": task.task_uid,
            "difficulty": task.metadata.get("difficulty", "unknown"),
            "board_size": f"{game.rows}x{game.cols}",
            "num_mines": game.num_mines,
            "message": f"Starting game {game_num}"
        })
        
        move_count = 0
        consecutive_errors = 0
        
        while game.status.value == "in_progress" and move_count < max_moves:
            move_count += 1
            
            # Get current board state
            board_state = game.get_board_state_for_ai()
            
            # Publish thinking event
            await publish_move_thinking(job_id, game_num, move_count, board_state)
            
            try:
                # Get model's move with function calling
                response = await self.model.play_move(
                    board_state, 
                    prompt_format, 
                    use_functions=True
                )
                
                # Stream reasoning if available
                if response.reasoning:
                    await publish_move_reasoning(
                        job_id, game_num, move_count, 
                        response.reasoning, partial=False
                    )
                
                # Parse action
                if not response.action:
                    raise InvalidModelResponseError("No action found in response")
                
                action = response.action
                
                # Store AI details
                ai_details = {
                    'prompt_sent': self.model.format_prompt(
                        board_state, 
                        prompt_format if prompt_format != "auto" else self.model.get_optimal_prompt_format(),
                        use_functions=True
                    ),
                    'full_response': response.content,
                    'model_reasoning': response.reasoning,
                    'tokens_used': response.tokens_used,
                    'function_call': response.function_call
                }
                
                # Make the move
                success, message, info = game.make_move(action, ai_details=ai_details)
                
                # Publish move completed
                await publish_move_completed(
                    job_id, game_num, move_count,
                    action.to_string(), success,
                    game.get_board_state_for_ai() if success else None
                )
                
                if verbose:
                    print(f"Move {move_count}: {action.to_string()} - {message}")
                
                # Reset error counter on successful move
                consecutive_errors = 0
                
            except InvalidModelResponseError as e:
                consecutive_errors += 1
                
                # Publish failed move
                await publish_event(job_id, EventType.MOVE_FAILED, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": str(e),
                    "consecutive_errors": consecutive_errors,
                    "message": f"Failed to parse move: {str(e)}"
                })
                
                if consecutive_errors >= 3:
                    break
                    
            except ModelTimeoutError as e:
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": "Model timeout",
                    "message": str(e)
                })
                break
                
            except GameAlreadyFinishedError:
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in game {game_num}", exc_info=True)
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": "Unexpected error",
                    "message": str(e)
                })
                break
        
        # Ensure game has end time
        if not game.end_time:
            game.end_time = datetime.now(timezone.utc)
        
        # Get game statistics
        stats = game.get_statistics()
        duration = (game.end_time - game.start_time).total_seconds() if game.end_time else 0
        
        # Publish game completed
        await publish_game_completed(
            job_id, game_num,
            stats['status'] == 'won',
            stats['moves_made'],
            stats['board_coverage'],
            duration
        )
        
        return game.get_transcript()
    
    async def run_multiple_games(
        self,
        tasks: List[Task],
        job_id: str,
        max_moves: int = 500,
        prompt_format: str = "auto",
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Run multiple games with live streaming.
        
        Args:
            tasks: List of tasks to run
            job_id: Job ID for event streaming
            max_moves: Maximum moves per game
            prompt_format: Prompt format to use
            verbose: Whether to print verbose output
            
        Returns:
            Dictionary with results and metrics
        """
        transcripts = []
        total_games = len(tasks)
        games_won = 0
        total_moves = 0
        
        # Publish session started
        await publish_event(job_id, EventType.STATUS_UPDATE, {
            "status": "started",
            "total_games": total_games,
            "message": f"Starting {total_games} games with {self.model_config.name}"
        })
        
        for i, task in enumerate(tasks):
            game_num = i + 1
            
            try:
                # Run single game
                transcript = await self.run_single_game(
                    task, job_id, game_num,
                    max_moves, prompt_format, verbose
                )
                
                transcripts.append(transcript)
                
                # Update metrics
                if transcript.final_state.status.value == "won":
                    games_won += 1
                total_moves += len(transcript.moves)
                
                # Publish metrics update
                win_rate = games_won / game_num
                avg_moves = total_moves / game_num
                
                await publish_metrics_update(
                    job_id, game_num, total_games,
                    win_rate, avg_moves
                )
                
            except Exception as e:
                logger.error(f"Failed to complete game {game_num}", exc_info=True)
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "error": "Game failed",
                    "message": str(e)
                })
        
        # Calculate final metrics
        from src.evaluation.metrics import calculate_metrics
        metrics = calculate_metrics(transcripts)
        
        # Publish session completed
        await publish_event(job_id, EventType.STATUS_UPDATE, {
            "status": "completed",
            "total_games": total_games,
            "games_won": games_won,
            "win_rate": metrics.get("win_rate", 0),
            "message": f"Completed {total_games} games"
        })
        
        return {
            "transcripts": transcripts,
            "metrics": metrics,
            "num_games": total_games
        }