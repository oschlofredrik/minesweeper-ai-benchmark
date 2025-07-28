# Vercel Migration Plan - Complete Implementation

## Current State
- ✅ API endpoints created (but mock implementations)
- ✅ Supabase database connected
- ✅ UI pages working
- ❌ No actual game execution
- ❌ No AI model integration
- ❌ No data migrated from Render

## Migration Tasks

### Phase 1: Core Game Logic
Need to create lightweight versions of game engines for Vercel:

1. **Minesweeper Engine**
   ```python
   # api/games/minesweeper.py
   - Board generation
   - Move validation
   - Game state management
   - Win/loss detection
   ```

2. **Risk Engine**
   ```python
   # api/games/risk.py
   - Territory management
   - Combat system
   - Turn phases
   - Victory conditions
   ```

### Phase 2: Model Integration
Add AI model execution to Vercel:

1. **Model Clients**
   ```python
   # api/models/openai_client.py
   # api/models/anthropic_client.py
   - Function calling
   - Streaming responses
   - Error handling
   ```

2. **Game Runner**
   ```python
   # api/runner.py
   - Execute games with AI
   - Track moves
   - Store results
   ```

### Phase 3: Data Migration
Migrate from Render PostgreSQL to Supabase:

1. **Export from Render**
   - Games table (with transcripts)
   - Leaderboard entries
   - Evaluations
   - Prompts

2. **Import to Supabase**
   - Transform data format
   - Preserve relationships
   - Update timestamps

### Phase 4: Missing Features

1. **Evaluation System**
   - Port evaluation metrics
   - Implement scoring logic
   - Add custom evaluations

2. **Task Management**
   - Generate benchmark tasks
   - Store in Supabase
   - Task selection logic

3. **Real-time Updates**
   - Implement SSE properly
   - Stream game progress
   - Live leaderboard updates

## File Structure Needed

```
/api/
├── games/
│   ├── __init__.py
│   ├── base.py          # Game interface
│   ├── minesweeper.py   # Minesweeper logic
│   └── risk.py          # Risk logic
├── models/
│   ├── __init__.py
│   ├── base.py          # Model interface
│   ├── openai_client.py # OpenAI integration
│   └── anthropic_client.py # Anthropic integration
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py       # Scoring logic
│   └── runner.py        # Evaluation execution
├── runner.py            # Main game runner
└── migrate_render.py    # Data migration script
```

## Implementation Order

1. **Create game engines** (simplified for serverless)
2. **Add model clients** (with API keys from env)
3. **Implement game runner** (connects games + models)
4. **Migrate data** (Render → Supabase)
5. **Test end-to-end** (create game → run → store results)

## Challenges

1. **10s Function Timeout** - Need to handle long games
2. **No Background Jobs** - Can't run evaluations async
3. **Cold Starts** - First request will be slow
4. **Memory Limits** - Keep game state minimal

## Solutions

1. **Chunked Execution** - Break games into moves
2. **Client Polling** - Frontend polls for updates
3. **Edge Functions** - For time-sensitive operations
4. **Efficient Storage** - Compress game states

Would you like me to start implementing these components?