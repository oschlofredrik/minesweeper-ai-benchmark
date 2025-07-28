"""Between-round showcase and learning features."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import asyncio


class ShowcaseType(Enum):
    """Types of showcase content."""
    TOP_PROMPTS = "top_prompts"  # Best performing prompts
    STRATEGY_ANALYSIS = "strategy_analysis"  # AI explains strategies
    CREATIVE_SOLUTIONS = "creative_solutions"  # Most innovative approaches
    LEARNING_MOMENT = "learning_moment"  # Educational insights
    PLAYER_COMPARISON = "player_comparison"  # Compare different approaches
    VOTING_SHOWCASE = "voting_showcase"  # Community voting on prompts


class VoteCategory(Enum):
    """Categories for voting."""
    MOST_CREATIVE = "most_creative"
    MOST_ELEGANT = "most_elegant"
    BEST_EXPLANATION = "best_explanation"
    MOST_EFFICIENT = "most_efficient"
    CROWD_FAVORITE = "crowd_favorite"


@dataclass
class ShowcaseItem:
    """An item to showcase between rounds."""
    item_id: str
    showcase_type: ShowcaseType
    round_number: int
    title: str
    description: str
    content: Dict[str, Any]
    featured_players: List[str]
    created_at: datetime
    duration: int = 30  # seconds
    
    # Voting data
    vote_category: Optional[VoteCategory] = None
    votes: Dict[str, str] = field(default_factory=dict)  # voter_id -> choice
    
    # Educational data
    learning_points: List[str] = field(default_factory=list)
    difficulty_level: str = "intermediate"
    
    def add_vote(self, voter_id: str, choice: str):
        """Add a vote to this showcase item."""
        self.votes[voter_id] = choice
    
    def get_vote_results(self) -> Dict[str, int]:
        """Get vote tally."""
        results = {}
        for choice in self.votes.values():
            results[choice] = results.get(choice, 0) + 1
        return results


@dataclass
class LearningInsight:
    """An educational insight from the round."""
    insight_type: str  # "strategy", "mistake", "pattern", "technique"
    title: str
    explanation: str
    example_data: Dict[str, Any]
    applicable_games: List[str]
    skill_level: str  # "beginner", "intermediate", "advanced"
    
    def to_display(self) -> Dict[str, Any]:
        """Format for display."""
        return {
            "type": self.insight_type,
            "title": self.title,
            "explanation": self.explanation,
            "example": self.example_data,
            "games": self.applicable_games,
            "level": self.skill_level
        }


class RoundShowcase:
    """Manages showcase content between competition rounds."""
    
    def __init__(self):
        self.showcase_items: List[ShowcaseItem] = []
        self.learning_insights: List[LearningInsight] = []
        self.player_highlights: Dict[str, List[Dict[str, Any]]] = {}
        self.strategy_analyzer = StrategyAnalyzer()
        self._event_handlers: Dict[str, List[callable]] = {}
    
    async def prepare_showcase(
        self,
        round_number: int,
        round_results: List[Dict[str, Any]],
        game_name: str,
        duration_limit: int = 120  # seconds
    ) -> List[ShowcaseItem]:
        """Prepare showcase content for between-round display."""
        showcase_items = []
        
        # 1. Top Prompts Showcase
        top_prompts = self._extract_top_prompts(round_results)
        if top_prompts:
            showcase_items.append(ShowcaseItem(
                item_id=f"showcase_{round_number}_top",
                showcase_type=ShowcaseType.TOP_PROMPTS,
                round_number=round_number,
                title="🏆 Top Performing Prompts",
                description="See how the best players approached this challenge",
                content={
                    "prompts": top_prompts,
                    "game_name": game_name
                },
                featured_players=[p["player_id"] for p in top_prompts],
                created_at=datetime.utcnow(),
                duration=30
            ))
        
        # 2. Strategy Analysis
        strategies = await self.strategy_analyzer.analyze_round(round_results, game_name)
        if strategies:
            showcase_items.append(ShowcaseItem(
                item_id=f"showcase_{round_number}_strategy",
                showcase_type=ShowcaseType.STRATEGY_ANALYSIS,
                round_number=round_number,
                title="🧠 Strategy Breakdown",
                description="AI explains why certain approaches worked better",
                content={
                    "strategies": strategies,
                    "game_name": game_name
                },
                featured_players=self._get_strategy_players(strategies),
                created_at=datetime.utcnow(),
                duration=40,
                learning_points=[s["key_insight"] for s in strategies[:3]]
            ))
        
        # 3. Creative Solutions
        creative = self._find_creative_solutions(round_results)
        if creative:
            showcase_items.append(ShowcaseItem(
                item_id=f"showcase_{round_number}_creative",
                showcase_type=ShowcaseType.CREATIVE_SOLUTIONS,
                round_number=round_number,
                title="💡 Creative Approaches",
                description="Innovative solutions that surprised everyone",
                content={
                    "solutions": creative,
                    "voting_enabled": True
                },
                featured_players=[c["player_id"] for c in creative],
                created_at=datetime.utcnow(),
                duration=30,
                vote_category=VoteCategory.MOST_CREATIVE
            ))
        
        # 4. Learning Moment
        learning = self._generate_learning_moment(round_results, game_name)
        if learning:
            showcase_items.append(ShowcaseItem(
                item_id=f"showcase_{round_number}_learn",
                showcase_type=ShowcaseType.LEARNING_MOMENT,
                round_number=round_number,
                title="📚 Learning Moment",
                description=learning.title,
                content={
                    "insight": learning.to_display(),
                    "interactive": True
                },
                featured_players=[],
                created_at=datetime.utcnow(),
                duration=25,
                learning_points=[learning.explanation]
            ))
        
        # 5. Player Comparison (if interesting contrasts)
        comparison = self._create_player_comparison(round_results)
        if comparison:
            showcase_items.append(ShowcaseItem(
                item_id=f"showcase_{round_number}_compare",
                showcase_type=ShowcaseType.PLAYER_COMPARISON,
                round_number=round_number,
                title="⚖️ Tale of Two Approaches",
                description="Compare different strategies side by side",
                content=comparison,
                featured_players=comparison["players"],
                created_at=datetime.utcnow(),
                duration=35
            ))
        
        # Store for later reference
        self.showcase_items.extend(showcase_items)
        
        # Emit event
        await self._emit_event("showcase_prepared", {
            "round": round_number,
            "item_count": len(showcase_items),
            "total_duration": sum(item.duration for item in showcase_items)
        })
        
        return showcase_items
    
    def _extract_top_prompts(
        self,
        round_results: List[Dict[str, Any]],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Extract top performing prompts from round results."""
        # Sort by score
        sorted_results = sorted(
            round_results,
            key=lambda r: r.get("score", 0),
            reverse=True
        )[:limit]
        
        top_prompts = []
        for result in sorted_results:
            if "prompt" in result and result.get("score", 0) > 0:
                top_prompts.append({
                    "player_id": result["player_id"],
                    "player_name": result.get("player_name", "Unknown"),
                    "prompt": result["prompt"],
                    "score": result["score"],
                    "key_moves": result.get("key_moves", []),
                    "execution_time": result.get("execution_time", 0)
                })
        
        return top_prompts
    
    def _find_creative_solutions(
        self,
        round_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find creative or unusual solutions."""
        creative = []
        
        for result in round_results:
            if not result.get("prompt"):
                continue
            
            # Simple creativity detection (would be more sophisticated)
            creativity_score = self._calculate_creativity_score(result)
            
            if creativity_score > 0.7:  # Threshold
                creative.append({
                    "player_id": result["player_id"],
                    "player_name": result.get("player_name", "Unknown"),
                    "prompt": result["prompt"],
                    "creativity_score": creativity_score,
                    "unique_aspects": self._identify_unique_aspects(result)
                })
        
        # Sort by creativity score
        creative.sort(key=lambda c: c["creativity_score"], reverse=True)
        return creative[:3]  # Top 3
    
    def _calculate_creativity_score(self, result: Dict[str, Any]) -> float:
        """Calculate creativity score for a result."""
        score = 0.0
        prompt = result.get("prompt", "")
        
        # Length variance (not too short, not too long)
        ideal_length = 200
        length_diff = abs(len(prompt) - ideal_length)
        if length_diff < 100:
            score += 0.2
        
        # Unique word usage
        unique_words = len(set(prompt.lower().split()))
        total_words = len(prompt.split())
        if total_words > 0:
            uniqueness_ratio = unique_words / total_words
            score += uniqueness_ratio * 0.3
        
        # Strategy keywords (inverse - less common = more creative)
        common_strategies = ["first", "then", "next", "finally", "therefore"]
        common_count = sum(1 for word in common_strategies if word in prompt.lower())
        if common_count < 3:
            score += 0.3
        
        # Success with unusual approach
        if result.get("score", 0) > 0.7 and score > 0.5:
            score += 0.2
        
        return min(1.0, score)
    
    def _identify_unique_aspects(self, result: Dict[str, Any]) -> List[str]:
        """Identify unique aspects of a solution."""
        aspects = []
        prompt = result.get("prompt", "")
        
        # Check for specific patterns
        if "imagine" in prompt.lower() or "pretend" in prompt.lower():
            aspects.append("Uses imaginative framing")
        
        if "?" in prompt and prompt.count("?") > 2:
            aspects.append("Question-based approach")
        
        if len(prompt.split('\n')) > 5:
            aspects.append("Highly structured format")
        
        if any(emoji in prompt for emoji in ["🎯", "💡", "🔍", "✨"]):
            aspects.append("Uses visual markers")
        
        return aspects
    
    def _generate_learning_moment(
        self,
        round_results: List[Dict[str, Any]],
        game_name: str
    ) -> Optional[LearningInsight]:
        """Generate educational insight from the round."""
        # Analyze common mistakes
        mistakes = self._analyze_common_mistakes(round_results)
        if mistakes:
            return LearningInsight(
                insight_type="mistake",
                title=f"Common Pitfall: {mistakes[0]['type']}",
                explanation=mistakes[0]['explanation'],
                example_data={
                    "mistake_example": mistakes[0]['example'],
                    "correct_approach": mistakes[0]['correction']
                },
                applicable_games=[game_name],
                skill_level="intermediate"
            )
        
        # Analyze successful patterns
        patterns = self._analyze_success_patterns(round_results)
        if patterns:
            return LearningInsight(
                insight_type="pattern",
                title=f"Success Pattern: {patterns[0]['name']}",
                explanation=patterns[0]['description'],
                example_data={
                    "pattern": patterns[0]['pattern'],
                    "usage_count": patterns[0]['count']
                },
                applicable_games=[game_name],
                skill_level="advanced"
            )
        
        # Default learning moment
        return LearningInsight(
            insight_type="technique",
            title="Prompt Structure Matters",
            explanation="Clear, structured prompts consistently outperform stream-of-consciousness approaches",
            example_data={
                "good_structure": "1. Analyze state\n2. Identify constraints\n3. Choose action",
                "poor_structure": "I think maybe we should try something and see what happens"
            },
            applicable_games=["all"],
            skill_level="beginner"
        )
    
    def _analyze_common_mistakes(
        self,
        round_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze common mistakes in the round."""
        mistakes = []
        
        # Look for low-scoring results
        poor_results = [r for r in round_results if r.get("score", 0) < 0.3]
        
        if len(poor_results) >= 3:
            # Find common patterns in failures
            # This is simplified - real implementation would be more sophisticated
            mistakes.append({
                "type": "Insufficient Analysis",
                "explanation": "Many players jumped to actions without analyzing the game state",
                "example": "Let me reveal a random cell",
                "correction": "First, let me analyze what we know from the visible numbers",
                "frequency": len(poor_results)
            })
        
        return mistakes
    
    def _analyze_success_patterns(
        self,
        round_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze patterns in successful approaches."""
        patterns = []
        
        # Look for high-scoring results
        good_results = [r for r in round_results if r.get("score", 0) > 0.7]
        
        if good_results:
            # Simplified pattern detection
            chain_of_thought_count = sum(
                1 for r in good_results
                if "step by step" in r.get("prompt", "").lower()
            )
            
            if chain_of_thought_count > len(good_results) / 2:
                patterns.append({
                    "name": "Chain of Thought",
                    "description": "Breaking down reasoning into clear steps",
                    "pattern": "step by step",
                    "count": chain_of_thought_count
                })
        
        return patterns
    
    def _create_player_comparison(
        self,
        round_results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Create interesting player comparisons."""
        if len(round_results) < 2:
            return None
        
        # Find contrasting approaches with similar scores
        sorted_results = sorted(
            round_results,
            key=lambda r: r.get("score", 0),
            reverse=True
        )
        
        for i in range(len(sorted_results) - 1):
            player1 = sorted_results[i]
            player2 = sorted_results[i + 1]
            
            # Similar scores but different approaches?
            score_diff = abs(player1.get("score", 0) - player2.get("score", 0))
            if score_diff < 0.1:  # Similar scores
                prompt1 = player1.get("prompt", "")
                prompt2 = player2.get("prompt", "")
                
                # Different lengths?
                if abs(len(prompt1) - len(prompt2)) > 100:
                    return {
                        "players": [player1["player_id"], player2["player_id"]],
                        "player_names": [
                            player1.get("player_name", "Player 1"),
                            player2.get("player_name", "Player 2")
                        ],
                        "prompts": [prompt1, prompt2],
                        "scores": [player1.get("score", 0), player2.get("score", 0)],
                        "comparison_type": "length",
                        "insight": "Both achieved similar scores with very different prompt lengths"
                    }
        
        return None
    
    def _get_strategy_players(self, strategies: List[Dict[str, Any]]) -> List[str]:
        """Get featured players from strategies."""
        players = []
        for strategy in strategies:
            if "example_player" in strategy:
                players.append(strategy["example_player"])
        return players[:3]  # Limit to 3
    
    async def start_voting(
        self,
        showcase_item_id: str,
        options: List[Dict[str, Any]],
        duration: int = 20
    ) -> str:
        """Start a voting period for a showcase item."""
        item = next((i for i in self.showcase_items if i.item_id == showcase_item_id), None)
        if not item or not item.vote_category:
            return ""
        
        # Set up voting options
        voting_id = f"vote_{showcase_item_id}"
        
        await self._emit_event("voting_started", {
            "voting_id": voting_id,
            "showcase_item_id": showcase_item_id,
            "category": item.vote_category.value,
            "options": options,
            "duration": duration
        })
        
        # Start timer
        asyncio.create_task(self._voting_timer(voting_id, duration))
        
        return voting_id
    
    async def _voting_timer(self, voting_id: str, duration: int):
        """Handle voting timer."""
        await asyncio.sleep(duration)
        
        # Find showcase item
        item = next(
            (i for i in self.showcase_items if f"vote_{i.item_id}" == voting_id),
            None
        )
        
        if item:
            results = item.get_vote_results()
            
            await self._emit_event("voting_completed", {
                "voting_id": voting_id,
                "results": results,
                "total_votes": len(item.votes),
                "winner": max(results.items(), key=lambda x: x[1])[0] if results else None
            })
    
    async def submit_vote(
        self,
        voter_id: str,
        showcase_item_id: str,
        choice: str
    ) -> bool:
        """Submit a vote for a showcase item."""
        item = next((i for i in self.showcase_items if i.item_id == showcase_item_id), None)
        
        if not item or not item.vote_category:
            return False
        
        item.add_vote(voter_id, choice)
        
        await self._emit_event("vote_submitted", {
            "voter_id": voter_id,
            "showcase_item_id": showcase_item_id,
            "choice": choice
        })
        
        return True
    
    def update_player_highlight(
        self,
        player_id: str,
        highlight_type: str,
        data: Dict[str, Any]
    ):
        """Update player highlights for showcase."""
        if player_id not in self.player_highlights:
            self.player_highlights[player_id] = []
        
        self.player_highlights[player_id].append({
            "type": highlight_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_showcase_schedule(
        self,
        items: List[ShowcaseItem],
        max_duration: int = 120
    ) -> List[Dict[str, Any]]:
        """Create optimal showcase schedule within time limit."""
        schedule = []
        total_time = 0
        
        # Prioritize by type
        priority_order = [
            ShowcaseType.TOP_PROMPTS,
            ShowcaseType.VOTING_SHOWCASE,
            ShowcaseType.STRATEGY_ANALYSIS,
            ShowcaseType.LEARNING_MOMENT,
            ShowcaseType.CREATIVE_SOLUTIONS,
            ShowcaseType.PLAYER_COMPARISON
        ]
        
        # Sort items by priority
        sorted_items = sorted(
            items,
            key=lambda i: priority_order.index(i.showcase_type)
        )
        
        for item in sorted_items:
            if total_time + item.duration <= max_duration:
                schedule.append({
                    "item": item,
                    "start_time": total_time,
                    "end_time": total_time + item.duration
                })
                total_time += item.duration
        
        return schedule
    
    def on(self, event: str, handler: callable):
        """Register event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Dict[str, Any]):
        """Emit event to handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                await handler(data)


class StrategyAnalyzer:
    """Analyzes strategies used in the round."""
    
    async def analyze_round(
        self,
        round_results: List[Dict[str, Any]],
        game_name: str
    ) -> List[Dict[str, Any]]:
        """Analyze strategies used in the round."""
        strategies = []
        
        # Group results by score ranges
        high_scorers = [r for r in round_results if r.get("score", 0) > 0.8]
        mid_scorers = [r for r in round_results if 0.4 < r.get("score", 0) <= 0.8]
        low_scorers = [r for r in round_results if r.get("score", 0) <= 0.4]
        
        # Analyze high scorers
        if high_scorers:
            common_patterns = self._find_common_patterns(high_scorers)
            if common_patterns:
                strategies.append({
                    "name": "Winning Formula",
                    "description": "Common elements in top-performing prompts",
                    "patterns": common_patterns,
                    "example_player": high_scorers[0]["player_id"],
                    "key_insight": common_patterns[0]["insight"]
                })
        
        # Compare high vs low
        if high_scorers and low_scorers:
            differences = self._compare_approaches(high_scorers, low_scorers)
            if differences:
                strategies.append({
                    "name": "Key Differentiators",
                    "description": "What separated winners from others",
                    "differences": differences,
                    "key_insight": differences[0]
                })
        
        return strategies
    
    def _find_common_patterns(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Find common patterns in results."""
        patterns = []
        
        # Simplified pattern detection
        structure_count = sum(
            1 for r in results
            if '\n' in r.get("prompt", "") and 
            len(r.get("prompt", "").split('\n')) > 3
        )
        
        if structure_count > len(results) / 2:
            patterns.append({
                "pattern": "Structured Format",
                "frequency": f"{structure_count}/{len(results)}",
                "insight": "Well-structured prompts with clear sections performed better"
            })
        
        return patterns
    
    def _compare_approaches(
        self,
        high_scorers: List[Dict[str, Any]],
        low_scorers: List[Dict[str, Any]]
    ) -> List[str]:
        """Compare approaches between groups."""
        differences = []
        
        # Average prompt length
        high_avg_length = sum(len(r.get("prompt", "")) for r in high_scorers) / len(high_scorers)
        low_avg_length = sum(len(r.get("prompt", "")) for r in low_scorers) / len(low_scorers)
        
        if high_avg_length > low_avg_length * 1.5:
            differences.append("Successful prompts were more detailed and thorough")
        elif low_avg_length > high_avg_length * 1.5:
            differences.append("Concise, focused prompts outperformed verbose ones")
        
        return differences