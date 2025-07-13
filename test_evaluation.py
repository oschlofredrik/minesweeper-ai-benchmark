#!/usr/bin/env python3
"""Test script to verify evaluations are working properly."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.types import ModelConfig, Difficulty
from src.tasks import TaskGenerator
from src.evaluation import EvaluationEngine
from src.core.logging_config import setup_logging

async def test_evaluation():
    """Run a simple evaluation test."""
    
    # Setup logging
    setup_logging(log_level="DEBUG", enable_console=True)
    
    print("\n=== Minesweeper AI Evaluation Test ===\n")
    
    # Generate a simple test task
    print("1. Generating test task...")
    generator = TaskGenerator()
    task = generator.generate_interactive_task(difficulty=Difficulty.BEGINNER)
    print(f"   ✓ Generated {task.difficulty.value} task with {task.board_config['rows']}x{task.board_config['cols']} board")
    
    # Test OpenAI model
    print("\n2. Testing OpenAI integration...")
    try:
        openai_config = ModelConfig(
            name="gpt-3.5-turbo",
            provider="openai",
            model_id="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500
        )
        
        engine = EvaluationEngine()
        results = await engine.evaluate_model(
            model_config=openai_config,
            tasks=[task],
            max_moves=50,
            verbose=True
        )
        
        print(f"\n   ✓ OpenAI evaluation completed!")
        print(f"   - Win rate: {results['metrics']['win_rate']:.1%}")
        print(f"   - Valid moves: {results['metrics']['valid_move_rate']:.1%}")
        
        # Check if we have detailed move data
        if results.get('game_results') and len(results['game_results']) > 0:
            game = results['game_results'][0]
            print(f"   - Moves made: {game['num_moves']}")
            if game.get('moves') and len(game['moves']) > 0:
                print(f"   - First move had prompt: {'Yes' if game['moves'][0].get('prompt_sent') else 'No'}")
                print(f"   - First move had response: {'Yes' if game['moves'][0].get('full_response') else 'No'}")
                print(f"   - First move had reasoning: {'Yes' if game['moves'][0].get('reasoning') else 'No'}")
        
    except Exception as e:
        print(f"   ✗ OpenAI test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Anthropic model
    print("\n3. Testing Anthropic integration...")
    try:
        anthropic_config = ModelConfig(
            name="claude-3-haiku-20240307",
            provider="anthropic",
            model_id="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=500
        )
        
        engine = EvaluationEngine()
        results = await engine.evaluate_model(
            model_config=anthropic_config,
            tasks=[task],
            max_moves=50,
            verbose=True
        )
        
        print(f"\n   ✓ Anthropic evaluation completed!")
        print(f"   - Win rate: {results['metrics']['win_rate']:.1%}")
        print(f"   - Valid moves: {results['metrics']['valid_move_rate']:.1%}")
        
        # Check if we have detailed move data
        if results.get('game_results') and len(results['game_results']) > 0:
            game = results['game_results'][0]
            print(f"   - Moves made: {game['num_moves']}")
            if game.get('moves') and len(game['moves']) > 0:
                print(f"   - First move had prompt: {'Yes' if game['moves'][0].get('prompt_sent') else 'No'}")
                print(f"   - First move had response: {'Yes' if game['moves'][0].get('full_response') else 'No'}")
                print(f"   - First move had reasoning: {'Yes' if game['moves'][0].get('reasoning') else 'No'}")
        
    except Exception as e:
        print(f"   ✗ Anthropic test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===\n")
    print("Check the logs in data/logs/ for detailed API interaction logs.")

if __name__ == "__main__":
    asyncio.run(test_evaluation())