"""Advanced metrics calculation including composite scores and MineBench compliance."""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
import hashlib
from datetime import datetime, timezone

from src.core.types import TaskType, GameTranscript, GameStatus
from src.core.logging_config import get_logger
from .statistical_analysis import StatisticalAnalyzer, SignificanceTestResult
from .reasoning_judge import ReasoningJudgment

logger = get_logger("evaluation.advanced_metrics")


@dataclass
class AdvancedMetrics:
    """Container for advanced evaluation metrics."""
    # Core metrics
    accuracy: float = 0.0
    win_rate: float = 0.0
    valid_output_rate: float = 0.0
    valid_move_rate: float = 0.0
    coverage: float = 0.0
    flag_precision: float = 0.0
    flag_recall: float = 0.0
    reasoning_score: float = 0.0
    
    # Composite scores
    ms_s_score: float = 0.0
    ms_i_score: float = 0.0
    global_score: float = 0.0
    
    # Additional metrics
    average_moves_to_win: Optional[float] = None
    average_moves_to_loss: Optional[float] = None
    move_efficiency: float = 0.0
    
    # Statistical info
    confidence_intervals: Dict[str, Tuple[float, float]] = None
    sample_sizes: Dict[str, int] = None
    
    def __post_init__(self):
        if self.confidence_intervals is None:
            self.confidence_intervals = {}
        if self.sample_sizes is None:
            self.sample_sizes = {}


