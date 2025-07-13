# Minesweeper AI Benchmark

A comprehensive benchmark platform for evaluating Large Language Models (LLMs) on logic-based reasoning tasks through expert-level Minesweeper gameplay.

## Overview

The Minesweeper AI Benchmark tests LLMs' ability to:
- Apply logical deduction to identify safe moves
- Maintain spatial awareness of game state
- Make strategic decisions under uncertainty
- Explain reasoning behind each move

## Features

- 🎮 **Complete Minesweeper Implementation** - Full game engine with multiple difficulty levels
- 🤖 **Multi-Model Support** - Integrated support for OpenAI and Anthropic models
- 📊 **Comprehensive Metrics** - Win rate, move accuracy, reasoning quality, and more
- 🔄 **Reproducible Benchmarks** - Deterministic task generation with seeding
- 💻 **Easy-to-Use CLI** - Simple commands for evaluation, comparison, and analysis
- 🧪 **Prompt Engineering** - A/B testing, optimization, and interactive prompt development
- 🌐 **Web Interface** - Interactive leaderboard and visualization tools
- 📈 **Extensible Architecture** - Modular design for adding new models and metrics

## Quick Start

### Option 1: Use Hosted Version
Visit the deployed platform at: [Coming Soon - Deploy with button below]

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/oschlofredrik/minesweeper-ai-benchmark)

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/oschlofredrik/minesweeper-ai-benchmark.git
cd minesweeper-benchmark

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Basic Usage

```bash
# Generate benchmark tasks
python -m src.cli.main generate-tasks --num-tasks 50

# Evaluate GPT-4
python -m src.cli.main evaluate --model gpt-4 --num-games 10

# Compare multiple models
python -m src.cli.main compare --models gpt-4 --models claude-3-opus-20240229

# View results
python -m src.cli.main show-results results/gpt4_results.json

# Start web interface
python -m src.cli.main serve --open-browser

# Test prompts interactively
python -m src.cli.main prompt test --model gpt-4
```

## Evaluation Metrics

- **Win Rate**: Percentage of games successfully completed
- **Valid Move Rate**: Percentage of legal moves made
- **Mine Identification**: Precision and recall of mine flagging
- **Board Coverage**: How much of the board was revealed
- **Reasoning Quality**: Coherence and correctness of explanations

## Documentation

- [Quick Start Guide](docs/quickstart.md) - Detailed usage instructions
- [Architecture Overview](docs/architecture.md) - System design and components
- [Project Status](docs/project-status.md) - Current capabilities and roadmap
- [Web Interface](docs/web-interface.md) - Using the web dashboard
- [Prompt Engineering](docs/prompt-engineering.md) - Optimizing prompts for better performance

## Project Structure

```
minesweeper-benchmark/
├── src/
│   ├── core/              # Core types and configuration
│   ├── games/             # Minesweeper game implementation
│   ├── models/            # LLM interfaces (OpenAI, Anthropic)
│   ├── evaluation/        # Evaluation engine and metrics
│   ├── tasks/             # Task generation and management
│   ├── prompt_engineering/# Prompt optimization tools
│   ├── api/               # Web interface and API
│   └── cli/               # Command-line interface
├── data/
│   ├── tasks/             # Generated benchmark tasks
│   ├── results/           # Evaluation results
│   └── prompts/           # Prompt templates
├── tests/                 # Test suite
└── docs/                  # Documentation

```

## Example Results

```
Model Comparison
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Model                 ┃ Win Rate ┃ Valid Moves ┃ Mine Precision ┃ Board Coverage ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ openai/gpt-4          │ 32.0%    │ 94.5%       │ 78.3%          │ 68.2%          │
│ anthropic/claude-3    │ 28.0%    │ 92.1%       │ 75.6%          │ 65.4%          │
└───────────────────────┴──────────┴─────────────┴────────────────┴────────────────┘
```

## Contributing

Contributions are welcome! Areas of interest:
- Adding support for more LLM providers
- Implementing new evaluation metrics
- Creating harder benchmark tasks
- Building visualization tools

## License

[License information to be added]

## Citation

If you use this benchmark in your research, please cite:
```
[Citation to be added]
```

## Acknowledgments

This benchmark draws inspiration from:
- BIG-bench for comprehensive LLM evaluation
- ARC for reasoning-focused benchmarking
- SWE-bench for complex task evaluation
- Various Minesweeper AI research papers