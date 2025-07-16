#!/usr/bin/env python3
"""Test to verify function calling is working from CLI."""

import asyncio
import sys
from src.models.openai import OpenAIModel
from src.core.config import settings

async def test_function_calling():
    """Test function calling with different prompt formats."""
    
    if not settings.openai_api_key:
        print("❌ No OpenAI API key found!")
        return
        
    # Test board
    board_state = """  0  1  2  3  4
0| ?  ?  ?  ?  ?
1| ?  1  ?  ?  ?
2| ?  ?  ?  ?  ?
3| ?  ?  ?  ?  ?
4| ?  ?  ?  ?  ?"""
    
    model = OpenAIModel({
        "model_id": "gpt-4-0125-preview",
        "api_key": settings.openai_api_key,
        "temperature": 0.7
    })
    
    print("Testing with prompt_format='standard' and use_functions=True")
    print("-" * 60)
    
    try:
        # This should use function calling
        response = await model.play_move(board_state, prompt_format="standard", use_functions=True)
        
        print(f"✅ Response received!")
        print(f"Has function call: {response.function_call is not None}")
        print(f"Has action: {response.action is not None}")
        if response.function_call:
            print(f"Function call: {response.function_call}")
        if response.action:
            print(f"Action: {response.action.to_string()}")
        print(f"Content length: {len(response.content) if response.content else 0}")
        print(f"Reasoning length: {len(response.reasoning) if response.reasoning else 0}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_function_calling())