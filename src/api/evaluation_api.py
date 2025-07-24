"""
API endpoints for the dynamic evaluation system.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.core.database import get_db
from src.core.evaluation_models import (
    Evaluation, EvaluationTemplate, GameEvaluation,
    EvaluationScore, EvaluationReview, EvaluationPreset
)
from src.evaluation.dynamic_engine import (
    DynamicEvaluationEngine, EvaluationContext
)
from src.api.auth import get_current_user
from src.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

# Initialize evaluation engine
evaluation_engine = DynamicEvaluationEngine()


# Pydantic models for API
from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    """Create a new evaluation"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scoring_type: str = Field(..., pattern="^(binary|proportional|cumulative)$")
    rules: List[Dict[str, Any]]
    normalization_config: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False


class EvaluationUpdate(BaseModel):
    """Update an evaluation"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    normalization_config: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class EvaluationTest(BaseModel):
    """Test data for evaluation"""
    prompt: str
    response: str
    metadata: Dict[str, Any] = {}
    round_history: List[Dict[str, Any]] = []


class GameEvaluationConfig(BaseModel):
    """Configuration for attaching evaluation to game"""
    evaluation_id: UUID
    weight: float = Field(..., ge=0, le=1)
    dimension: Optional[str] = None
    config_overrides: Optional[Dict[str, Any]] = None


class EvaluationReviewCreate(BaseModel):
    """Create a review for an evaluation"""
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None


# Evaluation Management Endpoints

@router.post("/", response_model=Dict[str, Any])
async def create_evaluation(
    evaluation: EvaluationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new evaluation definition"""
    logger.info(
        "Creating new evaluation",
        extra={
            "user_id": current_user.get("id"),
            "evaluation_name": evaluation.name,
            "event_type": "admin_activity",
            "activity": "create_evaluation"
        }
    )
    
    # Create evaluation
    db_evaluation = Evaluation(
        name=evaluation.name,
        description=evaluation.description,
        scoring_type=evaluation.scoring_type,
        rules=evaluation.rules,
        normalization_config=evaluation.normalization_config or {},
        category=evaluation.category,
        tags=evaluation.tags,
        is_public=evaluation.is_public,
        created_by=current_user.get("id")
    )
    
    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)
    
    return {
        "id": str(db_evaluation.id),
        "name": db_evaluation.name,
        "created_at": db_evaluation.created_at.isoformat(),
        "message": "Evaluation created successfully"
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_evaluations(
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List available evaluations"""
    logger.info(
        "Listing evaluations",
        extra={
            "category": category,
            "is_public": is_public,
            "event_type": "user_activity",
            "activity": "list_evaluations"
        }
    )
    
    query = db.query(Evaluation)
    
    # Apply filters
    if category:
        query = query.filter(Evaluation.category == category)
    if is_public is not None:
        query = query.filter(Evaluation.is_public == is_public)
    if search:
        query = query.filter(
            (Evaluation.name.ilike(f"%{search}%")) |
            (Evaluation.description.ilike(f"%{search}%"))
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    evaluations = query.order_by(desc(Evaluation.created_at))\
                      .offset(skip)\
                      .limit(limit)\
                      .all()
    
    return [
        {
            "id": str(eval.id),
            "name": eval.name,
            "description": eval.description,
            "scoring_type": eval.scoring_type,
            "category": eval.category,
            "tags": eval.tags,
            "is_public": eval.is_public,
            "created_at": eval.created_at.isoformat(),
            "total": total
        }
        for eval in evaluations
    ]


@router.get("/{evaluation_id}", response_model=Dict[str, Any])
async def get_evaluation(
    evaluation_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed evaluation information"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Get average rating
    avg_rating = db.query(func.avg(EvaluationReview.rating))\
                   .filter(EvaluationReview.evaluation_id == evaluation_id)\
                   .scalar() or 0
    
    # Get download count
    template = db.query(EvaluationTemplate)\
                 .filter(EvaluationTemplate.evaluation_id == evaluation_id)\
                 .first()
    
    return {
        "id": str(evaluation.id),
        "name": evaluation.name,
        "description": evaluation.description,
        "version": evaluation.version,
        "scoring_type": evaluation.scoring_type,
        "rules": evaluation.rules,
        "normalization_config": evaluation.normalization_config,
        "category": evaluation.category,
        "tags": evaluation.tags,
        "is_public": evaluation.is_public,
        "created_by": str(evaluation.created_by) if evaluation.created_by else None,
        "created_at": evaluation.created_at.isoformat(),
        "updated_at": evaluation.updated_at.isoformat(),
        "average_rating": float(avg_rating) if avg_rating else 0,
        "downloads": template.downloads if template else 0
    }


@router.put("/{evaluation_id}", response_model=Dict[str, Any])
async def update_evaluation(
    evaluation_id: UUID,
    evaluation_update: EvaluationUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an evaluation definition"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Check ownership
    if evaluation.created_by != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Not authorized to update this evaluation")
    
    # Update fields
    update_data = evaluation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(evaluation, field, value)
    
    # Increment version
    current_version = evaluation.version or "1.0"
    major, minor = map(int, current_version.split("."))
    evaluation.version = f"{major}.{minor + 1}"
    
    db.commit()
    db.refresh(evaluation)
    
    logger.info(
        "Updated evaluation",
        extra={
            "evaluation_id": str(evaluation_id),
            "version": evaluation.version,
            "event_type": "admin_activity",
            "activity": "update_evaluation"
        }
    )
    
    return {
        "id": str(evaluation.id),
        "version": evaluation.version,
        "message": "Evaluation updated successfully"
    }


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an evaluation"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Check ownership
    if evaluation.created_by != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this evaluation")
    
    db.delete(evaluation)
    db.commit()
    
    return {"message": "Evaluation deleted successfully"}


# Evaluation Testing

@router.post("/{evaluation_id}/test", response_model=Dict[str, Any])
async def test_evaluation(
    evaluation_id: UUID,
    test_data: EvaluationTest,
    db: Session = Depends(get_db)
):
    """Test an evaluation with sample data"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Create evaluation config
    eval_config = {
        "id": str(evaluation.id),
        "name": evaluation.name,
        "scoring_type": evaluation.scoring_type,
        "rules": evaluation.rules,
        "normalization_config": evaluation.normalization_config
    }
    
    # Test the evaluation
    try:
        result = evaluation_engine.test_evaluation(eval_config, test_data.dict())
        
        logger.info(
            "Tested evaluation",
            extra={
                "evaluation_id": str(evaluation_id),
                "test_score": result["result"]["normalized_score"],
                "event_type": "user_activity",
                "activity": "test_evaluation"
            }
        )
        
        return result
    except Exception as e:
        logger.error(f"Evaluation test failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Evaluation test failed: {str(e)}")


# Game Integration

@router.post("/games/{game_session_id}/attach")
async def attach_evaluations_to_game(
    game_session_id: UUID,
    evaluations: List[GameEvaluationConfig],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attach evaluations to a game session"""
    # Validate total weight
    total_weight = sum(e.weight for e in evaluations)
    if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
        raise HTTPException(
            status_code=400, 
            detail=f"Total weight must equal 1.0, got {total_weight}"
        )
    
    # Create game evaluation entries
    for eval_config in evaluations:
        # Check if evaluation exists
        evaluation = db.query(Evaluation).filter(
            Evaluation.id == eval_config.evaluation_id
        ).first()
        
        if not evaluation:
            raise HTTPException(
                status_code=404, 
                detail=f"Evaluation {eval_config.evaluation_id} not found"
            )
        
        # Create game evaluation
        game_eval = GameEvaluation(
            game_session_id=game_session_id,
            evaluation_id=eval_config.evaluation_id,
            weight=eval_config.weight,
            dimension=eval_config.dimension,
            config_overrides=eval_config.config_overrides
        )
        db.add(game_eval)
    
    db.commit()
    
    logger.info(
        "Attached evaluations to game",
        extra={
            "game_session_id": str(game_session_id),
            "num_evaluations": len(evaluations),
            "event_type": "admin_activity",
            "activity": "attach_evaluations"
        }
    )
    
    return {
        "message": f"Attached {len(evaluations)} evaluations to game",
        "game_session_id": str(game_session_id)
    }


@router.get("/games/{game_session_id}")
async def get_game_evaluations(
    game_session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get evaluations attached to a game session"""
    game_evals = db.query(GameEvaluation).filter(
        GameEvaluation.game_session_id == game_session_id
    ).all()
    
    return [
        {
            "evaluation_id": str(ge.evaluation_id),
            "evaluation_name": ge.evaluation.name if ge.evaluation else None,
            "weight": float(ge.weight),
            "dimension": ge.dimension,
            "config_overrides": ge.config_overrides
        }
        for ge in game_evals
    ]


# Marketplace

@router.get("/marketplace/", response_model=List[Dict[str, Any]])
async def browse_marketplace(
    category: Optional[str] = None,
    sort_by: str = Query("downloads", pattern="^(downloads|rating|recent)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Browse evaluation marketplace"""
    query = db.query(Evaluation, EvaluationTemplate)\
              .join(EvaluationTemplate)\
              .filter(Evaluation.is_public == True)
    
    if category:
        query = query.filter(Evaluation.category == category)
    
    # Apply sorting
    if sort_by == "downloads":
        query = query.order_by(desc(EvaluationTemplate.downloads))
    elif sort_by == "rating":
        query = query.order_by(desc(EvaluationTemplate.rating))
    else:  # recent
        query = query.order_by(desc(Evaluation.created_at))
    
    # Get results
    results = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(eval.id),
            "name": eval.name,
            "description": eval.description,
            "category": eval.category,
            "tags": eval.tags,
            "downloads": template.downloads,
            "rating": float(template.rating) if template.rating else 0,
            "featured": template.featured,
            "created_at": eval.created_at.isoformat()
        }
        for eval, template in results
    ]


@router.post("/marketplace/{evaluation_id}/import")
async def import_evaluation(
    evaluation_id: UUID,
    customize: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import an evaluation from marketplace"""
    # Get original evaluation
    original = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not original or not original.is_public:
        raise HTTPException(status_code=404, detail="Evaluation not found in marketplace")
    
    # Create a copy
    new_eval = Evaluation(
        name=f"{original.name} (Copy)" if customize else original.name,
        description=original.description,
        scoring_type=original.scoring_type,
        rules=original.rules,
        normalization_config=original.normalization_config,
        category=original.category,
        tags=original.tags,
        is_public=False,
        created_by=current_user.get("id")
    )
    
    db.add(new_eval)
    
    # Update download count
    template = db.query(EvaluationTemplate).filter(
        EvaluationTemplate.evaluation_id == evaluation_id
    ).first()
    
    if template:
        template.downloads += 1
    
    db.commit()
    db.refresh(new_eval)
    
    logger.info(
        "Imported evaluation from marketplace",
        extra={
            "original_id": str(evaluation_id),
            "new_id": str(new_eval.id),
            "customize": customize,
            "event_type": "user_activity",
            "activity": "import_evaluation"
        }
    )
    
    return {
        "id": str(new_eval.id),
        "message": "Evaluation imported successfully",
        "customize_url": f"/evaluations/{new_eval.id}/edit" if customize else None
    }


@router.post("/marketplace/{evaluation_id}/rate")
async def rate_evaluation(
    evaluation_id: UUID,
    review: EvaluationReviewCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate and review an evaluation"""
    # Check if evaluation exists and is public
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evaluation_id,
        Evaluation.is_public == True
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Check for existing review
    existing = db.query(EvaluationReview).filter(
        EvaluationReview.evaluation_id == evaluation_id,
        EvaluationReview.user_id == current_user.get("id")
    ).first()
    
    if existing:
        # Update existing review
        existing.rating = review.rating
        existing.review = review.review
    else:
        # Create new review
        db_review = EvaluationReview(
            evaluation_id=evaluation_id,
            user_id=current_user.get("id"),
            rating=review.rating,
            review=review.review
        )
        db.add(db_review)
    
    # Update average rating in template
    avg_rating = db.query(func.avg(EvaluationReview.rating))\
                   .filter(EvaluationReview.evaluation_id == evaluation_id)\
                   .scalar()
    
    template = db.query(EvaluationTemplate).filter(
        EvaluationTemplate.evaluation_id == evaluation_id
    ).first()
    
    if template and avg_rating:
        template.rating = avg_rating
    
    db.commit()
    
    return {"message": "Review submitted successfully"}