"""Simple environment check."""

import os

print("Direct environment variable check:")
print(f"OPENAI_API_KEY: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")
print(f"ANTHROPIC_API_KEY: {'SET' if os.environ.get('ANTHROPIC_API_KEY') else 'NOT SET'}")

# Now test what happens when we set it
os.environ['OPENAI_API_KEY'] = 'test-key-123'

from src.core.config import settings

print(f"\nAfter setting in os.environ:")
print(f"settings.openai_api_key: {settings.openai_api_key[:20] if settings.openai_api_key else 'None'}...")

# The issue: Pydantic Settings is already initialized with values from .env
# Let's force a reload
from importlib import reload
import src.core.config

# This won't work because settings is already instantiated
print("\nThe issue: settings object is already created with .env values")
print("On Render, if .env doesn't exist, it should use env vars properly")