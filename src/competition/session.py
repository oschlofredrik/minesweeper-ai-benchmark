"""Session management for AI competitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

from src.games.base import GameMode, GameConfig
from src.scoring.framework import ScoringProfile, CompetitionScoring


class SessionStatus(Enum):
    """Status of a competition session."""
    WAITING = "waiting"  # Waiting for players
    ACTIVE = "active"  # Currently playing
    PAUSED = "paused"  # Temporarily paused
    COMPLETED = "completed"  # Finished
    CANCELLED = "cancelled"  # Cancelled


class CompetitionFormat(Enum):
    """Format of the competition."""
    SINGLE_ROUND = "single_round"  # One game, one round
    MULTI_ROUND = "multi_round"  # Multiple rounds, same or different games
    TOURNAMENT = "tournament"  # Elimination or bracket style
    MARATHON = "marathon"  # Continuous play until time limit
    RELAY = "relay"  # Team-based relay format


@dataclass
class RoundConfig:
    """Configuration for a single round."""
    round_number: int
    game_name: str
    game_config: GameConfig
    scoring_profile: ScoringProfile
    time_limit: int  # seconds
    bonus_rules: List[Dict[str, Any]] = field(default_factory=list)
    penalty_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SessionConfig:
    """Complete configuration for a competition session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "AI Competition Session"
    description: str = ""
    format: CompetitionFormat = CompetitionFormat.SINGLE_ROUND
    rounds: List[RoundConfig] = field(default_factory=list)
    max_players: int = 50
    min_players: int = 1
    ai_model: str = "gpt-4"  # Default AI model
    allow_model_selection: bool = True  # Players can choose their AI model
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    join_code: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    is_public: bool = True
    creator_id: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "description": self.description,
            "format": self.format.value,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "game_name": r.game_name,
                    "game_config": {
                        "difficulty": r.game_config.difficulty,
                        "mode": r.game_config.mode.value,
                        "custom_settings": r.game_config.custom_settings,
                        "time_limit": r.game_config.time_limit
                    },
                    "scoring_profile": {
                        "name": r.scoring_profile.name,
                        "weights": [
                            {"component": w.component_name, "weight": w.weight}
                            for w in r.scoring_profile.weights
                        ]
                    },
                    "time_limit": r.time_limit,
                    "bonus_rules": r.bonus_rules,
                    "penalty_rules": r.penalty_rules
                }
                for r in self.rounds
            ],
            "max_players": self.max_players,
            "min_players": self.min_players,
            "ai_model": self.ai_model,
            "allow_model_selection": self.allow_model_selection,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "join_code": self.join_code,
            "is_public": self.is_public,
            "creator_id": self.creator_id,
            "tags": self.tags
        }


