"""Lobby system with practice area and warm-up features."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import random
import string

from src.competition.session import CompetitionSession, SessionConfig, Player
from src.games.registry import game_registry
from src.prompts.template_system import PromptAssistant, create_default_templates


class LobbyStatus(Enum):
    """Status of a lobby."""
    WAITING = "waiting"  # Waiting for players
    PRACTICING = "practicing"  # Practice mode active
    STARTING_SOON = "starting_soon"  # About to start
    IN_PROGRESS = "in_progress"  # Competition active
    FINISHED = "finished"  # Competition ended


class PracticeMode(Enum):
    """Types of practice available in lobby."""
    TUTORIAL = "tutorial"  # Guided tutorial
    FREE_PLAY = "free_play"  # Practice on sample boards
    PROMPT_LAB = "prompt_lab"  # Test prompts with instant feedback
    STRATEGY_GUIDE = "strategy_guide"  # Interactive strategy lessons
    MINI_CHALLENGE = "mini_challenge"  # Quick warm-up challenges


@dataclass
class PracticeActivity:
    """A practice activity in the lobby."""
    activity_id: str
    mode: PracticeMode
    game_name: str
    title: str
    description: str
    estimated_duration: int  # seconds
    difficulty: str
    content: Dict[str, Any]
    completed_by: Set[str] = field(default_factory=set)
    
    def mark_completed(self, player_id: str):
        """Mark activity as completed by a player."""
        self.completed_by.add(player_id)
    
    def is_completed_by(self, player_id: str) -> bool:
        """Check if player has completed this activity."""
        return player_id in self.completed_by


@dataclass
class LobbyChat:
    """Simple chat system for lobby."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    max_messages: int = 100
    
    def add_message(self, player_id: str, player_name: str, message: str):
        """Add a chat message."""
        self.messages.append({
            "player_id": player_id,
            "player_name": player_name,
            "message": message[:200],  # Limit length
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent messages."""
        return self.messages[-count:]


class CompetitionLobby:
    """Lobby for players waiting to start a competition."""
    
    def __init__(self, session_config: SessionConfig):
        self.session = CompetitionSession(session_config)
        self.status = LobbyStatus.WAITING
        self.practice_activities: List[PracticeActivity] = []
        self.chat = LobbyChat()
        self.prompt_assistant = PromptAssistant()
        self.practice_results: Dict[str, List[Dict[str, Any]]] = {}
        self.warmup_scores: Dict[str, float] = {}
        self.created_at = datetime.utcnow()
        self.start_countdown: Optional[int] = None
        self._event_handlers: Dict[str, List[callable]] = {}
        
        # Initialize practice activities
        self._create_practice_activities()
        
        # Initialize prompt templates
        for template in create_default_templates():
            self.prompt_assistant.register_template(template)
    
    def _create_practice_activities(self):
        """Create practice activities based on session games."""
        games_in_session = set()
        for round_config in self.session.config.rounds:
            games_in_session.add(round_config.game_name)
        
        for game_name in games_in_session:
            # Tutorial activity
            self.practice_activities.append(PracticeActivity(
                activity_id=f"tutorial_{game_name}",
                mode=PracticeMode.TUTORIAL,
                game_name=game_name,
                title=f"Learn {game_name.title()}",
                description=f"Quick tutorial on {game_name} basics",
                estimated_duration=180,
                difficulty="beginner",
                content={
                    "steps": self._get_tutorial_steps(game_name),
                    "interactive": True
                }
            ))
            
            # Free play activity
            self.practice_activities.append(PracticeActivity(
                activity_id=f"freeplay_{game_name}",
                mode=PracticeMode.FREE_PLAY,
                game_name=game_name,
                title=f"Practice {game_name.title()}",
                description="Try the game with instant AI feedback",
                estimated_duration=300,
                difficulty="adaptive",
                content={
                    "board_size": "small",
                    "unlimited_attempts": True
                }
            ))
            
            # Prompt lab
            self.practice_activities.append(PracticeActivity(
                activity_id=f"promptlab_{game_name}",
                mode=PracticeMode.PROMPT_LAB,
                game_name=game_name,
                title="Prompt Laboratory",
                description="Test and refine your prompts",
                estimated_duration=240,
                difficulty="intermediate",
                content={
                    "test_scenarios": 3,
                    "instant_feedback": True,
                    "comparison_mode": True
                }
            ))
        
        # Add general activities
        self.practice_activities.append(PracticeActivity(
            activity_id="strategy_guide",
            mode=PracticeMode.STRATEGY_GUIDE,
            game_name="all",
            title="Strategy Masterclass",
            description="Learn winning prompt strategies",
            estimated_duration=300,
            difficulty="intermediate",
            content={
                "lessons": [
                    "Chain of Thought",
                    "Constraint Analysis",
                    "Risk Assessment",
                    "Pattern Recognition"
                ]
            }
        ))
        
        self.practice_activities.append(PracticeActivity(
            activity_id="mini_challenge",
            mode=PracticeMode.MINI_CHALLENGE,
            game_name="all",
            title="Quick Challenge",
            description="5-minute warm-up puzzle",
            estimated_duration=300,
            difficulty="easy",
            content={
                "challenge_type": "daily",
                "leaderboard": True
            }
        ))
    
    def _get_tutorial_steps(self, game_name: str) -> List[Dict[str, str]]:
        """Get tutorial steps for a game."""
        tutorials = {
            "minesweeper": [
                {"title": "Understanding the Board", "content": "Numbers show adjacent mines..."},
                {"title": "Safe Moves", "content": "Start with cells that have clear constraints..."},
                {"title": "Flagging Strategy", "content": "Mark confirmed mines to track progress..."}
            ],
            "number_puzzle": [
                {"title": "Binary Search", "content": "Cut the search space in half each time..."},
                {"title": "Tracking Bounds", "content": "Update your min/max after each guess..."}
            ]
        }
        return tutorials.get(game_name, [{"title": "Basics", "content": "Learn the game rules..."}])
    
    async def add_player(self, player_id: str, player_name: str) -> Dict[str, Any]:
        """Add a player to the lobby."""
        if not self.session.add_player(player_id, player_name):
            return {"success": False, "error": "Lobby is full or player already joined"}
        
        # Initialize player data
        self.practice_results[player_id] = []
        self.warmup_scores[player_id] = 0.0
        
        # Announce in chat
        self.chat.add_message("system", "System", f"{player_name} joined the lobby")
        
        # Emit event
        await self._emit_event("player_joined", {
            "player_id": player_id,
            "player_name": player_name,
            "total_players": len(self.session.players)
        })
        
        return {
            "success": True,
            "lobby_info": self.get_lobby_info(),
            "practice_activities": self.get_available_activities(player_id)
        }
    
    async def remove_player(self, player_id: str) -> bool:
        """Remove a player from the lobby."""
        if player_id in self.session.players:
            player_name = self.session.players[player_id].name
            self.session.remove_player(player_id)
            
            # Clean up player data
            if player_id in self.practice_results:
                del self.practice_results[player_id]
            if player_id in self.warmup_scores:
                del self.warmup_scores[player_id]
            
            # Announce in chat
            self.chat.add_message("system", "System", f"{player_name} left the lobby")
            
            await self._emit_event("player_left", {
                "player_id": player_id,
                "total_players": len(self.session.players)
            })
            
            return True
        return False
    
    async def set_player_ready(self, player_id: str, ready: bool = True) -> Dict[str, Any]:
        """Set a player's ready status."""
        if not self.session.set_player_ready(player_id, ready):
            return {"success": False, "error": "Player not found"}
        
        await self._emit_event("player_ready_changed", {
            "player_id": player_id,
            "ready": ready,
            "ready_count": sum(1 for p in self.session.players.values() if p.is_ready),
            "total_players": len(self.session.players)
        })
        
        # Check if we can start
        if self.session.can_start() and self.status == LobbyStatus.WAITING:
            await self._initiate_countdown()
        
        return {"success": True, "can_start": self.session.can_start()}
    
    async def _initiate_countdown(self):
        """Start the countdown to begin."""
        self.status = LobbyStatus.STARTING_SOON
        self.start_countdown = 10  # 10 seconds
        
        await self._emit_event("countdown_started", {
            "seconds": self.start_countdown
        })
        
        # Start countdown task
        asyncio.create_task(self._countdown_timer())
    
    async def _countdown_timer(self):
        """Handle the countdown timer."""
        while self.start_countdown > 0:
            await asyncio.sleep(1)
            self.start_countdown -= 1
            
            await self._emit_event("countdown_update", {
                "seconds": self.start_countdown
            })
            
            # Check if conditions still met
            if not self.session.can_start():
                self.status = LobbyStatus.WAITING
                self.start_countdown = None
                await self._emit_event("countdown_cancelled", {})
                return
        
        # Start the competition
        await self.start_competition()
    
    async def start_competition(self):
        """Start the competition."""
        if self.session.start_session():
            self.status = LobbyStatus.IN_PROGRESS
            
            await self._emit_event("competition_started", {
                "session_id": self.session.config.session_id,
                "first_round": self.session.get_current_round_config()
            })
            
            return True
        return False
    
    async def start_practice_activity(
        self,
        player_id: str,
        activity_id: str
    ) -> Dict[str, Any]:
        """Start a practice activity for a player."""
        activity = next((a for a in self.practice_activities if a.activity_id == activity_id), None)
        
        if not activity:
            return {"success": False, "error": "Activity not found"}
        
        # Generate practice content based on activity type
        if activity.mode == PracticeMode.TUTORIAL:
            content = self._generate_tutorial_content(activity)
        elif activity.mode == PracticeMode.FREE_PLAY:
            content = self._generate_freeplay_content(activity)
        elif activity.mode == PracticeMode.PROMPT_LAB:
            content = self._generate_promptlab_content(activity)
        elif activity.mode == PracticeMode.STRATEGY_GUIDE:
            content = self._generate_strategy_content(activity)
        elif activity.mode == PracticeMode.MINI_CHALLENGE:
            content = self._generate_challenge_content(activity)
        else:
            content = {}
        
        # Record start
        self.practice_results[player_id].append({
            "activity_id": activity_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": "in_progress"
        })
        
        await self._emit_event("practice_started", {
            "player_id": player_id,
            "activity_id": activity_id
        })
        
        return {
            "success": True,
            "activity": activity,
            "content": content
        }
    
    def _generate_tutorial_content(self, activity: PracticeActivity) -> Dict[str, Any]:
        """Generate tutorial content."""
        game = game_registry.get_game(activity.game_name)
        if not game:
            return {}
        
        return {
            "game_info": {
                "name": game.display_name,
                "description": game.description,
                "rules": game.get_move_format_description()
            },
            "steps": activity.content["steps"],
            "practice_board": self._create_simple_game_instance(activity.game_name),
            "hints": [
                "Start with the basics",
                "Focus on understanding the rules",
                "Try different approaches"
            ]
        }
    
    def _generate_freeplay_content(self, activity: PracticeActivity) -> Dict[str, Any]:
        """Generate free play content."""
        return {
            "game_instance": self._create_simple_game_instance(activity.game_name),
            "suggested_prompts": self.prompt_assistant.get_templates_for_game(
                activity.game_name,
                level=None,
                category=None
            )[:3],
            "instant_feedback": True,
            "retry_allowed": True
        }
    
    def _generate_promptlab_content(self, activity: PracticeActivity) -> Dict[str, Any]:
        """Generate prompt lab content."""
        return {
            "test_scenarios": [
                self._create_simple_game_instance(activity.game_name)
                for _ in range(activity.content["test_scenarios"])
            ],
            "prompt_templates": self.prompt_assistant.get_templates_for_game(activity.game_name),
            "analysis_tools": {
                "quality_checker": True,
                "comparison_mode": True,
                "suggestion_engine": True
            }
        }
    
    def _generate_strategy_content(self, activity: PracticeActivity) -> Dict[str, Any]:
        """Generate strategy guide content."""
        return {
            "lessons": activity.content["lessons"],
            "interactive_examples": True,
            "quiz_questions": [
                {
                    "question": "What's the benefit of chain-of-thought prompting?",
                    "options": [
                        "Makes the AI think step by step",
                        "Reduces token usage",
                        "Increases speed",
                        "Simplifies the prompt"
                    ],
                    "correct": 0
                }
            ]
        }
    
    def _generate_challenge_content(self, activity: PracticeActivity) -> Dict[str, Any]:
        """Generate mini challenge content."""
        # Pick a random game from the session
        round_config = random.choice(self.session.config.rounds)
        game_name = round_config.game_name
        
        return {
            "challenge": {
                "game_name": game_name,
                "instance": self._create_simple_game_instance(game_name),
                "time_limit": 300,
                "goal": "Complete in minimum moves"
            },
            "leaderboard": self._get_challenge_leaderboard()
        }
    
    def _create_simple_game_instance(self, game_name: str) -> Dict[str, Any]:
        """Create a simple game instance for practice."""
        # This would actually create a game instance
        # For now, return mock data
        return {
            "game_name": game_name,
            "difficulty": "easy",
            "practice_mode": True,
            "state": "PRACTICE_STATE_DATA"
        }
    
    def _get_challenge_leaderboard(self) -> List[Dict[str, Any]]:
        """Get mini challenge leaderboard."""
        # Sort players by warmup scores
        leaderboard = []
        for player_id, score in sorted(
            self.warmup_scores.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if player_id in self.session.players:
                player = self.session.players[player_id]
                leaderboard.append({
                    "rank": len(leaderboard) + 1,
                    "player_name": player.name,
                    "score": score
                })
        
        return leaderboard[:10]  # Top 10
    
    async def complete_practice_activity(
        self,
        player_id: str,
        activity_id: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete a practice activity."""
        activity = next((a for a in self.practice_activities if a.activity_id == activity_id), None)
        
        if not activity:
            return {"success": False, "error": "Activity not found"}
        
        # Mark as completed
        activity.mark_completed(player_id)
        
        # Update practice results
        for result in self.practice_results[player_id]:
            if result["activity_id"] == activity_id and result["status"] == "in_progress":
                result["status"] = "completed"
                result["completed_at"] = datetime.utcnow().isoformat()
                result["results"] = results
                break
        
        # Update warmup score
        score_earned = results.get("score", 0) * 10  # Scale up for display
        self.warmup_scores[player_id] = self.warmup_scores.get(player_id, 0) + score_earned
        
        await self._emit_event("practice_completed", {
            "player_id": player_id,
            "activity_id": activity_id,
            "score_earned": score_earned,
            "total_warmup_score": self.warmup_scores[player_id]
        })
        
        return {
            "success": True,
            "score_earned": score_earned,
            "total_warmup_score": self.warmup_scores[player_id],
            "achievement": self._check_achievement(player_id, activity_id, results)
        }
    
    def _check_achievement(
        self,
        player_id: str,
        activity_id: str,
        results: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Check if player earned an achievement."""
        # Simple achievement system
        if "tutorial" in activity_id and results.get("completion_rate", 0) >= 1.0:
            return {
                "name": "Quick Learner",
                "description": "Completed a tutorial",
                "icon": "🎓"
            }
        elif "challenge" in activity_id and results.get("score", 0) >= 0.9:
            return {
                "name": "Challenge Master",
                "description": "Scored 90%+ on mini challenge",
                "icon": "🏆"
            }
        
        return None
    
    async def send_chat_message(
        self,
        player_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Send a chat message."""
        if player_id not in self.session.players:
            return {"success": False, "error": "Player not in lobby"}
        
        player = self.session.players[player_id]
        self.chat.add_message(player_id, player.name, message)
        
        await self._emit_event("chat_message", {
            "player_id": player_id,
            "player_name": player.name,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"success": True}
    
    def get_available_activities(self, player_id: str) -> List[Dict[str, Any]]:
        """Get available practice activities for a player."""
        activities = []
        
        for activity in self.practice_activities:
            activities.append({
                "activity_id": activity.activity_id,
                "mode": activity.mode.value,
                "title": activity.title,
                "description": activity.description,
                "duration": activity.estimated_duration,
                "difficulty": activity.difficulty,
                "completed": activity.is_completed_by(player_id),
                "game_name": activity.game_name
            })
        
        return activities
    
    def get_lobby_info(self) -> Dict[str, Any]:
        """Get current lobby information."""
        return {
            "session_id": self.session.config.session_id,
            "session_name": self.session.config.name,
            "status": self.status.value,
            "join_code": self.session.config.join_code,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "ready": p.is_ready,
                    "warmup_score": self.warmup_scores.get(p.player_id, 0)
                }
                for p in self.session.players.values()
            ],
            "player_count": len(self.session.players),
            "max_players": self.session.config.max_players,
            "min_players": self.session.config.min_players,
            "can_start": self.session.can_start(),
            "countdown": self.start_countdown,
            "practice_enabled": self.status == LobbyStatus.WAITING,
            "chat_messages": self.chat.get_recent_messages(),
            "session_config": {
                "format": self.session.config.format.value,
                "rounds": len(self.session.config.rounds),
                "games": list(set(r.game_name for r in self.session.config.rounds))
            }
        }
    
    def on(self, event: str, handler: callable):
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Any):
        """Emit an event to all handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                await handler(data)