class AdvancedMetricsCalculator:
    """Calculates advanced metrics including MineBench composite scores."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize calculator.
        
        Args:
            confidence_level: Confidence level for intervals
        """
        self.confidence_level = confidence_level
        self.stat_analyzer = StatisticalAnalyzer(confidence_level)
    
    def generate_task_uid(self, task_id: str, task_type: TaskType) -> str:
        """
        Generate MineBench-compliant task UID.
        
        Format: <code>-<hash6>
        """
        # Determine code based on task type
        if task_type == TaskType.STATIC:
            code = "MS-S"
        elif task_type == TaskType.INTERACTIVE:
            code = "MS-I"
        else:
            code = "UNK"
        
        # Generate 6-character hash from task_id
        hash_obj = hashlib.sha256(task_id.encode())
        hash6 = hash_obj.hexdigest()[:6]
        
        return f"{code}-{hash6}"
    
    def calculate_static_metrics(
        self,
        predictions: List[Dict[str, Any]],
        reasoning_judgments: Optional[List[ReasoningJudgment]] = None
    ) -> AdvancedMetrics:
        """
        Calculate metrics for static (MS-S) tasks.
        
        Args:
            predictions: List of predictions with 'correct' and 'valid' fields
            reasoning_judgments: Optional reasoning quality judgments
        
        Returns:
            AdvancedMetrics object
        """
        if not predictions:
            return AdvancedMetrics()
        
        # Basic counts
        total = len(predictions)
        correct = sum(1 for p in predictions if p.get("correct", False))
        valid = sum(1 for p in predictions if p.get("valid", True))
        
        # Core metrics
        accuracy = correct / total
        valid_output_rate = valid / total
        
        # Reasoning score
        reasoning_score = 0.0
        if reasoning_judgments:
            reasoning_score = sum(j.normalized_score for j in reasoning_judgments) / len(reasoning_judgments)
        
        # MS-S composite score: ACC × 0.7 + VOR × 0.1 + RS × 0.2
        ms_s_score = (accuracy * 0.7) + (valid_output_rate * 0.1) + (reasoning_score * 0.2)
        
        # Calculate confidence intervals
        acc_ci = self.stat_analyzer.calculate_confidence_interval(correct, total)
        vor_ci = self.stat_analyzer.calculate_confidence_interval(valid, total)
        
        metrics = AdvancedMetrics(
            accuracy=accuracy,
            valid_output_rate=valid_output_rate,
            reasoning_score=reasoning_score,
            ms_s_score=ms_s_score,
            global_score=ms_s_score,  # For static-only evaluation
            confidence_intervals={
                "accuracy": acc_ci,
                "valid_output_rate": vor_ci
            },
            sample_sizes={
                "predictions": total
            }
        )
        
        return metrics
    
    def calculate_interactive_metrics(
        self,
        transcripts: List[GameTranscript],
        reasoning_judgments: Optional[Dict[str, List[ReasoningJudgment]]] = None
    ) -> AdvancedMetrics:
        """
        Calculate metrics for interactive (MS-I) tasks.
        
        Args:
            transcripts: List of game transcripts
            reasoning_judgments: Optional dict mapping game_id to judgments
        
        Returns:
            AdvancedMetrics object
        """
        if not transcripts:
            return AdvancedMetrics()
        
        # Initialize counters
        total_games = len(transcripts)
        wins = 0
        total_moves = 0
        valid_moves = 0
        total_possible_cells = 0
        total_revealed_cells = 0
        true_positives = 0  # Correctly flagged mines
        false_positives = 0  # Incorrectly flagged cells
        total_mines = 0
        
        moves_to_win = []
        moves_to_loss = []
        
        # Process each transcript
        for transcript in transcripts:
            # Win rate
            if transcript.final_state.status == GameStatus.WON:
                wins += 1
                moves_to_win.append(transcript.num_moves)
            else:
                moves_to_loss.append(transcript.num_moves)
            
            # Valid moves
            for move in transcript.moves:
                total_moves += 1
                if move.was_valid:
                    valid_moves += 1
            
            # Coverage (board exploration)
            board_size = transcript.final_state.board_rows * transcript.final_state.board_cols
            mine_count = len(transcript.final_state.mine_positions)
            safe_cells = board_size - mine_count
            total_possible_cells += safe_cells
            
            # Count revealed cells
            revealed = len(transcript.final_state.revealed_cells)
            total_revealed_cells += revealed
            
            # Flag precision/recall
            total_mines += mine_count
            
            # Check flagged positions
            for move in transcript.moves:
                if move.action.action_type.value.lower() == "flag":
                    pos = move.action.position
                    if (pos.row, pos.col) in transcript.final_state.mine_positions:
                        true_positives += 1
                    else:
                        false_positives += 1
        
        # Calculate metrics
        win_rate = wins / total_games
        coverage = total_revealed_cells / total_possible_cells if total_possible_cells > 0 else 0
        valid_move_rate = valid_moves / total_moves if total_moves > 0 else 0
        
        # Flag metrics
        flag_precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        flag_recall = true_positives / total_mines if total_mines > 0 else 0
        
        # Average moves
        avg_moves_win = np.mean(moves_to_win) if moves_to_win else None
        avg_moves_loss = np.mean(moves_to_loss) if moves_to_loss else None
        
        # Reasoning score
        reasoning_score = 0.0
        if reasoning_judgments:
            all_judgments = []
            for judgments in reasoning_judgments.values():
                all_judgments.extend(judgments)
            if all_judgments:
                reasoning_score = sum(j.normalized_score for j in all_judgments) / len(all_judgments)
        
        # MS-I composite score: WR × 0.5 + COV × 0.2 + VMR × 0.1 + FLAG × 0.1 + RS × 0.1
        flag_score = (flag_precision + flag_recall) / 2
        ms_i_score = (
            (win_rate * 0.5) +
            (coverage * 0.2) +
            (valid_move_rate * 0.1) +
            (flag_score * 0.1) +
            (reasoning_score * 0.1)
        )
        
        # Calculate confidence intervals
        win_ci = self.stat_analyzer.calculate_confidence_interval(wins, total_games)
        vmr_ci = self.stat_analyzer.calculate_confidence_interval(valid_moves, total_moves)
        
        metrics = AdvancedMetrics(
            win_rate=win_rate,
            coverage=coverage,
            valid_move_rate=valid_move_rate,
            flag_precision=flag_precision,
            flag_recall=flag_recall,
            reasoning_score=reasoning_score,
            ms_i_score=ms_i_score,
            global_score=ms_i_score,  # For interactive-only evaluation
            average_moves_to_win=avg_moves_win,
            average_moves_to_loss=avg_moves_loss,
            confidence_intervals={
                "win_rate": win_ci,
                "valid_move_rate": vmr_ci
            },
            sample_sizes={
                "games": total_games,
                "moves": total_moves
            }
        )
        
        return metrics
    
    def calculate_global_score(
        self,
        ms_s_score: float,
        ms_i_score: float,
        ms_s_weight: float = 0.4,
        ms_i_weight: float = 0.6
    ) -> float:
        """
        Calculate global MineBench score.
        
        Uses weighted geometric mean.
        """
        # Normalize weights
        total_weight = ms_s_weight + ms_i_weight
        ms_s_weight /= total_weight
        ms_i_weight /= total_weight
        
        # Weighted geometric mean
        # G = (x1^w1 * x2^w2)^(1/(w1+w2))
        # Since weights sum to 1: G = x1^w1 * x2^w2
        
        # Handle zero scores
        if ms_s_score == 0 or ms_i_score == 0:
            return 0.0
        
        global_score = (ms_s_score ** ms_s_weight) * (ms_i_score ** ms_i_weight)
        
        return global_score
    
    def calculate_all_metrics(
        self,
        static_predictions: Optional[List[Dict[str, Any]]] = None,
        interactive_transcripts: Optional[List[GameTranscript]] = None,
        reasoning_judgments: Optional[Dict[str, Any]] = None
    ) -> AdvancedMetrics:
        """
        Calculate all metrics including composite scores.
        
        Args:
            static_predictions: Predictions for static tasks
            interactive_transcripts: Transcripts for interactive games
            reasoning_judgments: Reasoning quality judgments
        
        Returns:
            Complete AdvancedMetrics object
        """
        # Initialize with defaults
        ms_s_score = 0.0
        ms_i_score = 0.0
        
        # Calculate static metrics if available
        if static_predictions:
            static_judgments = reasoning_judgments.get("static", []) if reasoning_judgments else None
            static_metrics = self.calculate_static_metrics(
                static_predictions, static_judgments
            )
            ms_s_score = static_metrics.ms_s_score
        
        # Calculate interactive metrics if available
        if interactive_transcripts:
            interactive_judgments = reasoning_judgments.get("interactive", {}) if reasoning_judgments else None
            interactive_metrics = self.calculate_interactive_metrics(
                interactive_transcripts, interactive_judgments
            )
            ms_i_score = interactive_metrics.ms_i_score
        
        # Calculate global score if we have both
        if static_predictions and interactive_transcripts:
            global_score = self.calculate_global_score(ms_s_score, ms_i_score)
            
            # Merge metrics
            metrics = AdvancedMetrics(
                # Static metrics
                accuracy=static_metrics.accuracy,
                valid_output_rate=static_metrics.valid_output_rate,
                # Interactive metrics
                win_rate=interactive_metrics.win_rate,
                coverage=interactive_metrics.coverage,
                valid_move_rate=interactive_metrics.valid_move_rate,
                flag_precision=interactive_metrics.flag_precision,
                flag_recall=interactive_metrics.flag_recall,
                # Composite scores
                ms_s_score=ms_s_score,
                ms_i_score=ms_i_score,
                global_score=global_score,
                # Reasoning (averaged)
                reasoning_score=(
                    static_metrics.reasoning_score * 0.4 +
                    interactive_metrics.reasoning_score * 0.6
                ),
                # Additional
                average_moves_to_win=interactive_metrics.average_moves_to_win,
                average_moves_to_loss=interactive_metrics.average_moves_to_loss,
                # Statistical
                confidence_intervals={
                    **static_metrics.confidence_intervals,
                    **interactive_metrics.confidence_intervals
                },
                sample_sizes={
                    **static_metrics.sample_sizes,
                    **interactive_metrics.sample_sizes
                }
            )
            
            return metrics
        
        # Return whichever we have
        elif static_predictions:
            return static_metrics
        elif interactive_transcripts:
            return interactive_metrics
        else:
            return AdvancedMetrics()
    
    def test_significance(
        self,
        metrics1: AdvancedMetrics,
        metrics2: AdvancedMetrics,
        metric_name: str = "win_rate"
    ) -> SignificanceTestResult:
        """
        Test if a metric difference is statistically significant.
        
        Args:
            metrics1: First model's metrics
            metrics2: Second model's metrics
            metric_name: Metric to test
        
        Returns:
            SignificanceTestResult
        """
        # Map metric names to appropriate test types
        proportion_metrics = {
            "accuracy", "win_rate", "valid_output_rate", 
            "valid_move_rate", "flag_precision", "flag_recall"
        }
        
        if metric_name in proportion_metrics:
            # Get values and sample sizes
            value1 = getattr(metrics1, metric_name, 0)
            value2 = getattr(metrics2, metric_name, 0)
            
            # Determine sample size field
            if metric_name in ["accuracy", "valid_output_rate"]:
                n1 = metrics1.sample_sizes.get("predictions", 0)
                n2 = metrics2.sample_sizes.get("predictions", 0)
            elif metric_name in ["win_rate"]:
                n1 = metrics1.sample_sizes.get("games", 0)
                n2 = metrics2.sample_sizes.get("games", 0)
            else:
                n1 = metrics1.sample_sizes.get("moves", 0)
                n2 = metrics2.sample_sizes.get("moves", 0)
            
            # Convert to counts
            successes1 = int(value1 * n1)
            successes2 = int(value2 * n2)
            
            result = self.stat_analyzer.test_proportion_difference(
                successes1, n1, successes2, n2
            )
            result.metric_name = metric_name.replace("_", " ").title()
            
            return result
        
        else:
            raise ValueError(f"Significance testing not implemented for metric: {metric_name}")
    
    def create_leaderboard_entry(
        self,
        model_name: str,
        metrics: AdvancedMetrics,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a MineBench-compliant leaderboard entry.
        
        Args:
            model_name: Name of the model
            metrics: Calculated metrics
            metadata: Optional additional metadata
        
        Returns:
            Leaderboard entry dictionary
        """
        entry = {
            "model_id": model_name,
            "model_name": model_name,
            # Composite scores
            "ms_s_score": round(metrics.ms_s_score, 4),
            "ms_i_score": round(metrics.ms_i_score, 4),
            "global_score": round(metrics.global_score, 4),
            # Core metrics
            "accuracy": round(metrics.accuracy, 4),
            "win_rate": round(metrics.win_rate, 4),
            "coverage": round(metrics.coverage, 4),
            "valid_move_rate": round(metrics.valid_move_rate, 4),
            "flag_precision": round(metrics.flag_precision, 4),
            "flag_recall": round(metrics.flag_recall, 4),
            "reasoning_score": round(metrics.reasoning_score, 4),
            # Confidence intervals
            "confidence_intervals": {
                k: [round(v[0], 4), round(v[1], 4)]
                for k, v in metrics.confidence_intervals.items()
            },
            # Sample sizes
            "num_static_tasks": metrics.sample_sizes.get("predictions", 0),
            "num_games": metrics.sample_sizes.get("games", 0),
            # Timestamp
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add metadata if provided
        if metadata:
            entry["metadata"] = metadata
        
        return entry