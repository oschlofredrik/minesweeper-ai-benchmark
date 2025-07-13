"""Diagnose environment variable loading."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=== Environment Variable Diagnostics ===\n")

# Check raw environment variables
print("1. Raw environment variables:")
print(f"   OPENAI_API_KEY from os.environ: {os.environ.get('OPENAI_API_KEY', 'NOT SET')[:20]}...")
print(f"   ANTHROPIC_API_KEY from os.environ: {os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')[:20]}...")
print(f"   DATABASE_URL from os.environ: {os.environ.get('DATABASE_URL', 'NOT SET')[:30]}...")

# Check if .env file exists
env_file = Path(".env")
print(f"\n2. .env file exists: {env_file.exists()}")
if env_file.exists():
    with open(env_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('OPENAI_API_KEY'):
                print(f"   .env OPENAI_API_KEY: {line.split('=')[1][:20].strip()}...")
                break

# Import settings AFTER checking raw env vars
from src.core.config import settings

print("\n3. Settings object values:")
print(f"   settings.openai_api_key: {settings.openai_api_key[:20] if settings.openai_api_key else 'None'}...")
print(f"   settings.anthropic_api_key: {settings.anthropic_api_key[:20] if settings.anthropic_api_key else 'None'}...")
print(f"   settings.database_url: {settings.database_url[:30]}...")

# Check Pydantic settings config
print("\n4. Pydantic Settings configuration:")
print(f"   env_file: {settings.model_config.get('env_file')}")
print(f"   case_sensitive: {settings.model_config.get('case_sensitive')}")

# Test with explicit environment variable
print("\n5. Testing with explicit env var:")
os.environ['TEST_API_KEY'] = 'test-key-from-environ'

# Create a test settings class
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    test_api_key: str = "default-value"
    
    class Config:
        env_file = ".env"

test_settings = TestSettings()
print(f"   test_api_key: {test_settings.test_api_key}")

print("\n=== Diagnosis Complete ===")
print("\nIf you're on Render and env vars aren't loading:")
print("1. Check that env vars are set in Render dashboard")
print("2. Ensure no .env file is deployed (it should be in .gitignore)")
print("3. Verify that system env vars take precedence over .env file")