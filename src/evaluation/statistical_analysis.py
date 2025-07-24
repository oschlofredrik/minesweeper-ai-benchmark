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