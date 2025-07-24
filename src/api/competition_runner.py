"""Competition runner for managing multiplayer game sessions."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from src.core.logging_config import get_logger
from src.core.types import Task, TaskType, Difficulty
from src.tasks.generator import TaskGenerator
from src.evaluation.streaming_runner import StreamingGameRunner
from src.models import create_model
from src.core.types import ModelConfig
try:
    from src.api.event_streaming import publish_event, EventType
except ImportError:
    # Fallback for when event streaming is not available
    async def publish_event(session_id: str, event_type: str, data: Dict[str, Any]):
        logger.warning(f"Event streaming not available: {event_type} for session {session_id}")
    
    class EventType:
        STATUS_UPDATE = "status_update"
        ERROR = "error"

logger = get_logger("api.competition")


class CompetitionRunner:
    """Manages the execution of competition sessions."""
    
    def __init__(self, session_id: str, session_data: Dict[str, Any]):
        self.session_id = session_id
        self.session_data = session_data
        self.players = session_data["players"]
        self.rounds_config = session_data["rounds_config"]
        self.format = session_data["format"]
        
        # Competition state
        self.current_round = 0
        self.player_scores: Dict[str, Dict[str, float]] = {}
        self.round_results: List[Dict[str, Any]] = []
        self.is_running = False
        
        # Initialize player scores
        for player in self.players:
            self.player_scores[player["player_id"]] = {
                "total_score": 0.0,
                "rounds_won": 0,
                "games_played": 0,
                "games_won": 0,
                "average_moves": 0.0,
                "average_coverage": 0.0
            }
    
    async def run_competition(self):
        """Run the complete competition."""
        try:
            self.is_running = True
            logger.info(f"Starting competition {self.session_id}")
            
            # Publish competition started event
            await publish_event(self.session_id, EventType.STATUS_UPDATE, {
                "status": "competition_started",
                "message": "Competition has begun!",
                "total_rounds": len(self.rounds_config),
                "players": [p["name"] for p in self.players]
            })
            
            # Run each round
            for round_idx, round_config in enumerate(self.rounds_config):
                self.current_round = round_idx + 1
                await self.run_round(round_config)
                
                # Delay between rounds
                if round_idx < len(self.rounds_config) - 1:
                    await asyncio.sleep(5)
            
            # Competition completed
            await self.finalize_competition()
            
        except Exception as e:
            logger.error(f"Competition {self.session_id} failed: {e}", exc_info=True)
            await publish_event(self.session_id, EventType.ERROR, {
                "error": "Competition failed",
                "message": str(e)
            })
        finally:
            self.is_running = False
    
    async def run_round(self, round_config: Dict[str, Any]):
        """Run a single round of competition."""
        logger.info(f"Starting round {self.current_round} for competition {self.session_id}")
        
        # Publish round started event
        await publish_event(self.session_id, EventType.STATUS_UPDATE, {
            "status": "round_started",
            "round": self.current_round,
            "game": round_config.get("game_name", "minesweeper"),
            "difficulty": round_config.get("difficulty", "medium")
        })
        
        # Generate task for this round
        task = await self.generate_round_task(round_config)
        
        # Run games for each player
        round_results = {}
        player_tasks = []
        
        for player in self.players:
            if player["ai_model"]:
                player_task = self.run_player_game(player, task, round_config)
                player_tasks.append(player_task)
        
        # Run all player games concurrently
        results = await asyncio.gather(*player_tasks, return_exceptions=True)
        
        # Process results
        for i, player in enumerate(self.players):
            if player["ai_model"]:
                if isinstance(results[i], Exception):
                    logger.error(f"Player {player['name']} failed: {results[i]}")
                    round_results[player["player_id"]] = {
                        "error": str(results[i]),
                        "score": 0.0
                    }
                else:
                    round_results[player["player_id"]] = results[i]
        
        # Calculate round winner
        round_winner = self.calculate_round_winner(round_results)
        
        # Update scores
        self.update_scores(round_results, round_winner)
        
        # Store round results
        self.round_results.append({
            "round": self.current_round,
            "results": round_results,
            "winner": round_winner
        })
        
        # Publish round completed event
        await publish_event(self.session_id, EventType.STATUS_UPDATE, {
            "status": "round_completed",
            "round": self.current_round,
            "winner": round_winner,
            "scores": self.get_current_standings()
        })
    
    async def generate_round_task(self, round_config: Dict[str, Any]) -> Task:
        """Generate a task for the round."""
        generator = TaskGenerator()
        
        # Get difficulty
        difficulty_str = round_config.get("difficulty", "medium")
        difficulty_map = {
            "easy": Difficulty.BEGINNER,
            "medium": Difficulty.INTERMEDIATE,
            "hard": Difficulty.EXPERT
        }
        difficulty = difficulty_map.get(difficulty_str, Difficulty.INTERMEDIATE)
        
        # Generate task based on game
        game_name = round_config.get("game_name", "minesweeper")
        
        if game_name == "minesweeper":
            # Generate interactive Minesweeper task
            task = generator.generate_interactive_task(difficulty=difficulty)
        else:
            # For other games, create a generic task
            from src.core.types import Task, TaskType
            task = Task.create(
                task_type=TaskType.INTERACTIVE,
                difficulty=difficulty,
                board_config={
                    "game": game_name,
                    "difficulty": difficulty_str,
                    "seed": await self.generate_round_seed()
                },
                description=f"Play {game_name} at {difficulty_str} difficulty",
                metadata={"game": game_name}
            )
        
        return task
    
    async def generate_round_seed(self) -> int:
        """Generate a consistent seed for all players in a round."""
        # Use session ID and round number to generate deterministic seed
        import hashlib
        seed_string = f"{self.session_id}_{self.current_round}"
        seed_hash = hashlib.md5(seed_string.encode()).hexdigest()
        return int(seed_hash[:8], 16)
    
    async def run_player_game(self, player: Dict[str, Any], task: Task, round_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a game for a single player."""
        player_id = player["player_id"]
        logger.info(f"Running game for player {player['name']} ({player['ai_model']})")
        
        try:
            # Create model configuration
            model_config = ModelConfig(
                name=player["ai_model"],
                provider="openai" if "gpt" in player["ai_model"] else "anthropic",
                model_id=player["ai_model"],
                temperature=0,
                max_tokens=1000,
                additional_params={}
            )
            
            # Create runner
            runner = StreamingGameRunner(model_config)
            
            # Run single game with competition-specific job ID
            job_id = f"{self.session_id}_p{player_id}_r{self.current_round}"
            
            # Publish player game started
            await publish_event(self.session_id, EventType.STATUS_UPDATE, {
                "status": "player_game_started",
                "player": player["name"],
                "round": self.current_round
            })
            
            # Run the game
            game_name = round_config.get("game_name", "minesweeper")
            transcript = await runner.run_single_game(
                task=task,
                job_id=job_id,
                game_num=1,
                max_moves=500,
                prompt_format="auto",
                verbose=False,
                game_name=game_name
            )
            
            # Calculate score based on game results
            stats = transcript.final_state
            won = stats.status.value == "won"
            
            # Basic scoring
            score = 0.0
            if won:
                score += 100.0  # Base score for winning
                
                # Bonus for efficiency (fewer moves)
                if len(transcript.moves) < 50:
                    score += 20.0
                elif len(transcript.moves) < 100:
                    score += 10.0
                
                # Bonus for coverage (for Minesweeper)
                if hasattr(stats, 'board_coverage'):
                    score += stats.board_coverage * 50.0
            else:
                # Partial score based on progress
                if hasattr(stats, 'board_coverage'):
                    score += stats.board_coverage * 30.0
            
            return {
                "player_id": player_id,
                "won": won,
                "score": score,
                "moves": len(transcript.moves),
                "coverage": getattr(stats, 'board_coverage', 0.0),
                "game_id": transcript.game_id
            }
            
        except Exception as e:
            logger.error(f"Failed to run game for player {player['name']}: {e}")
            raise
    
    def calculate_round_winner(self, round_results: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Determine the winner of a round."""
        if not round_results:
            return None
        
        # Find player with highest score
        winner_id = None
        highest_score = -1
        
        for player_id, result in round_results.items():
            if "error" not in result and result.get("score", 0) > highest_score:
                highest_score = result["score"]
                winner_id = player_id
        
        if winner_id:
            # Get player name
            player = next((p for p in self.players if p["player_id"] == winner_id), None)
            return player["name"] if player else winner_id
        
        return None
    
    def update_scores(self, round_results: Dict[str, Dict[str, Any]], round_winner: Optional[str]):
        """Update player scores based on round results."""
        for player_id, result in round_results.items():
            if player_id in self.player_scores:
                scores = self.player_scores[player_id]
                
                # Update basic stats
                scores["games_played"] += 1
                scores["total_score"] += result.get("score", 0)
                
                if result.get("won"):
                    scores["games_won"] += 1
                
                # Update averages
                total_games = scores["games_played"]
                scores["average_moves"] = (
                    (scores["average_moves"] * (total_games - 1) + result.get("moves", 0)) 
                    / total_games
                )
                scores["average_coverage"] = (
                    (scores["average_coverage"] * (total_games - 1) + result.get("coverage", 0)) 
                    / total_games
                )
                
                # Check if this player won the round
                player = next((p for p in self.players if p["player_id"] == player_id), None)
                if player and player["name"] == round_winner:
                    scores["rounds_won"] += 1
    
    def get_current_standings(self) -> List[Dict[str, Any]]:
        """Get current competition standings."""
        standings = []
        
        for player in self.players:
            player_id = player["player_id"]
            scores = self.player_scores.get(player_id, {})
            
            standings.append({
                "rank": 0,  # Will be set after sorting
                "player_name": player["name"],
                "ai_model": player["ai_model"],
                "total_score": scores.get("total_score", 0),
                "rounds_won": scores.get("rounds_won", 0),
                "games_won": scores.get("games_won", 0),
                "games_played": scores.get("games_played", 0),
                "win_rate": (
                    scores.get("games_won", 0) / scores.get("games_played", 1) 
                    if scores.get("games_played", 0) > 0 else 0
                )
            })
        
        # Sort by total score
        standings.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Assign ranks
        for i, standing in enumerate(standings):
            standing["rank"] = i + 1
        
        return standings
    
    async def finalize_competition(self):
        """Finalize the competition and declare winner."""
        final_standings = self.get_current_standings()
        
        # Determine overall winner
        winner = final_standings[0] if final_standings else None
        
        # Publish competition completed event
        await publish_event(self.session_id, EventType.STATUS_UPDATE, {
            "status": "competition_completed",
            "winner": winner["player_name"] if winner else None,
            "final_standings": final_standings,
            "total_rounds": len(self.round_results)
        })
        
        logger.info(f"Competition {self.session_id} completed. Winner: {winner['player_name'] if winner else 'None'}")
        
        # TODO: Store competition results in database
        
        return {
            "winner": winner,
            "standings": final_standings,
            "rounds": self.round_results
        }


async def run_competition(session_id: str, session_data: Dict[str, Any]):
    """Entry point for running a competition."""
    runner = CompetitionRunner(session_id, session_data)
    await runner.run_competition()