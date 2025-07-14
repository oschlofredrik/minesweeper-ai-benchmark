# Minesweeper AI Benchmark Evaluation Guide

## Overview

The Minesweeper AI Benchmark implements a comprehensive evaluation framework based on the MineBench specification, incorporating modern AI evaluation best practices from 2025. This guide covers the evaluation methodology, metrics, and practical implementation details.

## Table of Contents

1. [Evaluation Philosophy](#evaluation-philosophy)
2. [Task Taxonomy](#task-taxonomy)
3. [Evaluation Metrics](#evaluation-metrics)
4. [Evaluation Pipeline](#evaluation-pipeline)
5. [Statistical Analysis](#statistical-analysis)
6. [Best Practices](#best-practices)
7. [Implementation Guide](#implementation-guide)

## Evaluation Philosophy

Our evaluation framework follows these core principles:

1. **Multi-dimensional Assessment**: Models are evaluated across multiple dimensions including accuracy, reasoning quality, efficiency, and robustness
2. **Reproducibility**: All evaluations use deterministic seeds and versioned specifications
3. **Statistical Rigor**: Results include confidence intervals and significance testing
4. **Human Alignment**: LLM judges are calibrated against human preferences
5. **Continuous Improvement**: Regular audits and metric updates based on findings

## Task Taxonomy

### MS-S (Minesweeper Static)
- **Type**: Single-turn prediction tasks
- **Goal**: Identify safe cells or certain mines on partially revealed boards
- **Evaluation**: Accuracy, valid output rate, reasoning quality
- **Use Case**: Testing logical deduction capabilities

### MS-I (Minesweeper Interactive)
- **Type**: Multi-turn full game episodes
- **Goal**: Play complete games to win/loss
- **Evaluation**: Win rate, coverage, move validity, flag precision/recall
- **Use Case**: Testing strategic planning and adaptation

### Task Identification
Each task has a unique identifier: `<category>-<hash6>` (e.g., `MS-S-3fa2bc`)

## Evaluation Metrics

### Static Task Metrics (MS-S)

| Metric | Symbol | Calculation | Weight |
|--------|--------|-------------|--------|
| Accuracy | ACC | `correct_predictions / total_items` | 0.7 |
| Valid Output Rate | VOR | `parsable_responses / total_items` | 0.1 |
| Reasoning Score | RS | Average judge rating (0-1) | 0.2 |

**Composite Score**: `MS-S Score = ACC × 0.7 + VOR × 0.1 + RS × 0.2`

### Interactive Task Metrics (MS-I)

| Metric | Symbol | Description | Weight |
|--------|--------|-------------|--------|
| Win Rate | WR | Games won / total games | 0.5 |
| Coverage | COV | Mean % safe cells revealed | 0.2 |
| Valid Move Rate | VMR | Legal moves / total moves | 0.1 |
| Flag Metrics | FP+FR | (Precision + Recall) / 2 | 0.1 |
| Reasoning Score | RS | Mean step-level scores | 0.1 |

**Composite Score**: `MS-I Score = WR × 0.5 + COV × 0.2 + VMR × 0.1 + FLAG × 0.1 + RS × 0.1`

### Global Score
`Global MineBench Score (GMS) = (MS-S^0.4 × MS-I^0.6)^(1/1.0)`

## Evaluation Pipeline

### 1. Data Preparation
```python
# Load tasks with appropriate split
from src.tasks import TaskRepository, DataSplitManager

repo = TaskRepository()
split_manager = DataSplitManager()

# Get public split for development
public_tasks = split_manager.get_public_tasks()

# Get hidden split for blind evaluation
hidden_tasks = split_manager.get_hidden_tasks(mask_solutions=True)
```

### 2. Model Evaluation
```python
from src.evaluation import EvaluationEngine

engine = EvaluationEngine()
results = await engine.evaluate_model(
    model_config=model_config,
    tasks=public_tasks,
    use_reasoning_judge=True,
    save_episodes=True
)
```

### 3. Metrics Calculation
```python
from src.evaluation.advanced_metrics import AdvancedMetricsCalculator

calculator = AdvancedMetricsCalculator()
metrics = calculator.calculate_all_metrics(
    transcripts=results['transcripts'],
    judgments=results['judgments']
)
```

### 4. Statistical Analysis
```python
# Compare two models with significance testing
significance = calculator.test_significance(
    metrics1=model1_metrics,
    metrics2=model2_metrics,
    metric='win_rate',
    alpha=0.05
)
```

## Statistical Analysis

### Confidence Intervals
- Win rates and accuracy: Wilson score intervals
- Coverage and other continuous metrics: Bootstrap confidence intervals
- Default confidence level: 95%

### Significance Testing
- Binary metrics (ACC, WR): Two-proportion z-test
- Continuous metrics: Welch's t-test
- Reasoning scores: Paired t-test (matched tasks)
- Significance threshold: α = 0.05

### Sample Size Requirements
- Minimum 30 games for reliable win rate estimates
- 100+ games recommended for narrow confidence intervals
- 1000+ static tasks for robust accuracy measurements

## Best Practices

### 1. Evaluation Design
- **Diverse Test Sets**: Include edge cases, adversarial examples
- **Balanced Difficulty**: Mix beginner/intermediate/expert boards
- **Version Control**: Track task sets and evaluation specs

### 2. Model Testing
- **Warm-up Runs**: Exclude first few calls to avoid cold start effects
- **Rate Limiting**: Respect API limits, implement exponential backoff
- **Error Handling**: Gracefully handle timeouts and API errors

### 3. Result Interpretation
- **Look Beyond Averages**: Examine distribution of performance
- **Consider Trade-offs**: Balance accuracy vs efficiency vs cost
- **Track Trends**: Monitor performance over time/versions

### 4. Reasoning Evaluation
- **Calibrate Judges**: Periodically validate against human ratings
- **Diverse Prompts**: Test multiple prompt formats
- **Chain-of-Thought**: Evaluate intermediate reasoning steps

## Implementation Guide

### Running Basic Evaluation
```bash
# Evaluate a model on public tasks
python -m src.cli.main evaluate \
    --model gpt-4 \
    --num-games 100 \
    --use-reasoning-judge

# Run on hidden split (no solutions shown)
python -m src.cli.main evaluate \
    --model gpt-4 \
    --split hidden \
    --no-solutions
```

### Advanced Evaluation Options
```bash
# Compare multiple models with statistical testing
python -m src.cli.main compare \
    --models gpt-4 claude-3-opus \
    --num-games 200 \
    --test-significance \
    --confidence-level 0.95

# Evaluate with custom prompts
python -m src.cli.main evaluate \
    --model gpt-4 \
    --prompt-file prompts/cot_enhanced.json \
    --num-games 100
```

### Batch Evaluation Script
```python
# evaluate_batch.py
import asyncio
from src.evaluation import BatchEvaluator

async def evaluate_all_models():
    models = [
        "gpt-4", "gpt-3.5-turbo",
        "claude-3-opus", "claude-3-sonnet"
    ]
    
    evaluator = BatchEvaluator()
    results = await evaluator.evaluate_models(
        models=models,
        tasks_per_model=100,
        parallel_limit=2
    )
    
    # Generate comparison report
    evaluator.generate_report(
        results,
        output_file="evaluation_report.html"
    )

asyncio.run(evaluate_all_models())
```

### Custom Metrics
```python
from src.evaluation.metrics import BaseMetric

class EfficiencyMetric(BaseMetric):
    """Custom metric for move efficiency."""
    
    def calculate(self, transcript):
        optimal_moves = self._calculate_optimal_path(transcript)
        actual_moves = len(transcript.moves)
        return optimal_moves / actual_moves if actual_moves > 0 else 0

# Register custom metric
from src.evaluation import MetricRegistry
MetricRegistry.register('efficiency', EfficiencyMetric)
```

## Output Formats

### Per-Item Results (JSON)
```json
{
  "task_uid": "MS-S-3fa2bc",
  "model_id": "gpt-4",
  "prompt_variant": "cot_v2",
  "prediction": "Reveal B3",
  "rationale": "Cell B3 must be safe because...",
  "is_correct": true,
  "reasoning_score": 0.9,
  "latency_ms": 1234,
  "tokens_used": 256
}
```

### Episode Log (JSONL)
```jsonl
{"turn":1,"board":"...","action":"Reveal D5","rationale":"Starting with center...","latency_ms":1050}
{"turn":2,"board":"...","action":"Flag B2","rationale":"B2 must be mine...","latency_ms":980}
```

### Leaderboard Entry
```json
{
  "model_id": "gpt-4",
  "ms_s_score": 0.89,
  "ms_i_score": 0.76,
  "global_score": 0.81,
  "confidence_intervals": {
    "win_rate": [0.72, 0.80],
    "accuracy": [0.86, 0.91]
  },
  "evaluated_at": "2025-01-13T10:30:00Z",
  "num_tasks": 1000
}
```

## Performance Benchmarks

### Expected Evaluation Times

| Setup | Model | 100 Static Tasks | 50 Games |
|-------|-------|------------------|----------|
| API | GPT-4 | ~2 min | ~15 min |
| API | Claude-3 | ~1.5 min | ~12 min |
| API | GPT-3.5 | ~30 sec | ~5 min |
| Local | Llama-70B | ~3 min | ~20 min |

### Resource Requirements
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: ~1MB per 100 games for logs
- **Network**: Stable connection for API models
- **Compute**: GPU beneficial for local models

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Solution: Reduce parallel evaluation, add delays
   - Use exponential backoff for retries

2. **Inconsistent Results**
   - Check: Model temperature settings (should be 0)
   - Verify: Deterministic seed usage
   - Review: Prompt consistency

3. **Judge Disagreements**
   - Calibrate judge with human annotations
   - Review edge cases in judge prompts
   - Consider using multiple judges

4. **Memory Issues**
   - Stream results to disk for large evaluations
   - Process in smaller batches
   - Clear transcript cache periodically

## Next Steps

1. Review the [MineBench Specification](./minebench-spec.md) for detailed requirements
2. See [Prompt Engineering Guide](./prompt-engineering.md) for optimization tips
3. Check [API Documentation](/docs) for programmatic access
4. Join our Discord for evaluation discussions and best practices

## References

- MineBench: A Systematic Evaluation Framework for Minesweeper AI (2025)
- "Evaluating LLMs as Judges" - Anthropic Research (2024)
- "Statistical Methods for AI Evaluation" - Stanford AI Lab (2025)