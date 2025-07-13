#!/usr/bin/env python3
"""Test API keys for OpenAI and Anthropic."""

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Load environment variables
load_dotenv()

async def test_openai():
    """Test OpenAI API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key not found in environment")
        return False
    
    print(f"Testing OpenAI API key: {api_key[:20]}...")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI API key is valid! Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API key is invalid: {e}")
        return False

async def test_anthropic():
    """Test Anthropic API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Anthropic API key not found in environment")
        return False
    
    print(f"\nTesting Anthropic API key: {api_key[:20]}...")
    
    try:
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            max_tokens=10
        )
        print(f"✅ Anthropic API key is valid! Response: {response.content[0].text}")
        return True
    except Exception as e:
        print(f"❌ Anthropic API key is invalid: {e}")
        return False

async def main():
    """Test both API keys."""
    print("Testing API Keys...")
    print("=" * 50)
    
    openai_valid = await test_openai()
    anthropic_valid = await test_anthropic()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"OpenAI: {'✅ Valid' if openai_valid else '❌ Invalid'}")
    print(f"Anthropic: {'✅ Valid' if anthropic_valid else '❌ Invalid'}")
    
    if not openai_valid or not anthropic_valid:
        print("\n⚠️  Please update your .env file with valid API keys")
        print("You can get API keys from:")
        print("- OpenAI: https://platform.openai.com/api-keys")
        print("- Anthropic: https://console.anthropic.com/settings/keys")

if __name__ == "__main__":
    asyncio.run(main())