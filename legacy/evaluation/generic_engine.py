"""Generic evaluation engine for the AI competition platform."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import uuid
import logging

from src.games.base import BaseGame, GameInstance, GameState, GameAction, GameResult, GameConfig
from src.games.registry import game_registry
from src.scoring.framework import ScoringProfile, ScoringCalculator, CompetitionScoring
from src.models.base import BaseModel
from src.core.logging_config import setup_logging


logger = logging.getLogger(__name__)


class GameEvaluationResult:
    """Result of evaluating a single game."""
    
    def __init__(
        self,
        game_id: str,
        game_name: str,
        player_id: str,
        ai_model: str,
        game_result: GameResult,
        score_components: Dict[str, float],
        final_score: float,
        evaluation_metadata: Dict[str, Any]
    ):
        self.game_id = game_id
        self.game_name = game_name
        self.player_id = player_id
        self.ai_model = ai_model
        self.game_result = game_result
        self.score_components = score_components
        self.final_score = final_score
        self.evaluation_metadata = evaluation_metadata
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "game_id": self.game_id,
            "game_name": self.game_name,
            "player_id": self.player_id,
            "ai_model": self.ai_model,
            "victory": self.game_result.victory,
            "moves_made": self.game_result.moves_made,
            "time_taken": self.game_result.time_taken,
            "score_components": self.score_components,
            "final_score": self.final_score,
            "evaluation_metadata": self.evaluation_metadata,
            "timestamp": self.timestamp.isoformat(),
            "move_history": [
                {
                    "action_type": move.action_type,
                    "parameters": move.parameters,
                    "reasoning": move.reasoning
                }
                for move in self.game_result.move_history
            ]
        }


class GenericEvaluationEngine:
    """Generic engine for evaluating AI performance on any game."""
    
    def __init__(self):
        self.scoring_calculator = ScoringCalculator()
        self.active_evaluations: Dict[str, Dict[str, Any]] = {}
    
    async def evaluate_game(
        self,
        game_name: str,
        game_config: GameConfig,
        ai_model: BaseModel,
        scoring_profile: ScoringProfile,
        player_id: str = "anonymous",
        evaluation_id: Optional[str] = None,
        stream_callback: Optional[callable] = None
    ) -> GameEvaluationResult:
        """
        Evaluate AI performance on a single game.
        
        Args:
            game_name: Name of the game to play
            game_config: Configuration for the game
            ai_model: AI model to evaluate
            scoring_profile: Scoring profile to use
            player_id: ID of the player
            evaluation_id: Optional evaluation ID
            stream_callback: Optional callback for streaming updates
        
        Returns:
            GameEvaluationResult with scores and metadata
        """
        evaluation_id = evaluation_id or str(uuid.uuid4())
        
        # Get game from registry
        game = game_registry.get_game(game_name)
        if not game:
            raise ValueError(f"Game '{game_name}' not found in registry")
        
        # Create game instance
        game_instance = game.create_instance(game_config)
        
        # Track evaluation
        self.active_evaluations[evaluation_id] = {
            "game_name": game_name,
            "player_id": player_id,
            "ai_model": ai_model.name,
            "start_time": datetime.utcnow(),
            "status": "in_progress"
        }
        
        try:
            # Play the game
            game_result = await self._play_game(
                game, game_instance, ai_model, game_config, stream_callback
            )
            
            # Calculate scores
            score_components = game_instance.calculate_score_components(game_result)
            
            # Get game-specific normalizers if available
            game_normalizers = getattr(game, 'get_score_normalizers', lambda: {})()
            
            # Calculate final score
            final_score = self.scoring_calculator.calculate_score(
                score_components,
                scoring_profile,
                game_normalizers
            )
            
            # Create evaluation result
            result = GameEvaluationResult(
                game_id=game_instance.instance_id,
                game_name=game_name,
                player_id=player_id,
                ai_model=ai_model.name,
                game_result=game_result,
                score_components=score_components,
                final_score=final_score,
                evaluation_metadata={
                    "game_config": {
                        "difficulty": game_config.difficulty,
                        "mode": game_config.mode.value,
                        "custom_settings": game_config.custom_settings
                    },
                    "scoring_profile": scoring_profile.name,
                    "evaluation_id": evaluation_id
                }
            )
            
            # Update tracking
            self.active_evaluations[evaluation_id]["status"] = "completed"
            self.active_evaluations[evaluation_id]["end_time"] = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating game {game_name}: {e}")
            self.active_evaluations[evaluation_id]["status"] = "error"
            self.active_evaluations[evaluation_id]["error"] = str(e)
            raise
        finally:
            # Clean up after a delay
            asyncio.create_task(self._cleanup_evaluation(evaluation_id))
    
    async def _play_game(
        self,
        game: BaseGame,
        game_instance: GameInstance,
        ai_model: BaseModel,
        game_config: GameConfig,
        stream_callback: Optional[callable] = None
    ) -> GameResult:
        """Play through a game with the AI model."""
        current_state = game_instance.get_initial_state()
        move_count = 0
        max_moves = 1000  # Safety limit
        consecutive_invalid_moves = 0
        max_consecutive_invalid = 3
        
        # Get AI interface if available
        ai_interface = getattr(game, 'get_ai_interface', lambda: None)()
        
        while not current_state.is_terminal and move_count < max_moves:
            move_count += 1
            
            try:
                # Get AI action
                action = await self._get_ai_action(
                    game, current_state, ai_model, game_config, ai_interface
                )
                
                # Apply action
                new_state, valid, error_msg = game_instance.make_move(current_state, action)
                
                if valid:
                    consecutive_invalid_moves = 0
                    current_state = new_state
                    
                    # Stream update if callback provided
                    if stream_callback:
                        await stream_callback({
                            "type": "move",
                            "move_number": move_count,
                            "action": action,
                            "valid": True,
                            "game_state": current_state.state_data
                        })
                else:
                    consecutive_invalid_moves += 1
                    logger.warning(f"Invalid move attempt {consecutive_invalid_moves}: {error_msg}")
                    
                    if consecutive_invalid_moves >= max_consecutive_invalid:
                        logger.error(f"Too many consecutive invalid moves, ending game")
                        break
                    
                    # Stream invalid move
                    if stream_callback:
                        await stream_callback({
                            "type": "move",
                            "move_number": move_count,
                            "action": action,
                            "valid": False,
                            "error": error_msg
                        })
                
            except Exception as e:
                logger.error(f"Error during move {move_count}: {e}")
                if stream_callback:
                    await stream_callback({
                        "type": "error",
                        "move_number": move_count,
                        "error": str(e)
                    })
                break
        
        # Get final result
        return game_instance.get_result(current_state)
    
    async def _get_ai_action(
        self,
        game: BaseGame,
        state: GameState,
        ai_model: BaseModel,
        game_config: GameConfig,
        ai_interface: Optional[Any] = None
    ) -> GameAction:
        """Get action from AI model."""
        # Format state for AI
        if ai_interface:
            prompt = ai_interface.format_state_for_ai(state, game_config)
        else:
            # Fallback to basic formatting
            prompt = game.get_ai_prompt_template().format(
                board_state=state.to_prompt_format(),
                **state.state_data
            )
        
        # Add move format description
        prompt += f"\n\n{game.get_move_format_description()}"
        
        # Get function calling schema if available
        if ai_interface:
            function_schema = ai_interface.get_function_calling_schema()
        else:
            function_schema = None
        
        # Call AI model
        response = await ai_model.get_completion(
            prompt=prompt,
            function_schema=function_schema,
            temperature=0.7 if game_config.mode == GameMode.CREATIVE else 0.1
        )
        
        # Parse response
        if ai_interface and isinstance(response, dict):
            action = ai_interface.parse_ai_response(response)
        else:
            # Fallback parsing - this would need to be game-specific
            action = self._parse_text_response(response, state.possible_actions)
        
        return action
    
    def _parse_text_response(self, response: str, possible_actions: List[GameAction]) -> GameAction:
        """Fallback text parsing when function calling is not available."""
        # This is a simplified parser - in practice, each game might need custom parsing
        response_lower = response.lower()
        
        # Try to find action type and parameters in response
        for action in possible_actions:
            action_str = f"{action.action_type} {action.parameters}"
            if action_str.lower() in response_lower:
                return action
        
        # Default to first possible action
        if possible_actions:
            return possible_actions[0]
        
        # Fallback
        return GameAction(
            action_type="unknown",
            parameters={},
            reasoning="Could not parse AI response"
        )
    
    async def _cleanup_evaluation(self, evaluation_id: str, delay: int = 300):
        """Clean up evaluation tracking after a delay."""
        await asyncio.sleep(delay)
        if evaluation_id in self.active_evaluations:
            del self.active_evaluations[evaluation_id]
    
    async def evaluate_session(
        self,
        session_config: Dict[str, Any],
        ai_models: Dict[str, BaseModel],
        stream_callback: Optional[callable] = None
    ) -> List[GameEvaluationResult]:
        """
        Evaluate a complete competition session.
        
        Args:
            session_config: Session configuration with rounds
            ai_models: Dictionary mapping player_id to AI model
            stream_callback: Optional callback for streaming updates
        
        Returns:
            List of evaluation results for all games
        """
        results = []
        
        for round_config in session_config["rounds"]:
            round_num = round_config["round_number"]
            game_name = round_config["game_name"]
            
            # Evaluate each player
            player_results = []
            
            for player_id, ai_model in ai_models.items():
                if stream_callback:
                    await stream_callback({
                        "type": "round_start",
                        "round": round_num,
                        "game": game_name,
                        "player": player_id
                    })
                
                # Create game config
                game_config = GameConfig(
                    difficulty=round_config["game_config"]["difficulty"],
                    mode=GameMode(round_config["game_config"]["mode"]),
                    custom_settings=round_config["game_config"].get("custom_settings", {}),
                    time_limit=round_config.get("time_limit")
                )
                
                # Create scoring profile
                scoring_profile = ScoringProfile(
                    name=round_config["scoring_profile"]["name"],
                    description="",
                    weights=[]  # Would be loaded from config
                )
                
                # Evaluate
                result = await self.evaluate_game(
                    game_name=game_name,
                    game_config=game_config,
                    ai_model=ai_model,
                    scoring_profile=scoring_profile,
                    player_id=player_id,
                    stream_callback=stream_callback
                )
                
                player_results.append(result)
            
            results.extend(player_results)
            
            if stream_callback:
                await stream_callback({
                    "type": "round_complete",
                    "round": round_num,
                    "results": [r.to_dict() for r in player_results]
                })
        
        return results
    
    def get_active_evaluations(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active evaluations."""
        return self.active_evaluations.copy()