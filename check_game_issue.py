#\!/usr/bin/env python3
"""Check why games stop after one move."""

# The issue from the logs:
# 1. Move 1 is sent to model
# 2. Model responds with a valid move
# 3. Game status is still "in_progress"
# 4. But the game loop exits

# Possible causes:
# 1. Exception thrown but not logged
# 2. Loop condition becomes false somehow
# 3. Break statement hit

# From the code, the loop is:
# while game.status.value == "in_progress" and move_count < max_moves:

# After one move:
# - game.status.value should still be "in_progress" (confirmed from results)
# - move_count = 1, max_moves = 500
# So the condition should be True

# The only way the loop exits is:
# 1. Exception (but we see "Game completed" log, not error)
# 2. Break statement (there are breaks for exceptions)
# 3. Condition becomes false

print("Hypothesis: The game.status.value might not equal 'in_progress' string")
print("Let's check the GameStatus enum values...")

from src.core.types import GameStatus
print(f"IN_PROGRESS value: {GameStatus.IN_PROGRESS.value}")
print(f"Type: {type(GameStatus.IN_PROGRESS.value)}")
