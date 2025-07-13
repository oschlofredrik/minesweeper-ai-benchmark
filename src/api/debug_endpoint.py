"""Debug endpoint to check environment variables in production."""

from fastapi import APIRouter
from src.core.config import settings
import os

router = APIRouter()

@router.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables (REMOVE IN PRODUCTION)."""
    
    # Check if we're in production
    is_production = os.environ.get('ENVIRONMENT') == 'production'
    
    return {
        "environment": os.environ.get('ENVIRONMENT', 'unknown'),
        "openai_key_set": bool(settings.openai_api_key),
        "openai_key_preview": settings.openai_api_key[:10] + "..." if settings.openai_api_key else None,
        "openai_key_length": len(settings.openai_api_key) if settings.openai_api_key else 0,
        "anthropic_key_set": bool(settings.anthropic_api_key),
        "database_url_set": bool(settings.database_url),
        "raw_env_openai": bool(os.environ.get('OPENAI_API_KEY')),
        "raw_env_preview": os.environ.get('OPENAI_API_KEY', '')[:10] + "..." if os.environ.get('OPENAI_API_KEY') else None,
        "settings_source": "Check if .env file exists on server",
        "note": "If keys are set but auth fails, check for extra spaces or encoding issues"
    }