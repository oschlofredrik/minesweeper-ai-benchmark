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
9. **Deployment**: Successfully deployed to Render
10. **UI/UX**: Minimalist black terminal-style interface
11. **Logging**: Comprehensive structured logging system
12. **Monitoring**: Real-time log streaming via Render API

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
- **Platform**: Render (live at https://minesweeper-ai-benchmark.onrender.com)
- **Service ID**: srv-d1prptqdbo4c73bs9jkg
- **Config**: render.yaml ready
- **Requirements**: requirements-render.txt
- **Health Check**: /health endpoint
- **CORS**: Enabled for API access
- **HTTPS**: Enforced with automatic upgrades

### API Keys Required
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- RENDER_API_KEY (for log streaming)

### Important Files
- `render.yaml` - Render deployment config
- `requirements-render.txt` - Production dependencies
- `DEPLOY_CHECKLIST.md` - Quick deployment guide
- `.env.example` - Environment variable template
- `render-api-logs.sh` - API-based log streaming script
- `stream-render-logs.sh` - CLI-based log viewer (requires workspace setup)
- `view-logs-browser.sh` - Quick browser log viewer

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

## Recent Updates (July 2025)

### UI/UX Improvements
- Redesigned interface with minimalist black terminal aesthetic
- Removed rounded corners and shadows for clean, straight lines
- Combined game generation and evaluation into single "Play" workflow
- Renamed "Tasks" to "Games" throughout the interface

### Logging & Monitoring
- Implemented structured JSON logging with rotation
- Added comprehensive logging throughout the application
- Created real-time log streaming solution using Render API
- Log viewer scripts for easy debugging and monitoring

### Deployment Fixes
- Fixed ModelConfig import issues
- Resolved HTTPS mixed content errors
- Fixed difficulty enum conversion bugs
- Corrected evaluate_model() API signature mismatches

### Monitoring Tools
```bash
# Stream logs using Render API (recommended)
export RENDER_API_KEY='rnd_your_key'
./render-api-logs.sh

# View logs in browser
./view-logs-browser.sh

# Use Render CLI (requires workspace setup)
render workspace set
render logs --resources srv-d1prptqdbo4c73bs9jkg --tail
```

## Final State
The Minesweeper AI Benchmark is production-ready and actively deployed. It provides a robust platform for evaluating LLM reasoning capabilities through strategic gameplay, with comprehensive monitoring, logging, and a clean terminal-inspired interface.