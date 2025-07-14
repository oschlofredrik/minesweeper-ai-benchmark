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