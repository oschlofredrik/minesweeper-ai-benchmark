#!/usr/bin/env python
"""Test to reproduce the pattern where AI only makes moves on the first row."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.games.tilts.board import TiltsBoard
from src.games.tilts.game import TiltsGame
from src.core.types import Position, Difficulty, ActionType
from src.models.factory import ModelFactory
from src.models.model_capabilities import MODEL_CAPABILITIES
from src.evaluation.streaming_runner import StreamingMinesweeperRunner
from src.core.logging_config import get_logger
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger("test_first_row")

async def test_first_row_pattern():
    """Test to see if AI exhibits first-row-only pattern."""
    
    # Create a test board with specific mine configuration
    board = TiltsBoard(rows=8, cols=8, mines=10, seed=42)
    game = TiltsGame(board=board)
    
    print("Initial board state:")
    print(game.get_board_state())
    print()
    
    # Get a model (use GPT-4 as example)
    model = ModelFactory.create_model("openai", "gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
    
    # Track moves made
    moves = []
    
    # Simulate 10 moves
    for move_num in range(1, 11):
        board_state = game.get_board_state()
        
        # Generate AI response
        try:
            response = await model.generate(
                board_state,
                use_functions=True
            )
            
            print(f"\nMove {move_num}:")
            print(f"Response: {response.content[:200]}...")
            
            # Parse the action from response
            if response.function_call:
                args = response.function_call.get("arguments", {})
                action_type = args.get("action", "").lower()
                row = args.get("row", -1)
                col = args.get("col", -1)
                
                print(f"Function call: {action_type} ({row}, {col})")
                moves.append((row, col))
                
                # Make the move
                if action_type == "reveal":
                    success, _ = game.reveal_cell(Position(row, col))
                elif action_type == "flag":
                    success = game.flag_cell(Position(row, col))
                    
                print(f"Move successful: {success}")
                
                # Check for pattern
                if len(moves) >= 3:
                    # Check if all moves are on row 0
                    if all(m[0] == 0 for m in moves[-3:]):
                        print("\n⚠️  PATTERN DETECTED: Last 3 moves all on row 0!")
                        print(f"Moves so far: {moves}")
                
            else:
                print("No function call in response!")
                
            # Show current board
            print("\nCurrent board:")
            print(game.get_board_state())
            
            # Check if game ended
            if game.is_game_over():
                print(f"\nGame ended: {'Won' if game.is_won() else 'Lost'}")
                break
                
        except Exception as e:
            print(f"Error during move {move_num}: {e}")
            logger.exception("Error details:")
            break
    
    # Analyze the pattern
    print("\n" + "="*50)
    print("MOVE ANALYSIS:")
    print(f"Total moves: {len(moves)}")
    print(f"Moves: {moves}")
    
    # Count moves by row
    row_counts = {}
    for row, col in moves:
        row_counts[row] = row_counts.get(row, 0) + 1
    
    print("\nMoves by row:")
    for row in sorted(row_counts.keys()):
        print(f"  Row {row}: {row_counts[row]} moves")
    
    # Check for sequential pattern
    sequential = True
    for i in range(1, len(moves)):
        if moves[i][0] != 0 or moves[i][1] != moves[i-1][1] + 1:
            sequential = False
            break
    
    if sequential and len(moves) > 2:
        print("\n⚠️  SEQUENTIAL PATTERN DETECTED!")
        print("AI is making moves sequentially along row 0!")

async def test_with_different_models():
    """Test the pattern with different models."""
    models_to_test = [
        ("gpt-4", "openai"),
        ("gpt-4o", "openai"),
        ("claude-3-5-sonnet-20241022", "anthropic"),
    ]
    
    for model_id, provider in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing with {model_id}")
        print('='*60)
        
        try:
            # Skip if no API key
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            if not api_key:
                print(f"Skipping {model_id} - no API key")
                continue
            
            model = ModelFactory.create_model(provider, model_id, api_key=api_key)
            
            # Create a simple test scenario
            board = TiltsBoard(rows=8, cols=8, mines=10, seed=42)
            game = TiltsGame(board=board)
            
            # Make first move to reveal some cells
            game.reveal_cell(Position(4, 4))
            
            moves = []
            for i in range(5):
                board_state = game.get_board_state()
                response = await model.generate(board_state, use_functions=True)
                
                if response.function_call:
                    args = response.function_call.get("arguments", {})
                    row = args.get("row", -1)
                    col = args.get("col", -1)
                    moves.append((row, col))
                    
                    # Make the move
                    action_type = args.get("action", "").lower()
                    if action_type == "reveal":
                        game.reveal_cell(Position(row, col))
                    elif action_type == "flag":
                        game.flag_cell(Position(row, col))
                
                if game.is_game_over():
                    break
            
            print(f"Moves made: {moves}")
            
            # Check for row 0 pattern
            row_0_moves = sum(1 for r, c in moves if r == 0)
            if row_0_moves >= 3:
                print(f"⚠️  Model tends to make moves on row 0: {row_0_moves}/{len(moves)} moves")
            
        except Exception as e:
            print(f"Error testing {model_id}: {e}")

async def test_board_representation():
    """Test how the board is represented to ensure coordinates are clear."""
    board = TiltsBoard(rows=5, cols=5, mines=5, seed=42)
    game = TiltsGame(board=board)
    
    # Make a few moves to create a test scenario
    game.reveal_cell(Position(2, 2))
    game.flag_cell(Position(0, 0))
    
    print("Board ASCII representation:")
    print(game.get_board_state())
    print()
    
    # Check column headers
    print("Analysis:")
    lines = game.get_board_state().split('\n')
    print(f"Column header: {lines[0]}")
    print(f"First data row: {lines[2]}")
    print()
    
    # Verify coordinates are clear
    print("The board uses 0-based indexing:")
    print("- Rows: 0 to 4 (top to bottom)")
    print("- Cols: 0 to 4 (left to right)")

if __name__ == "__main__":
    print("Testing first row pattern...")
    asyncio.run(test_first_row_pattern())
    
    print("\n\nTesting board representation...")
    asyncio.run(test_board_representation())
    
    print("\n\nTesting with different models...")
    asyncio.run(test_with_different_models())