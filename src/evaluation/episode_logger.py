"""Episode logging for interactive tasks with proper output schemas."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from src.core.types import GameTranscript, Move, TaskType
from .advanced_metrics import generate_task_uid


class EpisodeLogger:
    """Logger for game episodes with MineBench-compliant output format."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize episode logger.
        
        Args:
            output_dir: Directory for episode logs
        """
        self.output_dir = output_dir or Path("data/episodes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def log_episode(
        self,
        transcript: GameTranscript,
        task_type: TaskType,
        model_id: str,
        prompt_hash: str,
        reasoning_scores: Optional[List[float]] = None,
        latencies: Optional[List[float]] = None,
    ) -> Path:
        """
        Log a game episode in MineBench format.
        
        Args:
            transcript: Game transcript
            task_type: Type of task
            model_id: Model identifier
            prompt_hash: Hash of prompt template
            reasoning_scores: Per-turn reasoning scores
            latencies: Per-turn latencies in ms
        
        Returns:
            Path to episode log file
        """
        task_uid = generate_task_uid(task_type, transcript.task_id)
        
        # Create episode log
        episode_lines = []
        
        for i, move in enumerate(transcript.moves):
            turn_data = {
                "turn": i + 1,
                "board": move.board_state_before,
                "action": move.action.to_string() if move.action else "Invalid",
                "rationale": move.model_reasoning or "",
            }
            
            # Add optional fields
            if move.board_state_after:
                turn_data["board_after"] = move.board_state_after
            
            if reasoning_scores and i < len(reasoning_scores):
                turn_data["reasoning_score"] = reasoning_scores[i]
            
            if latencies and i < len(latencies):
                turn_data["latency_ms"] = latencies[i]
            
            episode_lines.append(json.dumps(turn_data))
        
        # Save episode log
        filename = f"{task_uid}_{model_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            f.write("\n".join(episode_lines))
        
        return filepath
    
    def create_item_result(
        self,
        task_id: str,
        task_type: TaskType,
        model_id: str,
        prompt_hash: str,
        prediction: str,
        rationale: str,
        is_correct: bool,
        reasoning_score: float,
        latency_ms: float,
    ) -> Dict[str, Any]:
        """
        Create per-item result in MineBench format.
        
        Args:
            task_id: Original task ID
            task_type: Type of task
            model_id: Model identifier
            prompt_hash: Hash of prompt template
            prediction: Model's prediction
            rationale: Model's reasoning
            is_correct: Whether prediction was correct
            reasoning_score: Judge score (0-1)
            latency_ms: Response latency
        
        Returns:
            Item result dictionary
        """
        task_uid = generate_task_uid(task_type, task_id)
        
        return {
            "task_uid": task_uid,
            "model_id": model_id,
            "prompt_hash": prompt_hash,
            "prediction": prediction,
            "rationale": rationale,
            "is_correct": is_correct,
            "reasoning_score": reasoning_score,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def save_batch_results(
        self,
        results: List[Dict[str, Any]],
        run_id: str,
        model_id: str,
        eval_spec: str = "v1.0",
    ) -> Path:
        """
        Save batch results in MineBench format.
        
        Args:
            results: List of item results
            run_id: Unique run identifier
            model_id: Model identifier
            eval_spec: Evaluation specification version
        
        Returns:
            Path to results file
        """
        batch_data = {
            "run_id": run_id,
            "model_id": model_id,
            "eval_spec": eval_spec,
            "start_ts": datetime.utcnow().isoformat(),
            "results": results,
            "summary": self._calculate_summary(results),
        }
        
        filename = f"batch_{run_id}_{model_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(batch_data, f, indent=2)
        
        return filepath
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for batch results."""
        if not results:
            return {}
        
        correct_count = sum(1 for r in results if r.get("is_correct", False))
        total_count = len(results)
        
        reasoning_scores = [r.get("reasoning_score", 0) for r in results]
        latencies = [r.get("latency_ms", 0) for r in results]
        
        return {
            "accuracy": correct_count / total_count if total_count > 0 else 0,
            "total_items": total_count,
            "correct_items": correct_count,
            "avg_reasoning_score": sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
        }


class MineBenchFormatter:
    """Format evaluation outputs for MineBench compliance."""
    
    @staticmethod
    def format_leaderboard_entry(
        model_id: str,
        metrics: Dict[str, float],
        eval_spec: str = "v1.0",
        prompt_variant: str = "standard",
        hidden_split: bool = False,
    ) -> Dict[str, Any]:
        """
        Format a leaderboard entry.
        
        Args:
            model_id: Model identifier
            metrics: Evaluation metrics
            eval_spec: Evaluation specification version
            prompt_variant: Prompt template used
            hidden_split: Whether evaluated on hidden split
        
        Returns:
            Leaderboard entry
        """
        return {
            "model_id": model_id,
            "eval_spec": eval_spec,
            "prompt_variant": prompt_variant,
            "hidden_split": hidden_split,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "ms_s_score": metrics.get("ms_s_score", 0.0),
                "ms_i_score": metrics.get("ms_i_score", 0.0),
                "global_score": metrics.get("global_score", 0.0),
                "win_rate": metrics.get("win_rate", 0.0),
                "accuracy": metrics.get("accuracy", 0.0),
                "coverage": metrics.get("coverage", 0.0),
                "reasoning_score": metrics.get("reasoning_score", 0.0),
            },
            "statistical_significance": metrics.get("significance", {}),
        }
    
    @staticmethod
    def hash_prompt_template(template: str) -> str:
        """Generate hash for prompt template."""
        import hashlib
        return hashlib.sha256(template.encode()).hexdigest()[:6]