@dataclass
class Player:
    """Player in a competition session."""
    player_id: str
    name: str
    ai_model: str
    joined_at: datetime
    is_ready: bool = False
    current_round: int = 0
    scores: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompetitionSession:
    """Manages a live competition session."""
    
    def __init__(self, config: SessionConfig):
        self.config = config
        self.status = SessionStatus.WAITING
        self.players: Dict[str, Player] = {}
        self.current_round = 0
        self.round_results: Dict[int, Dict[str, Any]] = {}
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
    
    def add_player(self, player_id: str, name: str, ai_model: Optional[str] = None) -> bool:
        """Add a player to the session."""
        if len(self.players) >= self.config.max_players:
            return False
        
        if player_id in self.players:
            return False
        
        if not self.config.allow_model_selection:
            ai_model = self.config.ai_model
        elif ai_model is None:
            ai_model = self.config.ai_model
        
        self.players[player_id] = Player(
            player_id=player_id,
            name=name,
            ai_model=ai_model,
            joined_at=datetime.utcnow()
        )
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the session."""
        if player_id in self.players:
            del self.players[player_id]
            return True
        return False
    
    def set_player_ready(self, player_id: str, ready: bool = True) -> bool:
        """Set a player's ready status."""
        if player_id in self.players:
            self.players[player_id].is_ready = ready
            return True
        return False
    
    def can_start(self) -> bool:
        """Check if the session can start."""
        if len(self.players) < self.config.min_players:
            return False
        
        # All players must be ready
        return all(p.is_ready for p in self.players.values())
    
    def start_session(self) -> bool:
        """Start the competition session."""
        if not self.can_start():
            return False
        
        if self.status != SessionStatus.WAITING:
            return False
        
        self.status = SessionStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.current_round = 1
        return True
    
    def get_current_round_config(self) -> Optional[RoundConfig]:
        """Get configuration for the current round."""
        if self.current_round <= 0 or self.current_round > len(self.config.rounds):
            return None
        return self.config.rounds[self.current_round - 1]
    
    def advance_round(self) -> bool:
        """Move to the next round."""
        if self.current_round >= len(self.config.rounds):
            # No more rounds
            self.end_session()
            return False
        
        self.current_round += 1
        return True
    
    def record_round_result(self, player_id: str, round_number: int, result: Dict[str, Any]):
        """Record a player's result for a round."""
        if round_number not in self.round_results:
            self.round_results[round_number] = {}
        
        self.round_results[round_number][player_id] = result
        
        # Update player's score list
        if player_id in self.players:
            score = result.get("final_score", 0)
            if len(self.players[player_id].scores) < round_number:
                self.players[player_id].scores.extend([0] * (round_number - len(self.players[player_id].scores)))
            if len(self.players[player_id].scores) == round_number - 1:
                self.players[player_id].scores.append(score)
            else:
                self.players[player_id].scores[round_number - 1] = score
    
    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get current leaderboard."""
        leaderboard = []
        
        for player_id, player in self.players.items():
            total_score = sum(player.scores)
            avg_score = total_score / len(player.scores) if player.scores else 0
            
            leaderboard.append({
                "player_id": player_id,
                "name": player.name,
                "ai_model": player.ai_model,
                "total_score": total_score,
                "average_score": avg_score,
                "rounds_played": len(player.scores),
                "scores": player.scores
            })
        
        # Sort by total score
        leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard
    
    def pause_session(self):
        """Pause the session."""
        if self.status == SessionStatus.ACTIVE:
            self.status = SessionStatus.PAUSED
    
    def resume_session(self):
        """Resume a paused session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
    
    def end_session(self):
        """End the session."""
        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.utcnow()
    
    def cancel_session(self):
        """Cancel the session."""
        self.status = SessionStatus.CANCELLED
        self.ended_at = datetime.utcnow()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the session."""
        return {
            "session_id": self.config.session_id,
            "name": self.config.name,
            "status": self.status.value,
            "format": self.config.format.value,
            "players": len(self.players),
            "rounds_total": len(self.config.rounds),
            "rounds_completed": self.current_round - 1 if self.status == SessionStatus.COMPLETED else self.current_round,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration": (self.ended_at - self.started_at).total_seconds() if self.ended_at and self.started_at else None,
            "join_code": self.config.join_code,
            "leaderboard": self.get_leaderboard() if self.status == SessionStatus.COMPLETED else None
        }


class SessionBuilder:
    """Builder for creating competition sessions with various presets."""
    
    @staticmethod
    def create_quick_match(game_name: str, ai_model: str = "gpt-4") -> SessionConfig:
        """Create a quick single-game match."""
        from src.scoring.framework import StandardScoringProfiles
        
        return SessionConfig(
            name=f"Quick {game_name} Match",
            description="A quick single-round competition",
            format=CompetitionFormat.SINGLE_ROUND,
            rounds=[
                RoundConfig(
                    round_number=1,
                    game_name=game_name,
                    game_config=GameConfig(difficulty="medium", mode=GameMode.SPEED),
                    scoring_profile=StandardScoringProfiles.SPEED_DEMON,
                    time_limit=300
                )
            ],
            ai_model=ai_model,
            max_players=20
        )
    
    @staticmethod
    def create_tournament(games: List[str], rounds_per_game: int = 1) -> SessionConfig:
        """Create a tournament with multiple games."""
        from src.scoring.framework import StandardScoringProfiles
        
        rounds = []
        round_num = 1
        
        # Alternate between different scoring profiles
        profiles = [
            StandardScoringProfiles.SPEED_DEMON,
            StandardScoringProfiles.PERFECTIONIST,
            StandardScoringProfiles.EFFICIENCY_MASTER
        ]
        
        for i, game in enumerate(games):
            for j in range(rounds_per_game):
                rounds.append(
                    RoundConfig(
                        round_number=round_num,
                        game_name=game,
                        game_config=GameConfig(
                            difficulty="medium" if j == 0 else "hard",
                            mode=GameMode.MIXED
                        ),
                        scoring_profile=profiles[round_num % len(profiles)],
                        time_limit=600
                    )
                )
                round_num += 1
        
        return SessionConfig(
            name="AI Tournament",
            description="Multi-game tournament with varying challenges",
            format=CompetitionFormat.TOURNAMENT,
            rounds=rounds,
            max_players=32,
            min_players=4
        )
    
    @staticmethod
    def create_educational_session(topic: str, games: List[str]) -> SessionConfig:
        """Create an educational session focused on learning."""
        from src.scoring.framework import StandardScoringProfiles
        
        rounds = []
        difficulties = ["easy", "easy", "medium", "medium", "hard"]
        
        for i, game in enumerate(games):
            rounds.append(
                RoundConfig(
                    round_number=i + 1,
                    game_name=game,
                    game_config=GameConfig(
                        difficulty=difficulties[i % len(difficulties)],
                        mode=GameMode.REASONING
                    ),
                    scoring_profile=StandardScoringProfiles.EXPLANATION_EXPERT,
                    time_limit=900,  # 15 minutes for educational focus
                    bonus_rules=[
                        {
                            "condition": {"field": "explanation_quality", "operator": "greater_than", "value": 0.8},
                            "type": "multiply",
                            "value": 1.2
                        }
                    ]
                )
            )
        
        return SessionConfig(
            name=f"Learn {topic}",
            description=f"Educational session focused on {topic}",
            format=CompetitionFormat.MULTI_ROUND,
            rounds=rounds,
            max_players=30,
            tags=["educational", topic.lower()]
        )