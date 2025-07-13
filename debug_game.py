#!/usr/bin/env python3
"""Debug script to see why games stop after one move."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.types import ModelConfig, Difficulty
from src.tasks import TaskGenerator
from src.evaluation import GameRunner
from src.games.minesweeper import MinesweeperGame
from src.core.logging_config import setup_logging

async def debug_game():
    """Debug a single game."""
    
    # Setup logging
    setup_logging(log_level="DEBUG", enable_console=True)
    
    print("\n=== Debugging Game Flow ===\n")
    
    # Generate a test task
    generator = TaskGenerator()
    task = generator.generate_interactive_task(difficulty=Difficulty.BEGINNER)
    
    # Create a simple model config
    model_config = ModelConfig(
        name="gpt-3.5-turbo",
        provider="openai", 
        model_id="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500
    )
    
    # Create runner
    runner = GameRunner(model_config)
    
    # Run the game with verbose output
    print("Starting game...")
    transcript = await runner.run_game(
        task=task,
        max_moves=10,  # Limit to 10 moves for debugging
        verbose=True
    )
    
    print(f"\n=== Game Summary ===")
    print(f"Game ID: {transcript.game_id}")
    print(f"Final status: {transcript.final_state.status.value}")
    print(f"Total moves: {len(transcript.moves)}")
    print(f"Board coverage: {transcript.final_state.board_coverage:.1%}" if hasattr(transcript.final_state, 'board_coverage') else "N/A")
    
    # Print move details
    print(f"\n=== Move Details ===")
    for i, move in enumerate(transcript.moves):
        print(f"\nMove {i+1}:")
        print(f"  Action: {move.action.to_string()}")
        print(f"  Valid: {move.was_valid}")
        if move.error_message:
            print(f"  Error: {move.error_message}")
        if move.reasoning:
            print(f"  Reasoning: {move.reasoning[:100]}...")

if __name__ == "__main__":
    asyncio.run(debug_game())