"""API endpoints for competition sessions."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
import random
import string

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from src.core.logging_config import get_logger
from src.games.registry import game_registry, register_builtin_games

# Initialize logger
logger = get_logger("api.sessions")

try:
    from .competition_runner import run_competition
except ImportError as e:
    logger.error(f"Failed to import competition_runner: {e}")
    # Fallback implementation
    async def run_competition(session_id: str, session_data: Dict[str, Any]):
        logger.warning(f"Competition runner not available, using stub for session {session_id}")

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# In-memory session storage (replace with database in production)
sessions: Dict[str, "CompetitionSession"] = {}
join_codes: Dict[str, str] = {}  # Maps join codes to session IDs


@router.get("/debug")
async def debug_endpoint():
    """Debug endpoint to check if sessions API is working."""
    return {
        "status": "ok",
        "sessions_count": len(sessions),
        "join_codes_count": len(join_codes),
        "imports_ok": True
    }


class CreateSessionRequest(BaseModel):
    """Request to create a new competition session."""
    name: str
    description: str
    format: str  # single_round, best_of_three, tournament
    rounds_config: List[Dict[str, Any]]
    creator_id: str
    max_players: int = 20
    is_public: bool = True
    flow_mode: str = "asynchronous"


class JoinSessionRequest(BaseModel):
    """Request to join a session."""
    join_code: str
    player_id: str
    player_name: str
    ai_model: Optional[str] = None


class Player(BaseModel):
    """A player in a competition session."""
    player_id: str
    player_name: str  # Changed from 'name' to avoid logging conflicts
    ai_model: Optional[str] = None
    is_ready: bool = False
    is_host: bool = False
    joined_at: datetime = None
    
    def __init__(self, **data):
        if 'joined_at' not in data:
            data['joined_at'] = datetime.utcnow()
        super().__init__(**data)


class CompetitionSession:
    """A competition session."""
    
    def __init__(self, session_id: str, config: CreateSessionRequest):
        self.session_id = session_id
        self.name = config.name
        self.description = config.description
        self.format = config.format
        self.rounds_config = config.rounds_config
        self.creator_id = config.creator_id
        self.max_players = config.max_players
        self.is_public = config.is_public
        self.flow_mode = config.flow_mode
        
        # Generate a join code
        self.join_code = self._generate_join_code()
        
        # Session state
        self.players: List[Player] = []
        self.status = "waiting"  # waiting, in_progress, completed
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Add creator as first player
        creator = Player(
            player_id=config.creator_id,
            player_name="Host",
            is_host=True,
            is_ready=False
        )
        self.players.append(creator)
    
    def _generate_join_code(self) -> str:
        """Generate a unique 6-character join code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in join_codes:
                return code
    
    def add_player(self, player: Player) -> bool:
        """Add a player to the session."""
        if len(self.players) >= self.max_players:
            return False
        
        # Check if player already in session
        if any(p.player_id == player.player_id for p in self.players):
            return False
        
        self.players.append(player)
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the session."""
        for i, player in enumerate(self.players):
            if player.player_id == player_id:
                del self.players[i]
                return True
        return False
    
    def set_player_ready(self, player_id: str, ready: bool) -> bool:
        """Set a player's ready status."""
        for player in self.players:
            if player.player_id == player_id:
                player.is_ready = ready
                return True
        return False
    
    def can_start(self) -> bool:
        """Check if the session can start."""
        if len(self.players) < 2:
            return False
        return all(p.is_ready for p in self.players)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "description": self.description,
            "format": self.format,
            "rounds_config": self.rounds_config,
            "join_code": self.join_code,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.player_name,
                    "ai_model": p.ai_model,
                    "is_ready": p.is_ready,
                    "is_host": p.is_host
                }
                for p in self.players
            ],
            "status": self.status,
            "max_players": self.max_players,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None
        }


@router.post("/create")
async def create_session(request: CreateSessionRequest):
    """Create a new competition session."""
    try:
        session_id = f"session_{uuid4().hex[:8]}"
        
        logger.info(f"Creating competition session", extra={
            "session_id": session_id,
            "session_name": request.name,
            "format": request.format,
            "creator": request.creator_id,
            "max_players": request.max_players,
            "rounds_count": len(request.rounds_config),
            "event_type": "user_activity",
            "activity": "competition_created",
            "endpoint": "/api/sessions/create"
        })
        
        # Create session
        session = CompetitionSession(session_id, request)
        sessions[session_id] = session
        join_codes[session.join_code] = session_id
        
        return {
            "session_id": session_id,
            "join_code": session.join_code,
            "status": "created",
            "message": f"Session '{request.name}' created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/join")
