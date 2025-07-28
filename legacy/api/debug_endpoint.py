"""Debug endpoint to check environment variables in production."""

from fastapi import APIRouter
from src.core.config import settings
from src.core.storage import get_storage
from src.core.database import get_db, LeaderboardEntry, Game, Evaluation
import os
import logging

router = APIRouter()
logger = logging.getLogger("api.debug")

@router.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables (REMOVE IN PRODUCTION)."""
    
    # Check if we're in production
    is_production = os.environ.get('ENVIRONMENT') == 'production'
    
    return {
        "environment": os.environ.get('ENVIRONMENT', 'unknown'),
        "openai_key_set": bool(settings.openai_api_key),
        "openai_key_preview": settings.openai_api_key[:10] + "..." if settings.openai_api_key else None,
        "openai_key_length": len(settings.openai_api_key) if settings.openai_api_key else 0,
        "anthropic_key_set": bool(settings.anthropic_api_key),
        "database_url_set": bool(settings.database_url),
        "raw_env_openai": bool(os.environ.get('OPENAI_API_KEY')),
        "raw_env_preview": os.environ.get('OPENAI_API_KEY', '')[:10] + "..." if os.environ.get('OPENAI_API_KEY') else None,
        "settings_source": "Check if .env file exists on server",
        "note": "If keys are set but auth fails, check for extra spaces or encoding issues"
    }


@router.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database connection and status."""
    logger.info("🔍 Database diagnostics requested")
    
    result = {
        "database_url_set": bool(os.environ.get('DATABASE_URL')),
        "database_url_preview": os.environ.get('DATABASE_URL', '')[:50] + "..." if os.environ.get('DATABASE_URL') else None,
        "storage_backend": None,
        "database_accessible": False,
        "table_counts": {},
        "errors": []
    }
    
    try:
        # Check storage backend
        storage = get_storage()
        result["storage_backend"] = "database" if storage.use_database else "file"
        logger.info(f"Storage backend: {result['storage_backend']}")
        
        if storage.use_database:
            # Try to access database
            try:
                db = next(get_db())
                result["database_accessible"] = True
                
                # Get table counts
                result["table_counts"]["leaderboard_entries"] = db.query(LeaderboardEntry).count()
                result["table_counts"]["games"] = db.query(Game).count()
                result["table_counts"]["evaluations"] = db.query(Evaluation).count()
                
                # Get sample leaderboard entry if exists
                sample_entry = db.query(LeaderboardEntry).first()
                if sample_entry:
                    result["sample_leaderboard_entry"] = {
                        "id": sample_entry.id,
                        "model_name": sample_entry.model_name,
                        "model_provider": sample_entry.model_provider,
                        "total_games": sample_entry.total_games,
                        "win_rate": sample_entry.win_rate,
                        "global_score": sample_entry.global_score,
                        "created_at": sample_entry.created_at.isoformat() if sample_entry.created_at else None,
                        "updated_at": sample_entry.updated_at.isoformat() if sample_entry.updated_at else None
                    }
                
                db.close()
                logger.info(f"Database access successful. Table counts: {result['table_counts']}")
                
            except Exception as e:
                result["errors"].append(f"Database access error: {type(e).__name__}: {str(e)}")
                logger.error(f"Database access error: {e}", exc_info=True)
        
    except Exception as e:
        result["errors"].append(f"Storage initialization error: {type(e).__name__}: {str(e)}")
        logger.error(f"Storage initialization error: {e}", exc_info=True)
    
    return result