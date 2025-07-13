# Prompt Engineering Guide

The Minesweeper AI Benchmark includes comprehensive prompt engineering tools to optimize how LLMs approach the game.

## Overview

The prompt engineering system provides:

- **Template Management**: Create, store, and version prompt templates
- **A/B Testing**: Statistically rigorous comparison of prompts
- **Interactive Testing**: Real-time prompt development and testing
- **Optimization**: Automated search for better prompt variations
- **Performance Tracking**: Metrics for each prompt template

## Quick Start

### List Available Templates

```bash
python -m src.cli.main prompt list
```

Shows all built-in and custom templates with their descriptions and tags.

### View a Template

```bash
python -m src.cli.main prompt show standard
```

Displays the full template text and metadata.

### Test a Template Interactively

```bash
python -m src.cli.main prompt test --model gpt-4 --provider openai
```

Opens an interactive session where you can:
- Create game scenarios
- Test prompts and see responses
- Edit templates on the fly
- Compare multiple prompts

## Creating Custom Templates

### Basic Template

```bash
python -m src.cli.main prompt create \
  --name my_prompt \
  --description "My custom Minesweeper prompt" \
  --tags strategic --tags concise
```

Then enter your template text. Use `{board_state}` as a placeholder.

### From File

```bash
python -m src.cli.main prompt create \
  --name advanced_cot \
  --template-file prompts/chain_of_thought.txt \
  --tags cot --tags detailed
```

### Creating Variations

```bash
python -m src.cli.main prompt variation \
  standard \
  standard_v2 \
  --description "Standard with pattern hints" \
  --tags patterns
```

## Template Format

Templates support Python string formatting with these variables:

- `{board_state}`: The current game board (ASCII or coordinate format)
- `{pattern_hints}`: Optional pattern recognition hints
- Custom parameters you define

Example template:
```
You are playing Minesweeper. Current board:

{board_state}

Analyze the board systematically:
1. Find all revealed numbers
2. Count adjacent mines vs flags for each
3. Identify cells that MUST be mines or safe
4. Choose the most certain move

{pattern_hints}

Respond with: Action: [reveal/flag] (row, col)
```

## A/B Testing

Compare two templates with statistical significance:

```bash
python -m src.cli.main prompt compare \
  standard \
  chain_of_thought \
  --model gpt-4 \
  --num-games 50
```

Output shows:
- Win rates for each template
- Statistical p-values
- Confidence intervals
- Winner (if statistically significant)

## Prompt Optimization

Automatically test variations of a base template:

```bash
python -m src.cli.main prompt optimize \
  --base-template standard \
  --model gpt-4 \
  --num-games 20 \
  --output optimization_results.json
```

The optimizer tests predefined variations:
- Expert player emphasis
- Pattern recognition hints
- Structured reasoning steps
- Parameter adjustments

## Built-in Templates

### Standard
Basic clear instructions with legend and format specification.

**Tags**: `basic`, `clear`

### Chain of Thought
Step-by-step reasoning approach with methodical analysis.

**Tags**: `cot`, `detailed`

### Structured
JSON output format for precise action parsing.

**Tags**: `json`, `structured`

### Pattern-Based
Emphasizes common Minesweeper patterns like 1-2-1.

**Tags**: `patterns`, `advanced`

## Interactive Testing Workflow

1. **Select Template**: Choose from available templates
2. **Create Scenario**: Set up a specific game state
3. **Test Prompt**: See model response and parsed action
4. **Compare**: Test multiple prompts on same scenario
5. **Edit**: Modify template based on results
6. **Save**: Store successful variations

## Performance Metrics

Each template tracks:
- **Win Rate**: Games won / total games
- **Valid Move Rate**: Valid actions / total actions
- **Response Time**: Average generation time
- **Reasoning Score**: Quality of explanations (if using judge)

## Best Practices

### Template Design

1. **Clear Instructions**: Specify exact output format
2. **Examples**: Include few-shot examples for complex formats
3. **Structure**: Guide reasoning process step-by-step
4. **Constraints**: Remind model of game rules
5. **Conciseness**: Balance detail with token efficiency

### Testing Strategy

1. **Diverse Scenarios**: Test on various board states
2. **Edge Cases**: Include difficult decisions
3. **Sufficient Samples**: Use 50+ games for A/B tests
4. **Control Variables**: Test one change at a time

### Optimization Tips

1. **Start Simple**: Begin with basic template
2. **Iterate**: Make incremental improvements
3. **Track Changes**: Document what works
4. **Model-Specific**: Optimize for target model
5. **Measure Impact**: Verify improvements statistically

## Advanced Features

### Grid Search

Test multiple parameter combinations:

```python
from src.prompt_engineering import PromptManager, PromptOptimizer

optimizer = PromptOptimizer(PromptManager())

results = await optimizer.grid_search(
    base_template="standard",
    model_config=model_config,
    parameter_grid={
        "thinking_style": ["analytical", "intuitive", "systematic"],
        "detail_level": ["concise", "moderate", "detailed"],
    },
    num_games=10,
)
```

### Custom Parameters

Add dynamic parameters to templates:

```python
template = PromptTemplate(
    name="adaptive",
    template="""Difficulty: {difficulty}
Board size: {board_size}

{board_state}

Adjust strategy for {difficulty} difficulty.
Action: [reveal/flag] (row, col)""",
    parameters={
        "board_state": "",
        "difficulty": "expert",
        "board_size": "9x9",
    }
)
```

### Performance Tracking

Templates automatically track performance over time:

```python
manager = PromptManager()
template = manager.get_template("my_prompt")

# After evaluation
manager.update_performance(
    "my_prompt",
    {"win_rate": 0.75, "avg_moves": 23.5}
)
```

## Troubleshooting

### Template Not Found
- Check template name with `prompt list`
- Ensure template was saved properly
- Check `data/prompts/` directory

### Poor Performance
- Verify output format is parseable
- Check for ambiguous instructions
- Test with verbose mode to see full responses
- Try simpler templates first

### A/B Test No Winner
- Increase sample size (100+ games)
- Ensure templates are sufficiently different
- Check if model is deterministic (temperature=0)

## Examples

### Minimalist Template
```
{board_state}
Choose safest move.
Action: [reveal/flag] (row, col)
```

### Detailed Analysis Template
```
MINESWEEPER ANALYSIS

Board State:
{board_state}

Step 1: Revealed Numbers
[List each number and its position]

Step 2: Mine Constraints
[For each number, calculate: adjacent_mines - adjacent_flags = remaining_mines]

Step 3: Deductions
[Identify cells that must be mines or safe]

Step 4: Decision
[Choose move with highest certainty]

Final Action: [reveal/flag] (row, col)
Confidence: [0-1]
Reasoning: [One sentence explanation]
```

### Pattern-Focused Template
```
{board_state}

Check patterns:
- 1-2-1: Middle is safe
- 1-2-2-1: Two middle are mines
- Corner 1 with one hidden: That cell is mine

Found pattern: [describe if any]
Action: [reveal/flag] (row, col)
```