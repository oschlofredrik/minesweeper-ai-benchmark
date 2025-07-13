"""Plugin interface for custom evaluation metrics."""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.core.types import GameResult, Action
from .base import Plugin, PluginType, PluginMetadata


@dataclass
class MetricResult:
    """Result from a metric calculation."""
    name: str
    value: float
    description: str
    metadata: Optional[Dict[str, Any]] = None


class MetricPlugin(Plugin):
    """Base class for custom metric plugins."""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Default metadata for metric plugins."""
        return PluginMetadata(
            name="custom_metric",
            version="1.0.0",
            description="Custom evaluation metric",
            author="Unknown",
            plugin_type=PluginType.METRIC,
        )
    
    @abstractmethod
    def calculate(
        self,
        game_results: List[GameResult],
        **kwargs
    ) -> List[MetricResult]:
        """
        Calculate metrics from game results.
        
        Args:
            game_results: List of completed game results
            **kwargs: Additional parameters
        
        Returns:
            List of calculated metrics
        """
        pass
    
    @abstractmethod
    def calculate_single_game(
        self,
        game_result: GameResult,
        **kwargs
    ) -> List[MetricResult]:
        """
        Calculate metrics for a single game.
        
        Args:
            game_result: Single game result
            **kwargs: Additional parameters
        
        Returns:
            List of metrics for this game
        """
        pass
    
    async def initialize(self) -> None:
        """Initialize the metric plugin."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup metric resources."""
        self._initialized = False
    
    def aggregate_metrics(
        self,
        metrics_list: List[List[MetricResult]]
    ) -> List[MetricResult]:
        """
        Aggregate metrics across multiple games.
        
        Args:
            metrics_list: List of metric results per game
        
        Returns:
            Aggregated metrics
        """
        # Default aggregation - can be overridden
        aggregated = {}
        
        for game_metrics in metrics_list:
            for metric in game_metrics:
                if metric.name not in aggregated:
                    aggregated[metric.name] = []
                aggregated[metric.name].append(metric.value)
        
        results = []
        for name, values in aggregated.items():
            avg_value = sum(values) / len(values) if values else 0
            results.append(MetricResult(
                name=f"avg_{name}",
                value=avg_value,
                description=f"Average {name} across games",
            ))
        
        return results


class EfficiencyMetricPlugin(MetricPlugin):
    """Example plugin that measures gameplay efficiency."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="efficiency_metrics",
            version="1.0.0",
            description="Measures gameplay efficiency and optimal play",
            author="Example Author",
            plugin_type=PluginType.METRIC,
        )
    
    def calculate(
        self,
        game_results: List[GameResult],
        **kwargs
    ) -> List[MetricResult]:
        """Calculate efficiency metrics across all games."""
        all_metrics = []
        
        for game_result in game_results:
            game_metrics = self.calculate_single_game(game_result)
            all_metrics.append(game_metrics)
        
        # Aggregate and add summary metrics
        aggregated = self.aggregate_metrics(all_metrics)
        
        # Add custom aggregated metrics
        total_games = len(game_results)
        perfect_games = sum(
            1 for metrics in all_metrics
            for m in metrics
            if m.name == "move_efficiency" and m.value == 1.0
        )
        
        aggregated.append(MetricResult(
            name="perfect_game_rate",
            value=perfect_games / total_games if total_games > 0 else 0,
            description="Percentage of games played with perfect efficiency",
        ))
        
        return aggregated
    
    def calculate_single_game(
        self,
        game_result: GameResult,
        **kwargs
    ) -> List[MetricResult]:
        """Calculate efficiency metrics for a single game."""
        metrics = []
        
        # Move efficiency: ratio of necessary moves to total moves
        if hasattr(game_result, 'moves') and hasattr(game_result, 'optimal_moves'):
            move_efficiency = (
                game_result.optimal_moves / len(game_result.moves)
                if game_result.moves else 0
            )
            metrics.append(MetricResult(
                name="move_efficiency",
                value=move_efficiency,
                description="Ratio of optimal moves to actual moves",
            ))
        
        # Flag efficiency: correct flags / total flags
        if hasattr(game_result, 'flags_placed') and hasattr(game_result, 'correct_flags'):
            flag_efficiency = (
                game_result.correct_flags / game_result.flags_placed
                if game_result.flags_placed > 0 else 1.0
            )
            metrics.append(MetricResult(
                name="flag_efficiency",
                value=flag_efficiency,
                description="Ratio of correct flags to total flags placed",
            ))
        
        # Time efficiency (if time data available)
        if hasattr(game_result, 'duration_seconds') and hasattr(game_result, 'expected_duration'):
            time_efficiency = (
                game_result.expected_duration / game_result.duration_seconds
                if game_result.duration_seconds > 0 else 0
            )
            metrics.append(MetricResult(
                name="time_efficiency",
                value=min(time_efficiency, 1.0),  # Cap at 1.0
                description="Time efficiency compared to expected duration",
            ))
        
        return metrics


class SafetyMetricPlugin(MetricPlugin):
    """Plugin that measures how safely the model plays."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="safety_metrics",
            version="1.0.0",
            description="Measures risk-taking and safety in gameplay",
            author="Example Author",
            plugin_type=PluginType.METRIC,
        )
    
    def calculate(
        self,
        game_results: List[GameResult],
        **kwargs
    ) -> List[MetricResult]:
        """Calculate safety metrics."""
        all_metrics = []
        
        for game_result in game_results:
            game_metrics = self.calculate_single_game(game_result)
            all_metrics.append(game_metrics)
        
        return self.aggregate_metrics(all_metrics)
    
    def calculate_single_game(
        self,
        game_result: GameResult,
        **kwargs
    ) -> List[MetricResult]:
        """Calculate safety metrics for a single game."""
        metrics = []
        
        # Risk score: number of risky moves / total moves
        if hasattr(game_result, 'risky_moves') and hasattr(game_result, 'moves'):
            risk_score = (
                len(game_result.risky_moves) / len(game_result.moves)
                if game_result.moves else 0
            )
            metrics.append(MetricResult(
                name="risk_score",
                value=risk_score,
                description="Proportion of risky moves taken",
            ))
        
        # Safety score: inverse of risk score
        metrics.append(MetricResult(
            name="safety_score",
            value=1.0 - risk_score if 'risk_score' in locals() else 1.0,
            description="How safely the model played (1.0 = very safe)",
        ))
        
        return metrics