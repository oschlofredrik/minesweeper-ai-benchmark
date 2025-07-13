# Minesweeper AI Benchmark - Quick Start Guide

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd minesweeper-benchmark
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
# or with poetry:
poetry install
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

## Basic Usage

### 1. Generate benchmark tasks
```bash
# Generate 30 tasks (mix of difficulties)
python -m src.cli.main generate-tasks --num-tasks 30

# Generate only expert-level interactive tasks
python -m src.cli.main generate-tasks --num-tasks 20 --task-type interactive
```

### 2. Evaluate a model
```bash
# Evaluate GPT-4 on 10 expert games
python -m src.cli.main evaluate --model gpt-4 --num-games 10 --difficulty expert

# Evaluate Claude 3 with custom settings
python -m src.cli.main evaluate \
  --model claude-3-opus-20240229 \
  --provider anthropic \
  --num-games 20 \
  --temperature 0.5 \
  --prompt-format cot \
  --output results/claude3_results.json
```

### 3. Compare multiple models
```bash
# Compare GPT-4 and Claude 3
python -m src.cli.main compare \
  --models openai/gpt-4 \
  --models anthropic/claude-3-opus-20240229 \
  --num-games 10
```

### 4. View results
```bash
# Display results from a previous run
python -m src.cli.main show-results results/claude3_results.json
```

### 5. Play Minesweeper yourself
```bash
# Play a beginner game (9x9, 10 mines)
python -m src.cli.main play

# Play expert level
python -m src.cli.main play --rows 16 --cols 30 --mines 99
```

## Command Reference

### `evaluate` - Run benchmark evaluation
```bash
Options:
  -m, --model TEXT         Model to evaluate (required)
  -p, --provider TEXT      Model provider [openai|anthropic]
  -n, --num-games INT      Number of games to play [default: 10]
  -d, --difficulty TEXT    Game difficulty [beginner|intermediate|expert]
  -t, --task-type TEXT     Task type [interactive|static]
  --prompt-format TEXT     Prompt format [standard|json|cot]
  -j, --parallel INT       Number of parallel games [default: 1]
  -v, --verbose           Show detailed progress
  --temperature FLOAT      Model temperature [default: 0.7]
  -o, --output PATH        Output file for results (JSON)
```

### `compare` - Compare multiple models
```bash
Options:
  -m, --models TEXT        Models to compare (multiple)
  -n, --num-games INT      Number of games per model
  -d, --difficulty TEXT    Game difficulty
  -o, --output PATH        Output file for comparison
```

### `generate-tasks` - Create benchmark tasks
```bash
Options:
  -n, --num-tasks INT      Number of tasks to generate
  -t, --task-type TEXT     Type of tasks [interactive|static|both]
  -c, --clear             Clear existing tasks first
```

### `play` - Interactive Minesweeper
```bash
Options:
  -r, --rows INT          Number of rows [default: 9]
  -c, --cols INT          Number of columns [default: 9]
  -m, --mines INT         Number of mines [default: 10]
  -s, --seed INT          Random seed for reproducibility
```

## Example Workflow

1. **Set up the benchmark**
```bash
# Generate a comprehensive task set
python -m src.cli.main generate-tasks --num-tasks 100 --task-type both
```

2. **Run initial evaluation**
```bash
# Test GPT-4
python -m src.cli.main evaluate \
  --model gpt-4 \
  --num-games 50 \
  --difficulty expert \
  --output results/gpt4_baseline.json

# Test Claude 3
python -m src.cli.main evaluate \
  --model claude-3-opus-20240229 \
  --num-games 50 \
  --difficulty expert \
  --output results/claude3_baseline.json
```

3. **Compare results**
```bash
python -m src.cli.main compare \
  --models openai/gpt-4 \
  --models anthropic/claude-3-opus-20240229 \
  --num-games 20 \
  --output results/comparison.json
```

4. **Experiment with prompts**
```bash
# Try chain-of-thought prompting
python -m src.cli.main evaluate \
  --model gpt-4 \
  --num-games 20 \
  --prompt-format cot \
  --output results/gpt4_cot.json
```

## Understanding Results

### Key Metrics

- **Win Rate**: Percentage of games successfully completed
- **Valid Move Rate**: Percentage of moves that were legal
- **Mine Precision**: Accuracy of mine flagging
- **Mine Recall**: Percentage of actual mines flagged
- **Board Coverage**: How much of the board was revealed (in losses)
- **Average Moves**: Number of moves to win/lose

### Output Format

Results are saved as JSON with the following structure:
```json
{
  "model": {
    "name": "openai/gpt-4",
    "temperature": 0.7
  },
  "evaluation": {
    "num_tasks": 10,
    "duration_seconds": 123.4
  },
  "metrics": {
    "win_rate": 0.3,
    "valid_move_rate": 0.95,
    "mine_identification_precision": 0.8,
    "board_coverage_on_loss": 0.65
  },
  "per_game_metrics": [...]
}
```

## Tips

1. **Start small**: Test with a few games first to ensure everything works
2. **Use seeds**: Set seeds for reproducible experiments
3. **Save results**: Always use `--output` to save results for later analysis
4. **Monitor costs**: API calls can add up - track your usage
5. **Parallel execution**: Use `--parallel` for faster evaluation (be mindful of rate limits)

## Troubleshooting

### "API key not found"
Make sure your `.env` file contains valid API keys:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### "Rate limit exceeded"
Reduce `--parallel` value or add delays between runs

### "Model not found"
Check available models with:
```bash
python -m src.cli.main list-models
```

### "Out of memory"
Reduce batch size or run fewer parallel games