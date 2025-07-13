#!/usr/bin/env python3
"""Diagnose API key issues for the Minesweeper benchmark."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Check environment setup."""
    print("🔍 Checking environment setup...")
    
    # Check if .env exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        print("   Create one by copying .env.example:")
        print("   cp .env.example .env")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print("\n🔑 Checking API keys...")
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY is set (starts with: {openai_key[:10]}...)")
        if not openai_key.startswith("sk-"):
            print("   ⚠️  Key doesn't start with 'sk-', might be invalid")
    else:
        print("❌ OPENAI_API_KEY is not set")
    
    if anthropic_key:
        print(f"✅ ANTHROPIC_API_KEY is set (starts with: {anthropic_key[:10]}...)")
        if not anthropic_key.startswith("sk-ant-"):
            print("   ⚠️  Key doesn't start with 'sk-ant-', might be invalid")
    else:
        print("❌ ANTHROPIC_API_KEY is not set")
    
    return bool(openai_key or anthropic_key)


def test_openai_key():
    """Test OpenAI API key."""
    print("\n🧪 Testing OpenAI API key...")
    
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ No OpenAI API key found")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Try to list models
        try:
            response = client.models.list()
            models = [m.id for m in list(response)[:5]]
            print(f"✅ OpenAI API key is valid!")
            print(f"   Available models: {models}")
            return True
        except Exception as e:
            if "401" in str(e):
                print("❌ OpenAI API key is invalid or expired")
                print(f"   Error: {str(e)[:200]}...")
                print("\n   Get a new API key from: https://platform.openai.com/api-keys")
            else:
                print(f"❌ OpenAI API error: {str(e)[:200]}...")
            return False
    except ImportError:
        print("❌ OpenAI package not installed")
        print("   Run: pip install openai")
        return False


def test_anthropic_key():
    """Test Anthropic API key."""
    print("\n🧪 Testing Anthropic API key...")
    
    try:
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("❌ No Anthropic API key found")
            return False
        
        client = Anthropic(api_key=api_key)
        
        # Try a simple completion
        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print("✅ Anthropic API key is valid!")
            return True
        except Exception as e:
            if "401" in str(e) or "authentication" in str(e).lower():
                print("❌ Anthropic API key is invalid or expired")
                print(f"   Error: {str(e)[:200]}...")
                print("\n   Get a new API key from: https://console.anthropic.com/settings/keys")
            else:
                print(f"❌ Anthropic API error: {str(e)[:200]}...")
            return False
    except ImportError:
        print("❌ Anthropic package not installed")
        print("   Run: pip install anthropic")
        return False


def suggest_fixes():
    """Suggest fixes for common issues."""
    print("\n💡 Suggested fixes:")
    print("1. Update your .env file with valid API keys")
    print("2. For OpenAI: Get a key from https://platform.openai.com/api-keys")
    print("3. For Anthropic: Get a key from https://console.anthropic.com/settings/keys")
    print("4. Make sure your API keys have sufficient credits/quota")
    print("5. Check that the keys are correctly formatted (no extra spaces)")
    print("\nExample .env file:")
    print("```")
    print("OPENAI_API_KEY=sk-...")
    print("ANTHROPIC_API_KEY=sk-ant-...")
    print("```")


def main():
    """Run diagnostics."""
    print("🏁 Minesweeper Benchmark API Diagnostics")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ Environment setup incomplete")
        suggest_fixes()
        return
    
    # Test API keys
    openai_ok = test_openai_key()
    anthropic_ok = test_anthropic_key()
    
    # Summary
    print("\n📊 Summary")
    print("=" * 50)
    
    if openai_ok and anthropic_ok:
        print("✅ All API keys are valid and working!")
        print("\nYou can now run evaluations with:")
        print("  python -m src.cli.main evaluate --model gpt-4 --num-games 10")
        print("  python -m src.cli.main evaluate --model claude-3-opus-20240229 --num-games 10")
    elif openai_ok:
        print("✅ OpenAI API key is valid")
        print("❌ Anthropic API key is invalid or missing")
        print("\nYou can run evaluations with OpenAI models:")
        print("  python -m src.cli.main evaluate --model gpt-4 --num-games 10")
    elif anthropic_ok:
        print("❌ OpenAI API key is invalid or missing")
        print("✅ Anthropic API key is valid")
        print("\nYou can run evaluations with Anthropic models:")
        print("  python -m src.cli.main evaluate --model claude-3-opus-20240229 --num-games 10")
    else:
        print("❌ No valid API keys found")
        suggest_fixes()


if __name__ == "__main__":
    main()