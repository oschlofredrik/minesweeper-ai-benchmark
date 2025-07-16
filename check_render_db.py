#!/usr/bin/env python3
"""Check Render PostgreSQL database schema and tables."""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database():
    """Check database connection and schema."""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Please set it in .env file or environment")
        return
    
    print(f"📡 Connecting to database...")
    print(f"   URL: {db_url[:30]}...")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Successfully connected to database!")
            
            # Get inspector
            inspector = inspect(engine)
            
            # List all tables
            tables = inspector.get_table_names()
            print(f"\n📋 Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
            
            # Check for expected tables
            expected_tables = ['games', 'leaderboard_entries', 'evaluations', 'tasks']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
            else:
                print("\n✅ All expected tables exist!")
            
            # Check leaderboard_entries schema
            if 'leaderboard_entries' in tables:
                print("\n📊 leaderboard_entries schema:")
                columns = inspector.get_columns('leaderboard_entries')
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
                
                # Count entries
                result = conn.execute(text("SELECT COUNT(*) FROM leaderboard_entries"))
                count = result.scalar()
                print(f"\n   Total entries: {count}")
                
                # Show sample data
                if count > 0:
                    result = conn.execute(text("""
                        SELECT model_name, win_rate, total_games 
                        FROM leaderboard_entries 
                        ORDER BY updated_at DESC 
                        LIMIT 5
                    """))
                    print("\n   Recent entries:")
                    for row in result:
                        print(f"   - {row.model_name}: {row.win_rate:.1%} win rate, {row.total_games} games")
            
            # Check games table
            if 'games' in tables:
                print("\n🎮 games table:")
                result = conn.execute(text("SELECT COUNT(*) FROM games"))
                game_count = result.scalar()
                print(f"   Total games: {game_count}")
                
                # Check recent games
                result = conn.execute(text("""
                    SELECT model_name, won, num_moves, created_at 
                    FROM games 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                print("\n   Recent games:")
                for row in result:
                    status = "Won" if row.won else "Lost"
                    print(f"   - {row.model_name}: {status} in {row.num_moves} moves")
            
            # Check if migrations are needed
            print("\n🔧 Checking for missing columns...")
            
            # Check games table for new columns
            if 'games' in tables:
                columns = [col['name'] for col in inspector.get_columns('games')]
                new_columns = ['status', 'error_message', 'full_transcript', 'task_id', 'job_id']
                missing_cols = [c for c in new_columns if c not in columns]
                if missing_cols:
                    print(f"   games table missing columns: {', '.join(missing_cols)}")
                    print("   Run: python scripts/migrate_db_add_columns.py")
            
            # Check leaderboard_entries for created_at
            if 'leaderboard_entries' in tables:
                columns = [col['name'] for col in inspector.get_columns('leaderboard_entries')]
                if 'created_at' not in columns:
                    print("   leaderboard_entries missing created_at column")
                    print("   Run: python scripts/migrate_db_add_columns.py")
                    
    except SQLAlchemyError as e:
        print(f"\n❌ Database error: {type(e).__name__}")
        print(f"   {str(e)}")
        
        # Common issues
        if "could not translate host name" in str(e):
            print("\n💡 This usually means:")
            print("   1. DATABASE_URL is pointing to a Render internal URL")
            print("   2. You're running this locally (not on Render)")
            print("   3. Use the external database URL for local testing")
        elif "password authentication failed" in str(e):
            print("\n💡 Authentication failed. Check your DATABASE_URL credentials")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    check_database()