async def join_session(request: JoinSessionRequest):
    """Join an existing session."""
    # Find session by join code
    join_code = request.join_code.upper()
    
    if join_code not in join_codes:
        raise HTTPException(status_code=404, detail="Invalid join code")
    
    session_id = join_codes[join_code]
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "waiting":
        raise HTTPException(status_code=400, detail="Session already started")
    
    # Create player
    player = Player(
        player_id=request.player_id,
        player_name=request.player_name,
        ai_model=request.ai_model,
        is_ready=False
    )
    
    # Add to session
    if not session.add_player(player):
        raise HTTPException(status_code=400, detail="Session is full or player already joined")
    
    logger.info(f"Player joined session", extra={
        "session_id": session_id,
        "player_id": request.player_id,
        "player_name": request.player_name,
        "ai_model": request.ai_model,
        "join_code": join_code,
        "event_type": "user_activity",
        "activity": "competition_joined",
        "endpoint": "/api/sessions/join"
    })
    
    return {
        "session_id": session_id,
        "status": "joined",
        "message": f"Joined session '{session.name}'"
    }


@router.get("/{session_id}/lobby")
async def get_lobby_status(session_id: str):
    """Get the current lobby status."""
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.to_dict()


@router.post("/{session_id}/ready")
async def set_ready_status(session_id: str, player_id: str, ready: bool = True):
    """Set a player's ready status."""
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.set_player_ready(player_id, ready):
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    return {
        "status": "updated",
        "ready": ready,
        "can_start": session.can_start()
    }


@router.post("/{session_id}/start")
async def start_competition(session_id: str, player_id: str, background_tasks: BackgroundTasks):
    """Start the competition (host only)."""
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if player is host
    host = next((p for p in session.players if p.is_host), None)
    if not host or host.player_id != player_id:
        raise HTTPException(status_code=403, detail="Only the host can start the competition")
    
    # Check if can start
    if not session.can_start():
        raise HTTPException(status_code=400, detail="Not all players are ready")
    
    # Update session status
    session.status = "in_progress"
    session.started_at = datetime.utcnow()
    
    # Start the actual competition in background
    background_tasks.add_task(run_competition, session_id, session.to_dict())
    
    logger.info(f"Competition started", extra={
        "session_id": session_id,
        "num_players": len(session.players),
        "format": session.format,
        "rounds_count": len(session.rounds_config),
        "event_type": "user_activity",
        "activity": "competition_started",
        "endpoint": "/api/sessions/start"
    })
    
    return {
        "status": "started",
        "message": "Competition has started!"
    }


@router.post("/{session_id}/leave")
async def leave_session(session_id: str, player_id: str):
    """Leave a session."""
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "waiting":
        raise HTTPException(status_code=400, detail="Cannot leave a session in progress")
    
    if not session.remove_player(player_id):
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # If no players left, delete session
    if len(session.players) == 0:
        del sessions[session_id]
        del join_codes[session.join_code]
        logger.info(f"Session deleted (no players)", extra={
            "session_id": session_id,
            "event_type": "user_activity",
            "activity": "session_deleted_empty",
            "endpoint": "/api/sessions/leave"
        })
    
    return {
        "status": "left",
        "message": "Left the session"
    }


@router.get("/templates/quick-match")
async def get_quick_match_templates():
    """Get quick match templates for easy session creation."""
    logger.info(
        "Quick match templates viewed",
        extra={
            "event_type": "user_activity",
            "activity": "quick_match_templates_view",
            "endpoint": "/api/sessions/templates/quick-match"
        }
    )
    
    # Ensure games are registered
    if not game_registry.list_games():
        register_builtin_games()
    
    templates = []
    
    # Add templates for each available game
    for game_info in game_registry.list_games():
        game_name = game_info["name"]
        display_name = game_info["display_name"]
        
        templates.append({
            "name": f"Quick {display_name}",
            "game": game_name,
            "description": f"Jump into a quick {display_name} match",
            "difficulty": "medium",
            "estimated_duration": 5 if game_name == "minesweeper" else 10
        })
    
    return templates


@router.get("/active")
async def get_active_sessions(limit: int = 10):
    """Get list of active public sessions."""
    active_sessions = []
    
    for session in sessions.values():
        if session.is_public and session.status == "waiting":
            active_sessions.append({
                "session_id": session.session_id,
                "name": session.name,
                "format": session.format,
                "players_count": len(session.players),
                "max_players": session.max_players,
                "join_code": session.join_code,
                "created_at": session.created_at.isoformat()
            })
    
    # Sort by creation time, newest first
    active_sessions.sort(key=lambda x: x["created_at"], reverse=True)
    
    return active_sessions[:limit]


@router.get("/{session_id}/status")
async def get_competition_status(session_id: str):
    """Get the current competition status."""
    session = sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "players": [p.player_name for p in session.players]
    }


# Background task to clean up old sessions
async def cleanup_old_sessions():
    """Remove sessions older than 1 hour."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        
        now = datetime.utcnow()
        to_delete = []
        
        for session_id, session in sessions.items():
            age = (now - session.created_at).total_seconds()
            if age > 3600 and session.status != "in_progress":  # 1 hour
                to_delete.append(session_id)
        
        for session_id in to_delete:
            session = sessions[session_id]
            del join_codes[session.join_code]
            del sessions[session_id]
            logger.info(f"Cleaned up old session", extra={
                "session_id": session_id,
                "age_seconds": age,
                "event_type": "system_activity",
                "activity": "session_cleanup"
            })