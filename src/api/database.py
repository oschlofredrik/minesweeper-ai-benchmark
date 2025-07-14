"""Database operations for the API (currently file-based)."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio

from src.core.storage import get_storage
from .models import LeaderboardEntry, ModelResult, GameReplay


async def get_leaderboard_data(
    task_type: Optional[str] = None,
    metric: str = "global_score",
    limit: int = 50,
) -> List[LeaderboardEntry]:
    """
    Get leaderboard data from storage backend.
    """
    storage = get_storage()
    
    # Get leaderboard data from storage
    leaderboard_data = storage.get_leaderboard()
    
    # Convert to LeaderboardEntry objects
    leaderboard_entries = []
    for data in leaderboard_data:
        entry = LeaderboardEntry(
            rank=data.get("rank", 0),
            model_id=data.get("model_name", "unknown"),
            model_name=data.get("model_name", "unknown"),
            global_score=data.get("global_score", 0.0),
            ms_s_score=data.get("global_score", 0.0),  # Using global_score as proxy
            ms_i_score=data.get("global_score", 0.0),  # Using global_score as proxy
            win_rate=data.get("win_rate", 0.0),
            accuracy=data.get("accuracy", 0.0),
            coverage=data.get("board_coverage", 0.0),
            reasoning_score=data.get("reasoning_score", 0.0),
            num_games=data.get("total_games", 0),
            last_updated=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc),
            valid_move_rate=data.get("valid_move_rate", 0.0),
            total_games=data.get("total_games", 0)
        )
        leaderboard_entries.append(entry)
    
    # Sort by metric if needed
    if metric != "global_score":
        leaderboard_entries.sort(
            key=lambda x: getattr(x, metric, 0.0),
            reverse=True
        )
        # Re-assign ranks
        for i, entry in enumerate(leaderboard_entries):
            entry.rank = i + 1
    
    return leaderboard_entries[:limit]


async def get_model_results(model_id: str) -> Optional[ModelResult]:
    """Get detailed results for a specific model."""
    results_dir = Path("data/results")
    
    # Find the most recent result file for this model
    model_files = list(results_dir.glob(f"*{model_id}*_summary.json"))
    if not model_files:
        return None
    
    # Sort by modification time and get the latest
    latest_file = max(model_files, key=lambda f: f.stat().st_mtime)
    
    try:
        with open(latest_file) as f:
            data = json.load(f)
        
        metrics = data.get("metrics", {})
        model_info = data.get("model", {})
        eval_info = data.get("evaluation", {})
        
        return ModelResult(
            model_id=model_id,
            model_name=model_info.get("name", model_id),
            provider=model_info.get("provider", "unknown"),
            evaluation_date=datetime.fromisoformat(
                eval_info.get("end_time", datetime.utcnow().isoformat())
            ),
            num_tasks=eval_info.get("num_tasks", 0),
            metrics=metrics,
            per_task_type_metrics={
                "static": {"accuracy": metrics.get("accuracy", 0.0)},
                "interactive": {"win_rate": metrics.get("win_rate", 0.0)},
            },
            confidence_intervals={
                "win_rate": (
                    metrics.get("win_rate", 0.0) - 0.05,
                    metrics.get("win_rate", 0.0) + 0.05,
                ),
            },
            prompt_variant=eval_info.get("prompt_format", "standard"),
        )
        
    except Exception as e:
        print(f"Error loading model results: {e}")
        return None


async def get_game_replay(game_id: str) -> Optional[Dict[str, Any]]:
    """Get replay data for a specific game."""
    storage = get_storage()
    
    # Try to load game from storage backend
    game_result = storage.load_game(game_id)
    if game_result:
        # Convert GameResult to replay format
        return {
            "game_id": game_id,
            "model_name": game_result.model_config.name,
            "task_id": game_result.task_id if hasattr(game_result, 'task_id') else "unknown",
            "moves": [move.to_dict() for move in game_result.moves],
            "final_status": "won" if game_result.won else "lost",
            "num_moves": game_result.num_moves,
        }
    
    # Fallback to looking for transcript files for backward compatibility
    transcripts_dir = Path("data/results")
    
    for file in transcripts_dir.glob("*_transcripts.json"):
        try:
            with open(file) as f:
                transcripts = json.load(f)
            
            for transcript in transcripts:
                if transcript.get("game_id") == game_id:
                    # Convert to replay format
                    return {
                        "game_id": game_id,
                        "model_name": transcript.get("model_name", "unknown"),
                        "task_id": transcript.get("task_id", "unknown"),
                        "moves": transcript.get("moves", []),
                        "final_status": transcript.get("final_status", "unknown"),
                        "num_moves": transcript.get("num_moves", 0),
                    }
                    
        except Exception as e:
            print(f"Error loading transcript: {e}")
            continue
    
    return None