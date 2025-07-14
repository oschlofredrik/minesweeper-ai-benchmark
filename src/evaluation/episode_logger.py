"""Episode logging for MineBench-compliant output formats."""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from src.core.types import GameTranscript
from src.core.logging_config import get_logger

logger = get_logger("evaluation.episode_logger")


class EpisodeLogger:
    """Logs evaluation episodes in MineBench-compliant formats."""
    
    def __init__(self, output_dir: str = "data/episodes"):
        """
        Initialize episode logger.
        
        Args:
            output_dir: Directory to save episode logs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def log_episode(
        self,
        transcript: GameTranscript,
        task_uid: str,
        model_id: str,
        prompt_variant: str = "standard"
    ) -> str:
        """
        Log a single game episode.
        
        Args:
            transcript: Game transcript
            task_uid: MineBench task UID
            model_id: Model identifier
            prompt_variant: Prompt variant used
        
        Returns:
            Path to saved episode file
        """
        # Create episode data
        episode_data = []
        
        for i, move in enumerate(transcript.moves):
            turn_data = {
                "turn": i + 1,
                "board": move.board_state_before,
                "action": move.action.to_string(),
                "rationale": move.model_reasoning or "",
                "was_valid": move.was_valid,
                "error": move.error_message,
                "latency_ms": int((move.timestamp - transcript.start_time).total_seconds() * 1000) if i == 0 else 100,  # Estimate
                "tokens_used": move.tokens_used
            }
            episode_data.append(turn_data)
        
        # Save as JSONL
        filename = f"{task_uid}_{model_id}_{transcript.game_id}.jsonl"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            for turn in episode_data:
                f.write(json.dumps(turn) + '\n')
        
        logger.info(f"Saved episode log: {filepath}")
        return str(filepath)
    
    def save_batch_results(
        self,
        results: Dict[str, Any],
        run_id: str,
        model_id: str
    ) -> str:
        """
        Save batch evaluation results.
        
        Args:
            results: Evaluation results dictionary
            run_id: Unique run identifier
            model_id: Model identifier
        
        Returns:
            Path to saved results file
        """
        # Add metadata
        results["run_id"] = run_id
        results["model_id"] = model_id
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Save results
        filename = f"results_{run_id}_{model_id}.json"
        filepath = self.output_dir.parent / "results" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved batch results: {filepath}")
        return str(filepath)


class MineBenchFormatter:
    """Formats evaluation data for MineBench compliance."""
    
    @staticmethod
    def format_per_item_result(
        task_uid: str,
        model_id: str,
        prompt_hash: str,
        prediction: str,
        rationale: str,
        is_correct: bool,
        reasoning_score: float,
        latency_ms: int
    ) -> Dict[str, Any]:
        """
        Format a single prediction result.
        
        Returns:
            MineBench-compliant result dictionary
        """
        return {
            "task_uid": task_uid,
            "model_id": model_id,
            "prompt_hash": prompt_hash[:6],  # First 6 chars
            "prediction": prediction,
            "rationale": rationale,
            "is_correct": is_correct,
            "reasoning_score": round(reasoning_score, 2),
            "latency_ms": latency_ms
        }
    
    @staticmethod
    def format_leaderboard_entry(
        model_id: str,
        metrics: Dict[str, float],
        eval_spec_version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        Format leaderboard entry.
        
        Returns:
            MineBench-compliant leaderboard entry
        """
        return {
            "model_id": model_id,
            "eval_spec": eval_spec_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "global_score": round(metrics.get("global_score", 0), 4),
                "ms_s_score": round(metrics.get("ms_s_score", 0), 4),
                "ms_i_score": round(metrics.get("ms_i_score", 0), 4),
                "details": metrics
            }
        }