"""Simple test to verify database setup."""

import os
from src.core.database import init_db, get_db, Game, Task
from datetime import datetime

# Test SQLite locally
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

def test_database():
    """Test basic database operations."""
    print("Initializing database...")
    engine = init_db()
    print(f"Database initialized: {engine.url}")
    
    # Get a session
    db = next(get_db())
    
    try:
        # Test creating a game
        game = Game(
            id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_provider="openai",
            model_name="gpt-4",
            difficulty="expert",
            rows=16,
            cols=30,
            mines=99,
            initial_board=[],
            moves=[],
            won=False,
            num_moves=0,
            valid_moves=0,
            invalid_moves=0,
            flags_placed=0,
            cells_revealed=0
        )
        
        db.add(game)
        db.commit()
        print(f"✓ Created game: {game.id}")
        
        # Test querying
        games = db.query(Game).all()
        print(f"✓ Found {len(games)} games in database")
        
        # Test creating a task
        task = Task(
            id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            difficulty="expert",
            rows=16,
            cols=30,
            mines=99,
            mine_positions=[],
            initial_state={}
        )
        
        db.add(task)
        db.commit()
        print(f"✓ Created task: {task.id}")
        
        print("\n✅ Database is working correctly!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database()