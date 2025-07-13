# Minesweeper AI Benchmark

[![Live Demo](https://img.shields.io/badge/Live-Demo-green)](https://minesweeper-ai-benchmark.onrender.com)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive benchmark platform for evaluating Large Language Models (LLMs) on logic-based reasoning tasks through expert-level Minesweeper gameplay.

## 🚀 Live Deployment

The platform is live at: https://minesweeper-ai-benchmark.onrender.com

## 🎯 Features

- **Comprehensive LLM Evaluation**: Test reasoning capabilities of OpenAI and Anthropic models
- **Function Calling Integration**: Native support for OpenAI function calling and Anthropic tool use
- **Advanced Metrics**: Win rate, mine detection precision/recall, board coverage analysis
- **MineBench Compliant**: Full implementation of the MineBench specification
- **Web Interface**: Clean, Dieter Rams-inspired UI for running evaluations
- **Complete Event Tracking**: Capture and display all prompts, responses, and reasoning
- **Real-time Monitoring**: Stream logs and track evaluation progress
- **Extensible Architecture**: Plugin system for custom models and metrics
- **Statistical Analysis**: Wilson confidence intervals and significance testing

## 🛠️ Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Anthropic API key (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/minesweeper-benchmark.git
cd minesweeper-benchmark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Start the web server
python -m src.cli.main serve --open-browser

# Or run evaluations from CLI
python -m src.cli.main evaluate --model gpt-4 --num-games 10
```

## 📊 Monitoring & Logs

### Stream Deployment Logs

```bash
# Using Render API (recommended)
export RENDER_API_KEY='your-render-api-key'
./render-api-logs.sh

# View in browser
./view-logs-browser.sh
```

See [Log Streaming Guide](docs/log-streaming.md) for detailed instructions.

## 🎮 How It Works

1. **Game Generation**: Creates Minesweeper puzzles with known solutions
2. **LLM Evaluation**: Models play games using strategic reasoning
3. **Function Calling**: Uses native OpenAI/Anthropic APIs for structured moves
4. **Metrics Collection**: Tracks performance across multiple dimensions
5. **Statistical Analysis**: Provides confidence intervals and significance tests

### 🤖 Function Calling Integration

The platform uses **function calling** (OpenAI) and **tool use** (Anthropic) for reliable, structured communication:

- **No Parsing Errors**: Moves come as structured JSON, not text
- **Complete Games**: Games run to completion without stopping
- **Rich Reasoning**: Every move includes detailed reasoning
- **Full Compatibility**: Works with GPT-4, GPT-3.5, Claude-3, and more

See [Function Calling Documentation](docs/function-calling.md) for details.

## 📚 Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Architecture Overview](docs/architecture.md)
- [Function Calling Integration](docs/function-calling.md)
- [Deployment Guide](docs/deployment-render.md)
- [Plugin Development](docs/plugin-development.md)
- [Prompt Engineering](docs/prompt-engineering.md)
- [Web Interface Guide](docs/web-interface.md)
- [Log Streaming Guide](docs/log-streaming.md)

## 🧩 Extending the Platform

### Adding a New Model

```python
from src.models.base import BaseModel

class MyCustomModel(BaseModel):
    async def get_action(self, game_state: GameState) -> Action:
        # Your implementation here
        pass
```

### Creating Custom Metrics

```python
from src.evaluation.metrics.base import BaseMetric

class MyMetric(BaseMetric):
    def calculate(self, games: List[Game]) -> float:
        # Your metric logic here
        pass
```

## 🔧 Configuration

Key environment variables:

```bash
# API Keys
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
RENDER_API_KEY=your-key

# Game Settings
DEFAULT_BOARD_ROWS=16
DEFAULT_BOARD_COLS=30
DEFAULT_MINE_COUNT=99

# Evaluation Settings
EVALUATION_BATCH_SIZE=10
EVALUATION_TIMEOUT=300
```

## 📈 Metrics

The platform tracks:

- **Win Rate**: Percentage of games won
- **Valid Move Rate**: Percentage of legal moves
- **Mine Detection**: Precision and recall for mine identification
- **Board Coverage**: Average percentage explored before loss
- **Move Efficiency**: Strategic quality of moves
- **Reasoning Quality**: LLM-judged explanation quality

## 🚀 Deployment

The platform is deployed on Render with:

- Automatic builds from GitHub
- PostgreSQL database (optional)
- HTTPS enforcement
- Health monitoring
- Auto-scaling capabilities

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- MineBench specification creators
- OpenAI and Anthropic for LLM APIs
- Render for hosting platform

## 📞 Support

- [GitHub Issues](https://github.com/yourusername/minesweeper-benchmark/issues)
- [Documentation](docs/)
- Email: your-email@example.com