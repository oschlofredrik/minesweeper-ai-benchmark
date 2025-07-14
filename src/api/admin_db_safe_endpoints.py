"""Safe database admin endpoints that handle missing columns."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_db, Game, LeaderboardEntry, Evaluation, Task
from src.core.logging_config import get_logger
from src.core.storage import get_storage

router = APIRouter(prefix="/api/admin/db", tags=["admin-db"])
logger = get_logger("api.admin_db_safe")


@router.get("/safe/stats")
async def get_database_stats_safe():
    """Get database statistics using raw SQL to avoid column issues."""
    logger.info("Safe database stats endpoint called")
    
    # Check if database is available
    storage = get_storage()
    if not storage.use_database:
        logger.warning("Database not available - returning empty stats")
        return {
            "games": {
                "total": 0,
                "won": 0,
                "lost": 0,
                "by_model": {}
            },
            "leaderboard_entries": 0,
            "evaluations": 0,
            "tasks": 0,
            "models": [],
            "database_available": False
        }
    
    try:
        db = next(get_db())
        logger.info("Got database connection")
        
        stats = {
            "games": {
                "total": 0,
                "won": 0,
                "lost": 0,
                "by_model": {}
            },
            "leaderboard_entries": 0,
            "evaluations": 0,
            "tasks": 0,
            "models": [],
            "database_available": True
        }
        
        # Use raw SQL to avoid column issues
        try:
            # Get game counts
            result = db.execute(text("SELECT COUNT(*) FROM games"))
            stats["games"]["total"] = result.scalar() or 0
            
            result = db.execute(text("SELECT COUNT(*) FROM games WHERE won = true"))
            stats["games"]["won"] = result.scalar() or 0
            
            stats["games"]["lost"] = stats["games"]["total"] - stats["games"]["won"]
            
            # Get per-model stats
            result = db.execute(text("""
                SELECT model_provider, model_name, 
                       COUNT(*) as total,
                       SUM(CASE WHEN won = true THEN 1 ELSE 0 END) as won
                FROM games
                GROUP BY model_provider, model_name
            """))
            
            for row in result:
                model_key = f"{row.model_provider}:{row.model_name}"
                stats["games"]["by_model"][model_key] = {
                    "total": row.total,
                    "won": row.won or 0
                }
                stats["models"].append({
                    "provider": row.model_provider,
                    "name": row.model_name
                })
            
            # Get other counts
            result = db.execute(text("SELECT COUNT(*) FROM leaderboard_entries"))
            stats["leaderboard_entries"] = result.scalar() or 0
            
            result = db.execute(text("SELECT COUNT(*) FROM evaluations"))
            stats["evaluations"] = result.scalar() or 0
            
            result = db.execute(text("SELECT COUNT(*) FROM tasks"))
            stats["tasks"] = result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error executing queries: {e}")
            # Return partial stats if some queries fail
            
        db.close()
        logger.info(f"Database stats retrieved successfully: {stats['games']['total']} games")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safe/games")
async def list_games_safe(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    won: Optional[bool] = None,
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0)
):
    """List games using raw SQL to avoid column issues."""
    logger.info(f"Safe list games called - model: {model_name}, provider: {provider}, won: {won}")
    
    # Check if database is available
    storage = get_storage()
    if not storage.use_database:
        logger.warning("Database not available")
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "games": [],
            "database_available": False
        }
    
    try:
        db = next(get_db())
        
        # Build WHERE clause
        where_parts = []
        params = {"limit": limit, "offset": offset}
        
        if model_name:
            where_parts.append("model_name = :model_name")
            params["model_name"] = model_name
        if provider:
            where_parts.append("model_provider = :provider")
            params["provider"] = provider
        if won is not None:
            where_parts.append("won = :won")
            params["won"] = won
            
        where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM games{where_clause}"
        result = db.execute(text(count_query), params)
        total = result.scalar() or 0
        
        # Get games with only existing columns
        games_query = f"""
            SELECT id, model_provider, model_name, difficulty,
                   rows, cols, mines, won, num_moves,
                   completed_at
            FROM games
            {where_clause}
            ORDER BY completed_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        result = db.execute(text(games_query), params)
        games = []
        
        for row in result:
            games.append({
                "id": row.id,
                "model": f"{row.model_provider}:{row.model_name}",
                "difficulty": row.difficulty,
                "board_size": f"{row.rows}x{row.cols}",
                "mines": row.mines,
                "won": row.won,
                "moves": row.num_moves,
                "created_at": row.completed_at.isoformat() if row.completed_at else None,
                "has_transcript": False  # We'll update this when column exists
            })
        
        db.close()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "games": games,
            "database_available": True
        }
        
    except Exception as e:
        logger.error(f"Error listing games: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))