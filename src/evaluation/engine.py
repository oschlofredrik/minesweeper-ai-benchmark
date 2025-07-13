"""Main evaluation engine orchestrating the benchmark process."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from src.core.types import ModelConfig, Task, EvaluationMetrics
from src.core.config import settings
from .runner import GameRunner
from .metrics import MetricsCalculator


class EvaluationEngine:
    """Orchestrates model evaluation on benchmark tasks."""
    
    def __init__(self, results_dir: Optional[Path] = None):
        """
        Initialize evaluation engine.
        
        Args:
            results_dir: Directory to save results (optional)
        """
        self.results_dir = results_dir or Path("data/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_calculator = MetricsCalculator()
    
    async def evaluate_model(
        self,
        model_config: ModelConfig,
        tasks: List[Task],
        max_moves: int = 500,
        prompt_format: str = "standard",
        parallel_games: int = 1,
        save_results: bool = True,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate a model on a set of tasks.
        
        Args:
            model_config: Model configuration
            tasks: List of tasks to evaluate
            max_moves: Maximum moves per game
            prompt_format: Prompt format to use
            parallel_games: Number of games to run in parallel
            save_results: Whether to save results to disk
            verbose: Whether to print progress
        
        Returns:
            Evaluation results dictionary
        """
        if verbose:
            print(f"\nEvaluating {model_config.name} on {len(tasks)} tasks")
            print(f"Parallel games: {parallel_games}")
        
        start_time = datetime.utcnow()
        
        # Create game runner
        runner = GameRunner(model_config)
        
        # Run games
        transcripts = await runner.run_multiple_games(
            tasks=tasks,
            max_moves=max_moves,
            prompt_format=prompt_format,
            parallel=parallel_games,
            verbose=verbose,
        )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        metrics = self.metrics_calculator.calculate_metrics(transcripts)
        
        # Calculate per-game metrics
        per_game_metrics = [
            self.metrics_calculator.calculate_per_game_metrics(t)
            for t in transcripts
        ]
        
        # Create results
        results = {
            "model": {
                "name": model_config.name,
                "provider": model_config.provider,
                "model_id": model_config.model_id,
                "temperature": model_config.temperature,
            },
            "evaluation": {
                "num_tasks": len(tasks),
                "max_moves": max_moves,
                "prompt_format": prompt_format,
                "parallel_games": parallel_games,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
            },
            "metrics": metrics.to_dict(),
            "per_game_metrics": per_game_metrics,
            "game_results": [  # Add detailed game results for summaries
                {
                    "game_id": game["game_id"],
                    "won": game["won"],
                    "final_status": game["status"],
                    "num_moves": game["moves"],
                    "board_coverage": game["board_coverage"],
                    "mines_correctly_flagged": int(game["flag_recall"] * len(transcripts[i].final_state.mine_positions)) if i < len(transcripts) else 0,
                    "total_mines": len(transcripts[i].final_state.mine_positions) if i < len(transcripts) else 0,
                    "valid_move_rate": game["valid_move_rate"],
                    "duration": game["duration_seconds"],
                    "moves": [  # Add move-by-move data with full AI interaction
                        {
                            "move_number": j + 1,
                            "action": move.action.to_string(),
                            "was_valid": move.was_valid,
                            "reasoning": move.model_reasoning,
                            "error": move.error_message,
                            "prompt_sent": move.prompt_sent,
                            "full_response": move.full_response,
                            "tokens_used": move.tokens_used,
                            "timestamp": move.timestamp.isoformat() if move.timestamp else None
                        }
                        for j, move in enumerate(transcripts[i].moves)
                    ] if i < len(transcripts) else []
                }
                for i, game in enumerate(per_game_metrics)
            ],
        }
        
        if save_results:
            self._save_results(results, model_config.name, transcripts)
        
        if verbose:
            self._print_summary(results)
        
        return results
    
    async def compare_models(
        self,
        model_configs: List[ModelConfig],
        tasks: List[Task],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Compare multiple models on the same tasks.
        
        Args:
            model_configs: List of model configurations
            tasks: List of tasks to evaluate
            **kwargs: Additional arguments for evaluate_model
        
        Returns:
            Comparison results
        """
        results = {}
        
        for model_config in model_configs:
            model_results = await self.evaluate_model(
                model_config=model_config,
                tasks=tasks,
                **kwargs
            )
            results[model_config.name] = model_results
        
        # Create comparison summary
        comparison = self._create_comparison_summary(results)
        
        return {
            "model_results": results,
            "comparison": comparison,
        }
    
    def _save_results(
        self,
        results: Dict[str, Any],
        model_name: str,
        transcripts: List[Any]
    ) -> None:
        """Save evaluation results to disk."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save summary results
        summary_file = self.results_dir / f"{model_name}_{timestamp}_summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Save transcripts (in a separate file due to size)
        transcripts_file = self.results_dir / f"{model_name}_{timestamp}_transcripts.json"
        transcript_data = []
        
        for transcript in transcripts:
            # Convert transcript to serializable format
            t_dict = {
                "game_id": transcript.game_id,
                "task_id": transcript.task_id,
                "model_name": transcript.model_name,
                "start_time": transcript.start_time.isoformat(),
                "end_time": transcript.end_time.isoformat(),
                "final_status": transcript.final_state.status.value,
                "num_moves": len(transcript.moves),
                "moves": [
                    {
                        "action": move.action.to_string(),
                        "timestamp": move.timestamp.isoformat(),
                        "was_valid": move.was_valid,
                        "reasoning": move.model_reasoning,
                        "error": move.error_message,
                        "prompt_sent": move.prompt_sent,
                        "full_response": move.full_response,
                        "tokens_used": move.tokens_used,
                    }
                    for move in transcript.moves
                ],
            }
            transcript_data.append(t_dict)
        
        with open(transcripts_file, "w") as f:
            json.dump(transcript_data, f, indent=2)
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Print evaluation summary."""
        metrics = results["metrics"]
        
        print("\n" + "=" * 50)
        print(f"Evaluation Results for {results['model']['name']}")
        print("=" * 50)
        
        print(f"\nGames played: {results['evaluation']['num_tasks']}")
        print(f"Total duration: {results['evaluation']['duration_seconds']:.1f}s")
        
        print("\nKey Metrics:")
        print(f"  Win Rate: {metrics['win_rate']:.1%}")
        print(f"  Valid Move Rate: {metrics['valid_move_rate']:.1%}")
        print(f"  Mine Precision: {metrics['mine_identification_precision']:.1%}")
        print(f"  Mine Recall: {metrics['mine_identification_recall']:.1%}")
        
        if metrics['average_moves_to_win'] is not None:
            print(f"  Avg Moves to Win: {metrics['average_moves_to_win']:.1f}")
        if metrics['average_moves_to_loss'] is not None:
            print(f"  Avg Moves to Loss: {metrics['average_moves_to_loss']:.1f}")
        
        print(f"  Board Coverage on Loss: {metrics['board_coverage_on_loss']:.1%}")
        
        if metrics['reasoning_quality_score'] is not None:
            print(f"  Reasoning Quality: {metrics['reasoning_quality_score']:.1%}")
    
    def _create_comparison_summary(
        self, results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create summary comparing multiple models."""
        comparison = {
            "models": list(results.keys()),
            "metrics": {},
        }
        
        # Compare key metrics
        metric_names = [
            "win_rate",
            "valid_move_rate",
            "mine_identification_precision",
            "mine_identification_recall",
            "board_coverage_on_loss",
        ]
        
        for metric in metric_names:
            comparison["metrics"][metric] = {
                model: results[model]["metrics"][metric]
                for model in results
            }
        
        # Find best model for each metric
        comparison["best_by_metric"] = {}
        for metric in metric_names:
            values = [
                (model, results[model]["metrics"][metric])
                for model in results
            ]
            best_model = max(values, key=lambda x: x[1])
            comparison["best_by_metric"][metric] = {
                "model": best_model[0],
                "value": best_model[1],
            }
        
        return comparison