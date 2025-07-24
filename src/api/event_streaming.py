"""Server-Sent Events (SSE) for live game streaming."""

import asyncio
import json
from typing import Dict, Optional, AsyncGenerator
from datetime import datetime, timezone
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.core.logging_config import get_logger

logger = get_logger("api.event_streaming")

router = APIRouter(prefix="/api/stream", tags=["streaming"])

# Event queues for each game session
game_event_queues: Dict[str, asyncio.Queue] = {}
# Active connections per game
game_connections: Dict[str, int] = defaultdict(int)


class EventType:
    """Event types for streaming."""
    GAME_STARTED = "game_started"
    GAME_COMPLETED = "game_completed"
    GAME_WON = "game_won"
    GAME_LOST = "game_lost"
    MOVE_STARTED = "move_started"
    MOVE_THINKING = "move_thinking"
    MOVE_REASONING = "move_reasoning"
    MOVE_COMPLETED = "move_completed"
    MOVE_FAILED = "move_failed"
    BOARD_UPDATE = "board_update"
    METRICS_UPDATE = "metrics_update"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


async def publish_event(job_id: str, event_type: str, data: Dict):
    """Publish an event to all connected clients for a game."""
    event = {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    
    # Create queue if it doesn't exist
    if job_id not in game_event_queues:
        game_event_queues[job_id] = asyncio.Queue(maxsize=1000)
        logger.debug(f"Created event queue for game {job_id}")
    
    queue = game_event_queues[job_id]
    # Don't block if queue is full
    try:
        await queue.put(event)
        logger.debug(f"Published {event_type} event for game {job_id}")
    except asyncio.QueueFull:
        logger.warning(f"Event queue full for game {job_id}, dropping event")


async def event_generator(request: Request, job_id: str) -> AsyncGenerator:
    """Generate events for SSE streaming."""
    # Create queue if it doesn't exist
    if job_id not in game_event_queues:
        game_event_queues[job_id] = asyncio.Queue(maxsize=1000)
        logger.debug(f"Created event queue for game {job_id} on client connect")
    
    # Register connection
    game_connections[job_id] += 1
    queue = game_event_queues[job_id]
    
    logger.info(f"Client connected to game stream {job_id} (total: {game_connections[job_id]})")
    
    try:
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        }
        
        # Stream events
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
                
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                # Format event for SSE
                yield {
                    "event": event["type"],
                    "data": json.dumps({
                        "timestamp": event["timestamp"],
                        **event["data"]
                    })
                }
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield {
                    "event": "ping",
                    "data": json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                }
                
    except asyncio.CancelledError:
        logger.info(f"Client disconnected from game stream {job_id}")
    finally:
        # Cleanup connection
        game_connections[job_id] -= 1
        if game_connections[job_id] == 0:
            # Remove queue if no more connections
            if job_id in game_event_queues:
                del game_event_queues[job_id]
            logger.info(f"Cleaned up event queue for game {job_id}")


@router.get("/games/{job_id}/events")
async def stream_game_events(job_id: str, request: Request):
    """Stream live events for a game session using SSE."""
    logger.info(f"Starting event stream for game {job_id}")
    
    # Create event source response
    return EventSourceResponse(
        event_generator(request, job_id),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


# Helper functions for publishing specific event types

async def publish_game_started(job_id: str, model_name: str, num_games: int):
    """Publish game started event."""
    await publish_event(job_id, EventType.GAME_STARTED, {
        "model_name": model_name,
        "num_games": num_games,
        "message": f"Starting {num_games} games with {model_name}"
    })


async def publish_move_thinking(job_id: str, game_num: int, move_num: int, board_state: str):
    """Publish move thinking event."""
    await publish_event(job_id, EventType.MOVE_THINKING, {
        "game_num": game_num,
        "move_num": move_num,
        "board_state": board_state,
        "message": f"Thinking about move {move_num}..."
    })


async def publish_move_reasoning(job_id: str, game_num: int, move_num: int, reasoning: str, partial: bool = False):
    """Publish move reasoning event (can be partial for streaming)."""
    await publish_event(job_id, EventType.MOVE_REASONING, {
        "game_num": game_num,
        "move_num": move_num,
        "reasoning": reasoning,
        "partial": partial,
        "message": "AI reasoning" if not partial else "AI reasoning (streaming)..."
    })


async def publish_move_completed(job_id: str, game_num: int, move_num: int, action: str, 
                               success: bool, board_state: Optional[str] = None,
                               move_details: Optional[Dict] = None):
    """Publish move completed event."""
    event_data = {
        "game_num": game_num,
        "move_num": move_num,
        "action": action,
        "success": success,
        "board_state": board_state,
        "message": f"{action} - {'Success' if success else 'Failed'}"
    }
    
    # Add move details if provided
    if move_details:
        event_data["move_details"] = move_details
    
    await publish_event(job_id, EventType.MOVE_COMPLETED, event_data)


async def publish_game_completed(job_id: str, game_num: int, won: bool, moves: int, 
                               coverage: float, duration: float):
    """Publish game completed event."""
    event_type = EventType.GAME_WON if won else EventType.GAME_LOST
    await publish_event(job_id, event_type, {
        "game_num": game_num,
        "won": won,
        "moves": moves,
        "coverage": coverage,
        "duration": duration,
        "message": f"Game {game_num} {'won' if won else 'lost'} in {moves} moves"
    })


async def publish_evaluation_update(evaluation_data: Dict[str, Any]):
    """Publish evaluation score update."""
    session_id = evaluation_data.get("session_id", "global")
    await publish_event(session_id, EventType.METRICS_UPDATE, {
        "type": "evaluation_update",
        "player_id": evaluation_data.get("player_id"),
        "timestamp": evaluation_data.get("timestamp"),
        "scores": evaluation_data.get("scores", {}),
        "breakdown": evaluation_data.get("breakdown", []),
        "current_total": evaluation_data.get("current_total", 0)
    })


async def publish_metrics_update(job_id: str, games_completed: int, games_total: int, 
                               win_rate: float, avg_moves: float):
    """Publish metrics update event."""
    await publish_event(job_id, EventType.METRICS_UPDATE, {
        "games_completed": games_completed,
        "games_total": games_total,
        "win_rate": win_rate,
        "avg_moves": avg_moves,
        "progress": games_completed / games_total if games_total > 0 else 0,
        "message": f"Progress: {games_completed}/{games_total} games"
    })