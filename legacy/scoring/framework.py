"""Flexible scoring framework for the AI competition platform."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import math


@dataclass
class ScoringWeight:
    """Weight configuration for a scoring component."""
    component_name: str
    weight: float  # 0.0 to 1.0
    
    def __post_init__(self):
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")


@dataclass
class ScoringProfile:
    """A complete scoring profile with weights for different components."""
    name: str
    description: str
    weights: List[ScoringWeight]
    
    def __post_init__(self):
        # Normalize weights to sum to 1.0
        total_weight = sum(w.weight for w in self.weights)
        if total_weight > 0:
            for weight in self.weights:
                weight.weight /= total_weight
    
    def get_weight(self, component_name: str) -> float:
        """Get weight for a specific component."""
        for weight in self.weights:
            if weight.component_name == component_name:
                return weight.weight
        return 0.0


class StandardScoringProfiles:
    """Pre-defined scoring profiles for common competition modes."""
    
    SPEED_DEMON = ScoringProfile(
        name="Speed Demon",
        description="Prioritizes fast completion above all else",
        weights=[
            ScoringWeight("speed", 0.7),
            ScoringWeight("completion", 0.2),
            ScoringWeight("accuracy", 0.1)
        ]
    )
    
    PERFECTIONIST = ScoringProfile(
        name="Perfectionist",
        description="Values accuracy and correctness",
        weights=[
            ScoringWeight("accuracy", 0.5),
            ScoringWeight("efficiency", 0.3),
            ScoringWeight("reasoning", 0.2)
        ]
    )
    
    EFFICIENCY_MASTER = ScoringProfile(
        name="Efficiency Master",
        description="Rewards optimal solutions with minimal moves",
        weights=[
            ScoringWeight("efficiency", 0.6),
            ScoringWeight("accuracy", 0.3),
            ScoringWeight("speed", 0.1)
        ]
    )
    
    CREATIVE_CHALLENGE = ScoringProfile(
        name="Creative Challenge",
        description="Rewards novel and creative approaches",
        weights=[
            ScoringWeight("creativity", 0.4),
            ScoringWeight("completion", 0.3),
            ScoringWeight("reasoning", 0.3)
        ]
    )
    
    EXPLANATION_EXPERT = ScoringProfile(
        name="Explanation Expert",
        description="Values clear reasoning and explanations",
        weights=[
            ScoringWeight("reasoning", 0.5),
            ScoringWeight("accuracy", 0.3),
            ScoringWeight("completion", 0.2)
        ]
    )
    
    BALANCED = ScoringProfile(
        name="Balanced",
        description="Equal weight to all components",
        weights=[
            ScoringWeight("completion", 0.2),
            ScoringWeight("speed", 0.2),
            ScoringWeight("accuracy", 0.2),
            ScoringWeight("efficiency", 0.2),
            ScoringWeight("reasoning", 0.2)
        ]
    )
    
    @classmethod
    def get_all_profiles(cls) -> List[ScoringProfile]:
        """Get all standard scoring profiles."""
        return [
            cls.SPEED_DEMON,
            cls.PERFECTIONIST,
            cls.EFFICIENCY_MASTER,
            cls.CREATIVE_CHALLENGE,
            cls.EXPLANATION_EXPERT,
            cls.BALANCED
        ]


class ScoringCalculator:
    """Calculates final scores based on components and weights."""
    
    def __init__(self):
        self.normalizers: Dict[str, Callable[[float], float]] = {
            # Standard normalizers for common components
            "completion": lambda x: 1.0 if x else 0.0,  # Binary
            "speed": self._normalize_time,
            "accuracy": lambda x: max(0, min(1, x)),  # Already 0-1
            "efficiency": self._normalize_efficiency,
            "reasoning": lambda x: max(0, min(1, x)),  # Already 0-1
            "creativity": lambda x: max(0, min(1, x)),  # Already 0-1
        }
    
    def _normalize_time(self, seconds: float, max_time: float = 300) -> float:
        """Normalize time to 0-1 score (faster is better)."""
        if seconds <= 0:
            return 1.0
        if seconds >= max_time:
            return 0.0
        # Exponential decay for time scoring
        return math.exp(-seconds / (max_time / 3))
    
    def _normalize_efficiency(self, moves_ratio: float) -> float:
        """Normalize efficiency ratio (optimal_moves/actual_moves) to 0-1."""
        if moves_ratio <= 0:
            return 0.0
        if moves_ratio >= 1:
            return 1.0
        # Sigmoid curve for efficiency
        return 1 / (1 + math.exp(-10 * (moves_ratio - 0.5)))
    
    def add_normalizer(self, component_name: str, normalizer: Callable[[float], float]):
        """Add a custom normalizer for a component."""
        self.normalizers[component_name] = normalizer
    
    def calculate_score(
        self,
        components: Dict[str, float],
        profile: ScoringProfile,
        game_specific_normalizers: Optional[Dict[str, Callable]] = None
    ) -> float:
        """
        Calculate final score from components and profile.
        
        Args:
            components: Raw component values
            profile: Scoring profile with weights
            game_specific_normalizers: Optional game-specific normalizers
        
        Returns:
            Final score (0-100)
        """
        normalized_scores = {}
        
        # Apply normalizers
        for component_name, value in components.items():
            normalizer = None
            
            # Check game-specific normalizers first
            if game_specific_normalizers and component_name in game_specific_normalizers:
                normalizer = game_specific_normalizers[component_name]
            elif component_name in self.normalizers:
                normalizer = self.normalizers[component_name]
            
            if normalizer:
                normalized_scores[component_name] = normalizer(value)
            else:
                # Default: assume already normalized
                normalized_scores[component_name] = max(0, min(1, value))
        
        # Apply weights and calculate final score
        final_score = 0.0
        for component_name, normalized_value in normalized_scores.items():
            weight = profile.get_weight(component_name)
            final_score += weight * normalized_value
        
        # Convert to 0-100 scale
        return round(final_score * 100, 2)


@dataclass
class CompetitionScoring:
    """Scoring configuration for a competition session."""
    profile: ScoringProfile
    bonus_rules: List[Dict[str, Any]] = None  # Special bonus conditions
    penalty_rules: List[Dict[str, Any]] = None  # Special penalty conditions
    
    def __post_init__(self):
        if self.bonus_rules is None:
            self.bonus_rules = []
        if self.penalty_rules is None:
            self.penalty_rules = []
    
    def apply_bonuses_and_penalties(self, base_score: float, game_result: Dict[str, Any]) -> float:
        """Apply bonus and penalty rules to the base score."""
        final_score = base_score
        
        # Apply bonuses
        for rule in self.bonus_rules:
            if self._check_condition(rule["condition"], game_result):
                if rule["type"] == "multiply":
                    final_score *= rule["value"]
                elif rule["type"] == "add":
                    final_score += rule["value"]
        
        # Apply penalties
        for rule in self.penalty_rules:
            if self._check_condition(rule["condition"], game_result):
                if rule["type"] == "multiply":
                    final_score *= rule["value"]
                elif rule["type"] == "subtract":
                    final_score -= rule["value"]
        
        # Keep score in valid range
        return max(0, min(100, final_score))
    
    def _check_condition(self, condition: Dict[str, Any], game_result: Dict[str, Any]) -> bool:
        """Check if a bonus/penalty condition is met."""
        # Simple condition checker - can be extended
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if field not in game_result:
            return False
        
        result_value = game_result[field]
        
        if operator == "equals":
            return result_value == value
        elif operator == "greater_than":
            return result_value > value
        elif operator == "less_than":
            return result_value < value
        elif operator == "contains":
            return value in result_value
        
        return False


class LeaderboardCalculator:
    """Calculates leaderboard rankings with different scoring modes."""
    
    def calculate_rankings(
        self,
        player_scores: List[Dict[str, Any]],
        scoring_profile: ScoringProfile,
        round_weights: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate final rankings for a competition.
        
        Args:
            player_scores: List of player results with scores per round
            scoring_profile: Profile used for the competition
            round_weights: Optional weights for different rounds
        
        Returns:
            Sorted list of final rankings
        """
        final_rankings = []
        
        for player in player_scores:
            total_score = 0.0
            rounds_played = len(player["round_scores"])
            
            if round_weights and len(round_weights) == rounds_played:
                # Apply round weights
                for i, round_score in enumerate(player["round_scores"]):
                    total_score += round_score * round_weights[i]
            else:
                # Simple average
                total_score = sum(player["round_scores"]) / rounds_played if rounds_played > 0 else 0
            
            final_rankings.append({
                "player_id": player["player_id"],
                "player_name": player["player_name"],
                "total_score": total_score,
                "rounds_played": rounds_played,
                "scoring_profile": scoring_profile.name
            })
        
        # Sort by total score (descending)
        final_rankings.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Add ranks
        for i, player in enumerate(final_rankings):
            player["rank"] = i + 1
        
        return final_rankings