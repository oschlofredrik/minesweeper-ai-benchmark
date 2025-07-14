"""FastAPI application for the Minesweeper benchmark platform."""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.core.database import init_db
from src.core.storage import StorageBackend
from src.evaluation import MineBenchFormatter
from .models import (
    LeaderboardEntry, ModelResult, TaskInfo, 
    EvaluationRequest, ComparisonResult
)
from .database import get_leaderboard_data, get_model_results, get_game_replay
from .evaluation_endpoints import router as evaluation_router
from .play_endpoints import router as play_router
from .admin_endpoints import router as admin_router
from .admin_db_endpoints import router as admin_db_router
from .admin_db_safe_endpoints import router as admin_db_safe_router
from .event_streaming import router as streaming_router

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

# Add middleware to handle HTTPS redirection
@app.middleware("http")
async def force_https(request, call_next):
    """Force HTTPS in production."""
    # Check if we're behind a proxy (like Render)
    x_forwarded_proto = request.headers.get("x-forwarded-proto")
    
    if x_forwarded_proto == "http":
        # Redirect to HTTPS
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url, status_code=301)
    
    response = await call_next(request)
    
    # Add security headers
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(evaluation_router)
app.include_router(play_router)
app.include_router(admin_router)
app.include_router(admin_db_router)
app.include_router(admin_db_safe_router)
app.include_router(streaming_router)

# Debug router (REMOVE IN PRODUCTION)
from .debug_endpoint import router as debug_router
app.include_router(debug_router)

# Test DB endpoint (TEMPORARY)
from .test_db_endpoint import router as test_router
app.include_router(test_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and storage on startup."""
    import logging
    logger = logging.getLogger("api.startup")
    
    try:
        # Check for DATABASE_URL
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            logger.info("DATABASE_URL found in environment")
            logger.info(f"Database URL format: {db_url[:20]}...{db_url[-20:]}")  # Log partial URL for security
            
            # Check URL format
            if db_url.startswith('postgres://'):
                logger.info("Database URL uses postgres:// format (will be converted)")
            elif db_url.startswith('postgresql://'):
                logger.info("Database URL uses postgresql:// format")
            else:
                logger.warning(f"Unexpected database URL format: {db_url[:30]}...")
            
            logger.info("Attempting to initialize database connection...")
            try:
                init_db()
                logger.info("✅ Database initialized successfully")
            except Exception as db_error:
                logger.error(f"❌ Database initialization failed: {type(db_error).__name__}: {str(db_error)}")
                raise
        else:
            logger.warning("❌ No DATABASE_URL found in environment variables")
            logger.info("Will use file-based storage")
        
        # Initialize storage backend
        logger.info("Initializing storage backend...")
        storage = StorageBackend()
        
        # Log storage backend status
        if storage.use_database:
            logger.info("✅ Storage backend: Using PostgreSQL database")
            # Try a test query
            try:
                from src.core.database import get_db
                from sqlalchemy import text
                db = next(get_db())
                result = db.execute(text("SELECT 1"))
                logger.info(f"✅ Database connection test successful: {result.scalar()}")
                db.close()
            except Exception as test_error:
                logger.error(f"❌ Database connection test failed: {test_error}")
        else:
            logger.info("ℹ️ Storage backend: Using file-based storage")
            logger.info("   Data directory: data/")
        
    except Exception as e:
        logger.error(f"❌ Critical error during startup: {type(e).__name__}: {str(e)}", exc_info=True)
        logger.warning("⚠️ Falling back to file storage due to initialization error")
        # Don't fail startup, just use file storage


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon."""
    favicon_path = static_dir / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")


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
    index_file = static_dir / "index-rams.html"
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


@app.get("/summary/{job_id}", response_class=HTMLResponse)
async def game_summary_page(job_id: str):
    """Serve the game summary page."""
    summary_file = static_dir / "summary.html"
    if summary_file.exists():
        return FileResponse(summary_file)
    else:
        return RedirectResponse(url="/")

@app.get("/design-preview", response_class=HTMLResponse)
async def design_preview():
    """Serve the design preview page."""
    preview_file = static_dir / "design-preview.html"
    if preview_file.exists():
        return FileResponse(preview_file)
    else:
        return RedirectResponse(url="/")

@app.get("/terminal", response_class=HTMLResponse)
async def terminal_design():
    """Serve the original terminal design."""
    terminal_file = static_dir / "index.html"
    if terminal_file.exists():
        return FileResponse(terminal_file)
    else:
        return RedirectResponse(url="/")


@app.get("/admin", response_class=HTMLResponse)
async def admin_interface():
    """Serve the admin interface."""
    admin_file = static_dir / "admin.html"
    if admin_file.exists():
        return FileResponse(admin_file)
    else:
        return RedirectResponse(url="/")


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
    from src.core.storage import get_storage
    storage = get_storage()
    
    # Try to get games from storage backend
    games = storage.list_games(model_name=model_id, limit=limit)
    
    if games:
        # Convert to expected format
        return [{
            "game_id": game.get("game_id"),
            "won": game.get("won", False),
            "moves": game.get("num_moves", 0),
            "board_coverage": game.get("board_coverage", 0),
        } for game in games]
    
    # Fallback to reading result files for backward compatibility
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
    from src.core.storage import get_storage
    storage = get_storage()
    
    # Try to get stats from storage backend
    tasks = storage.list_tasks()
    num_tasks = len(tasks)
    
    # For evaluations, we still need to count result files since they contain aggregate data
    results_dir = Path("data/results")
    num_evaluations = len(list(results_dir.glob("*.json")))
    
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
        "last_updated": datetime.now(timezone.utc).isoformat(),
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