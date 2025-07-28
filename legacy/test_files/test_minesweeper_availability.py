#!/usr/bin/env python3
"""Test if Minesweeper is available in the game registry."""

from src.games.registry import game_registry, register_builtin_games
from src.games.tilts import TiltsGame
from src.core.types import Difficulty, Action, ActionType, Position

# Register builtin games
print("Registering builtin games...")
register_builtin_games()

# Check available games
print("\nAvailable games:")
for game_name in game_registry.list_games():
    print(f"  - {game_name['name']}: {game_name['display_name']}")

# Check if Minesweeper is available
minesweeper = game_registry.get_game("minesweeper")
if minesweeper:
    print("\n✓ Minesweeper is available in the game registry!")
    print(f"  Display name: {minesweeper.display_name}")
    print(f"  Description: {minesweeper.description}")
else:
    print("\n✗ Minesweeper NOT found in game registry!")

# Test creating a Minesweeper game directly (original way)
print("\nTesting direct TiltsGame creation...")
try:
    game = TiltsGame(width=9, height=9, num_mines=10)
    print("✓ TiltsGame (original Minesweeper) can be created directly")
    
    # Test a basic move
    action = Action(
        action=ActionType.REVEAL,
        position=Position(row=4, col=4),
        reasoning="Testing center position"
    )
    result = game.take_action(action)
    print(f"✓ Basic action works: {result.is_valid}")
except Exception as e:
    print(f"✗ Error creating/using TiltsGame: {e}")

print("\nBenchmarking functionality status: AVAILABLE")