"""Game-agnostic API endpoints for the competition platform."""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from src.core.database_models import GameRegistry, Game, LeaderboardEntry
from src.games.registry import game_registry, register_builtin_games
from src.games.base import GameConfig, GameMode
from src.evaluation.generic_engine import GenericEvaluationEngine
from src.scoring.framework import StandardScoringProfiles
from src.core.database import get_db
from src.api.models import GameInfo, GameListResponse, GamePlayRequest, GamePlayResponse
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games", tags=["games"])

# Initialize game registry on startup
register_builtin_games()


@router.get("/", response_model=GameListResponse)
async def list_games(
    mode: Optional[str] = Query(None, description="Filter by game mode"),
    active_only: bool = Query(True, description="Only show active games"),
    db: Session = Depends(get_db)
) -> GameListResponse:
    """List all available games."""
    try:
        # Get games from registry
        games = game_registry.list_games()
        
        # Filter by mode if specified
        if mode:
            games = [g for g in games if mode in g["supported_modes"]]
        
        # Get additional info from database
        db_games = db.query(GameRegistry).all()
        db_game_map = {g.game_name: g for g in db_games}
        
        # Combine registry and database info
        game_list = []
        for game in games:
            db_game = db_game_map.get(game["name"])
            if active_only and db_game and not db_game.is_active:
                continue
                
            game_info = GameInfo(
                name=game["name"],
                display_name=game["display_name"],
                description=game["description"],
                supported_modes=game["supported_modes"],
                is_active=db_game.is_active if db_game else True,
                player_count=0  # Would query actual count
            )
            game_list.append(game_info)
        
        return GameListResponse(games=game_list, total=len(game_list))
        
    except Exception as e:
        logger.error(f"Error listing games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{game_name}")
