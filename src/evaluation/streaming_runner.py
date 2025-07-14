"""Game runner with live event streaming support."""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from src.core.types import ModelConfig, Task, GameTranscript, Action, ActionType, Position
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
        board_config = task.board_config
        game = MinesweeperGame(
            rows=board_config.get("rows", 16),
            cols=board_config.get("cols", 30),
            mines=board_config.get("mines", 99),
            seed=board_config.get("seed"),
            task_id=task.task_id,
            model_name=self.model_config.name,
        )
        
        # Make first move if specified
        if "first_move" in board_config:
            first_pos = board_config["first_move"]
            first_action = Action(
                ActionType.REVEAL,
                Position(first_pos["row"], first_pos["col"])
            )
            game.make_move(first_action)
        
        # Publish game started event
        logger.info(f"Publishing GAME_STARTED event for job {job_id}, game {game_num}")
        await publish_event(job_id, EventType.GAME_STARTED, {
            "game_num": game_num,
            "task_id": task.task_id,
            "difficulty": task.metadata.get("difficulty", "unknown"),
            "board_size": f"{game.board.rows}x{game.board.cols}",
            "num_mines": game.board.total_mines,
            "message": f"Starting game {game_num}"
        })
        
        move_count = 0
        consecutive_errors = 0
        
        while game.status.value == "in_progress" and move_count < max_moves:
            move_count += 1
            logger.info(f"Game {game_num} - Starting move {move_count}, status: {game.status.value}")
            
            # Get current board state
            board_state = game.get_board_representation("ascii")
            logger.debug(f"Game {game_num} - Board state length: {len(board_state)}")
            
            # Publish thinking event
            logger.info(f"Publishing MOVE_THINKING event for game {game_num}, move {move_count}")
            await publish_move_thinking(job_id, game_num, move_count, board_state)
            
            try:
                # Get model's move with function calling
                logger.info(f"Game {game_num} - Calling model.play_move with prompt_format={prompt_format}")
                response = await self.model.play_move(
                    board_state, 
                    prompt_format, 
                    use_functions=True
                )
                logger.info(f"Game {game_num} - Got response from model: has_action={response.action is not None}, has_reasoning={bool(response.reasoning)}")
                
                # Stream reasoning if available
                if response.reasoning:
                    logger.info(f"Publishing MOVE_REASONING event for game {game_num}, move {move_count}")
                    await publish_move_reasoning(
                        job_id, game_num, move_count, 
                        response.reasoning, partial=False
                    )
                else:
                    logger.warning(f"Game {game_num} - No reasoning in response")
                
                # Parse action
                if not response.action:
                    logger.error(f"Game {game_num} - No action found in response")
                    raise InvalidModelResponseError("No action found in response")
                
                action = response.action
                logger.info(f"Game {game_num} - Parsed action: {action.to_string()}")
                
                # Store AI details
                ai_details = {
                    'prompt_sent': self.model.format_prompt(
                        board_state, 
                        prompt_format if prompt_format != "auto" else self.model.get_optimal_prompt_format()
                    ),
                    'full_response': response.content,
                    'model_reasoning': response.reasoning,
                    'tokens_used': response.tokens_used,
                    'function_call': response.function_call
                }
                
                # Make the move
                logger.info(f"Game {game_num} - Executing move: {action.to_string()}")
                success, message, info = game.make_move(action, ai_details=ai_details)
                logger.info(f"Game {game_num} - Move result: success={success}, message={message}, new_status={info.get('game_status', 'unknown')}")
                
                # Publish move completed
                logger.info(f"Publishing MOVE_COMPLETED event for game {game_num}, move {move_count}")
                await publish_move_completed(
                    job_id, game_num, move_count,
                    action.to_string(), success,
                    game.get_board_representation("ascii") if success else None
                )
                
                if verbose:
                    print(f"Move {move_count}: {action.to_string()} - {message}")
                
                # Reset error counter on successful move
                consecutive_errors = 0
                logger.debug(f"Game {game_num} - Move {move_count} completed successfully")
                
            except InvalidModelResponseError as e:
                consecutive_errors += 1
                logger.error(f"Game {game_num} - Invalid model response: {str(e)}")
                
                # Publish failed move
                await publish_event(job_id, EventType.MOVE_FAILED, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": str(e),
                    "consecutive_errors": consecutive_errors,
                    "message": f"Failed to parse move: {str(e)}"
                })
                
                if consecutive_errors >= 3:
                    logger.error(f"Game {game_num} - Too many consecutive errors, ending game")
                    break
                    
            except ModelTimeoutError as e:
                logger.error(f"Game {game_num} - Model timeout: {str(e)}")
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": "Model timeout",
                    "message": str(e)
                })
                break
                
            except GameAlreadyFinishedError:
                logger.info(f"Game {game_num} - Game already finished")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in game {game_num}: {type(e).__name__}: {str(e)}", exc_info=True)
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": f"Unexpected error: {type(e).__name__}",
                    "message": str(e)
                })
                break
        
        # Ensure game has end time
        if not game.end_time:
            game.end_time = datetime.now(timezone.utc)
            logger.debug(f"Game {game_num} - Set end time")
        
        logger.info(f"Game {game_num} - Game loop ended, status: {game.status.value}, moves: {move_count}")
        
        # Get game statistics
        try:
            stats = game.get_statistics()
            duration = (game.end_time - game.start_time).total_seconds() if game.end_time else 0
            logger.info(f"Game {game_num} - Stats: status={stats['status']}, moves={stats['moves_made']}, coverage={stats['board_coverage']:.2%}")
        except Exception as e:
            logger.error(f"Game {game_num} - Error getting statistics: {type(e).__name__}: {str(e)}", exc_info=True)
            # Provide default stats if error
            stats = {
                'status': game.status.value,
                'moves_made': move_count,
                'board_coverage': 0.0
            }
            duration = 0
        
        # Publish game completed
        logger.info(f"Publishing GAME_COMPLETED event for game {game_num}")
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
        from src.evaluation.metrics import MetricsCalculator
        calculator = MetricsCalculator()
        metrics_obj = calculator.calculate_metrics(transcripts)
        
        # Convert to dict for backward compatibility
        metrics = {
            "win_rate": metrics_obj.win_rate,
            "valid_move_rate": metrics_obj.valid_move_rate,
            "mine_identification_precision": metrics_obj.mine_identification_precision,
            "mine_identification_recall": metrics_obj.mine_identification_recall,
            "average_moves_to_win": metrics_obj.average_moves_to_win,
            "average_moves_to_loss": metrics_obj.average_moves_to_loss,
            "board_coverage_on_loss": metrics_obj.board_coverage_on_loss,
            "reasoning_quality_score": metrics_obj.reasoning_quality_score,
        }
        
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