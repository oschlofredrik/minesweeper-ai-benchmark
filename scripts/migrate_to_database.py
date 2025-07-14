#!/usr/bin/env python3
"""
Migrate existing file-based results to PostgreSQL database.

This script reads evaluation results from data/results/ and imports them
into the database for persistence.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.storage import get_storage
from src.core.types import ModelConfig
from src.core.logging_config import setup_logging

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger("migrate")


def migrate_results_to_database():
    """Migrate file-based results to database."""
    results_dir = Path("data/results")
    if not results_dir.exists():
        logger.error("No results directory found")
        return
    
    storage = get_storage()
    if not storage.use_database:
        logger.error("Database not configured. Set DATABASE_URL environment variable.")
        return
    
    logger.info("Starting migration of results to database...")
    
    # Process each result file
    migrated = 0
    failed = 0
    
    for result_file in results_dir.glob("*.json"):
        try:
            logger.info(f"Processing {result_file.name}...")
            
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            # Skip if not a proper result file
            if 'metrics' not in data or 'model' not in data:
                logger.warning(f"Skipping {result_file.name} - not a valid result file")
                continue
            
            # Extract model info
            model_info = data.get('model', {})
            model_config = ModelConfig(
                provider=model_info.get('provider', 'unknown'),
                name=model_info.get('name', 'unknown'),
                api_key=""  # Not needed for migration
            )
            
            # Extract metrics
            metrics = data.get('metrics', {})
            
            # Prepare metrics for database
            db_metrics = {
                'num_games': data.get('num_games', data.get('evaluation', {}).get('num_tasks', 1)),
                'win_rate': metrics.get('win_rate', 0.0),
                'valid_move_rate': metrics.get('valid_move_rate', 0.0),
                'mine_identification_precision': metrics.get('mine_identification_precision', 0.0),
                'mine_identification_recall': metrics.get('mine_identification_recall', 0.0),
                'board_coverage': metrics.get('board_coverage_on_loss', 0.0),
                'efficiency_score': metrics.get('efficiency_score', 0.0),
                'strategic_score': metrics.get('strategic_score', 0.0),
                'reasoning_score': metrics.get('reasoning_score', 0.0),
                'composite_score': metrics.get('global_score', metrics.get('composite_score', 0.0)),
                'ms_s_score': metrics.get('ms_s_score', 0.0),
                'ms_i_score': metrics.get('ms_i_score', 0.0),
            }
            
            # Update leaderboard
            if storage.update_leaderboard(model_config, db_metrics):
                logger.info(f"✅ Migrated {model_config.name} with {db_metrics['num_games']} games")
                migrated += 1
            else:
                logger.error(f"❌ Failed to migrate {model_config.name}")
                failed += 1
                
        except Exception as e:
            logger.error(f"Error processing {result_file.name}: {e}")
            failed += 1
    
    logger.info(f"\nMigration complete: {migrated} succeeded, {failed} failed")
    
    # Verify migration
    try:
        from src.core.database import get_db, LeaderboardEntry
        db = next(get_db())
        count = db.query(LeaderboardEntry).count()
        logger.info(f"Database now contains {count} leaderboard entries")
        db.close()
    except Exception as e:
        logger.error(f"Could not verify migration: {e}")


if __name__ == "__main__":
    migrate_results_to_database()