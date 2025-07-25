"""Game runner for Vercel - executes games with AI models."""
import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

# Import games
from .games.minesweeper import MinesweeperGame
from .games.risk import RiskGame
from .games.base import GameMove

# Import models
from .models.openai_client import OpenAIModel
from .models.anthropic_client import AnthropicModel

# Import database
from . import supabase_db as db

class GameRunner:
    """Runs games with AI models and stores results."""
    
    GAME_CLASSES = {
        "minesweeper": MinesweeperGame,
        "risk": RiskGame
    }
    
    MODEL_CLASSES = {
        "openai": OpenAIModel,
        "anthropic": AnthropicModel
    }
    
    def __init__(self):
        self.max_moves = 200  # Prevent infinite games
        self.move_timeout = 30  # Seconds per move
    
    def run_game(self, game_type: str, model_name: str, model_provider: str, 
                 difficulty: str = "medium", job_id: str = None) -> Dict[str, Any]:
        """Run a single game and return results."""
        
        start_time = time.time()
        
        # Create game instance
        if game_type not in self.GAME_CLASSES:
            return {
                "error": f"Unknown game type: {game_type}",
                "status": "error"
            }
        
        game = self.GAME_CLASSES[game_type](difficulty=difficulty)
        game_state = game.new_game()
        
        # Create model instance
        try:
            if model_provider not in self.MODEL_CLASSES:
                return {
                    "error": f"Unknown model provider: {model_provider}",
                    "status": "error"
                }
            
            model = self.MODEL_CLASSES[model_provider](model_name=model_name)
        except Exception as e:
            return {
                "error": f"Failed to initialize model: {str(e)}",
                "status": "error"
            }
        
        # Create game record in database
        game_id = str(uuid.uuid4())
        game_data = {
            "id": game_id,
            "job_id": job_id,
            "game_type": game_type,
            "difficulty": difficulty,
            "model_name": model_name,
            "model_provider": model_provider,
            "status": "in_progress",
            "moves": []
        }
        
        db.create_game(game_data)
        
        # Game loop
        moves = []
        move_count = 0
        total_tokens = 0
        error_message = None
        
        while not game.is_game_over() and move_count < self.max_moves:
            move_count += 1
            
            try:
                # Get game state for AI
                board_state = game.get_board_state_for_ai()
                function_schema = game.get_function_schema()
                
                # Get move from model
                move_start = time.time()
                response = model.get_move(board_state, function_schema, moves)
                move_time = time.time() - move_start
                
                if response.action == "error":
                    error_message = response.reasoning
                    break
                
                total_tokens += response.tokens_used
                
                # Convert response to game move
                if game_type == "minesweeper":
                    position = response.parameters.get("position", [0, 0])
                    game_move = GameMove(
                        action=response.action,
                        position=tuple(position),
                        reasoning=response.reasoning
                    )
                elif game_type == "risk":
                    # Handle different Risk move types
                    if response.action == "reinforce":
                        game_move = GameMove(
                            action="reinforce",
                            position=(response.parameters.get("territory"), 
                                    response.parameters.get("armies", 1)),
                            reasoning=response.reasoning
                        )
                    elif response.action == "attack":
                        game_move = GameMove(
                            action="attack",
                            position=(response.parameters.get("from_territory"),
                                    response.parameters.get("to_territory")),
                            reasoning=response.reasoning
                        )
                    elif response.action == "fortify":
                        game_move = GameMove(
                            action="fortify",
                            position=(response.parameters.get("from_territory"),
                                    response.parameters.get("to_territory"),
                                    response.parameters.get("armies", 1)),
                            reasoning=response.reasoning
                        )
                    else:
                        # end_attack, end_turn
                        game_move = GameMove(
                            action=response.action,
                            position=(),
                            reasoning=response.reasoning
                        )
                
                # Make the move
                valid, message = game.make_move(game_move)
                
                # Record move
                move_record = {
                    "move_number": move_count,
                    "action": response.action,
                    "parameters": response.parameters,
                    "reasoning": response.reasoning,
                    "valid": valid,
                    "message": message,
                    "tokens_used": response.tokens_used,
                    "response_time": move_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                moves.append(move_record)
                
                # Store intermediate progress (every 10 moves)
                if move_count % 10 == 0:
                    db.update_game(game_id, {
                        "moves": moves,
                        "total_moves": move_count
                    })
                
            except Exception as e:
                error_message = f"Error during move {move_count}: {str(e)}"
                break
        
        # Game finished
        duration = time.time() - start_time
        
        # Determine final status
        if error_message:
            final_status = "error"
            won = False
        elif game.state.status == "won":
            final_status = "completed"
            won = True
        elif game.state.status == "lost":
            final_status = "completed" 
            won = False
        else:
            final_status = "timeout"
            won = False
        
        # Calculate game-specific metrics
        metrics = self._calculate_metrics(game_type, game, moves)
        
        # Update game record
        game_result = {
            "status": final_status,
            "won": won,
            "total_moves": move_count,
            "valid_moves": sum(1 for m in moves if m["valid"]),
            "duration": duration,
            "total_tokens": total_tokens,
            "moves": moves,
            "final_board_state": game.get_state_dict(),
            "error_message": error_message,
            **metrics
        }
        
        db.update_game(game_id, game_result)
        
        # Update leaderboard
        if final_status == "completed":
            db.update_leaderboard(model_name, game_result)
        
        return {
            "game_id": game_id,
            "status": final_status,
            "won": won,
            "moves": move_count,
            "duration": duration,
            "tokens_used": total_tokens,
            "metrics": metrics
        }
    
    def _calculate_metrics(self, game_type: str, game: Any, moves: List[Dict]) -> Dict[str, Any]:
        """Calculate game-specific metrics."""
        metrics = {}
        
        if game_type == "minesweeper" and hasattr(game, 'mines'):
            # Count flagged mines
            correct_flags = 0
            total_flags = 0
            
            for r in range(game.rows):
                for c in range(game.cols):
                    if game.flags[r][c]:
                        total_flags += 1
                        if (r, c) in game.mines:
                            correct_flags += 1
            
            metrics["mines_identified"] = correct_flags
            metrics["mines_total"] = len(game.mines)
            metrics["false_flags"] = total_flags - correct_flags
            
            # Calculate coverage
            revealed_safe = sum(1 for r in range(game.rows) for c in range(game.cols) 
                              if game.visible[r][c] and (r, c) not in game.mines)
            total_safe = game.rows * game.cols - len(game.mines)
            metrics["coverage_ratio"] = revealed_safe / total_safe if total_safe > 0 else 0
            
        elif game_type == "risk":
            # Risk-specific metrics
            if hasattr(game, 'territories'):
                player_territories = sum(1 for t in game.territories.values() 
                                      if t["owner"] == "Player")
                total_territories = len(game.territories)
                metrics["territory_control"] = player_territories / total_territories
                
                player_armies = sum(t["armies"] for t in game.territories.values() 
                                  if t["owner"] == "Player")
                metrics["total_armies"] = player_armies
        
        return metrics
    
    def run_evaluation(self, num_games: int, game_type: str, model_name: str, 
                      model_provider: str, difficulty: str = "medium") -> Dict[str, Any]:
        """Run multiple games for evaluation."""
        
        job_id = f"eval_{uuid.uuid4().hex[:8]}"
        results = []
        
        for i in range(num_games):
            result = self.run_game(
                game_type=game_type,
                model_name=model_name,
                model_provider=model_provider,
                difficulty=difficulty,
                job_id=job_id
            )
            results.append(result)
            
            # For Vercel, we should limit execution time
            if i > 0 and sum(r["duration"] for r in results) > 8:  # 8 second limit
                break
        
        # Calculate summary statistics
        completed_games = [r for r in results if r["status"] == "completed"]
        
        summary = {
            "job_id": job_id,
            "total_games": len(results),
            "completed_games": len(completed_games),
            "wins": sum(1 for r in completed_games if r["won"]),
            "win_rate": sum(1 for r in completed_games if r["won"]) / len(completed_games) if completed_games else 0,
            "avg_moves": sum(r["moves"] for r in results) / len(results) if results else 0,
            "avg_duration": sum(r["duration"] for r in results) / len(results) if results else 0,
            "total_tokens": sum(r["tokens_used"] for r in results),
            "games": [r["game_id"] for r in results]
        }
        
        return summary

# Global instance
runner = GameRunner()