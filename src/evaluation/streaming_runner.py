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
from src.games.tilts import TiltsGame
from src.games.registry import GameRegistry
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
        verbose: bool = False,
        game_name: str = "minesweeper"
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
        
        # Get game class from registry or default to Minesweeper
        if game_name == "minesweeper":
            game = TiltsGame(
                rows=board_config.get("rows", 16),
                cols=board_config.get("cols", 30),
                mines=board_config.get("mines", 99),
                seed=board_config.get("seed"),
                task_id=task.task_id,
                model_name=self.model_config.name,
            )
        else:
            # Use game registry for other games
            game_class = GameRegistry.get_game(game_name)
            if not game_class:
                raise ValueError(f"Unknown game: {game_name}")
            
            # Create game instance with appropriate config
            game_instance = game_class.create_instance(
                players=["AI", "Computer"],
                seed=board_config.get("seed"),
                scenario=board_config.get("scenario")
            )
            
            # Wrap in a compatibility layer to match TiltsGame interface
            from src.games.game_adapter import GameAdapter
            game = GameAdapter(game_instance, task_id=task.task_id, model_name=self.model_config.name)
        
        # Make first move if specified
        if "first_move" in board_config:
            first_pos = board_config["first_move"]
            first_action = Action(
                ActionType.REVEAL,
                Position(first_pos["row"], first_pos["col"])
            )
            game.make_move(first_action)
        
        # Publish game started event
        logger.info(f"Publishing GAME_STARTED event for job {job_id}, game {game_num}", extra={
            "model_name": self.model_config.name,
            "model_provider": self.model_config.provider
        })
        await publish_event(job_id, EventType.GAME_STARTED, {
            "game_num": game_num,
            "task_id": task.task_id,
            "difficulty": task.metadata.get("difficulty", "unknown"),
            "board_size": f"{game.board.rows}x{game.board.cols}",
            "num_mines": game.board.total_mines,
            "message": f"Starting game {game_num}"
        })
        
        # Send initial board state
        board_data = game.board.to_coordinate_list()
        await publish_event(job_id, EventType.BOARD_UPDATE, {
            "game_num": game_num,
            "board_data": board_data,
            "message": "Initial board state"
        })
        
        move_count = 0
        consecutive_errors = 0
        
        while game.status.value == "in_progress" and move_count < max_moves:
            move_count += 1
            logger.info(f"Game {game_num} - Starting move {move_count}, status: {game.status.value}", extra={
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider,
                "game_num": game_num,
                "move_num": move_count
            })
            
            # Get current board state
            board_state = game.get_board_representation("ascii")
            logger.debug(f"Game {game_num} - Board state length: {len(board_state)}", extra={
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider,
                "game_num": game_num,
                "move_num": move_count
            })
            
            # Publish thinking event
            logger.info(f"Publishing MOVE_THINKING event for game {game_num}, move {move_count}", extra={
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider,
                "game_num": game_num,
                "move_num": move_count
            })
            await publish_move_thinking(job_id, game_num, move_count, board_state)
            
            try:
                # Create a callback for streaming reasoning
                async def stream_reasoning(chunk: str):
                    # Publish partial reasoning as it comes
                    await publish_move_reasoning(
                        job_id, game_num, move_count, 
                        chunk, partial=True
                    )
                
                # Get model's move with function calling
                logger.info(f"Game {game_num} - Calling model.play_move with prompt_format={prompt_format}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                
                # Set up kwargs based on model capabilities
                kwargs = {}
                
                # Check if model supports function calling
                if hasattr(self.model, 'supports_function_calling'):
                    kwargs["use_functions"] = self.model.supports_function_calling
                else:
                    # Default to True for backward compatibility
                    kwargs["use_functions"] = True
                
                # Add stream callback if model supports streaming
                if hasattr(self.model, 'supports_streaming') and self.model.supports_streaming:
                    kwargs["stream_callback"] = stream_reasoning
                
                # Pass game context for proper function schema
                if game_name != "minesweeper":
                    kwargs["game_context"] = {
                        "game_name": game_name,
                        "game_instance": game
                    }
                
                response = await self.model.play_move(
                    board_state, 
                    prompt_format, 
                    **kwargs
                )
                logger.info(f"Game {game_num} - Got response from model: has_action={response.action is not None}, has_reasoning={bool(response.reasoning)}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                
                # Stream reasoning if available
                if response.reasoning:
                    logger.info(f"Publishing MOVE_REASONING event for game {game_num}, move {move_count}", extra={
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "game_num": game_num,
                        "move_num": move_count
                    })
                    await publish_move_reasoning(
                        job_id, game_num, move_count, 
                        response.reasoning, partial=False
                    )
                else:
                    logger.warning(f"Game {game_num} - No reasoning in response", extra={
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "game_num": game_num,
                        "move_num": move_count
                    })
                
                # Parse action
                if not response.action:
                    # For non-Minesweeper games with function calling, try to create action from function call
                    if game_name != "minesweeper" and response.function_call:
                        try:
                            # Create a special action that carries the function call data
                            from src.core.types import Action, ActionType, Position
                            action = Action(ActionType.REVEAL, Position(0, 0))  # Dummy action
                            action.function_data = response.function_call  # Attach function data
                        except Exception as e:
                            logger.error(f"Failed to create action from function call: {e}")
                            raise InvalidModelResponseError("No action found in response")
                    else:
                        logger.error(f"Game {game_num} - No action found in response. Content preview: {response.content[:200] if response.content else 'No content'}", extra={
                            "model_name": self.model_config.name,
                            "model_provider": self.model_config.provider,
                            "game_num": game_num,
                            "move_num": move_count
                        })
                        # Try to help by showing what patterns we're looking for
                        logger.info("Expected action format examples: 'reveal (2, 3)', 'flag 1,2', 'Action: reveal Position: (2,3)'")
                        raise InvalidModelResponseError("No action found in response")
                else:
                    action = response.action
                logger.info(f"Game {game_num} - Parsed action: {action.to_string()}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                
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
                logger.info(f"Game {game_num} - Executing move: {action.to_string()}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                success, message, info = game.make_move(action, ai_details=ai_details)
                logger.info(f"Game {game_num} - Move result: success={success}, message={message}, new_status={info.get('game_status', 'unknown')}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                
                # Publish move completed
                logger.info(f"Publishing MOVE_COMPLETED event for game {game_num}, move {move_count}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                # Include AI response details in the event
                move_details = {
                    "intended_action": action.to_string(),
                    "position": {"row": action.position.row, "col": action.position.col},
                    "function_call": response.function_call,
                    "raw_response_excerpt": response.content[:200] + "..." if len(response.content) > 200 else response.content
                }
                
                await publish_move_completed(
                    job_id, game_num, move_count,
                    action.to_string(), success,
                    game.get_board_representation("ascii") if success else None,
                    move_details=move_details
                )
                
                # Send board update with coordinate data
                if success:
                    board_data = game.board.to_coordinate_list()
                    await publish_event(job_id, EventType.BOARD_UPDATE, {
                        "game_num": game_num,
                        "move_num": move_count,
                        "board_data": board_data,
                        "last_move": {
                            "action": action.action_type.value,
                            "row": action.position.row,
                            "col": action.position.col
                        },
                        "message": f"Board after move {move_count}"
                    })
                
                if verbose:
                    print(f"Move {move_count}: {action.to_string()} - {message}")
                
                if success:
                    # Reset error counter on successful move
                    consecutive_errors = 0
                    logger.debug(f"Game {game_num} - Move {move_count} completed successfully", extra={
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "game_num": game_num,
                        "move_num": move_count
                    })
                else:
                    # Handle invalid moves
                    consecutive_errors += 1
                    logger.warning(f"Game {game_num} - Invalid move: {message}", extra={
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "game_num": game_num,
                        "move_num": move_count,
                        "action": action.to_string(),
                        "consecutive_errors": consecutive_errors
                    })
                    
                    if consecutive_errors >= 3:
                        logger.error(f"Game {game_num} - Too many consecutive invalid moves, ending game", extra={
                            "model_name": self.model_config.name,
                            "model_provider": self.model_config.provider,
                            "game_num": game_num,
                            "move_num": move_count
                        })
                        # Mark game as error due to repeated invalid moves
                        game.mark_as_error("Too many consecutive invalid moves")
                        break
                
            except InvalidModelResponseError as e:
                consecutive_errors += 1
                logger.error(f"Game {game_num} - Invalid model response: {str(e)}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count,
                    "error_type": "InvalidModelResponseError"
                })
                
                # Publish failed move
                await publish_event(job_id, EventType.MOVE_FAILED, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": str(e),
                    "consecutive_errors": consecutive_errors,
                    "message": f"Failed to parse move: {str(e)}"
                })
                
                if consecutive_errors >= 3:
                    logger.error(f"Game {game_num} - Too many consecutive errors, ending game", extra={
                        "model_name": self.model_config.name,
                        "model_provider": self.model_config.provider,
                        "game_num": game_num,
                        "move_num": move_count
                    })
                    break
                    
            except ModelTimeoutError as e:
                logger.error(f"Game {game_num} - Model timeout: {str(e)}", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count,
                    "error_type": "ModelTimeoutError"
                })
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "move_num": move_count,
                    "error": "Model timeout",
                    "message": str(e)
                })
                break
                
            except GameAlreadyFinishedError:
                logger.info(f"Game {game_num} - Game already finished", extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count
                })
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in game {game_num}: {type(e).__name__}: {str(e)}", exc_info=True, extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num,
                    "move_num": move_count,
                    "error_type": type(e).__name__
                })
                # Mark game as technical failure
                game.mark_as_error(f"{type(e).__name__}: {str(e)}")
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
        
        logger.info(f"Game {game_num} - Game loop ended, status: {game.status.value}, moves: {move_count}", extra={
            "model_name": self.model_config.name,
            "model_provider": self.model_config.provider,
            "game_num": game_num,
            "move_num": move_count
        })
        
        # Get game statistics
        try:
            stats = game.get_statistics()
            duration = (game.end_time - game.start_time).total_seconds() if game.end_time else 0
            logger.info(f"Game {game_num} - Stats: status={stats['status']}, moves={stats['moves_made']}, coverage={stats['board_coverage']:.2%}", extra={
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider,
                "game_num": game_num
            })
        except Exception as e:
            logger.error(f"Game {game_num} - Error getting statistics: {type(e).__name__}: {str(e)}", exc_info=True, extra={
                "model_name": self.model_config.name,
                "model_provider": self.model_config.provider,
                "game_num": game_num,
                "error_type": type(e).__name__
            })
            # Provide default stats if error
            stats = {
                'status': game.status.value,
                'moves_made': move_count,
                'board_coverage': 0.0
            }
            duration = 0
        
        # Publish game completed
        logger.info(f"Publishing GAME_COMPLETED event for game {game_num}", extra={
            "model_name": self.model_config.name,
            "model_provider": self.model_config.provider,
            "game_num": game_num
        })
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
        verbose: bool = False,
        game_name: str = "minesweeper"
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
                    max_moves, prompt_format, verbose, game_name
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
                
                # Add delay between games (except after last game)
                if game_num < total_games:
                    await asyncio.sleep(3.0)  # 3 second delay
                
            except Exception as e:
                logger.error(f"Failed to complete game {game_num}", exc_info=True, extra={
                    "model_name": self.model_config.name,
                    "model_provider": self.model_config.provider,
                    "game_num": game_num
                })
                await publish_event(job_id, EventType.ERROR, {
                    "game_num": game_num,
                    "error": "Game failed",
                    "message": str(e)
                })
        
        # Calculate final metrics
        from src.evaluation.metrics import MetricsCalculator
        from src.evaluation.advanced_metrics import AdvancedMetricsCalculator
        from src.evaluation.reasoning_judge import ReasoningJudge
        from src.core.types import TaskType
        
        # Basic metrics
        calculator = MetricsCalculator()
        metrics_obj = calculator.calculate_metrics(transcripts)
        
        # Judge reasoning quality (optional - for now use simple heuristic)
        reasoning_judgments = None
        
        # Check if reasoning judge is enabled
        try:
            from src.api.reasoning_config import USE_REASONING_JUDGE
            use_reasoning_judge = USE_REASONING_JUDGE
        except ImportError:
            use_reasoning_judge = True  # Default to proper AI evaluation
        
        if use_reasoning_judge and transcripts:
            logger.info("🧠 Evaluating reasoning quality with LLM judge...")
            judge = ReasoningJudge()
            reasoning_judgments = {}
            
            for transcript in transcripts:
                try:
                    judgments = await judge.judge_transcript(transcript)
                    reasoning_judgments[transcript.game_id] = judgments
                except Exception as e:
                    logger.error(f"Failed to judge reasoning for game {transcript.game_id}: {e}")
        
        # Advanced metrics (MineBench scores)
        adv_calculator = AdvancedMetricsCalculator()
        # For now, treat all as interactive tasks
        adv_metrics = adv_calculator.calculate_interactive_metrics(transcripts, reasoning_judgments)
        
        # If reasoning judge is disabled, calculate simple reasoning score
        if not use_reasoning_judge:
            # More realistic heuristic: score based on reasoning quality indicators
            total_moves = 0
            quality_scores = []
            
            for transcript in transcripts:
                for move in transcript.moves:
                    if move.was_valid:
                        total_moves += 1
                        
                        if move.model_reasoning:
                            reasoning = move.model_reasoning.lower()
                            score = 0.0
                            
                            # Length-based scoring (0-0.3)
                            if len(reasoning) > 50:
                                score += 0.1
                            if len(reasoning) > 100:
                                score += 0.1
                            if len(reasoning) > 200:
                                score += 0.1
                            
                            # Quality indicators (0-0.7)
                            # Check for logical reasoning keywords
                            logic_keywords = ['because', 'therefore', 'since', 'must be', 'cannot be', 
                                            'adjacent', 'surrounding', 'deduce', 'conclude', 'implies']
                            logic_count = sum(1 for word in logic_keywords if word in reasoning)
                            score += min(0.3, logic_count * 0.05)
                            
                            # Check for specific Minesweeper reasoning
                            game_keywords = ['mine', 'flag', 'safe', 'revealed', 'number', 'cell', 
                                           'hidden', 'adjacent mines', 'count']
                            game_count = sum(1 for word in game_keywords if word in reasoning)
                            score += min(0.2, game_count * 0.04)
                            
                            # Check for analytical structure
                            if any(pattern in reasoning for pattern in ['first,', 'second,', 'step 1', '1.', '2.']):
                                score += 0.1
                            
                            # Check for uncertainty/probability mentions
                            if any(word in reasoning for word in ['probability', 'likely', 'risk', 'chance', 'guess']):
                                score += 0.1
                            
                            quality_scores.append(min(1.0, score))
                        else:
                            quality_scores.append(0.0)
            
            # Calculate average quality score
            if quality_scores:
                adv_metrics.reasoning_score = sum(quality_scores) / len(quality_scores)
            else:
                adv_metrics.reasoning_score = 0.0
            
            moves_with_reasoning = sum(1 for s in quality_scores if s > 0)
            avg_quality = adv_metrics.reasoning_score
            logger.info(f"📊 Heuristic reasoning score: {avg_quality:.2f} ({moves_with_reasoning}/{total_moves} moves with reasoning, avg quality: {avg_quality:.2f})")
            logger.warning("⚠️ Using heuristic scoring. For proper AI evaluation, ensure USE_REASONING_JUDGE=true")
        
        # Convert to dict for backward compatibility
        metrics = {
            "win_rate": metrics_obj.win_rate,
            "valid_move_rate": metrics_obj.valid_move_rate,
            "mine_identification_precision": metrics_obj.mine_identification_precision,
            "mine_identification_recall": metrics_obj.mine_identification_recall,
            "average_moves_to_win": metrics_obj.average_moves_to_win,
            "average_moves_to_loss": metrics_obj.average_moves_to_loss,
            "board_coverage_on_loss": metrics_obj.board_coverage_on_loss,
            # MineBench scores
            "ms_s_score": adv_metrics.ms_s_score,
            "ms_i_score": adv_metrics.ms_i_score,
            "global_score": adv_metrics.global_score,
            "reasoning_score": adv_metrics.reasoning_score,
            "flag_precision": adv_metrics.flag_precision,
            "flag_recall": adv_metrics.flag_recall,
            "reasoning_quality_score": metrics_obj.reasoning_quality_score,
        }
        
        logger.info(f"📊 Final metrics - Win rate: {metrics['win_rate']:.2%}, Reasoning: {metrics['reasoning_score']:.2f}")
        
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