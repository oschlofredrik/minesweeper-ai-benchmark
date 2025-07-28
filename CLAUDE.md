# Claude Memory - Tilts

## Project Overview
This is a comprehensive benchmark platform for evaluating Large Language Models (LLMs) on logic-based reasoning tasks through games like Minesweeper and Risk. The platform features a flexible plugin architecture supporting multiple games and is ready for deployment.

## Current Status (Completed ✅)
1. **Core Game Engine**: Full Tilts implementation with solver
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
15. **Serverless Migration**: Complete Vercel deployment with all endpoints
16. **Database Integration**: Supabase connected and configured

## Key Technical Details

### Architecture
- **Language**: Python 3.11+
- **Web Framework**: FastAPI with Uvicorn (Render), HTTP handlers (Vercel)
- **Async**: Full async/await support for parallel evaluation
- **Type Safety**: Comprehensive type hints throughout
- **Storage**: Supabase (primary), JSON files (fallback)
- **Serverless**: Vercel Functions for API endpoints

### Project Structure
```
tilts/
├── src/
│   ├── core/              # Types, config, utilities
│   ├── games/             # Game implementations
│   │   ├── base.py        # Base game interfaces
│   │   ├── registry.py    # Game discovery and registration
│   │   ├── tilts.py       # Minesweeper implementation
│   │   └── implementations/
│   │       ├── risk/      # Risk game plugin
│   │       └── number_puzzle/
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

#### Logging and Debugging Improvements (July 14, 2025)
- **Enhanced Structured Logging**: Added model_name, model_provider, game_num, and move_num to all log entries
- **Better Render Debugging**: Can now filter logs by model to identify model-specific issues
- **Invalid Move Handling**: Fixed infinite loop when AI repeatedly tries invalid moves
  - Tracks consecutive invalid moves (e.g., revealing already-revealed cells)
  - Stops game after 3 consecutive invalid moves
  - Marks game as ERROR status (not counted as loss)
  - Prevents fairness issues from technical failures

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

## Risk Game Plugin Implementation (July 24, 2025)

### Overview
Successfully implemented Risk as a complete game plugin for the Tilts platform, demonstrating the flexibility of the plugin architecture.

### Risk Implementation Details
1. **Complete Game Logic**
   - 42 territories across 6 continents
   - Full reinforcement, attack, and fortify phases
   - Dice-based combat system following official Risk rules
   - Territory connections and continent bonuses

2. **AI Integration**
   - Optimized board state representations for LLMs
   - Function calling schema for structured moves
   - Clear phase-based prompting
   - Territory grouping by continent for readability

3. **Scenarios**
   - North America Conquest
   - Defend Australia
   - Europe vs Asia
   - Blitzkrieg (rapid expansion)
   - Last Stand (survival mode)

### Platform Updates for Multi-Game Support
1. **Streaming Runner**
   - Now accepts game_name parameter
   - Dynamically loads appropriate game class
   - Supports game-specific function schemas

2. **Game Adapter**
   - Created adapter pattern for non-Minesweeper games
   - Translates between game-specific and platform interfaces
   - Handles function call data for complex moves

3. **Model Updates**
   - OpenAI and Anthropic models handle game-specific tools
   - Function schemas dynamically loaded based on game
   - Proper move parsing for each game type

4. **UI Integration**
   - Added game selection dropdown
   - Dynamic difficulty options per game
   - Risk scenarios available as difficulty settings

### Key Files Added/Modified
- `src/games/implementations/risk/` - Complete Risk implementation
- `src/games/game_adapter.py` - Universal game adapter
- `src/evaluation/streaming_runner.py` - Multi-game support
- `src/models/base.py` - Game-aware function calling
- `src/api/static/app-rams.js` - UI game selection

### Testing
Risk game successfully:
- Registers with game registry
- Creates game instances with scenarios
- Generates AI-friendly board representations
- Provides function calling schemas
- Integrates with evaluation pipeline

## Final State
The Tilts platform is now a true multi-game AI evaluation system. The successful Risk implementation demonstrates that new games can be added as plugins without modifying core infrastructure. The platform maintains robust error handling, fair scoring, and comprehensive debugging while supporting diverse game types. Both Minesweeper and Risk (and other games) work seamlessly with OpenAI and Anthropic models using native function calling for reliable, structured gameplay.

## Serverless Deployment (July 2025)

### Vercel Setup
Successfully migrated entire platform to Vercel serverless architecture:
- All API endpoints converted to HTTP handlers
- Static file serving configured
- Multi-step wizard restored
- SSE for basic real-time updates
- **Full game engines implemented** (Minesweeper and Risk)
- **AI integration complete** (OpenAI and Anthropic with function calling)
- **Automatic game chaining** to handle Vercel timeouts
- **Live at**: https://tilts.vercel.app/

### Supabase Database Integration
**Project Details:**
- **Project ID**: mgkprogfsjmazekeyquq
- **Region**: eu-north-1
- **URL**: https://mgkprogfsjmazekeyquq.supabase.co
- **Database**: PostgreSQL with Row Level Security

**Schema Applied:**
- `sessions` - Competition sessions with join codes
- `games` - Individual game records with full transcripts
- `leaderboard_entries` - Model performance tracking
- `evaluations` - Custom evaluation metrics marketplace
- `prompts` - Prompt template library
- `session_players` - Session participants
- `settings` - System configuration

**Key Features:**
- Automatic fallback to JSON if Supabase unavailable
- All tables have RLS enabled (currently open for development)
- Update triggers for automatic timestamp management
- Demo data inserted (GPT-4 and Claude leaderboard entries)

### Environment Variables
```bash
# Supabase
SUPABASE_URL=https://mgkprogfsjmazekeyquq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI Models
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### File Structure
```
/api/
├── supabase_db.py    # Database abstraction with fallback
├── index.py          # Main routing handler
├── sessions.py       # Session management
├── play.py           # Game execution
├── evaluations.py    # Evaluation system
├── admin.py          # Admin endpoints
├── prompts.py        # Prompt library
├── events.py         # SSE real-time
└── requirements.txt  # Minimal deps (supabase, python-dotenv)

/supabase/
└── migrations/
    └── 001_initial_schema.sql  # Complete database schema
```

