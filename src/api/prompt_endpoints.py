"""Prompt library API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.prompts.library import PromptLibrary, PromptVisibility, SavedPrompt
from src.prompts.template_system import PromptAssistant, TemplateLevel
from src.core.database import get_db
from src.core.database_models import PromptLibrary as DBPromptLibrary
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# Global prompt library instance
prompt_library = PromptLibrary()
prompt_assistant = PromptAssistant()


@router.post("/save")
async def save_prompt(
    owner_id: str = Body(...),
    title: str = Body(...),
    content: str = Body(...),
    game_name: str = Body(...),
    visibility: str = Body("private"),
    tags: Optional[List[str]] = Body(None),
    template_id: Optional[str] = Body(None),
    parent_id: Optional[str] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Save a new prompt to the library."""
    try:
        # Save to in-memory library
        prompt_id = prompt_library.save_prompt(
            owner_id=owner_id,
            title=title,
            content=content,
            game_name=game_name,
            visibility=PromptVisibility(visibility),
            tags=tags,
            template_id=template_id,
            parent_id=parent_id
        )
        
        # Save to database
        db_prompt = DBPromptLibrary(
            prompt_id=prompt_id,
            owner_id=owner_id,
            title=title,
            content=content,
            game_name=game_name,
            template_id=template_id,
            visibility=visibility,
            tags=tags,
            version=1,
            parent_id=parent_id
        )
        db.add(db_prompt)
        db.commit()
        
        return {
            "success": True,
            "prompt_id": prompt_id,
            "message": "Prompt saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_prompts(
    user_id: str = Query(..., description="User making the request"),
    game_name: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    template_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    min_effectiveness: Optional[float] = Query(None),
    sort_by: str = Query("effectiveness", description="Sort by: effectiveness, recent, popular, score"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Search prompts with filters."""
    # Build query
    query = db.query(DBPromptLibrary)
    
    # Apply filters
    if game_name:
        query = query.filter(DBPromptLibrary.game_name == game_name)
    
    if owner_id:
        query = query.filter(DBPromptLibrary.owner_id == owner_id)
    
    if template_id:
        query = query.filter(DBPromptLibrary.template_id == template_id)
    
    # Visibility filter
    query = query.filter(
        or_(
            DBPromptLibrary.owner_id == user_id,
            DBPromptLibrary.visibility == "public",
            and_(
                DBPromptLibrary.visibility == "friends",
                # Would check friend relationship
                DBPromptLibrary.owner_id == user_id  # Placeholder
            )
        )
    )
    
    # Tag filter
    if tags:
        for tag in tags:
            query = query.filter(DBPromptLibrary.tags.contains([tag]))
    
    # Effectiveness filter
    if min_effectiveness:
        min_score = min_effectiveness * 100  # Convert to percentage
        query = query.filter(DBPromptLibrary.avg_score >= min_score)
    
    # Get total count
    total = query.count()
    
    # Sort
    if sort_by == "effectiveness":
        query = query.order_by(DBPromptLibrary.avg_score.desc())
    elif sort_by == "recent":
        query = query.order_by(DBPromptLibrary.updated_at.desc())
    elif sort_by == "popular":
        query = query.order_by(DBPromptLibrary.usage_count.desc())
    elif sort_by == "score":
        query = query.order_by(DBPromptLibrary.best_score.desc())
    
    # Paginate
    prompts = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "prompts": [
            {
                "prompt_id": p.prompt_id,
                "owner_id": p.owner_id,
                "title": p.title,
                "game_name": p.game_name,
                "visibility": p.visibility,
                "tags": p.tags or [],
                "version": p.version,
                "usage_count": p.usage_count,
                "avg_score": p.avg_score,
                "win_rate": p.win_rate,
                "likes": p.likes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in prompts
        ]
    }


@router.get("/{prompt_id}")
async def get_prompt_details(
    prompt_id: str,
    user_id: str = Query(..., description="User making the request"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about a prompt."""
    prompt = db.query(DBPromptLibrary).filter_by(prompt_id=prompt_id).first()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Check access
    if prompt.visibility == "private" and prompt.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "prompt_id": prompt.prompt_id,
        "owner_id": prompt.owner_id,
        "title": prompt.title,
        "content": prompt.content,
        "game_name": prompt.game_name,
        "template_id": prompt.template_id,
        "visibility": prompt.visibility,
        "tags": prompt.tags or [],
        "version": prompt.version,
        "parent_id": prompt.parent_id,
        "usage_count": prompt.usage_count,
        "total_score": prompt.total_score,
        "avg_score": prompt.avg_score,
        "win_rate": prompt.win_rate,
        "best_score": prompt.best_score,
        "likes": prompt.likes,
        "metadata": prompt.prompt_metadata or {},
        "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
        "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None
    }


@router.post("/{prompt_id}/fork")
async def fork_prompt(
    prompt_id: str,
    user_id: str = Body(...),
    new_title: Optional[str] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Fork someone else's prompt."""
    # Get original prompt
    original = db.query(DBPromptLibrary).filter_by(prompt_id=prompt_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Check access
    if original.visibility == "private" and original.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot fork private prompt")
    
    # Create fork
    new_prompt_id = prompt_library.save_prompt(
        owner_id=user_id,
        title=new_title or f"Fork of {original.title}",
        content=original.content,
        game_name=original.game_name,
        visibility=PromptVisibility.PRIVATE,
        tags=(original.tags or []) + ["forked"],
        template_id=original.template_id,
        parent_id=prompt_id
    )
    
    # Save to database
    db_fork = DBPromptLibrary(
        prompt_id=new_prompt_id,
        owner_id=user_id,
        title=new_title or f"Fork of {original.title}",
        content=original.content,
        game_name=original.game_name,
        template_id=original.template_id,
        visibility="private",
        tags=(original.tags or []) + ["forked"],
        version=1,
        parent_id=prompt_id,
        prompt_metadata={"forked_from": prompt_id, "forked_at": datetime.utcnow().isoformat()}
    )
    db.add(db_fork)
    
    # Update original's fork count
    original.prompt_metadata = original.prompt_metadata or {}
    original.prompt_metadata["fork_count"] = original.prompt_metadata.get("fork_count", 0) + 1
    
    db.commit()
    
    return {
        "success": True,
        "prompt_id": new_prompt_id,
        "message": "Prompt forked successfully"
    }


@router.post("/{prompt_id}/like")
async def like_prompt(
    prompt_id: str,
    user_id: str = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Like a prompt."""
    prompt = db.query(DBPromptLibrary).filter_by(prompt_id=prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Check if already liked (would need a separate likes table in real implementation)
    prompt.likes += 1
    db.commit()
    
    return {
        "success": True,
        "likes": prompt.likes
    }


@router.post("/{prompt_id}/record-usage")
async def record_prompt_usage(
    prompt_id: str,
    score: float = Body(...),
    won: bool = Body(...),
    game_details: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Record usage of a prompt."""
    prompt = db.query(DBPromptLibrary).filter_by(prompt_id=prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Update metrics
    prompt.usage_count += 1
    prompt.total_score += score
    prompt.avg_score = prompt.total_score / prompt.usage_count
    
    if won:
        wins = int(prompt.win_rate * (prompt.usage_count - 1))
        prompt.win_rate = (wins + 1) / prompt.usage_count
    else:
        wins = int(prompt.win_rate * (prompt.usage_count - 1))
        prompt.win_rate = wins / prompt.usage_count
    
    if score > prompt.best_score:
        prompt.best_score = score
    
    db.commit()
    
    # Also update in-memory library
    prompt_library.record_usage(prompt_id, score, won, game_details)
    
    return {
        "success": True,
        "new_stats": {
            "usage_count": prompt.usage_count,
            "avg_score": prompt.avg_score,
            "win_rate": prompt.win_rate,
            "best_score": prompt.best_score
        }
    }


@router.get("/recommendations/{game_name}")
async def get_prompt_recommendations(
    game_name: str,
    user_id: str = Query(...),
    limit: int = Query(5, le=20),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get prompt recommendations for a user and game."""
    # Get user's prompt history
    user_prompts = db.query(DBPromptLibrary).filter_by(
        owner_id=user_id,
        game_name=game_name
    ).all()
    
    if user_prompts:
        # Find similar successful prompts
        avg_score = sum(p.avg_score for p in user_prompts) / len(user_prompts)
        target_score = min(avg_score + 10, 90)  # Look for slightly better
        
        recommendations = db.query(DBPromptLibrary).filter(
            DBPromptLibrary.game_name == game_name,
            DBPromptLibrary.owner_id != user_id,
            DBPromptLibrary.visibility == "public",
            DBPromptLibrary.avg_score >= target_score
        ).order_by(DBPromptLibrary.avg_score.desc()).limit(limit).all()
    else:
        # New user - recommend popular beginner-friendly prompts
        recommendations = db.query(DBPromptLibrary).filter(
            DBPromptLibrary.game_name == game_name,
            DBPromptLibrary.visibility == "public",
            DBPromptLibrary.tags.contains(["beginner_friendly"])
        ).order_by(DBPromptLibrary.usage_count.desc()).limit(limit).all()
    
    return [
        {
            "prompt_id": p.prompt_id,
            "title": p.title,
            "owner_id": p.owner_id,
            "tags": p.tags or [],
            "avg_score": p.avg_score,
            "usage_count": p.usage_count,
            "reason": "Similar to your successful prompts" if user_prompts else "Popular with beginners"
        }
        for p in recommendations
    ]


@router.post("/collections/create")
async def create_collection(
    owner_id: str = Body(...),
    name: str = Body(...),
    description: str = Body(...),
    prompt_ids: Optional[List[str]] = Body(None),
    visibility: str = Body("private"),
    tags: Optional[List[str]] = Body(None)
) -> Dict[str, Any]:
    """Create a new prompt collection."""
    collection_id = prompt_library.create_collection(
        owner_id=owner_id,
        name=name,
        description=description,
        prompt_ids=prompt_ids,
        visibility=PromptVisibility(visibility),
        tags=tags
    )
    
    return {
        "success": True,
        "collection_id": collection_id,
        "message": "Collection created successfully"
    }


@router.get("/templates/analyze")
async def analyze_prompt_quality(
    prompt: str = Query(...),
    game_name: str = Query(...)
) -> Dict[str, Any]:
    """Analyze the quality of a prompt."""
    analysis = prompt_assistant.analyze_prompt_quality(prompt, game_name)
    
    return {
        "analysis": analysis,
        "overall_quality": "excellent" if analysis["overall_score"] > 0.8 else
                          "good" if analysis["overall_score"] > 0.6 else
                          "fair" if analysis["overall_score"] > 0.4 else "needs improvement"
    }


@router.get("/templates/suggestions")
async def get_prompt_suggestions(
    partial_prompt: str = Query(...),
    game_name: str = Query(...),
    cursor_position: int = Query(...)
) -> List[Dict[str, Any]]:
    """Get auto-completion suggestions for a partial prompt."""
    game_context = {"game_name": game_name}
    
    suggestions = prompt_assistant.suggest_completion(
        partial_prompt, game_context, cursor_position
    )
    
    return suggestions


@router.post("/export")
async def export_prompts(
    user_id: str = Body(...),
    prompt_ids: Optional[List[str]] = Body(None),
    format: str = Body("json"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Export prompts for backup or sharing."""
    # Get prompts from database
    query = db.query(DBPromptLibrary).filter_by(owner_id=user_id)
    
    if prompt_ids:
        query = query.filter(DBPromptLibrary.prompt_id.in_(prompt_ids))
    
    prompts = query.all()
    
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "prompts": [
            {
                "prompt_id": p.prompt_id,
                "title": p.title,
                "content": p.content,
                "game_name": p.game_name,
                "tags": p.tags,
                "version": p.version,
                "stats": {
                    "usage_count": p.usage_count,
                    "avg_score": p.avg_score,
                    "win_rate": p.win_rate
                }
            }
            for p in prompts
        ]
    }
    
    if format == "json":
        return export_data
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")