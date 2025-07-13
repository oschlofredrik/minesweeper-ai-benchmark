#!/usr/bin/env python3
"""Test API keys directly"""

import os
from dotenv import load_dotenv
import openai
import anthropic

load_dotenv()

print("Testing API Keys...")
print("=" * 50)

# Test OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI Key present: {bool(openai_key)}")
print(f"OpenAI Key starts with: {openai_key[:10] if openai_key else 'N/A'}...")

if openai_key:
    try:
        client = openai.OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )
        print("✓ OpenAI API key is valid!")
        print(f"  Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✗ OpenAI API key error: {e}")

print("\n" + "-" * 50 + "\n")

# Test Anthropic
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
print(f"Anthropic Key present: {bool(anthropic_key)}")
print(f"Anthropic Key starts with: {anthropic_key[:10] if anthropic_key else 'N/A'}...")

if anthropic_key:
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )
        print("✓ Anthropic API key is valid!")
        print(f"  Response: {response.content[0].text}")
    except Exception as e:
        print(f"✗ Anthropic API key error: {e}")