"""Admin endpoints for managing prompts and settings."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.core.prompts import PromptTemplate, prompt_manager
from src.core.config import settings
from src.core.logging_config import get_logger
from src.core.types import ModelConfig
from src.models import list_providers
from src.core.database import get_db, Game, LeaderboardEntry, Evaluation, Task

logger = get_logger("api.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PromptUpdateRequest(BaseModel):
    """Request to update a prompt template."""
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    supports_function_calling: bool
    is_active: bool = True


class SettingUpdateRequest(BaseModel):
    """Request to update a setting."""
    key: str
    value: Any
    description: Optional[str] = None


class FeatureToggle(BaseModel):
    """A feature toggle."""
    key: str
    name: str
    description: str
    enabled: bool
    updated_at: datetime


class ModelConfigRequest(BaseModel):
    """Request to create or update a model configuration."""
    name: str
    provider: str
    model_id: str
    temperature: float = 0.0
    max_tokens: int = 1000
    api_key: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None
    enabled: bool = True


# In-memory storage for settings and feature toggles
# In production, this would be in a database
admin_settings = {
    "default_temperature": {
        "value": 0.0,
        "description": "Default temperature for models",
        "type": "float"
    },
    "max_moves_per_game": {
        "value": 500,
        "description": "Maximum moves allowed per game",
        "type": "int"
    },
    "evaluation_timeout": {
        "value": 300,
        "description": "Timeout for evaluations in seconds",
        "type": "int"
    },
    "use_function_calling_default": {
        "value": True,
        "description": "Use function calling by default when available",
        "type": "bool"
    },
    "reasoning_judge_model": {
        "value": "gpt-4o",
        "description": "Model to use for reasoning quality judging",
        "type": "string"
    }
}

feature_toggles = {
    "function_calling": FeatureToggle(
        key="function_calling",
        name="Function Calling",
        description="Enable function calling/tool use for compatible models",
        enabled=True,
        updated_at=datetime.now(timezone.utc)
    ),
    "reasoning_judge": FeatureToggle(
        key="reasoning_judge",
        name="Reasoning Judge",
        description="Enable LLM-based reasoning quality evaluation",
        enabled=True,
        updated_at=datetime.now(timezone.utc)
    ),
    "advanced_metrics": FeatureToggle(
        key="advanced_metrics",
        name="Advanced Metrics",
        description="Calculate MineBench composite scores and confidence intervals",
        enabled=True,
        updated_at=datetime.now(timezone.utc)
    ),
    "episode_logging": FeatureToggle(
        key="episode_logging",
        name="Episode Logging",
        description="Save detailed episode logs in JSONL format",
        enabled=True,
        updated_at=datetime.now(timezone.utc)
    )
}

# Model configurations storage
model_configs = {
    "gpt-4": {
        "name": "gpt-4",
        "provider": "openai",
        "model_id": "gpt-4",
        "temperature": 0.0,
        "max_tokens": 1000,
        "enabled": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    "gpt-3.5-turbo": {
        "name": "gpt-3.5-turbo",
        "provider": "openai",
        "model_id": "gpt-3.5-turbo",
        "temperature": 0.0,
        "max_tokens": 1000,
        "enabled": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    "claude-3-opus": {
        "name": "claude-3-opus",
        "provider": "anthropic",
        "model_id": "claude-3-opus-20240229",
        "temperature": 0.0,
        "max_tokens": 1000,
        "enabled": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    "claude-3-sonnet": {
        "name": "claude-3-sonnet",
        "provider": "anthropic",
        "model_id": "claude-3-sonnet-20240229",
        "temperature": 0.0,
        "max_tokens": 1000,
        "enabled": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
}


@router.get("/prompts")
async def list_prompts():
    """List all prompt templates."""
    templates = prompt_manager.list_templates()
    return {
        "prompts": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "supports_function_calling": t.supports_function_calling,
                "is_active": t.is_active,
                "updated_at": t.updated_at.isoformat()
            }
            for t in templates.values()
        ]
    }


@router.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """Get a specific prompt template."""
    template = prompt_manager.get_template(prompt_id)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "system_prompt": template.system_prompt,
        "user_prompt_template": template.user_prompt_template,
        "supports_function_calling": template.supports_function_calling,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
        "metadata": template.metadata
    }


@router.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, request: PromptUpdateRequest):
    """Update a prompt template."""
    template = prompt_manager.get_template(prompt_id)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # Update template
    template.name = request.name
    template.description = request.description
    template.system_prompt = request.system_prompt
    template.user_prompt_template = request.user_prompt_template
    template.supports_function_calling = request.supports_function_calling
    template.is_active = request.is_active
    template.updated_at = datetime.now(timezone.utc)
    
    # Save updated template
    prompt_manager.add_template(template)
    
    logger.info(f"Updated prompt template: {prompt_id}")
    
    return {"message": "Prompt template updated successfully", "id": prompt_id}


@router.post("/prompts")
async def create_prompt(request: PromptUpdateRequest):
    """Create a new prompt template."""
    # Generate ID from name
    prompt_id = request.name.lower().replace(" ", "_")
    
    # Check if already exists
    if prompt_manager.get_template(prompt_id):
        raise HTTPException(status_code=400, detail="Prompt template with this ID already exists")
    
    # Create new template
    template = PromptTemplate(
        id=prompt_id,
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        supports_function_calling=request.supports_function_calling,
        is_active=request.is_active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Save template
    prompt_manager.add_template(template)
    
    logger.info(f"Created new prompt template: {prompt_id}")
    
    return {"message": "Prompt template created successfully", "id": prompt_id}


@router.get("/settings")
async def list_settings():
    """List all admin settings."""
    return {"settings": admin_settings}


@router.put("/settings/{key}")
async def update_setting(key: str, request: SettingUpdateRequest):
    """Update an admin setting."""
    if key not in admin_settings:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    # Validate type
    setting_type = admin_settings[key]["type"]
    try:
        if setting_type == "int":
            value = int(request.value)
        elif setting_type == "float":
            value = float(request.value)
        elif setting_type == "bool":
            value = bool(request.value)
        else:
            value = str(request.value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid value type for {key}")
    
    # Update setting
    admin_settings[key]["value"] = value
    if request.description:
        admin_settings[key]["description"] = request.description
    
    logger.info(f"Updated setting {key} to {value}")
    
    return {"message": "Setting updated successfully", "key": key, "value": value}


@router.get("/features")
async def list_features():
    """List all feature toggles."""
    return {
        "features": [
            {
                "key": f.key,
                "name": f.name,
                "description": f.description,
                "enabled": f.enabled,
                "updated_at": f.updated_at.isoformat()
            }
            for f in feature_toggles.values()
        ]
    }


@router.put("/features/{key}")
async def toggle_feature(key: str, enabled: bool):
    """Toggle a feature on or off."""
    if key not in feature_toggles:
        raise HTTPException(status_code=404, detail="Feature toggle not found")
    
    feature_toggles[key].enabled = enabled
    feature_toggles[key].updated_at = datetime.now(timezone.utc)
    
    logger.info(f"Toggled feature {key} to {enabled}")
    
    return {
        "message": "Feature toggle updated successfully",
        "key": key,
        "enabled": enabled
    }


@router.get("/export")
async def export_config():
    """Export all admin configuration."""
    # Load saved prompts from disk
    prompt_manager.load_from_disk()
    
    config = {
        "prompts": {
            tid: {
                "name": t.name,
                "description": t.description,
                "system_prompt": t.system_prompt,
                "user_prompt_template": t.user_prompt_template,
                "supports_function_calling": t.supports_function_calling,
                "is_active": t.is_active
            }
            for tid, t in prompt_manager.list_templates().items()
        },
        "settings": admin_settings,
        "features": {
            key: {
                "name": f.name,
                "description": f.description,
                "enabled": f.enabled
            }
            for key, f in feature_toggles.items()
        },
        "exported_at": datetime.now(timezone.utc).isoformat()
    }
    
    return config


@router.post("/import")
async def import_config(config: Dict[str, Any]):
    """Import admin configuration."""
    imported = {"prompts": 0, "settings": 0, "features": 0}
    
    # Import prompts
    if "prompts" in config:
        for prompt_id, prompt_data in config["prompts"].items():
            template = PromptTemplate(
                id=prompt_id,
                name=prompt_data["name"],
                description=prompt_data["description"],
                system_prompt=prompt_data["system_prompt"],
                user_prompt_template=prompt_data["user_prompt_template"],
                supports_function_calling=prompt_data["supports_function_calling"],
                is_active=prompt_data.get("is_active", True),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            prompt_manager.add_template(template)
            imported["prompts"] += 1
    
    # Import settings
    if "settings" in config:
        for key, setting in config["settings"].items():
            if key in admin_settings:
                admin_settings[key] = setting
                imported["settings"] += 1
    
    # Import features
    if "features" in config:
        for key, feature_data in config["features"].items():
            if key in feature_toggles:
                feature_toggles[key].enabled = feature_data["enabled"]
                feature_toggles[key].updated_at = datetime.now(timezone.utc)
                imported["features"] += 1
    
    logger.info(f"Imported configuration: {imported}")
    
    return {"message": "Configuration imported successfully", "imported": imported}


@router.get("/models")
async def list_models():
    """List all model configurations."""
    return {
        "models": [
            {
                "name": config["name"],
                "provider": config["provider"],
                "model_id": config["model_id"],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"],
                "enabled": config["enabled"],
                "updated_at": config["updated_at"].isoformat()
            }
            for config in model_configs.values()
        ],
        "providers": list_providers()
    }


@router.get("/models/{model_name}")
async def get_model_config(model_name: str):
    """Get a specific model configuration."""
    if model_name not in model_configs:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    config = model_configs[model_name]
    return {
        "name": config["name"],
        "provider": config["provider"],
        "model_id": config["model_id"],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "enabled": config["enabled"],
        "additional_params": config.get("additional_params", {}),
        "created_at": config["created_at"].isoformat(),
        "updated_at": config["updated_at"].isoformat()
    }


@router.put("/models/{model_name}")
async def update_model_config(model_name: str, request: ModelConfigRequest):
    """Update a model configuration."""
    if model_name not in model_configs:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    # Update configuration
    config = model_configs[model_name]
    config.update({
        "name": request.name,
        "provider": request.provider,
        "model_id": request.model_id,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "enabled": request.enabled,
        "updated_at": datetime.now(timezone.utc)
    })
    
    if request.additional_params:
        config["additional_params"] = request.additional_params
    
    # Handle API key separately (don't store in config)
    if request.api_key:
        # In production, this would update secure storage
        logger.info(f"API key updated for model: {model_name}")
    
    logger.info(f"Updated model configuration: {model_name}")
    
    return {"message": "Model configuration updated successfully", "name": model_name}


@router.post("/models")
async def create_model_config(request: ModelConfigRequest):
    """Create a new model configuration."""
    model_name = request.name
    
    # Check if already exists
    if model_name in model_configs:
        raise HTTPException(status_code=400, detail="Model configuration already exists")
    
    # Create new configuration
    model_configs[model_name] = {
        "name": request.name,
        "provider": request.provider,
        "model_id": request.model_id,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "enabled": request.enabled,
        "additional_params": request.additional_params or {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Handle API key separately
    if request.api_key:
        # In production, this would store in secure storage
        logger.info(f"API key stored for new model: {model_name}")
    
    logger.info(f"Created new model configuration: {model_name}")
    
    return {"message": "Model configuration created successfully", "name": model_name}


@router.delete("/models/{model_name}")
async def delete_model_config(model_name: str):
    """Delete a model configuration."""
    if model_name not in model_configs:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    del model_configs[model_name]
    
    logger.info(f"Deleted model configuration: {model_name}")
    
    return {"message": "Model configuration deleted successfully", "name": model_name}


@router.get("/api-keys")
async def get_api_key_status():
    """Get status of API keys (without revealing the actual keys)."""
    return {
        "openai": {
            "configured": bool(settings.openai_api_key),
            "key_prefix": settings.openai_api_key[:8] + "..." if settings.openai_api_key else None
        },
        "anthropic": {
            "configured": bool(settings.anthropic_api_key),
            "key_prefix": settings.anthropic_api_key[:8] + "..." if settings.anthropic_api_key else None
        }
    }


@router.put("/api-keys/{provider}")
async def update_api_key(provider: str, api_key: str):
    """Update an API key for a provider."""
    if provider not in ["openai", "anthropic"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    # In production, this would update secure storage
    # For now, just log that it was updated
    logger.info(f"API key updated for provider: {provider}")
    
    return {"message": f"API key updated for {provider}", "provider": provider}# Database Admin Endpoints (to be appended to admin_endpoints.py)

@router.get("/database/stats")
async def get_database_stats():
    """Get database statistics."""
    try:
        db = next(get_db())
        
        stats = {
            "games": {
                "total": db.query(Game).count(),
                "won": db.query(Game).filter(Game.won == True).count(),
                "lost": db.query(Game).filter(Game.won == False).count(),
                "by_model": {}
            },
            "leaderboard_entries": db.query(LeaderboardEntry).count(),
            "evaluations": db.query(Evaluation).count(),
            "tasks": db.query(Task).count(),
            "models": []
        }
        
        # Get per-model stats
        models = db.query(Game.model_name, Game.model_provider).distinct().all()
        for model_name, provider in models:
            model_games = db.query(Game).filter(
                Game.model_name == model_name,
                Game.model_provider == provider
            )
            stats["games"]["by_model"][f"{provider}:{model_name}"] = {
                "total": model_games.count(),
                "won": model_games.filter(Game.won == True).count()
            }
            stats["models"].append({
                "provider": provider,
                "name": model_name
            })
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/games")
async def list_games(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    won: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
):
    """List games with filtering options."""
    try:
        db = next(get_db())
        
        query = db.query(Game)
        
        # Apply filters
        if model_name:
            query = query.filter(Game.model_name == model_name)
        if provider:
            query = query.filter(Game.model_provider == provider)
        if won is not None:
            query = query.filter(Game.won == won)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        games = query.order_by(Game.created_at.desc()).offset(offset).limit(limit).all()
        
        result = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "games": [
                {
                    "id": game.id,
                    "model": f"{game.model_provider}:{game.model_name}",
                    "difficulty": game.difficulty,
                    "board_size": f"{game.rows}x{game.cols}",
                    "mines": game.mines,
                    "won": game.won,
                    "moves": game.num_moves,
                    "created_at": game.created_at.isoformat() if game.created_at else None,
                    "has_transcript": game.full_transcript is not None
                }
                for game in games
            ]
        }
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"Error listing games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/database/games/{game_id}")
async def delete_game(game_id: str):
    """Delete a specific game and its evaluations."""
    try:
        db = next(get_db())
        
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Delete will cascade to evaluations
        db.delete(game)
        db.commit()
        
        db.close()
        logger.info(f"Deleted game {game_id}")
        
        return {"message": f"Game {game_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting game: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/cleanup")
async def cleanup_database(
    delete_model: Optional[str] = None,
    delete_provider: Optional[str] = None,
    delete_before: Optional[str] = None,
    delete_empty_games: bool = False
):
    """Clean up database based on criteria."""
    try:
        db = next(get_db())
        
        query = db.query(Game)
        
        # Apply filters
        if delete_model:
            query = query.filter(Game.model_name == delete_model)
        if delete_provider:
            query = query.filter(Game.model_provider == delete_provider)
        if delete_before:
            date = datetime.fromisoformat(delete_before)
            query = query.filter(Game.created_at < date)
        if delete_empty_games:
            query = query.filter(Game.num_moves == 0)
        
        # Get count before deletion
        count = query.count()
        
        if count == 0:
            db.close()
            return {"message": "No games matched the criteria", "deleted": 0}
        
        # Delete all matching games
        query.delete()
        db.commit()
        
        db.close()
        logger.info(f"Deleted {count} games")
        
        return {"message": f"Deleted {count} games", "deleted": count}
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/database/leaderboard/{model_name}")
async def delete_leaderboard_entry(model_name: str, provider: str):
    """Delete a specific leaderboard entry."""
    try:
        db = next(get_db())
        
        entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.model_name == model_name,
            LeaderboardEntry.model_provider == provider
        ).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Leaderboard entry not found")
        
        db.delete(entry)
        db.commit()
        
        db.close()
        logger.info(f"Deleted leaderboard entry for {provider}:{model_name}")
        
        return {"message": f"Leaderboard entry deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting leaderboard entry: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/reset/{model_name}")
async def reset_model_stats(model_name: str, provider: str):
    """Reset all statistics for a specific model."""
    try:
        db = next(get_db())
        
        # Delete all games for this model
        deleted_games = db.query(Game).filter(
            Game.model_name == model_name,
            Game.model_provider == provider
        ).delete()
        
        # Delete leaderboard entry
        deleted_entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.model_name == model_name,
            LeaderboardEntry.model_provider == provider
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"Reset stats for {provider}:{model_name}")
        
        return {
            "message": f"Reset complete",
            "games_deleted": deleted_games,
            "leaderboard_reset": deleted_entry > 0
        }
        
    except Exception as e:
        logger.error(f"Error resetting model stats: {e}")
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=str(e))