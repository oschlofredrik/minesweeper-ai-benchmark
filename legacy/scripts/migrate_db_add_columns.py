#!/usr/bin/env python3
"""
Database migration script to add missing columns.
Run this to update your database schema.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Convert postgres:// to postgresql:// for SQLAlchemy
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    return db_url


def add_column_if_not_exists(engine, table_name, column_name, column_type, default_value=None):
    """Add a column to a table if it doesn't exist."""
    inspector = inspect(engine)
    
    # Check if column exists
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name not in columns:
        logger.info(f"Adding column {column_name} to {table_name} table...")
        
        # Build the ALTER TABLE statement
        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            alter_stmt += f" DEFAULT {default_value}"
        
        try:
            with engine.connect() as conn:
                conn.execute(text(alter_stmt))
                conn.commit()
            logger.info(f"✓ Added column {column_name} to {table_name}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to add column {column_name}: {e}")
            return False
    else:
        logger.info(f"✓ Column {column_name} already exists in {table_name}")
        return True


def main():
    """Run the migration."""
    logger.info("Starting database migration...")
    
    # Get database connection
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        sys.exit(1)
    
    # Add missing columns
    migrations_successful = True
    
    # Add full_transcript to games table
    if not add_column_if_not_exists(
        engine, 
        'games', 
        'full_transcript', 
        'JSON',
        'NULL'
    ):
        migrations_successful = False
    
    # Add task_id to games table
    if not add_column_if_not_exists(
        engine, 
        'games', 
        'task_id', 
        'VARCHAR',
        'NULL'
    ):
        migrations_successful = False
    
    # Add job_id to games table
    if not add_column_if_not_exists(
        engine, 
        'games', 
        'job_id', 
        'VARCHAR',
        'NULL'
    ):
        migrations_successful = False
    
    # Add created_at to leaderboard_entries table if it doesn't exist
    if not add_column_if_not_exists(
        engine,
        'leaderboard_entries',
        'created_at',
        'TIMESTAMP',
        'CURRENT_TIMESTAMP'
    ):
        migrations_successful = False
    
    # Check if all migrations were successful
    if migrations_successful:
        logger.info("\n✓ All migrations completed successfully!")
        
        # Show current schema
        inspector = inspect(engine)
        
        logger.info("\nCurrent games table columns:")
        for col in inspector.get_columns('games'):
            logger.info(f"  - {col['name']}: {col['type']}")
        
        logger.info("\nCurrent leaderboard_entries table columns:")
        for col in inspector.get_columns('leaderboard_entries'):
            logger.info(f"  - {col['name']}: {col['type']}")
    else:
        logger.error("\n✗ Some migrations failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()