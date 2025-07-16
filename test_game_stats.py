#!/usr/bin/env python3
"""Test the game stats display functionality."""

import asyncio
import json
from src.api.event_streaming import publish_event, EventType

async def test_game_stats():
    """Simulate a game with events to test stats display."""
    job_id = "test-stats-123"
    
    print("Testing game stats display...")
    print("1. Publishing game_started event...")
    
    # Game started event
    await publish_event(job_id, EventType.GAME_STARTED, {
        "game_num": 1,
        "task_id": "test-task",
        "difficulty": "intermediate",
        "board_size": "16x16",
        "num_mines": 40,
        "message": "Starting game 1"
    })
    
    await asyncio.sleep(1)
    
    print("2. Publishing initial board_update...")
    
    # Initial board state
    await publish_event(job_id, EventType.BOARD_UPDATE, {
        "game_num": 1,
        "board_data": {
            "board_size": {"rows": 16, "cols": 16},
            "revealed": [],
            "flagged": []
        },
        "message": "Initial board state"
    })
    
    await asyncio.sleep(1)
    
    print("3. Simulating moves with board updates...")
    
    # Simulate some moves
    revealed_cells = []
    for move_num in range(1, 6):
        # Add some revealed cells
        for i in range(3):
            revealed_cells.append({
                "row": move_num - 1,
                "col": i,
                "value": 0 if i == 0 else i
            })
        
        await publish_event(job_id, EventType.MOVE_COMPLETED, {
            "game_num": 1,
            "move_num": move_num,
            "action": f"reveal ({move_num-1}, 0)",
            "success": True,
            "message": f"Move {move_num} completed"
        })
        
        await asyncio.sleep(0.5)
        
        # Board update after move
        await publish_event(job_id, EventType.BOARD_UPDATE, {
            "game_num": 1,
            "move_num": move_num,
            "board_data": {
                "board_size": {"rows": 16, "cols": 16},
                "revealed": revealed_cells,
                "flagged": []
            },
            "last_move": {
                "action": "reveal",
                "row": move_num - 1,
                "col": 0
            },
            "message": f"Board after move {move_num}"
        })
        
        await asyncio.sleep(0.5)
        
        # Metrics update
        await publish_event(job_id, EventType.METRICS_UPDATE, {
            "games_completed": 0,
            "games_total": 5,
            "win_rate": 0.0,
            "avg_moves": move_num,
            "progress": 0.0
        })
        
        await asyncio.sleep(1)
    
    print("4. Publishing game completion...")
    
    # Game completed
    await publish_event(job_id, EventType.GAME_COMPLETED, {
        "game_num": 1,
        "won": False,
        "moves": 5,
        "coverage": len(revealed_cells) / 256.0,
        "duration": 10.5,
        "total_games": 5
    })
    
    print("\nTest complete! Check the browser to see if:")
    print("- Game stats are displayed above the board")
    print("- Current moves count updates with each move")
    print("- Board coverage percentage updates as cells are revealed")
    print("- Win rate updates from metrics events")

if __name__ == "__main__":
    asyncio.run(test_game_stats())