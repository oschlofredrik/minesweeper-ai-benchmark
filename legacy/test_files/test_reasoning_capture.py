#!/usr/bin/env python3
"""Test script to verify reasoning capture with function calling."""

import asyncio
import json
from src.models.openai import OpenAIModel
from src.models.anthropic import AnthropicModel
from src.core.config import settings

# Test board state
TEST_BOARD = """  0  1  2  3  4  5  6  7  8
0| 1  1  .  .  .  .  .  .  .
1| ?  1  .  .  .  .  .  .  .
2| ?  1  .  .  1  1  1  .  .
3| ?  1  .  .  1  ?  1  .  .
4| ?  1  .  .  1  1  1  .  .
5| ?  1  .  .  .  .  .  .  .
6| ?  ?  1  .  .  .  .  .  .
7| ?  ?  1  .  .  .  .  .  .
8| ?  ?  1  .  .  .  .  .  ."""

async def test_model(model_name: str, model_class):
    """Test a model's reasoning capture."""
    print(f"\n{'='*60}")
    print(f"Testing {model_name}")
    print('='*60)
    
    try:
        # Initialize model
        if model_class == OpenAIModel:
            model = model_class({"model_id": model_name, "api_key": settings.openai_api_key})
        else:
            model = model_class({"model_id": model_name, "api_key": settings.anthropic_api_key})
        
        # Generate response
        response = await model.generate(TEST_BOARD, use_functions=True, use_tools=True)
        
        print(f"\n📝 Full Content (length: {len(response.content)}):")
        print("-" * 40)
        print(response.content[:500] + "..." if len(response.content) > 500 else response.content)
        
        if response.reasoning:
            print(f"\n🧠 Captured Reasoning (length: {len(response.reasoning)}):")
            print("-" * 40)
            print(response.reasoning[:500] + "..." if len(response.reasoning) > 500 else response.reasoning)
        
        if response.function_call:
            print(f"\n🔧 Function Call:")
            print("-" * 40)
            print(json.dumps(response.function_call, indent=2))
        
        if response.action:
            print(f"\n🎯 Parsed Action:")
            print("-" * 40)
            print(response.action.to_string())
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run tests on different models."""
    print("Testing reasoning capture with function calling\n")
    
    # Test OpenAI models
    if settings.openai_api_key:
        await test_model("gpt-4-0125-preview", OpenAIModel)
        # await test_model("gpt-3.5-turbo", OpenAIModel)
    
    # Test Anthropic models
    if settings.anthropic_api_key:
        await test_model("claude-3-opus-20240229", AnthropicModel)
        # await test_model("claude-3-sonnet-20240229", AnthropicModel)

if __name__ == "__main__":
    asyncio.run(main())