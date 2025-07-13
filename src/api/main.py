"""FastAPI application for the Minesweeper benchmark platform."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.evaluation import MineBenchFormatter
from .models import (
    LeaderboardEntry, ModelResult, TaskInfo, 
    EvaluationRequest, ComparisonResult
)
from .database import get_leaderboard_data, get_model_results, get_game_replay
from .evaluation_endpoints import router as evaluation_router
from .play_endpoints import router as play_router

# Initialize logging
setup_logging(
    log_level=settings.log_level if hasattr(settings, 'log_level') else "INFO",
    log_file="data/logs/minesweeper_api.log",
    enable_console=True,
    enable_file=True,
    structured=True
)

app = FastAPI(
    title="Minesweeper AI Benchmark",
    description="Benchmark platform for evaluating LLMs on Minesweeper",
    version="1.0.0",
)

# Configure CORS for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(evaluation_router)
app.include_router(play_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        # Return a simple HTML page if index.html doesn't exist yet
        return """
        <html>
            <head>
                <title>Minesweeper AI Benchmark</title>
            </head>
            <body>
                <h1>Minesweeper AI Benchmark</h1>
                <p>Web interface coming soon!</p>
                <p>API endpoints available:</p>
                <ul>
                    <li><a href="/docs">/docs</a> - API documentation</li>
                    <li><a href="/api/leaderboard">/api/leaderboard</a> - Current leaderboard</li>
                </ul>
            </body>
        </html>
        """


@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    task_type: Optional[str] = Query(None, description="Filter by task type (static/interactive)"),
    metric: Optional[str] = Query("global_score", description="Metric to sort by"),
    limit: int = Query(50, description="Number of entries to return"),
):
    """Get current leaderboard rankings."""
    try:
        data = await get_leaderboard_data(task_type, metric, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_id}/results", response_model=ModelResult)
async def get_model_details(model_id: str):
    """Get detailed results for a specific model."""
    try:
        results = await get_model_results(model_id)
        if not results:
            raise HTTPException(status_code=404, detail="Model not found")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_id}/games")
async def get_model_games(
    model_id: str,
    limit: int = Query(20, description="Number of games to return"),
):
    """Get list of games played by a model."""
    # Load game transcripts for the model
    results_dir = Path("data/results")
    games = []
    
    for file in results_dir.glob(f"*{model_id}*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
                if "per_game_metrics" in data:
                    for game in data["per_game_metrics"][:limit]:
                        games.append({
                            "game_id": game.get("game_id"),
                            "won": game.get("won", False),
                            "moves": game.get("moves", 0),
                            "board_coverage": game.get("board_coverage", 0),
                        })
        except:
            continue
    
    return games[:limit]


@app.get("/api/games/{game_id}/replay")
async def get_game_replay_data(game_id: str):
    """Get replay data for a specific game."""
    try:
        replay_data = await get_game_replay(game_id)
        if not replay_data:
            raise HTTPException(status_code=404, detail="Game not found")
        return replay_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare", response_model=ComparisonResult)
async def compare_models(request: EvaluationRequest):
    """Compare multiple models on the same tasks."""
    # This would trigger a comparison evaluation
    # For now, return a placeholder
    return ComparisonResult(
        models=request.models,
        message="Comparison queued. This feature is not yet implemented.",
        comparison_id="comp_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
    )


@app.get("/api/stats")
async def get_platform_stats():
    """Get overall platform statistics."""
    results_dir = Path("data/results")
    tasks_dir = Path("data/tasks")
    
    # Count files
    num_evaluations = len(list(results_dir.glob("*.json")))
    num_tasks = len(list(tasks_dir.glob("**/*.json")))
    
    # Get unique models from results
    models = set()
    for file in results_dir.glob("*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
                if "model" in data:
                    models.add(data["model"]["name"])
        except:
            continue
    
    return {
        "total_evaluations": num_evaluations,
        "total_tasks": num_tasks,
        "unique_models": len(models),
        "model_list": sorted(list(models)),
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/api/metrics")
async def get_available_metrics():
    """Get list of available metrics."""
    return {
        "primary_metrics": [
            {"id": "global_score", "name": "Global Score", "description": "Overall MineBench score"},
            {"id": "ms_s_score", "name": "Static Score", "description": "Static task composite score"},
            {"id": "ms_i_score", "name": "Interactive Score", "description": "Interactive task composite score"},
        ],
        "detailed_metrics": [
            {"id": "win_rate", "name": "Win Rate", "description": "Percentage of games won"},
            {"id": "accuracy", "name": "Accuracy", "description": "Correct predictions (static tasks)"},
            {"id": "coverage", "name": "Board Coverage", "description": "Average cells revealed"},
            {"id": "valid_move_rate", "name": "Valid Move Rate", "description": "Percentage of legal moves"},
            {"id": "reasoning_score", "name": "Reasoning Score", "description": "Quality of explanations"},
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}