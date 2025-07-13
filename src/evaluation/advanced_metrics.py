"""Advanced metrics with composite scores and statistical testing."""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from scipy import stats
from datetime import datetime

from src.core.types import GameTranscript, TaskType
from .metrics import MetricsCalculator
from .judge import JudgmentResult


@dataclass
class AdvancedMetrics:
    """Advanced evaluation metrics with composite scores."""
    # Basic metrics
    accuracy: float = 0.0
    win_rate: float = 0.0
    coverage: float = 0.0
    valid_move_rate: float = 0.0
    valid_output_rate: float = 0.0
    flag_precision: float = 0.0
    flag_recall: float = 0.0
    avg_moves_to_win: Optional[float] = None
    reasoning_score: float = 0.0
    
    # Composite scores
    ms_s_score: float = 0.0  # Static task score
    ms_i_score: float = 0.0  # Interactive task score
    global_score: float = 0.0  # Global MineBench Score
    
    # Additional metrics
    latency_mean_ms: float = 0.0
    latency_p95_ms: float = 0.0
    
    # Statistical info
    num_tasks: int = 0
    confidence_interval: Optional[Tuple[float, float]] = None


class AdvancedMetricsCalculator:
    """Calculate advanced metrics including composite scores."""
    
    def __init__(self):
        self.base_calculator = MetricsCalculator()
    
    def calculate_advanced_metrics(
        self,
        transcripts: List[GameTranscript],
        judgments: Dict[str, List[JudgmentResult]],
        task_type: TaskType,
        latencies: Optional[List[float]] = None,
    ) -> AdvancedMetrics:
        """
        Calculate advanced metrics including composite scores.
        
        Args:
            transcripts: Game transcripts
            judgments: Reasoning judgments by task_uid
            task_type: Type of tasks (static or interactive)
            latencies: Response latencies in milliseconds
        
        Returns:
            Advanced metrics with composite scores
        """
        if not transcripts:
            return AdvancedMetrics()
        
        # Calculate base metrics
        base_metrics = self.base_calculator.calculate_metrics(transcripts)
        
        # Calculate reasoning score from judgments
        reasoning_score = self._calculate_reasoning_score(judgments)
        
        # Calculate valid output rate (successfully parsed actions)
        valid_output_rate = self._calculate_valid_output_rate(transcripts)
        
        # Calculate latency metrics
        latency_mean = 0.0
        latency_p95 = 0.0
        if latencies:
            latency_mean = np.mean(latencies)
            latency_p95 = np.percentile(latencies, 95)
        
        # Build advanced metrics
        metrics = AdvancedMetrics(
            accuracy=base_metrics.win_rate if task_type == TaskType.STATIC else 0.0,
            win_rate=base_metrics.win_rate,
            coverage=base_metrics.board_coverage_on_loss,
            valid_move_rate=base_metrics.valid_move_rate,
            valid_output_rate=valid_output_rate,
            flag_precision=base_metrics.mine_identification_precision,
            flag_recall=base_metrics.mine_identification_recall,
            avg_moves_to_win=base_metrics.average_moves_to_win,
            reasoning_score=reasoning_score,
            latency_mean_ms=latency_mean,
            latency_p95_ms=latency_p95,
            num_tasks=len(transcripts),
        )
        
        # Calculate composite scores
        if task_type == TaskType.STATIC:
            metrics.ms_s_score = self._calculate_ms_s_score(metrics)
        else:
            metrics.ms_i_score = self._calculate_ms_i_score(metrics)
        
        # Calculate confidence interval for main metric
        if task_type == TaskType.STATIC:
            metrics.confidence_interval = self._calculate_confidence_interval(
                metrics.accuracy, metrics.num_tasks
            )
        else:
            metrics.confidence_interval = self._calculate_confidence_interval(
                metrics.win_rate, metrics.num_tasks
            )
        
        return metrics
    
    def calculate_global_score(
        self,
        static_metrics: Optional[AdvancedMetrics] = None,
        interactive_metrics: Optional[AdvancedMetrics] = None,
        weights: Dict[str, float] = None,
    ) -> float:
        """
        Calculate Global MineBench Score (GMS).
        
        Args:
            static_metrics: Metrics for static tasks
            interactive_metrics: Metrics for interactive tasks
            weights: Category weights (default: MS-S 40%, MS-I 60%)
        
        Returns:
            Global score (geometric mean)
        """
        if weights is None:
            weights = {"ms_s": 0.4, "ms_i": 0.6}
        
        scores = []
        total_weight = 0.0
        
        if static_metrics and static_metrics.num_tasks > 0:
            scores.append(static_metrics.ms_s_score ** weights["ms_s"])
            total_weight += weights["ms_s"]
        
        if interactive_metrics and interactive_metrics.num_tasks > 0:
            scores.append(interactive_metrics.ms_i_score ** weights["ms_i"])
            total_weight += weights["ms_i"]
        
        if not scores:
            return 0.0
        
        # Geometric mean (product of weighted scores)
        global_score = 1.0
        for score in scores:
            global_score *= score
        
        # Normalize by total weight
        if total_weight > 0:
            global_score = global_score ** (1.0 / total_weight)
        
        return global_score
    
    def _calculate_ms_s_score(self, metrics: AdvancedMetrics) -> float:
        """Calculate composite score for static tasks."""
        return (
            metrics.accuracy * 0.7 +
            metrics.valid_output_rate * 0.1 +
            metrics.reasoning_score * 0.2
        )
    
    def _calculate_ms_i_score(self, metrics: AdvancedMetrics) -> float:
        """Calculate composite score for interactive tasks."""
        flag_score = (metrics.flag_precision + metrics.flag_recall) / 2
        
        return (
            metrics.win_rate * 0.5 +
            metrics.coverage * 0.2 +
            metrics.valid_move_rate * 0.1 +
            flag_score * 0.1 +
            metrics.reasoning_score * 0.1
        )
    
    def _calculate_reasoning_score(
        self, judgments: Dict[str, List[JudgmentResult]]
    ) -> float:
        """Calculate average reasoning score from judgments."""
        all_scores = []
        
        for task_judgments in judgments.values():
            for judgment in task_judgments:
                all_scores.append(judgment.score)
        
        return np.mean(all_scores) if all_scores else 0.0
    
    def _calculate_valid_output_rate(
        self, transcripts: List[GameTranscript]
    ) -> float:
        """Calculate rate of successfully parsed outputs."""
        total_outputs = 0
        valid_outputs = 0
        
        for transcript in transcripts:
            for move in transcript.moves:
                total_outputs += 1
                if move.was_valid and move.action is not None:
                    valid_outputs += 1
        
        return valid_outputs / total_outputs if total_outputs > 0 else 0.0
    
    def _calculate_confidence_interval(
        self, proportion: float, n: int, confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for a proportion."""
        if n == 0:
            return (0.0, 0.0)
        
        # Wilson score interval
        z = stats.norm.ppf((1 + confidence) / 2)
        denominator = 1 + z**2 / n
        centre = (proportion + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt(proportion * (1 - proportion) / n + z**2 / (4 * n**2)) / denominator
        
        return (
            max(0, centre - margin),
            min(1, centre + margin)
        )
    
    def test_significance(
        self,
        metrics1: AdvancedMetrics,
        metrics2: AdvancedMetrics,
        metric_name: str = "win_rate",
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Test statistical significance between two models.
        
        Args:
            metrics1: First model's metrics
            metrics2: Second model's metrics
            metric_name: Metric to test
            alpha: Significance level
        
        Returns:
            Test results including p-value and significance
        """
        # Get metric values
        value1 = getattr(metrics1, metric_name, 0.0)
        value2 = getattr(metrics2, metric_name, 0.0)
        n1 = metrics1.num_tasks
        n2 = metrics2.num_tasks
        
        if n1 == 0 or n2 == 0:
            return {
                "significant": False,
                "p_value": 1.0,
                "test": "none",
                "message": "Insufficient data"
            }
        
        # Two-proportion z-test for proportions
        if metric_name in ["win_rate", "accuracy", "valid_move_rate"]:
            # Pooled proportion
            p_pooled = (value1 * n1 + value2 * n2) / (n1 + n2)
            
            # Standard error
            se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
            
            if se == 0:
                return {
                    "significant": False,
                    "p_value": 1.0,
                    "test": "two-proportion-z",
                    "message": "No variance"
                }
            
            # Z-score
            z = (value1 - value2) / se
            
            # Two-tailed p-value
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))
            
            return {
                "significant": p_value < alpha,
                "p_value": p_value,
                "test": "two-proportion-z",
                "difference": value1 - value2,
                "relative_improvement": (value1 - value2) / value2 if value2 > 0 else 0,
                "message": f"{'Significant' if p_value < alpha else 'Not significant'} at α={alpha}"
            }
        
        # For other metrics, use t-test (would need raw data)
        return {
            "significant": False,
            "p_value": None,
            "test": "not-implemented",
            "message": f"Statistical test not implemented for {metric_name}"
        }


def generate_task_uid(task_type: TaskType, task_id: str) -> str:
    """
    Generate task UID in format <code>-<hash6>.
    
    Args:
        task_type: Type of task
        task_id: Original task ID
    
    Returns:
        Task UID like "MS-S-3fa2bc"
    """
    import hashlib
    
    # Task type codes
    type_codes = {
        TaskType.STATIC: "MS-S",
        TaskType.INTERACTIVE: "MS-I",
    }
    
    code = type_codes.get(task_type, "UNK")
    hash6 = hashlib.sha256(task_id.encode()).hexdigest()[:6]
    
    return f"{code}-{hash6}"