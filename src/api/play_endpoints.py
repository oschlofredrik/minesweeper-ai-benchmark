"""API endpoints for the combined play functionality."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
import json
import time
import traceback

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from src.core.config import settings
from src.core.logging_config import get_logger, LogContext
from src.core.types import Difficulty
from src.evaluation import EvaluationEngine
from src.tasks import TaskRepository, TaskGenerator
from src.models import create_model, ModelConfig

# Initialize logger
logger = get_logger("api.play")

router = APIRouter(prefix="/api/play", tags=["play"])


class PlayRequest(BaseModel):
    """Request to start playing games."""
    model_name: str
    model_provider: str  # "openai" or "anthropic"
    num_games: int = 10
    game_type: Optional[str] = None  # "static" or "interactive"
    difficulty: Optional[str] = None  # "beginner", "intermediate", "expert"
    api_key: Optional[str] = None  # Optional API key


class PlayResponse(BaseModel):
    """Response from starting play."""
    job_id: str
    status: str
    model: str
    num_games: int
    message: str


class GameStatus(BaseModel):
    """Status of a game session."""
    job_id: str
    model_name: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    message: str
    games_completed: int = 0
    games_total: int = 0
    current_metrics: Optional[Dict[str, float]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results_file: Optional[str] = None  # Path to results JSON


# In-memory game tracking
games: Dict[str, GameStatus] = {}


@router.post("", response_model=PlayResponse)
async def start_play(
    request: PlayRequest,
    background_tasks: BackgroundTasks
):
    """Start playing games with automatic evaluation."""
    job_id = f"play_{uuid4().hex[:8]}"
    
    # Validate model provider
    if request.model_provider not in ["openai", "anthropic"]:
        logger.warning(
            f"Invalid model provider requested",
            extra={
                "provider": request.model_provider,
                "job_id": job_id
            }
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid model provider. Must be 'openai' or 'anthropic'"
        )
    
    logger.info(
        f"Play session requested",
        extra={
            "job_id": job_id,
            "model": request.model_name,
            "provider": request.model_provider,
            "num_games": request.num_games,
            "game_type": request.game_type,
            "difficulty": request.difficulty,
            "has_api_key": bool(request.api_key)
        }
    )
    
    # Create game status
    games[job_id] = GameStatus(
        job_id=job_id,
        model_name=request.model_name,
        status="pending",
        progress=0.0,
        message=f"Preparing to play {request.num_games} games...",
        games_total=request.num_games,
        started_at=datetime.utcnow()
    )
    
    # Run play session in background
    background_tasks.add_task(
        run_play_session,
        job_id,
        request.model_name,
        request.model_provider,
        request.num_games,
        request.game_type,
        request.difficulty,
        request.api_key
    )
    
    return PlayResponse(
        job_id=job_id,
        status="started",
        model=request.model_name,
        num_games=request.num_games,
        message="Game session started. Games will be generated and played automatically."
    )


@router.get("/games", response_model=List[GameStatus])
async def list_games(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, description="Number of games to return")
):
    """List all game sessions."""
    game_list = list(games.values())
    
    # Filter by status if provided
    if status:
        game_list = [g for g in game_list if g.status == status]
    
    # Sort by started_at descending
    game_list.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
    
    return game_list[:limit]


@router.get("/games/{job_id}", response_model=GameStatus)
async def get_game_status(job_id: str):
    """Get the status of a specific game session."""
    if job_id not in games:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    return games[job_id]


class PlaySummary(BaseModel):
    """Detailed summary of a play session."""
    job_id: str
    model_name: str
    status: str
    num_games: int
    metrics: Dict[str, float]
    game_results: List[Dict[str, Any]]
    aggregate_stats: Dict[str, Any]
    timestamp: str


@router.get("/games/{job_id}/summary")
async def get_game_summary(job_id: str):
    """Get detailed summary and results of a completed game session."""
    if job_id not in games:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    game_status = games[job_id]
    
    # Check if game is completed
    if game_status.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Game session is {game_status.status}. Summary only available for completed sessions."
        )
    
    # Check if results file exists
    if not game_status.results_file:
        raise HTTPException(status_code=404, detail="Results file not found")
    
    results_path = Path("data/results") / game_status.results_file
    
    if not results_path.exists():
        raise HTTPException(status_code=404, detail="Results file not found on disk")
    
    # Load results
    try:
        with open(results_path, "r") as f:
            results = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load results file", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load results")
    
    # Extract game-by-game results if available
    game_results = []
    if "game_results" in results:
        for game in results["game_results"]:
            game_results.append({
                "game_id": game.get("game_id"),
                "won": game.get("won", False),
                "num_moves": game.get("num_moves", 0),
                "final_status": game.get("final_status"),
                "board_coverage": game.get("board_coverage", 0),
                "mines_correctly_flagged": game.get("mines_correctly_flagged", 0),
                "total_mines": game.get("total_mines", 0)
            })
    
    # Create summary response
    summary = {
        "job_id": job_id,
        "model_name": game_status.model_name,
        "status": game_status.status,
        "num_games": results.get("num_games", game_status.games_total),
        "metrics": results.get("metrics", game_status.current_metrics or {}),
        "game_results": game_results,
        "aggregate_stats": {
            "total_games": len(game_results),
            "games_won": sum(1 for g in game_results if g.get("won")),
            "average_moves": sum(g.get("num_moves", 0) for g in game_results) / len(game_results) if game_results else 0,
            "average_coverage": sum(g.get("board_coverage", 0) for g in game_results) / len(game_results) if game_results else 0,
        },
        "timestamp": results.get("timestamp", ""),
        "started_at": game_status.started_at.isoformat() if game_status.started_at else None,
        "completed_at": game_status.completed_at.isoformat() if game_status.completed_at else None,
        "duration": (game_status.completed_at - game_status.started_at).total_seconds() if game_status.completed_at and game_status.started_at else None
    }
    
    return summary


async def run_play_session(
    job_id: str,
    model_name: str,
    model_provider: str,
    num_games: int,
    game_type: Optional[str],
    difficulty: Optional[str],
    api_key: Optional[str]
):
    """Background task to run a play session (generate games and evaluate)."""
    start_time = time.time()
    
    with LogContext(logger, job_id=job_id, model=model_name):
        try:
            logger.info(f"Starting play session")
            games[job_id].status = "running"
            games[job_id].message = f"Generating {num_games} games..."
            
            # Step 1: Generate games
            logger.info(f"Generating games for play session")
            generator = TaskGenerator()
            repository = TaskRepository()
            
            generated_tasks = []
            for i in range(num_games):
                try:
                    # Update progress
                    games[job_id].progress = (i / num_games) * 0.3  # First 30% for generation
                    
                    # Convert string difficulty to enum if provided
                    diff_enum = None
                    if difficulty:
                        try:
                            diff_enum = Difficulty(difficulty.lower())
                        except ValueError:
                            logger.warning(f"Invalid difficulty '{difficulty}', using default")
                            diff_enum = Difficulty.EXPERT
                    else:
                        diff_enum = Difficulty.EXPERT
                    
                    # Generate task based on type
                    if game_type == "static":
                        task = generator.generate_static_task(difficulty=diff_enum)
                    elif game_type == "interactive":
                        task = generator.generate_interactive_task(difficulty=diff_enum)
                    else:
                        # Mix of both
                        task = (generator.generate_static_task(difficulty=diff_enum) 
                                if i % 2 == 0 else 
                                generator.generate_interactive_task(difficulty=diff_enum))
                    
                    # Save task
                    repository.save_task(task)
                    generated_tasks.append(task)
                    
                except Exception as task_error:
                    logger.warning(
                        f"Failed to generate game {i}",
                        extra={"error": str(task_error)},
                        exc_info=True
                    )
            
            if not generated_tasks:
                raise Exception("Failed to generate any games")
            
            logger.info(f"Generated {len(generated_tasks)} games")
            games[job_id].message = f"Playing {len(generated_tasks)} games with {model_name}..."
            
            # Step 2: Create model and evaluate
            logger.debug(f"Creating model configuration")
            model_config = ModelConfig(
                name=model_name,
                provider=model_provider,
                model_id=model_name,
                temperature=0.7,
                max_tokens=1000,
                additional_params={}
            )
            
            if api_key:
                model_config.additional_params["api_key"] = api_key
            
            # Create evaluation engine
            engine = EvaluationEngine()
            
            # Run evaluation on generated tasks with manual progress tracking
            logger.info(f"Starting to play games")
            
            # Since evaluate_model doesn't support progress callbacks,
            # we'll run the evaluation and update progress manually
            start_eval_time = time.time()
            
            # Update status before starting
            games[job_id].message = f"Playing {len(generated_tasks)} games with {model_name}..."
            games[job_id].progress = 0.3  # 30% done with generation
            
            try:
                results = await engine.evaluate_model(
                    model_config=model_config,
                    tasks=generated_tasks,
                    prompt_format="standard",
                    verbose=False  # We'll handle our own logging
                )
                
                # Update to completed
                games[job_id].progress = 1.0
                games[job_id].games_completed = len(generated_tasks)
                
            except Exception as eval_error:
                logger.error(f"Evaluation failed: {str(eval_error)}", exc_info=True)
                raise
            
            # Extract metrics
            metrics = results.get("metrics", {})
            games[job_id].current_metrics = {
                "win_rate": metrics.get("win_rate", 0.0),
                "accuracy": metrics.get("accuracy", 0.0),
                "valid_move_rate": metrics.get("valid_move_rate", 0.0),
                "coverage": metrics.get("board_coverage_on_loss", 0.0)
            }
            
            # Save results with job_id in filename for easy lookup
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = f"play_{job_id}_{model_name}_{timestamp}.json"
            results_path = Path("data/results") / results_file
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add job_id to results for reference
            results["job_id"] = job_id
            results["model_name"] = model_name
            results["num_games"] = len(generated_tasks)
            results["timestamp"] = timestamp
            
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            
            # Complete
            duration = time.time() - start_time
            games[job_id].status = "completed"
            games[job_id].progress = 1.0
            games[job_id].games_completed = len(generated_tasks)
            games[job_id].message = f"Completed {len(generated_tasks)} games successfully!"
            games[job_id].completed_at = datetime.utcnow()
            games[job_id].results_file = str(results_file)  # Store the filename
            
            logger.info(
                f"Play session completed",
                extra={
                    "duration": duration,
                    "games_played": len(generated_tasks),
                    "win_rate": metrics.get("win_rate", 0.0),
                    "metrics": games[job_id].current_metrics
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            games[job_id].status = "failed"
            games[job_id].message = f"Error: {str(e)}"
            games[job_id].completed_at = datetime.utcnow()
            
            logger.error(
                f"Play session failed",
                extra={
                    "duration": duration,
                    "error_type": type(e).__name__,
                    "error_details": traceback.format_exc()
                },
                exc_info=True
            )