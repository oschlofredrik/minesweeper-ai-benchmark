#!/usr/bin/env python3
"""Test function calling with OpenAI and Anthropic models."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.types import ModelConfig
from src.models import create_model
from src.core.logging_config import setup_logging

async def test_function_calling():
    """Test function calling with both providers."""
    
    # Setup logging
    setup_logging(log_level="INFO", enable_console=True)
    
    # Test board state
    board_state = """    0  1  2  3  4  5  6  7  8
   --------------------------
 0| ? ? ? ? ? ? ? ? ?
 1| ? 1 . . . . . 1 ?
 2| ? 1 . . . . . 1 ?
 3| ? 1 . . . . . 1 ?
 4| ? 1 . . . . . 1 ?
 5| ? 1 . . . . . 1 ?
 6| ? 1 . . . . . 1 ?
 7| ? 1 . . . . . 1 ?
 8| ? ? ? ? ? ? ? ? ?"""

    print("\n=== Testing Function Calling ===\n")
    
    # Test OpenAI
    print("1. Testing OpenAI with function calling...")
    try:
        openai_config = ModelConfig(
            name="gpt-3.5-turbo",
            provider="openai",
            model_id="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500
        )
        
        model = create_model(openai_config)
        response = await model.play_move(board_state, "standard")
        
        print(f"   Response received:")
        print(f"   - Has function call: {response.function_call is not None}")
        if response.function_call:
            print(f"   - Action: {response.function_call.get('action')}")
            print(f"   - Position: ({response.function_call.get('row')}, {response.function_call.get('col')})")
            print(f"   - Reasoning: {response.function_call.get('reasoning', '')[:100]}...")
        print(f"   - Parsed action: {response.action.to_string() if response.action else 'None'}")
        print(f"   - Content: {response.content[:100]}...")
        
    except Exception as e:
        print(f"   ✗ OpenAI test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testing Anthropic with tool use...")
    try:
        anthropic_config = ModelConfig(
            name="claude-3-haiku-20240307",
            provider="anthropic",
            model_id="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=500
        )
        
        model = create_model(anthropic_config)
        response = await model.play_move(board_state, "standard")
        
        print(f"   Response received:")
        print(f"   - Has function call: {response.function_call is not None}")
        if response.function_call:
            print(f"   - Action: {response.function_call.get('action')}")
            print(f"   - Position: ({response.function_call.get('row')}, {response.function_call.get('col')})")
            print(f"   - Reasoning: {response.function_call.get('reasoning', '')[:100]}...")
        print(f"   - Parsed action: {response.action.to_string() if response.action else 'None'}")
        print(f"   - Content: {response.content[:100]}...")
        
    except Exception as e:
        print(f"   ✗ Anthropic test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Function Calling Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_function_calling())