"""Test OpenAI authentication."""

import os
import asyncio
from src.core.config import settings
from src.models import create_model
from src.core.types import ModelConfig

async def test_auth():
    """Test OpenAI authentication."""
    print("Testing OpenAI authentication...")
    print(f"API Key from settings: {settings.openai_api_key[:20]}..." if settings.openai_api_key else "No API key found!")
    print(f"API Key from env: {os.getenv('OPENAI_API_KEY', 'Not found')[:20]}...")
    
    # Create model config
    model_config = ModelConfig(
        name="gpt-3.5-turbo",
        provider="openai",
        model_id="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=100
    )
    
    try:
        # Create model and test
        model = create_model(model_config)
        print(f"Model created successfully")
        print(f"Model client API key: {model.client.api_key[:20]}..." if hasattr(model.client, 'api_key') else "Can't access API key")
        
        # Try a simple request
        response = await model.generate("Say 'Hello World'")
        print(f"Response: {response.content}")
        print("✅ Authentication successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth())