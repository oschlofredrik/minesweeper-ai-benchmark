# Claude Memory - Minesweeper AI Benchmark

## Project Overview
This is a comprehensive benchmark platform for evaluating Large Language Models (LLMs) on logic-based reasoning tasks through expert-level Minesweeper gameplay. The platform is now feature-complete and ready for deployment.

## Current Status (Completed ✅)
1. **Core Game Engine**: Full Minesweeper implementation with solver
2. **Model Interfaces**: OpenAI and Anthropic integrations
3. **Evaluation System**: Advanced metrics with statistical testing
4. **Task Management**: Generation and storage of benchmark scenarios
5. **CLI Tools**: Comprehensive command-line interface
6. **Web Interface**: Leaderboard and API with FastAPI
7. **Prompt Engineering**: A/B testing and optimization tools
8. **Plugin System**: Extensible architecture for custom components
9. **Deployment**: Render configuration with one-click deploy

## Key Technical Details

### Architecture
- **Language**: Python 3.11+
- **Web Framework**: FastAPI with Uvicorn
- **Async**: Full async/await support for parallel evaluation
- **Type Safety**: Comprehensive type hints throughout
- **Storage**: File-based (with optional PostgreSQL)

### Project Structure
```
minesweeper-benchmark/
├── src/
│   ├── core/              # Types, config, utilities
│   ├── games/             # Minesweeper implementation
│   ├── models/            # LLM interfaces
│   ├── evaluation/        # Metrics and scoring
│   ├── tasks/             # Task generation
│   ├── prompt_engineering/# Prompt optimization
│   ├── plugins/           # Plugin system
│   ├── api/               # Web interface
│   └── cli/               # Command-line tools
├── data/                  # Tasks, results, prompts
├── plugins/               # Custom plugins directory
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

### Key Commands
```bash
# Generate tasks
python -m src.cli.main generate-tasks --num-tasks 50

# Run evaluation
python -m src.cli.main evaluate --model gpt-4 --num-games 10

# Start web server
python -m src.cli.main serve --open-browser

# Prompt engineering
python -m src.cli.main prompt test --model gpt-4

# Plugin management
python -m src.cli.main plugin list
```

### Deployment
- **Platform**: Render (configured)
- **Config**: render.yaml ready
- **Requirements**: requirements-render.txt
- **Health Check**: /health endpoint
- **CORS**: Enabled for API access

### API Keys Required
- OPENAI_API_KEY
- ANTHROPIC_API_KEY

### Important Files
- `render.yaml` - Render deployment config
- `requirements-render.txt` - Production dependencies
- `DEPLOY_CHECKLIST.md` - Quick deployment guide
- `.env.example` - Environment variable template

### Evaluation Metrics
- Win rate, valid move rate
- Mine identification precision/recall
- Board coverage analysis
- LLM-based reasoning judge
- Composite scores (MS-S, MS-I)
- Statistical significance testing

### Advanced Features
1. **Prompt Engineering**
   - Template management
   - A/B testing
   - Grid search optimization
   - Performance tracking

2. **Plugin System**
   - Model plugins for new LLMs
   - Metric plugins for custom evaluation
   - Game plugins for variants
   - Dynamic loading

3. **Web Interface**
   - Interactive leaderboard
   - REST API
   - Game replay (data ready)
   - Platform statistics

### MineBench Compliance
- Implements full MineBench specification
- LLM reasoning judge with GPT-4
- Statistical testing (Wilson intervals)
- Public/hidden data splits
- Composite scoring system

## Next Steps for Users

1. **Deploy to Render**:
   - Push to GitHub
   - Create Render account
   - Follow DEPLOY_CHECKLIST.md

2. **Run Evaluations**:
   - Set API keys in .env
   - Generate tasks
   - Evaluate models
   - View results on web interface

3. **Extend Platform**:
   - Create custom plugins
   - Add new prompt templates
   - Implement new metrics

## Known Considerations
- Free Render tier sleeps after 15 min inactivity
- File-based storage works well for <10k evaluations
- For production: upgrade Render instance and add PostgreSQL
- API rate limits depend on OpenAI/Anthropic plans

## Support Resources
- `/docs` folder has comprehensive guides
- API documentation at `/docs` endpoint
- GitHub issues for bug reports
- Render community for deployment help

## Final State
The Minesweeper AI Benchmark is production-ready with all planned features implemented. It provides a robust platform for evaluating LLM reasoning capabilities through strategic gameplay, with tools for researchers and developers to extend and customize the benchmarks.