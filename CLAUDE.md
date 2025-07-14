# Claude Memory - Minesweeper AI Benchmark

## Project Overview
This is a comprehensive benchmark platform for evaluating Large Language Models (LLMs) on logic-based reasoning tasks through expert-level Minesweeper gameplay. The platform is now feature-complete and ready for deployment.

## Current Status (Completed ✅)
1. **Core Game Engine**: Full Minesweeper implementation with solver
2. **Model Interfaces**: OpenAI and Anthropic integrations with function calling
3. **Evaluation System**: Advanced metrics with statistical testing
4. **Task Management**: Generation and storage of benchmark scenarios
5. **CLI Tools**: Comprehensive command-line interface
6. **Web Interface**: Leaderboard and API with FastAPI
7. **Prompt Engineering**: A/B testing and optimization tools
8. **Plugin System**: Extensible architecture for custom components
9. **Deployment**: Successfully deployed to Render
10. **UI/UX**: Minimalist Dieter Rams-inspired interface
11. **Logging**: Comprehensive structured logging system
12. **Monitoring**: Real-time log streaming via Render API
13. **Function Calling**: Native OpenAI and Anthropic function/tool use
14. **Event Tracking**: Full prompt/response/reasoning capture and display

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

### Function Calling Integration (NEW)
- **OpenAI Function Calling**: Uses native `tools` API for structured responses
- **Anthropic Tool Use**: Implements Claude's tool use for reliable move formatting
- **No More Parsing**: Eliminates regex parsing errors that caused games to stop
- **Structured Actions**: Moves come as JSON with action, row, col, and reasoning
- **Reasoning Models**: Special handling for o1 and Claude with thinking

### Enhanced Event Tracking
- **Full AI Interaction Capture**: Stores prompts, responses, reasoning, tokens
- **Event Log UI**: Collapsible details with pause-on-hover functionality
- **Persistent Storage**: All move data saved in results JSON files
- **Move-by-Move Details**: Complete interaction history for analysis

### UI/UX Improvements
- Redesigned interface with minimalist Dieter Rams aesthetic
- Clean, functional design with optimal typography and spacing
- Combined game generation and evaluation into single "Play" workflow
- Event Log preserves open state during auto-refresh

### Logging & Monitoring
- Implemented structured JSON logging with rotation
- Added comprehensive logging throughout the application
- Created real-time log streaming solution using Render API
- Debug logging for game loop investigation

### API Integration Updates
- **Prompt Handling**: Automatic format selection based on model type
- **Reasoning Extraction**: Captures reasoning that comes before actions
- **Token Tracking**: Accurate token usage for both providers
- **Error Handling**: Robust error handling with detailed logging

### Monitoring Tools
```bash
# Stream logs using Render API (recommended)
export RENDER_API_KEY='rnd_your_key'
./render-api-logs.sh

# View logs in browser
./view-logs-browser.sh

# Test function calling
python test_function_calling.py

# Test evaluation flow
python test_evaluation.py
```

## Key Features Added

### Function Calling Benefits
1. **Reliability**: No parsing errors - moves always in correct format
2. **Consistency**: Structured responses with guaranteed fields
3. **Full Games**: Games run to completion instead of stopping after 1 move
4. **Rich Data**: Reasoning included with every move automatically

### Data Captured Per Move
- `prompt_sent`: Exact prompt sent to the AI
- `full_response`: Complete AI response
- `reasoning`: Extracted reasoning/thinking
- `action`: The move made (reveal/flag/unflag)
- `position`: Row and column
- `tokens_used`: Token count for the request
- `timestamp`: When the move was made
- `was_valid`: Whether the move was valid
- `error`: Any error message

## Technical Implementation

### OpenAI Function Calling
```python
# Automatically uses tools API for structured responses
tools = [{"type": "function", "function": {"name": "make_move", ...}}]
```

### Anthropic Tool Use  
```python
# Uses Claude's native tool use feature
tools = [{"name": "make_move", "input_schema": {...}}]
```

### Recent Fixes and Improvements (Latest)

#### Database Administration
- **Admin Panel Database Tab**: Complete database management interface
- **Safe SQL Endpoints**: Handle missing columns gracefully before migration
- **Migration Script**: `scripts/migrate_db_add_columns.py` adds missing fields
- **Database Stats**: View games, leaderboard entries, and model performance
- **Bulk Operations**: Delete games, reset model stats, cleanup database

#### UI/UX Refinements
- **Admin Button**: Moved to left sidebar (text-only, no icon)
- **Live Game Stream**: Removed all colored icons and backgrounds
- **Consistent Design**: Pure Dieter Rams aesthetic throughout
- **Leaderboard Tooltips**: Hover explanations for all metrics
- **Favicon**: Minimalist Minesweeper grid icon

#### Error Handling & Fairness
- **Technical Failure Handling**: New GameStatus.ERROR for API/system failures
- **Fair Scoring**: Technical failures don't count as losses
- **Error Tracking**: Full error messages stored with game transcripts
- **Leaderboard Accuracy**: Only valid games count toward rankings
- **Debug Information**: Detailed logging for troubleshooting

#### Model-Specific Fixes
- **o1 Models**: Fixed system message incompatibility
- **o3/o4 Models**: Proper timeout configurations (2-5 minutes)
- **Reasoning Models**: Special handling for models without function calling
- **API Compatibility**: Automatic message format adaptation

### Database Schema Updates
Run migration if upgrading existing deployment:
```bash
python scripts/migrate_db_add_columns.py
```

Adds:
- `games.full_transcript` - Complete game transcript with reasoning
- `games.task_id` - Reference to benchmark task
- `games.job_id` - Reference to play session
- `leaderboard_entries.created_at` - Timestamp tracking

### Admin Features
Access via Admin button in left sidebar:
- **Prompts**: Create/edit prompt templates
- **Models**: Configure model settings and API keys
- **Settings**: System configuration
- **Features**: Toggle feature flags
- **Database**: Manage games and leaderboard
- **Export/Import**: Backup configuration

### Error Status Tracking
Games now have four possible statuses:
- `IN_PROGRESS`: Game is active
- `WON`: Successfully completed
- `LOST`: Hit a mine
- `ERROR`: Technical failure (not counted in stats)

## Final State
The Minesweeper AI Benchmark is production-ready with robust error handling and fair scoring. Technical failures are distinguished from game losses, ensuring accurate model evaluation. The platform features comprehensive database administration, consistent Dieter Rams design, and detailed debugging capabilities. All models are properly supported with appropriate message formatting and timeout configurations.