async def get_game_details(
    game_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about a specific game."""
    game = game_registry.get_game(game_name)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    # Get metadata
    metadata = game_registry.get_game_metadata(game_name)
    
    # Get statistics from database
    stats = db.query(Game).filter_by(game_name=game_name).count()
    
    # Get leaderboard preview
    top_players = db.query(LeaderboardEntry)\
        .filter_by(game_name=game_name)\
        .order_by(LeaderboardEntry.avg_score.desc())\
        .limit(5)\
        .all()
    
    return {
        "game": metadata,
        "statistics": {
            "total_games_played": stats,
            "active_players": len(top_players),
            "average_score": sum(p.avg_score for p in top_players) / len(top_players) if top_players else 0
        },
        "top_players": [
            {
                "model_name": p.model_name,
                "avg_score": p.avg_score,
                "games_played": p.games_played,
                "win_rate": p.win_rate
            }
            for p in top_players
        ]
    }


@router.post("/{game_name}/play", response_model=GamePlayResponse)
async def play_game(
    game_name: str,
    request: GamePlayRequest,
    db: Session = Depends(get_db)
) -> GamePlayResponse:
    """Start a new game instance."""
    # Verify game exists
    game = game_registry.get_game(game_name)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    # Create game configuration
    game_config = GameConfig(
        difficulty=request.difficulty,
        mode=GameMode(request.mode) if request.mode else GameMode.MIXED,
        custom_settings=request.custom_settings or {},
        time_limit=request.time_limit
    )
    
    # Create game instance
    game_instance = game.create_instance(game_config)
    if not game_instance:
        raise HTTPException(status_code=500, detail="Failed to create game instance")
    
    # Create database entry
    db_game = Game(
        game_name=game_name,
        player_id=request.player_id,
        ai_model=request.ai_model,
        session_id=request.session_id,
        round_number=request.round_number,
        start_time=datetime.utcnow(),
        status="in_progress",
        board_config=game_config.custom_settings
    )
    db.add(db_game)
    db.commit()
    
    # Get initial state
    initial_state = game_instance.get_initial_state()
    
    return GamePlayResponse(
        game_id=db_game.id,
        instance_id=game_instance.instance_id,
        initial_state=initial_state.state_data,
        visualization_data=game.get_visualization_data(initial_state)
    )


@router.get("/{game_name}/leaderboard")
async def get_game_leaderboard(
    game_name: str,
    scoring_profile: Optional[str] = Query(None, description="Filter by scoring profile"),
    limit: int = Query(20, description="Number of entries to return"),
    offset: int = Query(0, description="Number of entries to skip"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get leaderboard for a specific game."""
    # Verify game exists
    if not game_registry.get_game(game_name):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    # Build query
    query = db.query(LeaderboardEntry).filter_by(game_name=game_name)
    
    if scoring_profile:
        query = query.filter_by(scoring_profile=scoring_profile)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    entries = query.order_by(LeaderboardEntry.avg_score.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return {
        "game_name": game_name,
        "scoring_profile": scoring_profile,
        "total_entries": total,
        "offset": offset,
        "limit": limit,
        "entries": [
            {
                "rank": offset + i + 1,
                "model_name": entry.model_name,
                "games_played": entry.games_played,
                "games_won": entry.games_won,
                "win_rate": entry.win_rate,
                "avg_score": entry.avg_score,
                "best_score": entry.best_score,
                "score_components": entry.score_components,
                "last_updated": entry.updated_at.isoformat() if entry.updated_at else None
            }
            for i, entry in enumerate(entries)
        ]
    }


@router.get("/{game_name}/templates")
async def get_game_templates(
    game_name: str,
    level: Optional[str] = Query(None, description="Template difficulty level"),
    category: Optional[str] = Query(None, description="Template category")
) -> List[Dict[str, Any]]:
    """Get prompt templates for a specific game."""
    from src.prompts.template_system import PromptAssistant, TemplateLevel, TemplateCategory
    
    # Verify game exists
    if not game_registry.get_game(game_name):
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    # Get templates
    assistant = PromptAssistant()
    
    # Convert string parameters to enums
    template_level = TemplateLevel(level) if level else None
    template_category = TemplateCategory(category) if category else None
    
    templates = assistant.get_templates_for_game(game_name, template_level, template_category)
    
    return [
        {
            "template_id": t.template_id,
            "name": t.name,
            "description": t.description,
            "level": t.level.value,
            "category": t.category.value,
            "success_rate": t.success_rate,
            "usage_count": t.usage_count,
            "variables": [
                {
                    "name": v.name,
                    "description": v.description,
                    "example": v.example,
                    "required": v.required
                }
                for v in t.variables
            ],
            "example": t.example_filled
        }
        for t in templates
    ]


@router.post("/{game_name}/validate-move")
async def validate_move(
    game_name: str,
    game_state: Dict[str, Any],
    action: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate if a move is legal in the current game state."""
    # Get game
    game = game_registry.get_game(game_name)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
    
    # This would need actual implementation per game
    # For now, return a mock response
    return {
        "valid": True,
        "message": "Move appears valid",
        "warnings": []
    }


@router.get("/modes/all")
async def get_all_game_modes() -> List[Dict[str, str]]:
    """Get all available game modes across all games."""
    return [
        {
            "mode": mode.value,
            "name": mode.value.replace("_", " ").title(),
            "description": {
                GameMode.SPEED: "Complete as quickly as possible",
                GameMode.ACCURACY: "Focus on correct solutions",
                GameMode.EFFICIENCY: "Use minimum moves/resources",
                GameMode.CREATIVE: "Find innovative solutions",
                GameMode.REASONING: "Provide detailed explanations",
                GameMode.MIXED: "Balanced scoring across metrics"
            }.get(mode, "")
        }
        for mode in GameMode
    ]


@router.get("/scoring-profiles")
async def get_scoring_profiles(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all available scoring profiles."""
    from src.core.database_models import ScoringProfile
    
    # Get from database
    db_profiles = db.query(ScoringProfile).all()
    
    # Also include standard profiles
    profiles = []
    
    # Add standard profiles
    for profile in StandardScoringProfiles.get_all_profiles():
        profiles.append({
            "profile_id": profile.name.lower().replace(" ", "_"),
            "name": profile.name,
            "description": profile.description,
            "weights": {w.component_name: w.weight for w in profile.weights},
            "is_preset": True
        })
    
    # Add custom profiles from database
    for profile in db_profiles:
        if not profile.is_preset:  # Don't duplicate presets
            profiles.append({
                "profile_id": profile.profile_id,
                "name": profile.name,
                "description": profile.description,
                "weights": profile.weights,
                "is_preset": False,
                "created_by": profile.created_by
            })
    
    return profiles


@router.post("/scoring-profiles")
async def create_scoring_profile(
    name: str,
    description: str,
    weights: Dict[str, float],
    created_by: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a custom scoring profile."""
    from src.core.database_models import ScoringProfile
    
    # Validate weights sum to 1.0
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Weights must sum to 1.0, got {total_weight}"
        )
    
    # Create profile
    profile = ScoringProfile(
        profile_id=str(uuid.uuid4()),
        name=name,
        description=description,
        weights=weights,
        is_preset=False,
        created_by=created_by
    )
    
    db.add(profile)
    db.commit()
    
    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "description": profile.description,
        "weights": profile.weights,
        "created_by": profile.created_by
    }