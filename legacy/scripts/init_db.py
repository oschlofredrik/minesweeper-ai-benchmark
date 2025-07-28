#!/usr/bin/env python3
"""Initialize database tables for Render deployment."""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def init_database():
    """Initialize database tables."""
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL", "")
    
    # Convert to asyncpg format if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    print(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Create tables
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id SERIAL PRIMARY KEY,
                model_name VARCHAR(255) NOT NULL,
                task_type VARCHAR(50) NOT NULL,
                difficulty VARCHAR(50) NOT NULL,
                metrics JSONB NOT NULL,
                game_results JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                evaluation_id VARCHAR(255) UNIQUE,
                prompt_template VARCHAR(255),
                model_config JSONB
            )
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_model_name ON evaluation_results(model_name);
            CREATE INDEX IF NOT EXISTS idx_created_at ON evaluation_results(created_at);
            CREATE INDEX IF NOT EXISTS idx_task_type ON evaluation_results(task_type);
        ''')
        
        print("✅ Database tables created successfully")
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())