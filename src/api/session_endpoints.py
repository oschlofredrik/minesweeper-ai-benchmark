"""Competition session API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json

from src.competition.session import (
    CompetitionSession, SessionConfig, SessionBuilder,
    CompetitionFormat, RoundConfig
)
from src.competition.lobby import CompetitionLobby, PracticeMode
from src.competition.async_flow import AsyncGameFlowManager, FlowMode
from src.competition.showcase import RoundShowcase
from src.competition.realtime_queue import RealTimeEvaluationQueue, QueuePriority
from src.competition.spectator_mode import SpectatorMode, SpectatorPermission
from src.games.registry import game_registry
from src.games.base import GameConfig, GameMode
from src.scoring.framework import StandardScoringProfiles, ScoringProfile, ScoringWeight
from src.core.database import get_db
from src.core.database_models import CompetitionSession as DBSession, SessionPlayer, SessionRound
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# In-memory storage for active sessions (in production, use Redis)
active_lobbies: Dict[str, CompetitionLobby] = {}
active_flows: Dict[str, AsyncGameFlowManager] = {}
active_showcases: Dict[str, RoundShowcase] = {}
evaluation_queue: Optional[RealTimeEvaluationQueue] = None

def get_evaluation_queue():
    """Get or create the evaluation queue."""
    global evaluation_queue
    if evaluation_queue is None:
        evaluation_queue = RealTimeEvaluationQueue(max_workers=5)
    return evaluation_queue


@router.post("/create")
async def create_session(
    name: str,
    description: str,
    format: str,
    rounds_config: List[Dict[str, Any]],
    creator_id: str,
    max_players: int = 50,
    is_public: bool = True,
    flow_mode: str = "synchronous",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new competition session."""
    try:
        # Parse format
        competition_format = CompetitionFormat(format)
        
        # Create rounds
        rounds = []
        for i, round_data in enumerate(rounds_config):
            # Validate game exists
            if not game_registry.get_game(round_data["game_name"]):
                raise HTTPException(
                    status_code=400,
                    detail=f"Game '{round_data['game_name']}' not found"
                )
            
            # Get scoring profile
            profile_name = round_data.get("scoring_profile", "balanced")
            scoring_profile = None
            
            # Try standard profiles first
            for profile in StandardScoringProfiles.get_all_profiles():
                if profile.name.lower().replace(" ", "_") == profile_name:
                    scoring_profile = profile
                    break
            
            if not scoring_profile:
                # Default to balanced
                scoring_profile = StandardScoringProfiles.BALANCED
            
            round_config = RoundConfig(
                round_number=i + 1,
                game_name=round_data["game_name"],
                game_config=GameConfig(
                    difficulty=round_data.get("difficulty", "medium"),
                    mode=GameMode(round_data.get("mode", "mixed")),
                    custom_settings=round_data.get("custom_settings", {})
                ),
                scoring_profile=scoring_profile,
                time_limit=round_data.get("time_limit", 300)
            )
            rounds.append(round_config)
        
        # Create session config
        session_config = SessionConfig(
            name=name,
            description=description,
            format=competition_format,
            rounds=rounds,
            max_players=max_players,
            is_public=is_public,
            creator_id=creator_id
        )
        
        # Save to database
        db_session = DBSession(
            session_id=session_config.session_id,
            name=name,
            description=description,
            format=format,
            join_code=session_config.join_code,
            is_public=is_public,
            max_players=max_players,
            creator_id=creator_id,
            status="waiting",
            config=session_config.to_dict()
        )
        db.add(db_session)
        
        # Add rounds to database
        for round_config in rounds:
            db_round = SessionRound(
                round_id=f"{session_config.session_id}_r{round_config.round_number}",
                session_id=session_config.session_id,
                round_number=round_config.round_number,
                game_name=round_config.game_name,
                game_config={
                    "difficulty": round_config.game_config.difficulty,
                    "mode": round_config.game_config.mode.value,
                    "custom_settings": round_config.game_config.custom_settings
                },
                scoring_profile={
                    "name": round_config.scoring_profile.name,
                    "weights": [
                        {"component": w.component_name, "weight": w.weight}
                        for w in round_config.scoring_profile.weights
                    ]
                },
                time_limit=round_config.time_limit
            )
            db.add(db_round)
        
        db.commit()
        
        # Create lobby
        lobby = CompetitionLobby(session_config)
        active_lobbies[session_config.session_id] = lobby
        
        # Create flow manager
        flow_manager = AsyncGameFlowManager(
            evaluation_engine=None,  # Will be set when needed
            flow_mode=FlowMode(flow_mode)
        )
        active_flows[session_config.session_id] = flow_manager
        
        # Create showcase manager
        showcase = RoundShowcase()
        active_showcases[session_config.session_id] = showcase
        
        return {
            "session_id": session_config.session_id,
            "join_code": session_config.join_code,
            "status": "created",
            "lobby_url": f"/api/sessions/{session_config.session_id}/lobby"
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/join")
async def join_session(
    join_code: str,
    player_id: str,
    player_name: str,
    ai_model: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Join a competition session using join code."""
    # Find session by join code
    db_session = db.query(DBSession).filter_by(join_code=join_code).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Invalid join code")
    
    # Get lobby
    lobby = active_lobbies.get(db_session.session_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Session lobby not found")
    
    # Add player
    result = await lobby.add_player(player_id, player_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Save to database
    db_player = SessionPlayer(
        session_id=db_session.session_id,
        player_id=player_id,
        player_name=player_name,
        ai_model=ai_model or "gpt-4"
    )
    db.add(db_player)
    db.commit()
    
    return {
        "success": True,
        "session_id": db_session.session_id,
        "session_name": db_session.name,
        "lobby_info": result["lobby_info"],
        "practice_activities": result["practice_activities"]
    }


@router.get("/{session_id}/lobby")
async def get_lobby_info(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current lobby information."""
    lobby = active_lobbies.get(session_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    return lobby.get_lobby_info()


@router.post("/{session_id}/ready")
async def set_player_ready(
    session_id: str,
    player_id: str,
    ready: bool = True,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Set player ready status."""
    lobby = active_lobbies.get(session_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    result = await lobby.set_player_ready(player_id, ready)
    
    # Update database
    db_player = db.query(SessionPlayer).filter_by(
        session_id=session_id,
        player_id=player_id
    ).first()
    
    if db_player:
        db_player.is_ready = ready
        db.commit()
    
    return result


@router.post("/{session_id}/practice/{activity_id}")
async def start_practice_activity(
    session_id: str,
    player_id: str,
    activity_id: str
) -> Dict[str, Any]:
    """Start a practice activity in the lobby."""
    lobby = active_lobbies.get(session_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    return await lobby.start_practice_activity(player_id, activity_id)


@router.post("/{session_id}/chat")
async def send_chat_message(
    session_id: str,
    player_id: str,
    message: str
) -> Dict[str, Any]:
    """Send a chat message in the lobby."""
    lobby = active_lobbies.get(session_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    
    return await lobby.send_chat_message(player_id, message)


@router.post("/{session_id}/submit-prompt")
async def submit_prompt(
    session_id: str,
    player_id: str,
    round_number: int,
    prompt: str,
    game_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Submit a prompt for evaluation."""
    flow_manager = active_flows.get(session_id)
    if not flow_manager:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Submit to flow manager
    result = await flow_manager.submit_prompt(
        player_id, round_number, prompt, game_config
    )
    
    # Also submit to evaluation queue
    queue_id = await get_evaluation_queue().submit(
        player_id=player_id,
        session_id=session_id,
        round_number=round_number,
        game_name=game_config["game_name"],
        prompt=prompt,
        priority=QueuePriority.NORMAL
    )
    
    result["queue_id"] = queue_id
    return result


@router.get("/{session_id}/round/{round_number}/status")
async def get_round_status(
    session_id: str,
    round_number: int
) -> Dict[str, Any]:
    """Get status of a specific round."""
    flow_manager = active_flows.get(session_id)
    if not flow_manager:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return flow_manager.get_round_status(round_number)


@router.get("/{session_id}/showcase/{round_number}")
async def get_round_showcase(
    session_id: str,
    round_number: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get showcase content for between rounds."""
    showcase = active_showcases.get(session_id)
    if not showcase:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get round results (mock for now)
    round_results = []  # Would get from database
    
    # Prepare showcase
    items = await showcase.prepare_showcase(
        round_number, round_results, "minesweeper"  # Would get game from round config
    )
    
    return [
        {
            "item_id": item.item_id,
            "type": item.showcase_type.value,
            "title": item.title,
            "description": item.description,
            "duration": item.duration,
            "content": item.content
        }
        for item in items
    ]


@router.post("/{session_id}/spectate")
async def join_as_spectator(
    session_id: str,
    spectator_id: str,
    name: str,
    access_token: Optional[str] = None
) -> Dict[str, Any]:
    """Join a session as a spectator."""
    # Get or create spectator mode
    if session_id not in active_lobbies:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # For now, create spectator mode on demand
    spectator_mode = SpectatorMode(session_id)
    
    result = await spectator_mode.add_spectator(
        spectator_id, name, access_token
    )
    
    if not result["success"]:
        raise HTTPException(status_code=403, detail=result["error"])
    
    return result


@router.get("/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """Get global evaluation queue status."""
    return get_evaluation_queue().get_queue_status()


@router.get("/queue/item/{item_id}")
async def get_queue_item_status(item_id: str) -> Dict[str, Any]:
    """Get status of a specific queue item."""
    status = get_evaluation_queue().get_item_status(item_id)
    if not status:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return status


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    player_id: str
):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    # Subscribe to relevant events
    flow_manager = active_flows.get(session_id)
    if not flow_manager:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    # Event handler
    async def handle_event(event: str, data: Dict[str, Any]):
        try:
            await websocket.send_json({
                "event": event,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass  # Connection closed
    
    # Register handlers
    flow_manager.register_callback("round_started", lambda d: handle_event("round_started", d))
    flow_manager.register_callback("prompt_submitted", lambda d: handle_event("prompt_submitted", d))
    flow_manager.register_callback("evaluation_completed", lambda d: handle_event("evaluation_completed", d))
    flow_manager.register_callback("round_completed", lambda d: handle_event("round_completed", d))
    
    # Also subscribe to queue updates
    get_evaluation_queue().subscribe("item_queued", lambda e, d: handle_event(e, d))
    get_evaluation_queue().subscribe("item_processing", lambda e, d: handle_event(e, d))
    get_evaluation_queue().subscribe("item_completed", lambda e, d: handle_event(e, d))
    
    try:
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            
    except WebSocketDisconnect:
        # Clean up subscriptions
        pass


@router.get("/templates/quick-match")
async def get_quick_match_templates() -> List[Dict[str, Any]]:
    """Get quick match session templates."""
    games = game_registry.list_games()
    
    templates = []
    for game in games[:5]:  # Top 5 games
        templates.append({
            "name": f"Quick {game['display_name']}",
            "description": f"Single round of {game['display_name']}",
            "game": game['name'],
            "format": "single_round",
            "estimated_duration": 5,  # minutes
            "difficulty": "medium"
        })
    
    return templates


@router.post("/templates/use/{template_id}")
async def use_session_template(
    template_id: str,
    creator_id: str,
    customizations: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a session from a template."""
    # This would have pre-defined templates
    # For now, create a simple single-game session
    
    game_name = template_id.replace("quick_", "")
    if not game_registry.get_game(game_name):
        game_name = "minesweeper"  # Default
    
    return await create_session(
        name=f"Quick {game_name.title()} Match",
        description="A quick competition",
        format="single_round",
        rounds_config=[{
            "game_name": game_name,
            "difficulty": customizations.get("difficulty", "medium") if customizations else "medium",
            "mode": "mixed",
            "time_limit": 300
        }],
        creator_id=creator_id,
        max_players=20,
        is_public=True
    )