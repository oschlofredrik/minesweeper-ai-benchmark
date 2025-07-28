"""Prompt optimization and A/B testing functionality."""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import numpy as np
from scipy import stats

from src.core.types import ModelConfig, TaskType, Difficulty
from src.evaluation import EvaluationEngine
from src.tasks import TaskRepository
from .prompt_manager import PromptManager, PromptTemplate


@dataclass
class OptimizationRun:
    """Results from a single optimization run."""
    template_name: str
    metrics: Dict[str, float]
    num_samples: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)


@dataclass
class ABTestResult:
    """Results from an A/B test between two prompts."""
    template_a: str
    template_b: str
    metrics_a: Dict[str, float]
    metrics_b: Dict[str, float]
    p_values: Dict[str, float]
    winner: Optional[str] = None
    confidence_level: float = 0.95
    num_samples: int = 0


class PromptOptimizer:
    """Optimizes prompts through A/B testing and performance analysis."""
    
    def __init__(
        self,
        prompt_manager: PromptManager,
        results_dir: Optional[Path] = None,
    ):
        """
        Initialize prompt optimizer.
        
        Args:
            prompt_manager: Manager for prompt templates
            results_dir: Directory for storing optimization results
        """
        self.prompt_manager = prompt_manager
        self.results_dir = results_dir or Path("data/optimization_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.evaluation_engine = EvaluationEngine()
        self.task_repo = TaskRepository()
    
    async def optimize_prompt(
        self,
        base_template: str,
        model_config: ModelConfig,
        variations: List[Dict[str, Any]],
        num_games: int = 20,
        task_type: TaskType = TaskType.INTERACTIVE,
        difficulty: Difficulty = Difficulty.EXPERT,
    ) -> Dict[str, Any]:
        """
        Optimize a prompt by testing variations.
        
        Args:
            base_template: Name of base template
            model_config: Model configuration
            variations: List of variations to test
            num_games: Number of games per variation
            task_type: Type of tasks
            difficulty: Task difficulty
        
        Returns:
            Optimization results
        """
        # Load tasks for testing
        tasks = self.task_repo.load_tasks(
            task_type=task_type,
            difficulty=difficulty,
            limit=num_games,
        )
        
        if len(tasks) < num_games:
            raise ValueError(f"Not enough tasks available. Found {len(tasks)}, need {num_games}")
        
        # Test base template
        base_prompt = self.prompt_manager.get_template(base_template)
        if not base_prompt:
            raise ValueError(f"Base template '{base_template}' not found")
        
        results = {
            "base_template": base_template,
            "model": model_config.name,
            "num_games": num_games,
            "timestamp": datetime.utcnow().isoformat(),
            "runs": [],
        }
        
        # Evaluate base template
        print(f"Testing base template: {base_template}")
        base_results = await self._evaluate_template(
            template=base_prompt,
            model_config=model_config,
            tasks=tasks,
        )
        results["runs"].append(base_results)
        
        # Test each variation
        for i, variation_spec in enumerate(variations):
            variation_name = f"{base_template}_var_{i+1}"
            
            # Create variation
            variation = self.prompt_manager.create_variation(
                base_template=base_template,
                name=variation_name,
                modifications=variation_spec,
            )
            
            print(f"Testing variation {i+1}/{len(variations)}: {variation_name}")
            
            # Evaluate variation
            var_results = await self._evaluate_template(
                template=variation,
                model_config=model_config,
                tasks=tasks,
            )
            results["runs"].append(var_results)
        
        # Find best performing template
        best_run = max(
            results["runs"],
            key=lambda r: r.metrics.get("win_rate", 0)
        )
        results["best_template"] = best_run.template_name
        results["best_metrics"] = best_run.metrics
        
        # Save results
        self._save_results(results)
        
        return results
    
    async def ab_test(
        self,
        template_a: str,
        template_b: str,
        model_config: ModelConfig,
        num_games: int = 50,
        task_type: TaskType = TaskType.INTERACTIVE,
        difficulty: Difficulty = Difficulty.EXPERT,
        confidence_level: float = 0.95,
    ) -> ABTestResult:
        """
        Perform A/B test between two templates.
        
        Args:
            template_a: First template name
            template_b: Second template name
            model_config: Model configuration
            num_games: Number of games per template
            task_type: Type of tasks
            difficulty: Task difficulty
            confidence_level: Statistical confidence level
        
        Returns:
            A/B test results
        """
        # Load templates
        prompt_a = self.prompt_manager.get_template(template_a)
        prompt_b = self.prompt_manager.get_template(template_b)
        
        if not prompt_a or not prompt_b:
            raise ValueError("One or both templates not found")
        
        # Load tasks
        tasks = self.task_repo.load_tasks(
            task_type=task_type,
            difficulty=difficulty,
            limit=num_games * 2,  # Need enough for both
        )
        
        if len(tasks) < num_games * 2:
            raise ValueError(f"Not enough tasks. Found {len(tasks)}, need {num_games * 2}")
        
        # Split tasks
        tasks_a = tasks[:num_games]
        tasks_b = tasks[num_games:num_games * 2]
        
        # Run evaluations in parallel
        print(f"Running A/B test: {template_a} vs {template_b}")
        
        results_a, results_b = await asyncio.gather(
            self._evaluate_template(prompt_a, model_config, tasks_a),
            self._evaluate_template(prompt_b, model_config, tasks_b),
        )
        
        # Perform statistical tests
        p_values = {}
        
        # Test win rate difference
        if "game_outcomes" in results_a.__dict__ and "game_outcomes" in results_b.__dict__:
            wins_a = sum(1 for outcome in results_a.game_outcomes if outcome == "won")
            wins_b = sum(1 for outcome in results_b.game_outcomes if outcome == "won")
            
            # Two-proportion z-test
            p_values["win_rate"] = self._two_proportion_z_test(
                wins_a, num_games,
                wins_b, num_games,
            )
        
        # Determine winner
        winner = None
        if p_values.get("win_rate", 1.0) < (1 - confidence_level):
            # Statistically significant difference
            if results_a.metrics["win_rate"] > results_b.metrics["win_rate"]:
                winner = template_a
            else:
                winner = template_b
        
        return ABTestResult(
            template_a=template_a,
            template_b=template_b,
            metrics_a=results_a.metrics,
            metrics_b=results_b.metrics,
            p_values=p_values,
            winner=winner,
            confidence_level=confidence_level,
            num_samples=num_games,
        )
    
    async def grid_search(
        self,
        base_template: str,
        model_config: ModelConfig,
        parameter_grid: Dict[str, List[Any]],
        num_games: int = 10,
        task_type: TaskType = TaskType.INTERACTIVE,
        difficulty: Difficulty = Difficulty.EXPERT,
    ) -> Dict[str, Any]:
        """
        Perform grid search over template parameters.
        
        Args:
            base_template: Base template name
            model_config: Model configuration
            parameter_grid: Dict of parameter names to values to test
            num_games: Number of games per configuration
            task_type: Type of tasks
            difficulty: Task difficulty
        
        Returns:
            Grid search results
        """
        # Generate all parameter combinations
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        
        combinations = []
        for values in self._cartesian_product(*param_values):
            combo = dict(zip(param_names, values))
            combinations.append(combo)
        
        print(f"Testing {len(combinations)} parameter combinations")
        
        # Create variations for each combination
        variations = []
        for combo in combinations:
            variations.append({
                "parameters": combo,
                "description": f"Grid search: {combo}",
            })
        
        # Run optimization
        results = await self.optimize_prompt(
            base_template=base_template,
            model_config=model_config,
            variations=variations,
            num_games=num_games,
            task_type=task_type,
            difficulty=difficulty,
        )
        
        # Add grid search specific analysis
        results["grid_search"] = {
            "parameter_grid": parameter_grid,
            "best_parameters": combinations[
                results["runs"].index(
                    max(results["runs"], key=lambda r: r.metrics.get("win_rate", 0))
                ) - 1  # -1 because first run is base template
            ] if len(results["runs"]) > 1 else {},
        }
        
        return results
    
    async def _evaluate_template(
        self,
        template: PromptTemplate,
        model_config: ModelConfig,
        tasks: List[Any],
    ) -> OptimizationRun:
        """Evaluate a single template."""
        # Set prompt format to use our template
        eval_results = await self.evaluation_engine.evaluate_model(
            model_config=model_config,
            tasks=tasks,
            prompt_template=template,
            parallel_games=5,
            verbose=False,
        )
        
        # Extract metrics
        metrics = eval_results["metrics"]
        
        # Calculate confidence intervals
        confidence_intervals = {}
        if "game_outcomes" in eval_results:
            outcomes = eval_results["game_outcomes"]
            wins = sum(1 for o in outcomes if o == "won")
            n = len(outcomes)
            
            # Wilson confidence interval for win rate
            if n > 0:
                ci_low, ci_high = self._wilson_confidence_interval(wins, n)
                confidence_intervals["win_rate"] = (ci_low, ci_high)
        
        return OptimizationRun(
            template_name=template.name,
            metrics=metrics,
            num_samples=len(tasks),
            confidence_intervals=confidence_intervals,
        )
    
    def _two_proportion_z_test(
        self,
        successes_a: int,
        n_a: int,
        successes_b: int,
        n_b: int,
    ) -> float:
        """Perform two-proportion z-test."""
        p_a = successes_a / n_a if n_a > 0 else 0
        p_b = successes_b / n_b if n_b > 0 else 0
        
        # Pooled proportion
        p_pool = (successes_a + successes_b) / (n_a + n_b)
        
        # Standard error
        se = np.sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))
        
        if se == 0:
            return 1.0  # No difference
        
        # Z-score
        z = (p_a - p_b) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        return p_value
    
    def _wilson_confidence_interval(
        self,
        successes: int,
        n: int,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """Calculate Wilson confidence interval."""
        if n == 0:
            return (0, 0)
        
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        p_hat = successes / n
        
        denominator = 1 + z**2 / n
        centre = (p_hat + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denominator
        
        return (centre - margin, centre + margin)
    
    def _cartesian_product(self, *arrays):
        """Generate Cartesian product of input arrays."""
        la = len(arrays)
        dtype = np.result_type(*arrays)
        arr = np.empty([len(a) for a in arrays] + [la], dtype=dtype)
        
        for i, a in enumerate(np.ix_(*arrays)):
            arr[..., i] = a
        
        return arr.reshape(-1, la)
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save optimization results."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_{timestamp}.json"
        filepath = self.results_dir / filename
        
        # Convert OptimizationRun objects to dicts
        results_copy = results.copy()
        results_copy["runs"] = [
            {
                "template_name": run.template_name,
                "metrics": run.metrics,
                "num_samples": run.num_samples,
                "timestamp": run.timestamp.isoformat(),
                "confidence_intervals": run.confidence_intervals,
            }
            for run in results["runs"]
        ]
        
        with open(filepath, "w") as f:
            json.dump(results_copy, f, indent=2)