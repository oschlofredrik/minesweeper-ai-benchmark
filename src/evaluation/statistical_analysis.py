"""Statistical analysis utilities for evaluation metrics."""

import numpy as np
from typing import Dict, Tuple, List, Optional, Any
from scipy import stats
from statsmodels.stats.proportion import proportion_confint
from dataclasses import dataclass
import warnings

from src.core.logging_config import get_logger

logger = get_logger("evaluation.statistical_analysis")


@dataclass
class SignificanceTestResult:
    """Result of a statistical significance test."""
    metric_name: str
    sample1_value: float
    sample2_value: float
    p_value: float
    is_significant: bool
    confidence_level: float
    test_type: str
    sample1_size: int
    sample2_size: int
    confidence_interval_1: Tuple[float, float]
    confidence_interval_2: Tuple[float, float]
    effect_size: Optional[float] = None
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        sig_text = "IS" if self.is_significant else "IS NOT"
        return (
            f"{self.metric_name}: {self.sample1_value:.3f} vs {self.sample2_value:.3f} "
            f"{sig_text} significantly different (p={self.p_value:.4f}, α={1-self.confidence_level:.2f})"
        )


class StatisticalAnalyzer:
    """Performs statistical analysis on evaluation metrics."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize analyzer.
        
        Args:
            confidence_level: Confidence level for intervals and tests (default 0.95)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
    
    def calculate_confidence_interval(
        self,
        successes: int,
        trials: int,
        method: str = "wilson"
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for a proportion.
        
        Args:
            successes: Number of successes
            trials: Total number of trials
            method: Method to use ('wilson', 'normal', 'exact')
        
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if trials == 0:
            return (0.0, 0.0)
        
        # Use Wilson score interval by default (better for small samples)
        lower, upper = proportion_confint(
            count=successes,
            nobs=trials,
            alpha=self.alpha,
            method=method
        )
        
        return (float(lower), float(upper))
    
    def test_proportion_difference(
        self,
        successes1: int,
        trials1: int,
        successes2: int,
        trials2: int
    ) -> SignificanceTestResult:
        """
        Test if two proportions are significantly different.
        
        Args:
            successes1: Successes in sample 1
            trials1: Trials in sample 1
            successes2: Successes in sample 2
            trials2: Trials in sample 2
        
        Returns:
            SignificanceTestResult object
        """
        # Calculate proportions
        p1 = successes1 / trials1 if trials1 > 0 else 0
        p2 = successes2 / trials2 if trials2 > 0 else 0
        
        # Calculate confidence intervals
        ci1 = self.calculate_confidence_interval(successes1, trials1)
        ci2 = self.calculate_confidence_interval(successes2, trials2)
        
        # Two-proportion z-test
        if trials1 > 0 and trials2 > 0:
            # Pooled proportion
            p_pool = (successes1 + successes2) / (trials1 + trials2)
            
            # Standard error
            se = np.sqrt(p_pool * (1 - p_pool) * (1/trials1 + 1/trials2))
            
            # Z-statistic
            if se > 0:
                z = (p1 - p2) / se
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
            else:
                p_value = 1.0
        else:
            p_value = 1.0
        
        # Calculate effect size (Cohen's h)
        effect_size = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
        
        return SignificanceTestResult(
            metric_name="proportion",
            sample1_value=p1,
            sample2_value=p2,
            p_value=p_value,
            is_significant=p_value < self.alpha,
            confidence_level=self.confidence_level,
            test_type="two_proportion_z_test",
            sample1_size=trials1,
            sample2_size=trials2,
            confidence_interval_1=ci1,
            confidence_interval_2=ci2,
            effect_size=effect_size
        )
    
    def test_mean_difference(
        self,
        sample1: List[float],
        sample2: List[float],
        paired: bool = False
    ) -> SignificanceTestResult:
        """
        Test if two means are significantly different.
        
        Args:
            sample1: First sample values
            sample2: Second sample values
            paired: Whether samples are paired
        
        Returns:
            SignificanceTestResult object
        """
        # Convert to numpy arrays
        s1 = np.array(sample1)
        s2 = np.array(sample2)
        
        # Remove NaN values
        s1 = s1[~np.isnan(s1)]
        s2 = s2[~np.isnan(s2)]
        
        if len(s1) == 0 or len(s2) == 0:
            logger.warning("Empty sample(s) provided for mean comparison")
            return SignificanceTestResult(
                metric_name="mean",
                sample1_value=0,
                sample2_value=0,
                p_value=1.0,
                is_significant=False,
                confidence_level=self.confidence_level,
                test_type="t_test",
                sample1_size=0,
                sample2_size=0,
                confidence_interval_1=(0, 0),
                confidence_interval_2=(0, 0)
            )
        
        # Calculate means
        mean1 = np.mean(s1)
        mean2 = np.mean(s2)
        
        # Calculate confidence intervals (using t-distribution)
        def mean_confidence_interval(data):
            n = len(data)
            if n <= 1:
                return (float(data[0]) if n == 1 else 0, float(data[0]) if n == 1 else 0)
            
            mean = np.mean(data)
            se = stats.sem(data)
            interval = se * stats.t.ppf((1 + self.confidence_level) / 2, n - 1)
            return (mean - interval, mean + interval)
        
        ci1 = mean_confidence_interval(s1)
        ci2 = mean_confidence_interval(s2)
        
        # Perform appropriate t-test
        if paired and len(s1) == len(s2):
            statistic, p_value = stats.ttest_rel(s1, s2)
            test_type = "paired_t_test"
        else:
            # Welch's t-test (doesn't assume equal variances)
            statistic, p_value = stats.ttest_ind(s1, s2, equal_var=False)
            test_type = "welch_t_test"
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(s1, ddof=1) + np.var(s2, ddof=1)) / 2)
        effect_size = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        
        return SignificanceTestResult(
            metric_name="mean",
            sample1_value=float(mean1),
            sample2_value=float(mean2),
            p_value=float(p_value),
            is_significant=p_value < self.alpha,
            confidence_level=self.confidence_level,
            test_type=test_type,
            sample1_size=len(s1),
            sample2_size=len(s2),
            confidence_interval_1=ci1,
            confidence_interval_2=ci2,
            effect_size=float(effect_size)
        )
    
    def calculate_sample_size(
        self,
        effect_size: float,
        power: float = 0.8,
        test_type: str = "proportion"
    ) -> int:
        """
        Calculate required sample size for detecting an effect.
        
        Args:
            effect_size: Expected effect size
            power: Statistical power (default 0.8)
            test_type: Type of test ('proportion' or 'mean')
        
        Returns:
            Required sample size per group
        """
        from statsmodels.stats.power import zt_ind_solve_power, tt_ind_solve_power
        
        if test_type == "proportion":
            # For proportions
            n = zt_ind_solve_power(
                effect_size=effect_size,
                alpha=self.alpha,
                power=power,
                ratio=1.0
            )
        else:
            # For means
            n = tt_ind_solve_power(
                effect_size=effect_size,
                alpha=self.alpha,
                power=power,
                ratio=1.0
            )
        
        return int(np.ceil(n))
    
    def analyze_metrics_comparison(
        self,
        metrics1: Dict[str, Any],
        metrics2: Dict[str, Any],
        game_transcripts1: Optional[List[Any]] = None,
        game_transcripts2: Optional[List[Any]] = None
    ) -> Dict[str, SignificanceTestResult]:
        """
        Perform comprehensive statistical comparison of two models.
        
        Args:
            metrics1: Metrics for model 1
            metrics2: Metrics for model 2
            game_transcripts1: Optional game transcripts for model 1
            game_transcripts2: Optional game transcripts for model 2
        
        Returns:
            Dictionary mapping metric names to test results
        """
        results = {}
        
        # Win rate comparison (proportion test)
        if "win_rate" in metrics1 and "win_rate" in metrics2:
            if game_transcripts1 and game_transcripts2:
                wins1 = sum(1 for t in game_transcripts1 if t.final_state.status == "won")
                wins2 = sum(1 for t in game_transcripts2 if t.final_state.status == "won")
                
                results["win_rate"] = self.test_proportion_difference(
                    wins1, len(game_transcripts1),
                    wins2, len(game_transcripts2)
                )
                results["win_rate"].metric_name = "Win Rate"
        
        # Accuracy comparison (proportion test)
        if "accuracy" in metrics1 and "accuracy" in metrics2:
            # Assuming we have counts
            if "correct_predictions" in metrics1 and "total_predictions" in metrics1:
                results["accuracy"] = self.test_proportion_difference(
                    metrics1["correct_predictions"], metrics1["total_predictions"],
                    metrics2["correct_predictions"], metrics2["total_predictions"]
                )
                results["accuracy"].metric_name = "Accuracy"
        
        # Coverage comparison (mean test)
        if game_transcripts1 and game_transcripts2:
            coverage1 = [t.final_state.board_coverage for t in game_transcripts1]
            coverage2 = [t.final_state.board_coverage for t in game_transcripts2]
            
            if coverage1 and coverage2:
                results["coverage"] = self.test_mean_difference(coverage1, coverage2)
                results["coverage"].metric_name = "Board Coverage"
        
        # Valid move rate comparison
        if "valid_move_rate" in metrics1 and "valid_move_rate" in metrics2:
            if game_transcripts1 and game_transcripts2:
                valid_moves1 = sum(m.was_valid for t in game_transcripts1 for m in t.moves)
                total_moves1 = sum(len(t.moves) for t in game_transcripts1)
                valid_moves2 = sum(m.was_valid for t in game_transcripts2 for m in t.moves)
                total_moves2 = sum(len(t.moves) for t in game_transcripts2)
                
                if total_moves1 > 0 and total_moves2 > 0:
                    results["valid_move_rate"] = self.test_proportion_difference(
                        valid_moves1, total_moves1,
                        valid_moves2, total_moves2
                    )
                    results["valid_move_rate"].metric_name = "Valid Move Rate"
        
        return results
    
    def create_comparison_report(
        self,
        model1_name: str,
        model2_name: str,
        test_results: Dict[str, SignificanceTestResult]
    ) -> str:
        """
        Create a formatted comparison report.
        
        Args:
            model1_name: Name of first model
            model2_name: Name of second model
            test_results: Dictionary of test results
        
        Returns:
            Formatted report string
        """
        report = f"Statistical Comparison: {model1_name} vs {model2_name}\n"
        report += "=" * 60 + "\n\n"
        
        # Summary
        significant_count = sum(1 for r in test_results.values() if r.is_significant)
        report += f"Summary: {significant_count}/{len(test_results)} metrics show significant differences\n"
        report += f"Confidence Level: {self.confidence_level * 100:.0f}%\n\n"
        
        # Detailed results
        for metric, result in test_results.items():
            report += f"{result.metric_name}:\n"
            report += f"  {model1_name}: {result.sample1_value:.3f} "
            report += f"[{result.confidence_interval_1[0]:.3f}, {result.confidence_interval_1[1]:.3f}]\n"
            report += f"  {model2_name}: {result.sample2_value:.3f} "
            report += f"[{result.confidence_interval_2[0]:.3f}, {result.confidence_interval_2[1]:.3f}]\n"
            report += f"  p-value: {result.p_value:.4f}"
            
            if result.is_significant:
                report += " ✓ SIGNIFICANT"
                if result.effect_size is not None:
                    report += f" (effect size: {result.effect_size:.3f})"
            
            report += "\n\n"
        
        # Interpretation
        report += "Interpretation:\n"
        for metric, result in test_results.items():
            if result.is_significant:
                better_model = model1_name if result.sample1_value > result.sample2_value else model2_name
                report += f"- {better_model} performs significantly better on {result.metric_name}\n"
        
        return report


# Convenience functions
def quick_significance_test(
    metric_name: str,
    value1: float,
    count1: int,
    value2: float,
    count2: int,
    metric_type: str = "proportion"
) -> bool:
    """
    Quick significance test for a single metric.
    
    Returns True if significantly different at 95% confidence.
    """
    analyzer = StatisticalAnalyzer()
    
    if metric_type == "proportion":
        successes1 = int(value1 * count1)
        successes2 = int(value2 * count2)
        result = analyzer.test_proportion_difference(
            successes1, count1, successes2, count2
        )
    else:
        # For means, we need the actual samples
        # This is a simplified version
        logger.warning("Quick test for means requires actual samples")
        return False
    
    return result.is_significant


def calculate_wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score confidence interval."""
    analyzer = StatisticalAnalyzer(confidence_level=confidence)
    return analyzer.calculate_confidence_interval(successes, trials, method="wilson")