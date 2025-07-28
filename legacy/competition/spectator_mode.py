"""Spectator mode with multi-view options for AI competitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json


class ViewMode(Enum):
    """Different viewing modes for spectators."""
    OVERVIEW = "overview"  # Bird's eye view of all players
    FOCUS = "focus"  # Focus on single player
    SPLIT = "split"  # Split screen (2-4 players)
    LEADERBOARD = "leaderboard"  # Leaderboard focused
    COMMENTARY = "commentary"  # Host commentary view
    HIGHLIGHTS = "highlights"  # Auto-switching to interesting moments


class SpectatorPermission(Enum):
    """Permission levels for spectators."""
    PUBLIC = "public"  # Anyone can watch
    LINK_ONLY = "link_only"  # Need direct link
    APPROVED = "approved"  # Need host approval
    EDUCATIONAL = "educational"  # Special educational access


@dataclass
class ViewConfiguration:
    """Configuration for a spectator view."""
    mode: ViewMode
    target_players: List[str] = field(default_factory=list)  # For focus/split modes
    show_prompts: bool = True
    prompt_delay: int = 30  # Seconds to delay prompt display
    show_scores: bool = True
    show_reasoning: bool = True
    enable_predictions: bool = True
    enable_chat: bool = True
    auto_switch_interval: int = 20  # For highlights mode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode.value,
            "target_players": self.target_players,
            "show_prompts": self.show_prompts,
            "prompt_delay": self.prompt_delay,
            "show_scores": self.show_scores,
            "show_reasoning": self.show_reasoning,
            "enable_predictions": self.enable_predictions,
            "enable_chat": self.enable_chat,
            "auto_switch_interval": self.auto_switch_interval
        }


@dataclass
class SpectatorPrediction:
    """A prediction made by a spectator."""
    spectator_id: str
    round_number: int
    prediction_type: str  # "winner", "score_range", "completion_time"
    prediction_data: Dict[str, Any]
    made_at: datetime
    resolved: bool = False
    correct: Optional[bool] = None
    points_earned: int = 0


@dataclass
class HighlightMoment:
    """A highlight moment in the competition."""
    moment_id: str
    timestamp: datetime
    round_number: int
    player_id: Optional[str]
    moment_type: str  # "high_score", "comeback", "fast_solve", "creative_prompt"
    title: str
    description: str
    clip_data: Dict[str, Any]  # Game state, prompt, result
    importance_score: float  # 0-1, for auto-switching


class SpectatorMode:
    """Manages spectator viewing experience."""
    
    def __init__(self, session_id: str, permission: SpectatorPermission = SpectatorPermission.PUBLIC):
        self.session_id = session_id
        self.permission = permission
        self.spectators: Dict[str, Dict[str, Any]] = {}  # spectator_id -> info
        self.view_configs: Dict[str, ViewConfiguration] = {}  # spectator_id -> config
        self.predictions: List[SpectatorPrediction] = []
        self.highlights: List[HighlightMoment] = []
        self.spectator_chat: List[Dict[str, Any]] = []
        self.view_stats: Dict[str, Dict[str, Any]] = {}  # Track what spectators watch
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._highlight_detector = HighlightDetector()
        
    async def add_spectator(
        self,
        spectator_id: str,
        name: str,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new spectator."""
        # Check permission
        if self.permission == SpectatorPermission.APPROVED:
            # Would check approval list
            if not self._is_approved(spectator_id, access_token):
                return {"success": False, "error": "Not approved to spectate"}
        elif self.permission == SpectatorPermission.LINK_ONLY:
            if not access_token:
                return {"success": False, "error": "Access token required"}
        
        # Add spectator
        self.spectators[spectator_id] = {
            "name": name,
            "joined_at": datetime.utcnow(),
            "prediction_score": 0,
            "watch_time": 0,
            "interactions": 0
        }
        
        # Default view configuration
        self.view_configs[spectator_id] = ViewConfiguration(
            mode=ViewMode.OVERVIEW
        )
        
        # Initialize view stats
        self.view_stats[spectator_id] = {
            "views_by_player": {},
            "favorite_mode": ViewMode.OVERVIEW,
            "total_predictions": 0
        }
        
        await self._emit_event("spectator_joined", {
            "spectator_id": spectator_id,
            "name": name,
            "total_spectators": len(self.spectators)
        })
        
        return {
            "success": True,
            "view_options": self._get_view_options(),
            "current_state": self._get_spectator_state()
        }
    
    def _is_approved(self, spectator_id: str, access_token: Optional[str]) -> bool:
        """Check if spectator is approved."""
        # In real implementation, check against approval list
        return access_token == "APPROVED_TOKEN"
    
    def _get_view_options(self) -> List[Dict[str, Any]]:
        """Get available view options."""
        return [
            {
                "mode": ViewMode.OVERVIEW.value,
                "name": "Overview",
                "description": "See all players at once",
                "icon": "grid"
            },
            {
                "mode": ViewMode.FOCUS.value,
                "name": "Player Focus",
                "description": "Follow a single player closely",
                "icon": "user"
            },
            {
                "mode": ViewMode.SPLIT.value,
                "name": "Split Screen",
                "description": "Compare 2-4 players side by side",
                "icon": "split"
            },
            {
                "mode": ViewMode.LEADERBOARD.value,
                "name": "Leaderboard",
                "description": "Focus on rankings and scores",
                "icon": "trophy"
            },
            {
                "mode": ViewMode.COMMENTARY.value,
                "name": "Commentary",
                "description": "Host's perspective with annotations",
                "icon": "microphone"
            },
            {
                "mode": ViewMode.HIGHLIGHTS.value,
                "name": "Auto Highlights",
                "description": "Automatically switch to interesting moments",
                "icon": "star"
            }
        ]
    
    def _get_spectator_state(self) -> Dict[str, Any]:
        """Get current state for spectators."""
        return {
            "session_id": self.session_id,
            "spectator_count": len(self.spectators),
            "recent_highlights": [h.__dict__ for h in self.highlights[-5:]],
            "prediction_leaders": self._get_prediction_leaders()
        }
    
    async def update_view_config(
        self,
        spectator_id: str,
        config_update: Dict[str, Any]
    ) -> bool:
        """Update spectator's view configuration."""
        if spectator_id not in self.view_configs:
            return False
        
        config = self.view_configs[spectator_id]
        
        # Update configuration
        if "mode" in config_update:
            config.mode = ViewMode(config_update["mode"])
            self.view_stats[spectator_id]["favorite_mode"] = config.mode
        
        if "target_players" in config_update:
            config.target_players = config_update["target_players"]
            # Track player interest
            for player_id in config.target_players:
                if player_id not in self.view_stats[spectator_id]["views_by_player"]:
                    self.view_stats[spectator_id]["views_by_player"][player_id] = 0
                self.view_stats[spectator_id]["views_by_player"][player_id] += 1
        
        # Update other settings
        for key in ["show_prompts", "prompt_delay", "show_scores", 
                    "show_reasoning", "enable_predictions", "enable_chat"]:
            if key in config_update:
                setattr(config, key, config_update[key])
        
        await self._emit_event("view_config_updated", {
            "spectator_id": spectator_id,
            "new_config": config.to_dict()
        })
        
        return True
    
    async def make_prediction(
        self,
        spectator_id: str,
        round_number: int,
        prediction_type: str,
        prediction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a prediction about the competition."""
        if spectator_id not in self.spectators:
            return {"success": False, "error": "Not a registered spectator"}
        
        # Validate prediction type
        valid_types = ["winner", "score_range", "completion_time", "best_prompt"]
        if prediction_type not in valid_types:
            return {"success": False, "error": "Invalid prediction type"}
        
        # Create prediction
        prediction = SpectatorPrediction(
            spectator_id=spectator_id,
            round_number=round_number,
            prediction_type=prediction_type,
            prediction_data=prediction_data,
            made_at=datetime.utcnow()
        )
        
        self.predictions.append(prediction)
        self.view_stats[spectator_id]["total_predictions"] += 1
        
        await self._emit_event("prediction_made", {
            "spectator_id": spectator_id,
            "prediction_type": prediction_type,
            "round": round_number
        })
        
        return {
            "success": True,
            "prediction_id": len(self.predictions) - 1,
            "potential_points": self._calculate_potential_points(prediction_type)
        }
    
    def _calculate_potential_points(self, prediction_type: str) -> int:
        """Calculate potential points for a prediction."""
        points_map = {
            "winner": 50,
            "score_range": 30,
            "completion_time": 20,
            "best_prompt": 40
        }
        return points_map.get(prediction_type, 10)
    
    async def record_highlight(
        self,
        round_number: int,
        player_id: Optional[str],
        moment_type: str,
        game_state: Dict[str, Any],
        metadata: Dict[str, Any]
    ):
        """Record a highlight moment."""
        # Use highlight detector to determine importance
        importance = self._highlight_detector.calculate_importance(
            moment_type, metadata
        )
        
        if importance < 0.3:  # Threshold for highlights
            return
        
        highlight = HighlightMoment(
            moment_id=f"hl_{len(self.highlights)}",
            timestamp=datetime.utcnow(),
            round_number=round_number,
            player_id=player_id,
            moment_type=moment_type,
            title=self._generate_highlight_title(moment_type, metadata),
            description=self._generate_highlight_description(moment_type, metadata),
            clip_data={
                "game_state": game_state,
                "metadata": metadata
            },
            importance_score=importance
        )
        
        self.highlights.append(highlight)
        
        # Notify spectators in highlights mode
        await self._notify_highlight_viewers(highlight)
        
        await self._emit_event("highlight_recorded", {
            "highlight_id": highlight.moment_id,
            "title": highlight.title,
            "importance": importance
        })
    
    def _generate_highlight_title(self, moment_type: str, metadata: Dict[str, Any]) -> str:
        """Generate title for a highlight."""
        titles = {
            "high_score": f"New High Score: {metadata.get('score', 0):.1f}!",
            "comeback": f"{metadata.get('player_name', 'Player')} Makes a Comeback!",
            "fast_solve": f"Lightning Fast: {metadata.get('time', 0):.1f}s!",
            "creative_prompt": "Creative Approach Discovered!",
            "perfect_game": "Perfect Game Achieved!",
            "close_finish": "Photo Finish!"
        }
        return titles.get(moment_type, "Highlight Moment")
    
    def _generate_highlight_description(
        self,
        moment_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate description for a highlight."""
        # Context-aware descriptions
        if moment_type == "high_score":
            return f"Achieved {metadata.get('score', 0)} points, beating the previous best by {metadata.get('margin', 0)}"
        elif moment_type == "comeback":
            return f"Climbed from position {metadata.get('from_pos', 0)} to {metadata.get('to_pos', 0)}"
        elif moment_type == "creative_prompt":
            return f"Used an innovative {metadata.get('strategy', 'approach')} that surprised everyone"
        
        return "An exciting moment in the competition"
    
    async def _notify_highlight_viewers(self, highlight: HighlightMoment):
        """Notify spectators in highlights mode about new highlight."""
        for spectator_id, config in self.view_configs.items():
            if config.mode == ViewMode.HIGHLIGHTS:
                await self._emit_event("highlight_switch", {
                    "spectator_id": spectator_id,
                    "highlight": highlight.__dict__,
                    "auto_switch": True
                })
    
    async def send_spectator_message(
        self,
        spectator_id: str,
        message: str,
        message_type: str = "chat"
    ) -> bool:
        """Send a message as spectator."""
        if spectator_id not in self.spectators:
            return False
        
        # Check if chat is enabled for this spectator
        config = self.view_configs.get(spectator_id)
        if config and not config.enable_chat and message_type == "chat":
            return False
        
        spectator = self.spectators[spectator_id]
        
        self.spectator_chat.append({
            "spectator_id": spectator_id,
            "name": spectator["name"],
            "message": message[:200],  # Limit length
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep chat size manageable
        if len(self.spectator_chat) > 200:
            self.spectator_chat = self.spectator_chat[-200:]
        
        spectator["interactions"] += 1
        
        await self._emit_event("spectator_message", {
            "spectator_id": spectator_id,
            "message": message,
            "type": message_type
        })
        
        return True
    
    async def resolve_predictions(self, round_number: int, results: Dict[str, Any]):
        """Resolve predictions for a completed round."""
        for prediction in self.predictions:
            if prediction.round_number == round_number and not prediction.resolved:
                prediction.resolved = True
                
                # Check if prediction was correct
                if prediction.prediction_type == "winner":
                    prediction.correct = (
                        prediction.prediction_data.get("player_id") == 
                        results.get("winner_id")
                    )
                elif prediction.prediction_type == "score_range":
                    winner_score = results.get("winner_score", 0)
                    range_min = prediction.prediction_data.get("min", 0)
                    range_max = prediction.prediction_data.get("max", 100)
                    prediction.correct = range_min <= winner_score <= range_max
                # Add more prediction type checks...
                
                # Award points
                if prediction.correct:
                    base_points = self._calculate_potential_points(prediction.prediction_type)
                    # Bonus for early predictions
                    time_bonus = max(0, 60 - (datetime.utcnow() - prediction.made_at).seconds) / 60
                    prediction.points_earned = int(base_points * (1 + time_bonus * 0.5))
                    
                    # Update spectator score
                    if prediction.spectator_id in self.spectators:
                        self.spectators[prediction.spectator_id]["prediction_score"] += prediction.points_earned
        
        await self._emit_event("predictions_resolved", {
            "round": round_number,
            "total_predictions": sum(1 for p in self.predictions if p.round_number == round_number),
            "correct_predictions": sum(
                1 for p in self.predictions 
                if p.round_number == round_number and p.correct
            )
        })
    
    def get_spectator_stats(self, spectator_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific spectator."""
        if spectator_id not in self.spectators:
            return None
        
        spectator = self.spectators[spectator_id]
        view_stats = self.view_stats[spectator_id]
        
        # Calculate watch time
        watch_time = (datetime.utcnow() - spectator["joined_at"]).total_seconds()
        
        # Get prediction accuracy
        spectator_predictions = [p for p in self.predictions if p.spectator_id == spectator_id]
        resolved_predictions = [p for p in spectator_predictions if p.resolved]
        correct_predictions = [p for p in resolved_predictions if p.correct]
        
        accuracy = (
            len(correct_predictions) / len(resolved_predictions) 
            if resolved_predictions else 0
        )
        
        return {
            "spectator_id": spectator_id,
            "name": spectator["name"],
            "watch_time_seconds": watch_time,
            "prediction_score": spectator["prediction_score"],
            "total_predictions": len(spectator_predictions),
            "prediction_accuracy": accuracy,
            "favorite_players": sorted(
                view_stats["views_by_player"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
            "favorite_view_mode": view_stats["favorite_mode"].value,
            "interactions": spectator["interactions"]
        }
    
    def _get_prediction_leaders(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top prediction scorers."""
        leaders = []
        
        for spectator_id, spectator in self.spectators.items():
            leaders.append({
                "spectator_id": spectator_id,
                "name": spectator["name"],
                "score": spectator["prediction_score"]
            })
        
        leaders.sort(key=lambda x: x["score"], reverse=True)
        return leaders[:limit]
    
    def create_clip(
        self,
        spectator_id: str,
        start_time: datetime,
        end_time: datetime,
        title: Optional[str] = None
    ) -> Optional[str]:
        """Create a shareable clip of a moment."""
        if spectator_id not in self.spectators:
            return None
        
        # Find highlights in time range
        relevant_highlights = [
            h for h in self.highlights
            if start_time <= h.timestamp <= end_time
        ]
        
        if not relevant_highlights:
            return None
        
        # Create clip ID
        clip_id = f"clip_{self.session_id}_{len(self.highlights)}"
        
        # In real implementation, this would create a shareable clip
        # For now, return the clip ID
        
        self.spectators[spectator_id]["interactions"] += 5  # Bonus for creating clips
        
        return clip_id
    
    def on(self, event: str, handler: Callable):
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Dict[str, Any]):
        """Emit an event to all handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                await handler(data)


class HighlightDetector:
    """Detects and scores highlight moments."""
    
    def calculate_importance(self, moment_type: str, metadata: Dict[str, Any]) -> float:
        """Calculate importance score for a moment."""
        base_scores = {
            "high_score": 0.7,
            "comeback": 0.8,
            "fast_solve": 0.6,
            "creative_prompt": 0.9,
            "perfect_game": 1.0,
            "close_finish": 0.8,
            "first_completion": 0.5,
            "streak": 0.6
        }
        
        score = base_scores.get(moment_type, 0.4)
        
        # Adjust based on metadata
        if moment_type == "high_score":
            margin = metadata.get("margin", 0)
            if margin > 20:
                score += 0.2
        elif moment_type == "comeback":
            positions_gained = metadata.get("from_pos", 0) - metadata.get("to_pos", 0)
            score += min(0.3, positions_gained * 0.05)
        elif moment_type == "fast_solve":
            time_saved = metadata.get("time_saved_percent", 0)
            score += min(0.3, time_saved / 100)
        
        return min(1.0, score)