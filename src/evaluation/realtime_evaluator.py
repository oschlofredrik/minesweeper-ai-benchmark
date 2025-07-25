"""
Real-time evaluation execution service for game sessions.

This service integrates with the dynamic evaluation system to run evaluations
during game play and stream results in real-time.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from src.core.evaluation_models import (
    Evaluation, GameEvaluation, EvaluationScore
)
from src.evaluation.dynamic_engine import (
    DynamicEvaluationEngine, EvaluationContext
)
from src.api.event_streaming import publish_evaluation_update
from src.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RealtimeEvaluator:
    """Handles real-time evaluation execution during game sessions."""
    
    def __init__(self):
        self.engine = DynamicEvaluationEngine()
        self.active_sessions: Dict[str, 'SessionEvaluator'] = {}
    
    async def start_session_evaluation(
        self,
        session_id: str,
        evaluations: List[Dict[str, Any]],
        db: Optional[Session] = None
    ) -> None:
        """Start evaluation tracking for a game session."""
        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already being evaluated")
            return
        
        # Create session evaluator
        session_evaluator = SessionEvaluator(
            session_id=session_id,
            evaluations=evaluations,
            engine=self.engine
        )
        
        self.active_sessions[session_id] = session_evaluator
        
        # Initialize evaluations in database if provided
        if db:
            await session_evaluator.initialize_in_db(db)
        
        logger.info(
            f"Started evaluation for session {session_id}",
            extra={
                "session_id": session_id,
                "num_evaluations": len(evaluations)
            }
        )
    
    async def evaluate_move(
        self,
        session_id: str,
        player_id: str,
        move_data: Dict[str, Any],
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a single move in real-time."""
        if session_id not in self.active_sessions:
            logger.warning(f"No active evaluation for session {session_id}")
            return {}
        
        session_evaluator = self.active_sessions[session_id]
        
        # Evaluate the move
        results = await session_evaluator.evaluate_move(
            player_id=player_id,
            move_data=move_data,
            game_state=game_state
        )
        
        # Publish real-time update
        await self._publish_evaluation_results(
            session_id=session_id,
            player_id=player_id,
            results=results
        )
        
        return results
    
    async def evaluate_round(
        self,
        session_id: str,
        player_id: str,
        round_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a completed round."""
        if session_id not in self.active_sessions:
            logger.warning(f"No active evaluation for session {session_id}")
            return {}
        
        session_evaluator = self.active_sessions[session_id]
        
        # Evaluate the round
        results = await session_evaluator.evaluate_round(
            player_id=player_id,
            round_data=round_data
        )
        
        # Store results in database
        await self._store_round_results(
            session_id=session_id,
            player_id=player_id,
            results=results
        )
        
        return results
    
    async def get_session_scores(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get current scores for all players in a session."""
        if session_id not in self.active_sessions:
            return {}
        
        return self.active_sessions[session_id].get_current_scores()
    
    async def end_session_evaluation(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """End evaluation for a session and return final results."""
        if session_id not in self.active_sessions:
            logger.warning(f"No active evaluation for session {session_id}")
            return {}
        
        session_evaluator = self.active_sessions[session_id]
        final_results = session_evaluator.get_final_results()
        
        # Clean up
        del self.active_sessions[session_id]
        
        logger.info(
            f"Ended evaluation for session {session_id}",
            extra={
                "session_id": session_id,
                "final_results": final_results
            }
        )
        
        return final_results
    
    async def _publish_evaluation_results(
        self,
        session_id: str,
        player_id: str,
        results: Dict[str, Any]
    ) -> None:
        """Publish evaluation results to event stream."""
        try:
            await publish_evaluation_update({
                "session_id": session_id,
                "player_id": player_id,
                "timestamp": datetime.utcnow().isoformat(),
                "scores": results.get("scores", {}),
                "breakdown": results.get("breakdown", []),
                "current_total": results.get("total_score", 0)
            })
        except Exception as e:
            logger.error(f"Failed to publish evaluation results: {e}")
    
    async def _store_round_results(
        self,
        session_id: str,
        player_id: str,
        results: Dict[str, Any]
    ) -> None:
        """Store round evaluation results in database."""
        try:
            db = get_db()
            try:
                for eval_id, score_data in results.get("evaluations", {}).items():
                    score = EvaluationScore(
                        game_session_id=UUID(session_id),
                        player_id=UUID(player_id),
                        evaluation_id=UUID(eval_id),
                        round_number=results.get("round_number", 1),
                        raw_score=score_data.get("raw_score", 0),
                        normalized_score=score_data.get("normalized_score", 0),
                        rule_breakdown=score_data.get("breakdown", []),
                        dimension_scores=score_data.get("dimensions", {}),
                        context_snapshot={
                            "game_state": results.get("game_state", {}),
                            "move_count": results.get("move_count", 0)
                        }
                    )
                    db.add(score)
                
                db.commit()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to store round results: {e}")


class SessionEvaluator:
    """Handles evaluation for a single game session."""
    
    def __init__(
        self,
        session_id: str,
        evaluations: List[Dict[str, Any]],
        engine: DynamicEvaluationEngine
    ):
        self.session_id = session_id
        self.evaluations = evaluations
        self.engine = engine
        self.player_scores: Dict[str, Dict[str, float]] = {}
        self.round_history: List[Dict[str, Any]] = []
        self.move_count: Dict[str, int] = {}
    
    async def initialize_in_db(self, db: Session) -> None:
        """Initialize game evaluations in database."""
        for eval_config in self.evaluations:
            if not eval_config.get("is_quick", False):
                game_eval = GameEvaluation(
                    game_session_id=UUID(self.session_id),
                    evaluation_id=UUID(eval_config["evaluation_id"]),
                    weight=eval_config.get("weight", 0),
                    dimension=eval_config.get("dimension"),
                    config_overrides=eval_config.get("config_overrides", {})
                )
                db.add(game_eval)
        
        db.commit()
    
    async def evaluate_move(
        self,
        player_id: str,
        move_data: Dict[str, Any],
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a single move."""
        # Track move count
        if player_id not in self.move_count:
            self.move_count[player_id] = 0
        self.move_count[player_id] += 1
        
        # Create evaluation context
        context = EvaluationContext(
            prompt=move_data.get("prompt", ""),
            response=move_data.get("response", ""),
            metadata={
                "game_state": game_state,
                "move_number": self.move_count[player_id],
                "action": move_data.get("action"),
                "position": move_data.get("position"),
                "response_time": move_data.get("response_time", 0)
            },
            round_history=self.round_history
        )
        
        # Run evaluations
        results = {
            "scores": {},
            "breakdown": [],
            "total_score": 0
        }
        
        for eval_config in self.evaluations:
            try:
                eval_result = await self._run_single_evaluation(
                    eval_config,
                    context
                )
                
                if eval_result:
                    eval_id = eval_config["evaluation_id"]
                    weight = eval_config.get("weight", 0)
                    
                    results["scores"][eval_id] = {
                        "raw": eval_result["raw_score"],
                        "normalized": eval_result["normalized_score"],
                        "weighted": eval_result["normalized_score"] * weight
                    }
                    
                    results["breakdown"].extend(eval_result.get("breakdown", []))
                    results["total_score"] += eval_result["normalized_score"] * weight
                    
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
        
        # Update player total
        if player_id not in self.player_scores:
            self.player_scores[player_id] = {}
        
        for eval_id, scores in results["scores"].items():
            if eval_id not in self.player_scores[player_id]:
                self.player_scores[player_id][eval_id] = 0
            self.player_scores[player_id][eval_id] += scores["weighted"]
        
        return results
    
    async def evaluate_round(
        self,
        player_id: str,
        round_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a completed round."""
        # Create context for round evaluation
        context = EvaluationContext(
            prompt=round_data.get("initial_prompt", ""),
            response=json.dumps(round_data.get("moves", [])),
            metadata={
                "round_number": len(self.round_history) + 1,
                "game_result": round_data.get("result"),
                "total_moves": round_data.get("total_moves", 0),
                "duration": round_data.get("duration", 0),
                "final_state": round_data.get("final_state", {})
            },
            round_history=self.round_history
        )
        
        # Run round-level evaluations
        results = {
            "round_number": len(self.round_history) + 1,
            "evaluations": {},
            "total_score": 0,
            "game_state": round_data.get("final_state", {}),
            "move_count": round_data.get("total_moves", 0)
        }
        
        for eval_config in self.evaluations:
            try:
                eval_result = await self._run_single_evaluation(
                    eval_config,
                    context,
                    is_round_eval=True
                )
                
                if eval_result:
                    eval_id = eval_config["evaluation_id"]
                    weight = eval_config.get("weight", 0)
                    
                    results["evaluations"][eval_id] = {
                        "raw_score": eval_result["raw_score"],
                        "normalized_score": eval_result["normalized_score"],
                        "weighted_score": eval_result["normalized_score"] * weight,
                        "breakdown": eval_result.get("breakdown", []),
                        "dimensions": eval_result.get("dimensions", {})
                    }
                    
                    results["total_score"] += eval_result["normalized_score"] * weight
                    
            except Exception as e:
                logger.error(f"Round evaluation failed: {e}")
        
        # Add to history
        self.round_history.append({
            "round_number": results["round_number"],
            "player_id": player_id,
            "scores": results["evaluations"],
            "game_result": round_data.get("result")
        })
        
        return results
    
    async def _run_single_evaluation(
        self,
        eval_config: Dict[str, Any],
        context: EvaluationContext,
        is_round_eval: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Run a single evaluation."""
        try:
            # Handle quick evaluations (created in UI)
            if eval_config.get("is_quick", False):
                return self._run_quick_evaluation(eval_config, context)
            
            # Load evaluation from database
            eval_id = eval_config["evaluation_id"]
            
            # Get evaluation definition
            db = get_db()
            try:
                evaluation = db.query(Evaluation).filter(
                    Evaluation.id == UUID(eval_id)
                ).first()
                
                if not evaluation:
                    logger.warning(f"Evaluation {eval_id} not found")
                    return None
                
                # Create evaluation config
                config = {
                    "id": str(evaluation.id),
                    "name": evaluation.name,
                    "scoring_type": evaluation.scoring_type,
                    "rules": evaluation.rules,
                    "normalization_config": evaluation.normalization_config
                }
                
                # Apply overrides
                if eval_config.get("config_overrides"):
                    config.update(eval_config["config_overrides"])
                
                # Run evaluation
                result = self.engine.evaluate(config, context)
                
                return result
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to run evaluation: {e}")
            return None
    
    def _run_quick_evaluation(
        self,
        eval_config: Dict[str, Any],
        context: EvaluationContext
    ) -> Dict[str, Any]:
        """Run a quick evaluation created in the UI."""
        # Simple implementation for quick evaluations
        # These would be predefined templates
        
        eval_type = eval_config.get("type", "time_bonus")
        raw_score = 0
        
        if eval_type == "time_bonus":
            max_time = eval_config.get("max_time", 300)
            max_bonus = eval_config.get("max_bonus", 100)
            response_time = context.metadata.get("response_time", 0)
            
            if response_time < max_time:
                raw_score = max_bonus * (1 - response_time / max_time)
        
        elif eval_type == "accuracy_threshold":
            min_accuracy = eval_config.get("min_accuracy", 80)
            accuracy = context.metadata.get("accuracy", 0) * 100
            raw_score = 100 if accuracy >= min_accuracy else 0
        
        # Normalize
        normalized = min(1.0, max(0.0, raw_score / 100))
        
        return {
            "raw_score": raw_score,
            "normalized_score": normalized,
            "breakdown": [{
                "type": eval_type,
                "score": raw_score,
                "details": eval_config
            }]
        }
    
    def get_current_scores(self) -> Dict[str, Any]:
        """Get current scores for all players."""
        scores = {}
        
        for player_id, eval_scores in self.player_scores.items():
            total_score = sum(eval_scores.values())
            scores[player_id] = {
                "total": total_score,
                "evaluations": eval_scores,
                "rounds_played": len([
                    r for r in self.round_history 
                    if r["player_id"] == player_id
                ])
            }
        
        return scores
    
    def get_final_results(self) -> Dict[str, Any]:
        """Get final evaluation results."""
        return {
            "session_id": self.session_id,
            "player_scores": self.get_current_scores(),
            "round_history": self.round_history,
            "evaluation_configs": self.evaluations
        }


# Global instance
realtime_evaluator = RealtimeEvaluator()