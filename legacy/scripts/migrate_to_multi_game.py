#!/usr/bin/env python3
"""Script to migrate database to multi-game support."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from src.core.config import settings
from src.core.database_models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database_exists():
    """Check if database exists and has tables."""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Check if any tables exist
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            ))
            tables = [row[0] for row in result]
            logger.info(f"Existing tables: {tables}")
            return len(tables) > 0
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False


def backup_database():
    """Create a backup of the existing database."""
    if settings.database_url.startswith('sqlite:///'):
        db_path = settings.database_url.replace('sqlite:///', '')
        if os.path.exists(db_path):
            import shutil
            backup_path = f"{db_path}.backup"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")


def run_migration():
    """Run the Alembic migration."""
    try:
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Run the migration
        logger.info("Running database migration...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def populate_game_registry():
    """Populate the games registry with available games."""
    from sqlalchemy.orm import sessionmaker
    from src.core.database_models import GameRegistry
    
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if games already exist
        existing = session.query(GameRegistry).first()
        if existing:
            logger.info("Games registry already populated")
            return
        
        # Add Minesweeper
        minesweeper = GameRegistry(
            game_name='minesweeper',
            display_name='Minesweeper',
            description='Classic logic puzzle where players uncover cells while avoiding hidden mines',
            supported_modes=['speed', 'accuracy', 'efficiency', 'reasoning', 'mixed'],
            scoring_components=[
                {'name': 'completion', 'weight': 0.2},
                {'name': 'speed', 'weight': 0.2},
                {'name': 'accuracy', 'weight': 0.2},
                {'name': 'efficiency', 'weight': 0.2},
                {'name': 'mine_detection', 'weight': 0.2}
            ],
            is_active=True
        )
        session.add(minesweeper)
        
        # Add Number Puzzle
        number_puzzle = GameRegistry(
            game_name='number_puzzle',
            display_name='Number Puzzle',
            description='Guess the target number using binary search strategy',
            supported_modes=['speed', 'efficiency', 'reasoning', 'mixed'],
            scoring_components=[
                {'name': 'completion', 'weight': 0.25},
                {'name': 'speed', 'weight': 0.25},
                {'name': 'efficiency', 'weight': 0.25},
                {'name': 'reasoning', 'weight': 0.25}
            ],
            is_active=True
        )
        session.add(number_puzzle)
        
        session.commit()
        logger.info("Games registry populated successfully")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to populate games registry: {e}")
    finally:
        session.close()


def update_existing_data():
    """Update existing data to work with multi-game schema."""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Update existing games to have game_name
            conn.execute(text(
                "UPDATE games SET game_name = 'minesweeper' WHERE game_name IS NULL"
            ))
            conn.commit()
            
            # Update existing leaderboard entries
            conn.execute(text(
                "UPDATE leaderboard_entries SET game_name = 'minesweeper' WHERE game_name IS NULL"
            ))
            conn.commit()
            
            logger.info("Existing data updated successfully")
            
    except Exception as e:
        logger.error(f"Failed to update existing data: {e}")


def verify_migration():
    """Verify the migration was successful."""
    engine = create_engine(settings.database_url)
    
    expected_tables = [
        'games_registry',
        'competition_sessions',
        'session_rounds',
        'session_players',
        'prompt_library',
        'spectator_sessions',
        'scoring_profiles',
        'player_profiles',
        'queue_items'
    ]
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            ))
            actual_tables = [row[0] for row in result]
            
            missing_tables = set(expected_tables) - set(actual_tables)
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                return False
            
            logger.info("All expected tables exist")
            
            # Check columns in games table
            result = conn.execute(text("PRAGMA table_info(games)"))
            columns = [row[1] for row in result]
            
            expected_columns = ['game_name', 'session_id', 'round_number', 'ai_model']
            missing_columns = set(expected_columns) - set(columns)
            
            if missing_columns:
                logger.warning(f"Missing columns in games table: {missing_columns}")
                return False
            
            logger.info("Database migration verified successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


def main():
    """Main migration function."""
    logger.info("Starting database migration to multi-game support...")
    
    # Check if database exists
    if not check_database_exists():
        logger.info("No existing database found. Creating new database...")
        # Create all tables from scratch
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(engine)
        populate_game_registry()
        logger.info("Database created successfully!")
        return
    
    # Backup existing database
    backup_database()
    
    # Run migration
    try:
        run_migration()
        
        # Populate game registry
        populate_game_registry()
        
        # Update existing data
        update_existing_data()
        
        # Verify migration
        if verify_migration():
            logger.info("Migration completed successfully!")
        else:
            logger.warning("Migration completed with warnings. Please check the logs.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.info("Database backup is available if needed.")
        raise


if __name__ == "__main__":
    main()