### Deployment Details
**Live URL**: https://tilts.vercel.app/

### Deployment Commands
```bash
# Apply Supabase migrations
supabase link --project-ref mgkprogfsjmazekeyquq
supabase db push --password '/vETxuZ??DExSr8'

# Deploy to Vercel
git push origin main
```

### Migration Tools
- `migrate-to-supabase.py` - Migrate JSON data to Supabase
- `apply-migrations.sh` - Apply database schema

The platform now runs fully serverless with persistent storage, maintaining all original features while adding scalability and reducing operational overhead.

## Sub-Agent Architecture (July 2025)

### Available Sub-Agents

The project includes specialized sub-agents for complex tasks. Proactively use these when appropriate:

1. **benchmark-analyzer**
   - **Purpose**: Analyze game results, calculate statistics, identify patterns
   - **When to use**: 
     - User asks about model performance comparisons
     - Needs statistical analysis of benchmark results
     - Wants to understand why certain models fail
     - Requests leaderboard insights or trends
   - **Example triggers**: "analyze performance", "compare models", "why is GPT-4 losing", "statistical significance"

2. **game-implementer**
   - **Purpose**: Implement new games following platform architecture
   - **When to use**:
     - User wants to add a new game (Chess, Sudoku, etc.)
     - Needs to modify existing game logic
     - Asks about game plugin architecture
     - Wants to create game variants
   - **Example triggers**: "add new game", "implement chess", "create game variant", "modify game rules"

3. **performance-optimizer**
   - **Purpose**: Optimize platform performance, reduce latency, improve efficiency
   - **When to use**:
     - User reports slow loading times
     - Needs to optimize database queries
     - Wants to reduce bundle sizes
     - Asks about performance metrics
   - **Example triggers**: "slow loading", "optimize performance", "reduce latency", "improve speed"

### Sub-Agent Usage Guidelines

**IMPORTANT**: Proactively suggest using sub-agents when tasks match their expertise. Don't wait for explicit requests.

Examples of proactive usage:
- User: "The leaderboard shows GPT-4 with lower scores than expected"
  → Immediately suggest: "I'll use the benchmark-analyzer sub-agent to investigate this issue"

- User: "I want to add Chess to the platform"
  → Immediately suggest: "I'll use the game-implementer sub-agent to help implement Chess"

- User: "The benchmark page takes forever to load"
  → Immediately suggest: "I'll use the performance-optimizer sub-agent to diagnose and fix this"

### How to Invoke Sub-Agents

Use the Task tool with the appropriate subagent_type:
```
Task(
    description="Analyze model performance",
    prompt="Use the benchmark-analyzer sub-agent to analyze why Claude-3-Opus outperforms GPT-4 in Minesweeper",
    subagent_type="general-purpose"
)
```

### Sub-Agent Best Practices

1. **Delegate Complex Analysis**: Don't try to analyze 100+ games manually - use benchmark-analyzer
2. **Maintain Architecture**: Always use game-implementer for new games to ensure consistency
3. **Profile Before Optimizing**: Use performance-optimizer to measure before making changes
4. **Preserve Context**: Sub-agents work in separate contexts, keeping main conversation clean

### Creating New Sub-Agents

If a task requires specialized expertise not covered by existing sub-agents, create a new one:
1. Identify the specific domain and responsibilities
2. Create `.claude/agents/[name].md` with clear system prompt
3. Define which tools the sub-agent needs
4. Update this documentation