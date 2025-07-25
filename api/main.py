"""FastAPI application for Vercel deployment."""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tilts - Minesweeper AI Benchmark",
    description="Platform for evaluating LLMs on strategic reasoning tasks",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the static files path
static_path = Path(__file__).parent.parent / "serverless-migration" / "src" / "api" / "static"

# Mount static files if directory exists
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main page."""
    index_path = static_path / "index-rams.html"
    if index_path.exists():
        content = index_path.read_text()
        # Fix static file paths
        content = content.replace('href="/static/', 'href="/static/')
        content = content.replace('src="/static/', 'src="/static/')
        return HTMLResponse(content=content)
    return HTMLResponse("<h1>Tilts Platform</h1><p>Static files not found.</p>")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tilts", "version": "1.0.0"}

@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get leaderboard data."""
    return {
        "entries": [
            {
                "model_name": "gpt-4",
                "games_played": 250,
                "win_rate": 0.85,
                "avg_moves": 45,
                "valid_move_rate": 0.98,
                "mine_identification_precision": 0.92,
                "mine_identification_recall": 0.88,
                "coverage_ratio": 0.75,
                "reasoning_score": 0.90,
                "composite_score": 0.86,
                "last_updated": "2024-07-25T12:00:00Z"
            },
            {
                "model_name": "claude-3-opus",
                "games_played": 200,
                "win_rate": 0.82,
                "avg_moves": 48,
                "valid_move_rate": 0.97,
                "mine_identification_precision": 0.90,
                "mine_identification_recall": 0.85,
                "coverage_ratio": 0.73,
                "reasoning_score": 0.88,
                "composite_score": 0.83,
                "last_updated": "2024-07-25T11:00:00Z"
            }
        ]
    }

@app.get("/api/overview/stats")
async def get_stats():
    """Get platform statistics."""
    return {
        "total_games": 1000,
        "total_models": 5,
        "best_model": "gpt-4",
        "best_win_rate": 0.85,
        "avg_game_duration": 120,
        "platform_uptime": "99.9%"
    }

@app.get("/api/sessions")
async def get_sessions():
    """Get user sessions."""
    return {"sessions": []}

@app.get("/api/games/active")
async def get_active_games():
    """Get active games."""
    return {"games": []}

@app.post("/api/play")
async def start_play():
    """Start a new evaluation."""
    return {
        "job_id": "demo-job-123",
        "status": "started",
        "message": "Demo mode - evaluation started"
    }

# Vercel handler
from mangum import Mangum
handler = Mangum(app)