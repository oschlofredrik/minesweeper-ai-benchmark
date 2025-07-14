#!/usr/bin/env python3
"""Test script for advanced evaluation features."""

import asyncio
import os
from pathlib import Path

from src.core.types import ModelConfig, TaskType, Difficulty
from src.evaluation import EvaluationEngine
from src.tasks import TaskGenerator, TaskRepository
from src.evaluation.advanced_metrics import AdvancedMetricsCalculator
from src.evaluation.reasoning_judge import ReasoningJudge


async def test_advanced_evaluation():
    """Test the advanced evaluation features."""
    print("Testing Advanced Evaluation Features")
    print("=" * 50)
    
    # 1. Generate test tasks
    print("\n1. Generating test tasks...")
    generator = TaskGenerator()
    tasks = []
    
    # Generate a few interactive tasks
    for i in range(5):
        task = generator.generate_interactive_task(difficulty=Difficulty.INTERMEDIATE)
        tasks.append(task)
    
    print(f"   Generated {len(tasks)} interactive tasks")
    
    # 2. Create model configuration
    print("\n2. Setting up model configuration...")
    model_config = ModelConfig(
        name="gpt-3.5-turbo",
        provider="openai",
        model_id="gpt-3.5-turbo",
        temperature=0.0,
        max_tokens=1000,
        additional_params={}
    )
    
    # 3. Run evaluation with advanced features
    print("\n3. Running evaluation with advanced metrics...")
    engine = EvaluationEngine()
    
    results = await engine.evaluate_model(
        model_config=model_config,
        tasks=tasks,
        max_moves=100,
        use_reasoning_judge=True,  # Enable reasoning judge
        calculate_advanced_metrics=True,  # Enable advanced metrics
        verbose=True
    )
    
    # 4. Display results
    print("\n4. Evaluation Results:")
    print("-" * 30)
    
    # Basic metrics
    metrics = results["metrics"]
    print(f"Win Rate: {metrics['win_rate']:.1%}")
    print(f"Valid Move Rate: {metrics['valid_move_rate']:.1%}")
    print(f"Board Coverage: {metrics['board_coverage_on_loss']:.1%}")
    
    # Advanced metrics
    if "advanced_metrics" in results:
        adv = results["advanced_metrics"]
        print(f"\nAdvanced Metrics:")
        print(f"MS-I Score: {adv['ms_i_score']:.3f}")
        print(f"Reasoning Score: {adv['reasoning_score']:.3f}")
        print(f"Win Rate CI (95%): [{adv['win_rate_ci'][0]:.1%}, {adv['win_rate_ci'][1]:.1%}]")
    
    # 5. Test statistical significance (simulated)
    print("\n5. Testing Statistical Significance...")
    
    # Create fake second model results for comparison
    from src.evaluation.advanced_metrics import AdvancedMetrics
    from src.evaluation.statistical_analysis import StatisticalAnalyzer
    
    metrics1 = AdvancedMetrics(
        win_rate=0.4,
        valid_move_rate=0.95,
        sample_sizes={"games": 50, "moves": 1000}
    )
    
    metrics2 = AdvancedMetrics(
        win_rate=0.6,
        valid_move_rate=0.98,
        sample_sizes={"games": 50, "moves": 1200}
    )
    
    calculator = AdvancedMetricsCalculator()
    sig_result = calculator.test_significance(metrics1, metrics2, "win_rate")
    
    print(f"Comparing win rates: {metrics1.win_rate:.1%} vs {metrics2.win_rate:.1%}")
    print(f"p-value: {sig_result.p_value:.4f}")
    print(f"Is significant: {sig_result.is_significant}")
    print(f"Effect size: {sig_result.effect_size:.3f}")
    
    # 6. Test reasoning judge (standalone)
    print("\n6. Testing Reasoning Judge...")
    
    judge = ReasoningJudge()
    
    # Example board state and reasoning
    board_state = """
       0  1  2  3  4
    0| ?  ?  ?  ?  ?
    1| ?  1  1  ?  ?
    2| ?  1  .  1  ?
    3| ?  ?  1  1  ?
    4| ?  ?  ?  ?  ?
    """
    
    action = "reveal (0, 0)"
    reasoning = "The cell at (1,1) shows 1, and there's already a revealed 1 at (1,2). Since (0,0) is diagonal to (1,1) and there are other hidden cells adjacent to (1,1), it's likely safe to reveal (0,0)."
    
    judgment = await judge.judge_reasoning(
        task_uid="test-001",
        board_state=board_state,
        action=action,
        reasoning=reasoning
    )
    
    print(f"Reasoning Score: {judgment.normalized_score:.1f}/1.0")
    print(f"Confidence: {judgment.confidence}")
    print(f"Feedback: {judgment.feedback}")
    
    print("\n✅ Advanced evaluation test completed!")


async def test_model_comparison():
    """Test model comparison with significance testing."""
    print("\n\nTesting Model Comparison with Significance")
    print("=" * 50)
    
    # Generate tasks
    generator = TaskGenerator()
    tasks = [generator.generate_interactive_task() for _ in range(10)]
    
    # Create two model configs
    model1 = ModelConfig(
        name="gpt-3.5-turbo",
        provider="openai",
        model_id="gpt-3.5-turbo",
        temperature=0.0
    )
    
    model2 = ModelConfig(
        name="gpt-4",
        provider="openai",
        model_id="gpt-4",
        temperature=0.0
    )
    
    # Run comparison
    engine = EvaluationEngine()
    
    print("\nRunning model comparison...")
    comparison = await engine.compare_models_with_significance(
        model_configs=[model1, model2],
        tasks=tasks,
        verbose=False
    )
    
    # Display results
    print("\nComparison Results:")
    print("-" * 30)
    
    for comp_key, comp_data in comparison["comparisons"].items():
        print(f"\n{comp_key}:")
        for metric, test in comp_data["significance_tests"].items():
            print(f"  {metric}:")
            print(f"    Values: {test['values'][0]:.3f} vs {test['values'][1]:.3f}")
            print(f"    p-value: {test['p_value']:.4f}")
            print(f"    Significant: {'Yes' if test['is_significant'] else 'No'}")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    # Run tests
    asyncio.run(test_advanced_evaluation())
    
    # Optionally run comparison test
    # asyncio.run(test_model_comparison())