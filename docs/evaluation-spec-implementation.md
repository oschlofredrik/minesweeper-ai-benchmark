# MineBench Evaluation Specification Implementation

This document describes the implementation of the MineBench evaluation specification features.

## Implemented Features

### 1. LLM Judge for Reasoning Quality ✅

**Location**: `src/evaluation/judge.py`

- GPT-4o-based reasoning judge with 0-2 rubric
- Deterministic judging (temperature=0)
- Batch processing support
- Structured feedback output

**Usage**:
```python
from src.evaluation import ReasoningJudge

judge = ReasoningJudge()
result = await judge.judge_reasoning(
    task_uid="MS-S-3fa2bc",
    board_state=board_ascii,
    action="Reveal B3",
    reasoning="Cell B3 is safe because..."
)
print(f"Score: {result.score}")  # 0.0-1.0
```

### 2. Advanced Metrics & Composite Scores ✅

**Location**: `src/evaluation/advanced_metrics.py`

Implemented composite scores:
- **MS-S Score**: ACC × 0.7 + VOR × 0.1 + RS × 0.2
- **MS-I Score**: WR × 0.5 + COV × 0.2 + VMR × 0.1 + FLAG × 0.1 + RS × 0.1
- **Global MineBench Score**: Weighted geometric mean

Statistical testing:
- Two-proportion z-test for win rate differences
- Confidence intervals (Wilson score method)
- Significance flagging (α=0.05)

### 3. Task UID System ✅

**Location**: `src/evaluation/advanced_metrics.py`

- Format: `<code>-<hash6>` (e.g., "MS-S-3fa2bc", "MS-I-8e9d1a")
- Deterministic generation from task IDs
- Used throughout evaluation pipeline

### 4. Episode Logging ✅

**Location**: `src/evaluation/episode_logger.py`

MineBench-compliant output formats:
- Per-item JSON results
- Newline-delimited JSON episode logs
- Batch result aggregation
- Leaderboard entry formatting

**Example episode log**:
```jsonl
{"turn":1,"board":"...","action":"Reveal D5","rationale":"...","reasoning_score":0.8,"latency_ms":1234}
{"turn":2,"board":"...","action":"Flag B2","rationale":"...","reasoning_score":1.0,"latency_ms":987}
```

### 5. Data Splits (Public/Hidden) ✅

**Location**: `src/tasks/splits.py`

- 80/20 public/hidden split management
- Hidden answer validation
- Solution masking for hidden tasks
- Split persistence and tracking

**Usage**:
```python
from src.tasks import DataSplitManager

manager = DataSplitManager()
public_tasks, hidden_tasks = manager.create_splits(all_tasks)
masked_tasks = manager.mask_hidden_solutions(hidden_tasks)
```

## Integration with Existing System

### Updated Evaluation Pipeline

1. **Task Loading**: Now supports split filtering
2. **Game Execution**: Tracks latencies per move
3. **Reasoning Judgment**: Async judging during evaluation
4. **Metrics Calculation**: Advanced metrics with composite scores
5. **Result Logging**: MineBench-compliant output formats

### CLI Extensions Needed

To fully utilize these features, the CLI should be extended with:

```bash
# Evaluate with reasoning judge
python -m src.cli.main evaluate --model gpt-4 --use-judge --split public

# Run hidden split evaluation
python -m src.cli.main evaluate --model gpt-4 --split hidden --no-solutions

# Compare with statistical significance
python -m src.cli.main compare --models gpt-4 claude-3 --test-significance
```

## Performance Considerations

### Reasoning Judge
- Adds ~1-2s per move for GPT-4o calls
- Batch processing reduces overhead
- Can be disabled for faster evaluation

### Statistical Testing
- Negligible computation time
- Requires minimum sample sizes (n≥30 recommended)

## Next Steps

1. **CLI Integration**: Update CLI to use new evaluation features
2. **Database Schema**: Implement PostgreSQL schema from spec
3. **Leaderboard System**: Build web interface with new metrics
4. **Human Audit System**: Implement quarterly review process
5. **Versioning**: Add evaluation spec version tracking

## Example Advanced Evaluation

```python
from src.evaluation import (
    AdvancedMetricsCalculator, 
    ReasoningJudge,
    EpisodeLogger
)

# Run evaluation with all features
calculator = AdvancedMetricsCalculator()
judge = ReasoningJudge()
logger = EpisodeLogger()

# Evaluate model
transcripts = await run_games(model, tasks)
judgments = await judge_all_moves(transcripts)
metrics = calculator.calculate_advanced_metrics(
    transcripts, judgments, TaskType.INTERACTIVE
)

# Log results
logger.save_batch_results(results, run_id, model_id)

# Test significance
significance = calculator.test_significance(
    metrics1, metrics2, "win_rate"
)
```

## Compliance Status

✅ **Fully Implemented**:
- Task taxonomy (MS-S, MS-I)
- Metric definitions
- Composite scores
- LLM judge pipeline
- Output schemas
- Task UID system

🚧 **Partially Implemented**:
- Data splits (logic complete, needs CLI integration)
- Statistical significance (implemented, needs UI)
- Performance benchmarks (needs testing)

❌ **Not Yet Implemented**:
- PostgreSQL database schema
- Quarterly human audits
- Version migration system
- Web leaderboard with new metrics