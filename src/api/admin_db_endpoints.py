"""Database admin endpoints for managing games and leaderboard."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.core.database import get_db, Game, LeaderboardEntry, Evaluation, Task
from src.core.logging_config import get_logger

router = APIRouter(prefix="/api/admin/db", tags=["admin-db"])
logger = get_logger("api.admin_db")


@router.get("/stats")
async def get_database_stats():
    """Get database statistics."""
    try:
        db = next(get_db())
        
        stats = {
            "games": {
                "total": db.query(Game).count(),
                "won": db.query(Game).filter(Game.won == True).count(),
                "lost": db.query(Game).filter(Game.won == False).count(),
                "by_model": {}
            },
            "leaderboard_entries": db.query(LeaderboardEntry).count(),
            "evaluations": db.query(Evaluation).count(),
            "tasks": db.query(Task).count(),
            "models": []
        }
        
        # Get per-model stats
        models = db.query(Game.model_name, Game.model_provider).distinct().all()
        for model_name, provider in models:
            model_games = db.query(Game).filter(
                Game.model_name == model_name,
                Game.model_provider == provider
            )
            stats["games"]["by_model"][f"{provider}:{model_name}"] = {
                "total": model_games.count(),
                "won": model_games.filter(Game.won == True).count()
            }
            stats["models"].append({
                "provider": provider,
                "name": model_name
            })
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games")
async def list_games(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    won: Optional[bool] = None,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0)
):
    """List games with filtering options."""
    try:
        db = next(get_db())
        
        query = db.query(Game)
        
        # Apply filters
        if model_name:
            query = query.filter(Game.model_name == model_name)
        if provider:
            query = query.filter(Game.model_provider == provider)
        if won is not None:
            query = query.filter(Game.won == won)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        games = query.order_by(Game.created_at.desc()).offset(offset).limit(limit).all()
        
        result = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "games": [
                {
                    "id": game.id,
                    "model": f"{game.model_provider}:{game.model_name}",
                    "difficulty": game.difficulty,
                    "board_size": f"{game.rows}x{game.cols}",
                    "mines": game.mines,
                    "won": game.won,
                    "moves": game.num_moves,
                    "created_at": game.created_at.isoformat() if game.created_at else None,
                    "has_transcript": game.full_transcript is not None
                }
                for game in games
            ]
        }
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"Error listing games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/games/{game_id}")
async def delete_game(game_id: str):
    """Delete a specific game and its evaluations."""
    try:
        db = next(get_db())
        
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Delete will cascade to evaluations
        db.delete(game)
        db.commit()
        
        db.close()
        logger.info(f"Deleted game {game_id}")
        
        return {"message": f"Game {game_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting game: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/games")
async def delete_games(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    won: Optional[bool] = None,
    before_date: Optional[str] = None
):
    """Delete multiple games based on filters."""
    try:
        db = next(get_db())
        
        query = db.query(Game)
        
        # Apply filters
        if model_name:
            query = query.filter(Game.model_name == model_name)
        if provider:
            query = query.filter(Game.model_provider == provider)
        if won is not None:
            query = query.filter(Game.won == won)
        if before_date:
            date = datetime.fromisoformat(before_date)
            query = query.filter(Game.created_at < date)
        
        # Get count before deletion
        count = query.count()
        
        if count == 0:
            db.close()
            return {"message": "No games matched the criteria", "deleted": 0}
        
        # Delete all matching games
        query.delete()
        db.commit()
        
        db.close()
        logger.info(f"Deleted {count} games")
        
        return {"message": f"Deleted {count} games", "deleted": count}
        
    except Exception as e:
        logger.error(f"Error deleting games: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_leaderboard_entries():
    """Get all leaderboard entries with management info."""
    try:
        db = next(get_db())
        
        entries = db.query(LeaderboardEntry).order_by(
            LeaderboardEntry.global_score.desc()
        ).all()
        
        result = [
            {
                "id": entry.id,
                "model": f"{entry.model_provider}:{entry.model_name}",
                "provider": entry.model_provider,
                "model_name": entry.model_name,
                "total_games": entry.total_games,
                "win_rate": entry.win_rate,
                "global_score": entry.global_score,
                "reasoning_score": entry.reasoning_score,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
            }
            for entry in entries
        ]
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/leaderboard/{entry_id}")
async def delete_leaderboard_entry(entry_id: int):
    """Delete a specific leaderboard entry."""
    try:
        db = next(get_db())
        
        entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.id == entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Leaderboard entry not found")
        
        model_info = f"{entry.model_provider}:{entry.model_name}"
        db.delete(entry)
        db.commit()
        
        db.close()
        logger.info(f"Deleted leaderboard entry for {model_info}")
        
        return {"message": f"Leaderboard entry for {model_info} deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting leaderboard entry: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leaderboard/reset/{model_name}")
async def reset_model_stats(model_name: str, provider: str = Query(...)):
    """Reset statistics for a specific model."""
    try:
        db = next(get_db())
        
        # Delete all games for this model
        deleted_games = db.query(Game).filter(
            Game.model_name == model_name,
            Game.model_provider == provider
        ).delete()
        
        # Reset or delete leaderboard entry
        entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.model_name == model_name,
            LeaderboardEntry.model_provider == provider
        ).first()
        
        if entry:
            db.delete(entry)
        
        db.commit()
        db.close()
        
        logger.info(f"Reset stats for {provider}:{model_name}, deleted {deleted_games} games")
        
        return {
            "message": f"Reset complete for {provider}:{model_name}",
            "games_deleted": deleted_games,
            "leaderboard_reset": entry is not None
        }
        
    except Exception as e:
        logger.error(f"Error resetting model stats: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_database(
    delete_orphaned_evaluations: bool = False,
    delete_games_without_moves: bool = False,
    delete_old_tasks: bool = False
):
    """Clean up database by removing orphaned or incomplete data."""
    try:
        db = next(get_db())
        
        cleanup_stats = {}
        
        # Delete orphaned evaluations
        if delete_orphaned_evaluations:
            orphaned = db.query(Evaluation).filter(
                ~Evaluation.game_id.in_(db.query(Game.id))
            ).delete()
            cleanup_stats["orphaned_evaluations"] = orphaned
        
        # Delete games without moves
        if delete_games_without_moves:
            empty_games = db.query(Game).filter(Game.num_moves == 0).delete()
            cleanup_stats["empty_games"] = empty_games
        
        # Delete old unused tasks
        if delete_old_tasks:
            old_tasks = db.query(Task).filter(Task.used_count == 0).delete()
            cleanup_stats["unused_tasks"] = old_tasks
        
        db.commit()
        db.close()
        
        logger.info(f"Database cleanup completed: {cleanup_stats}")
        
        return {
            "message": "Cleanup completed",
            "stats": cleanup_stats
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))