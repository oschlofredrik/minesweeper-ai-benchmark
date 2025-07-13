#!/usr/bin/env python3
"""Quick test to verify local environment is set up correctly."""

import sys
import os

print("🔍 Testing local environment setup...")
print("=" * 50)

# Check Python version
print(f"✓ Python version: {sys.version.split()[0]}")
if sys.version_info < (3, 11):
    print("  ⚠️  Warning: Python 3.11+ recommended")

# Check if we can import main modules
try:
    from src.api.main import app
    print("✓ FastAPI app imports correctly")
except ImportError as e:
    print(f"✗ Error importing FastAPI app: {e}")
    print("  Try: export PYTHONPATH=\"${PYTHONPATH}:$(pwd)\"")

# Check for .env file
if os.path.exists(".env"):
    print("✓ .env file exists")
    
    # Check for API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    has_openai = bool(os.getenv("OPENAI_API_KEY", "").strip())
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    
    if has_openai:
        print("✓ OPENAI_API_KEY is set")
    else:
        print("✗ OPENAI_API_KEY is missing")
    
    if has_anthropic:
        print("✓ ANTHROPIC_API_KEY is set") 
    else:
        print("⚠️  ANTHROPIC_API_KEY is missing (optional)")
else:
    print("✗ .env file not found")
    print("  Run: cp .env.example .env")

# Check directories
dirs = ["data/tasks", "data/results", "data/logs"]
for dir_path in dirs:
    if os.path.exists(dir_path):
        print(f"✓ Directory exists: {dir_path}")
    else:
        print(f"⚠️  Creating directory: {dir_path}")
        os.makedirs(dir_path, exist_ok=True)

print("=" * 50)
print("\nIf all checks pass, run: ./run-local.sh")