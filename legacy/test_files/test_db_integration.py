"""Test database integration locally."""

import os
import asyncio
from datetime import datetime
from src.core.storage import get_storage
from src.core.types import GameResult, ModelConfig, Move, MoveType, EvaluationMetrics
from src.games.minesweeper import GameDifficulty

# Remove DATABASE_URL to test SQLite locally
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

async def test_storage():
    """Test the storage backend."""
    storage = get_storage()
    print(f"Using storage backend: {'Database' if storage.use_database else 'File'}")
    
    # Create a test game result
    model_config = ModelConfig(
        provider="openai",
        name="gpt-4",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create a sample game
    game_result = GameResult(
        game_id=f"test_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        model_config=model_config,
        difficulty=GameDifficulty.EXPERT.value,
        board_size=(16, 30),
        mine_count=99,
        moves=[
            Move(row=5, col=5, move_type=MoveType.REVEAL, reasoning="Starting move"),
            Move(row=5, col=6, move_type=MoveType.REVEAL, reasoning="Adjacent cell")
        ],
        won=False,
        num_moves=2,
        valid_moves=2,
        invalid_moves=0,
        flags_placed=0,
        cells_revealed=8,
        initial_board=[[0 for _ in range(30)] for _ in range(16)],
        final_board=None
    )
    
    # Test saving game
    print("\n1. Testing game save...")
    game_id = storage.save_game(game_result)
    print(f"   ✓ Saved game: {game_id}")
    
    # Test loading game
    print("\n2. Testing game load...")
    loaded_game = storage.load_game(game_id)
    if loaded_game:
        print(f"   ✓ Loaded game: {loaded_game.game_id}")
        print(f"   - Model: {loaded_game.model_config.name}")
        print(f"   - Moves: {loaded_game.num_moves}")
    else:
        print("   ✗ Failed to load game")
    
    # Test listing games
    print("\n3. Testing game list...")
    games = storage.list_games(limit=5)
    print(f"   ✓ Found {len(games)} games")
    for game in games[:3]:
        print(f"   - {game.get('game_id', 'Unknown')}: {game.get('model', {}).get('name', 'Unknown model')}")
    
    # Test evaluation save
    print("\n4. Testing evaluation save...")
    metrics = EvaluationMetrics(
        win_rate=0.5,
        valid_move_rate=0.95,
        mine_identification_precision=0.8,
        mine_identification_recall=0.7,
        board_coverage=0.6,
        efficiency_score=0.75,
        strategic_score=0.7,
        reasoning_score=0.8,
        composite_score=0.73
    )
    
    success = storage.save_evaluation(game_id, metrics, {"test": "data"}, 120.5)
    print(f"   {'✓' if success else '✗'} Saved evaluation")
    
    # Test task operations
    print("\n5. Testing task operations...")
    task_data = {
        "task_id": f"test_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "difficulty": "expert",
        "board_size": [16, 30],
        "mine_count": 99,
        "mine_positions": [[0, 0], [0, 1], [1, 1]],
        "initial_state": {}
    }
    
    task_id = storage.save_task(task_data)
    print(f"   ✓ Saved task: {task_id}")
    
    loaded_task = storage.load_task(task_id)
    if loaded_task:
        print(f"   ✓ Loaded task: {loaded_task['task_id']}")
    
    tasks = storage.list_tasks()
    print(f"   ✓ Found {len(tasks)} tasks")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_storage())