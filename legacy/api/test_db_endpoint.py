"""Test endpoint to debug database saving."""

from fastapi import APIRouter
from src.core.storage import get_storage
from src.core.types import ModelConfig
import logging

router = APIRouter()
logger = logging.getLogger("api.test_db")

@router.post("/test/db-save")
async def test_database_save():
    """Test database saving with minimal data."""
    logger.info("🧪 Starting test database save")
    
    try:
        # Get storage backend
        storage = get_storage()
        logger.info(f"Storage backend: use_database={storage.use_database}")
        
        # Create test model config
        model_config = ModelConfig(
            provider="openai",
            name="test-model",
            model_id="test-model",
            temperature=0,
            max_tokens=1000,
            additional_params={}
        )
        
        # Create test metrics
        test_metrics = {
            'num_games': 1,
            'win_rate': 0.5,
            'valid_move_rate': 0.9,
            'mine_identification_precision': 0.8,
            'mine_identification_recall': 0.7,
            'board_coverage': 0.6,
            'efficiency_score': 0.75,
            'strategic_score': 0.8,
            'reasoning_score': 0.85,
            'composite_score': 0.77,
            'ms_s_score': 0.7,
            'ms_i_score': 0.8,
        }
        
        logger.info("📊 Test metrics prepared")
        logger.info(f"Metrics: {test_metrics}")
        
        # Try to update leaderboard
        logger.info("🚀 Calling update_leaderboard...")
        result = storage.update_leaderboard(model_config, test_metrics)
        
        logger.info(f"Result: {result}")
        
        # Check if it worked
        leaderboard = storage.get_leaderboard()
        
        return {
            "success": result,
            "storage_type": "database" if storage.use_database else "file",
            "leaderboard_count": len(leaderboard),
            "test_entry_exists": any(e.get('model_name') == 'test-model' for e in leaderboard)
        }
        
    except Exception as e:
        logger.error(f"Test failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }