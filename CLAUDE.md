# Tilts Platform - Claude Development Context

## Recent Updates (July 30, 2025)

### Completed Tasks
1. **Removed all fallbacks** that were hiding API failures
2. **Fixed AI Minesweeper performance** - simplified prompts to prevent risky guessing
3. **Migrated to Vercel AI SDK** for all AI endpoints
4. **Simplified to single play-game endpoint** using Node.js/Vercel AI SDK
5. **Fixed slow deployments** by removing Python dependencies
6. **Added comprehensive model support**:
   - OpenAI: GPT-4o series, O3/O1 reasoning models
   - Anthropic: Claude 4, Claude 3.7, Claude 3.5 models
7. **Fixed O3 model support** with proper reasoning parameters

### Key Technical Decisions
- Using Vercel AI SDK exclusively for AI interactions
- Single `play-game-sdk.js` endpoint handles all game playing
- Removed complex evaluation framework in favor of simple game playing
- Frontend expects camelCase (e.g., `totalMoves` not `total_moves`)

### Current Architecture
- **Frontend**: Static HTML/JS with real-time game visualization
- **Backend**: Vercel serverless functions (Node.js)
- **AI Integration**: Vercel AI SDK with support for streaming and reasoning models
- **Games**: Minesweeper and Risk implementations

### Important Files
- `/packages/api/play-game-sdk.js` - Main game playing endpoint
- `/benchmark-sdk.js` - Frontend handler for benchmarks
- `/game-visualizer.js` - Real-time game visualization
- `/index.html` - Main UI with model selection

### Minesweeper AI Strategy
The AI is instructed to:
1. Only reveal cells that are 100% guaranteed safe
2. Leave areas where safe moves cannot be deduced
3. Never guess when multiple mine locations are possible
4. Explore different parts of the board to gather information

### Model-Specific Handling
- **O3/O1 models**: Use `reasoningEffort` parameter, no temperature
- **Standard models**: Use temperature 0.2 for consistent play
- **Claude models**: Use correct API format (e.g., `claude-opus-4-20250514`)

### Known Issues Resolved
- AI no longer hits obvious mines
- O3 models now return proper responses
- Board visualization updates correctly
- Deployment is fast (removed Python dependencies)

### Testing Commands
When testing, use these commands to check code quality:
- `npm run lint` - Check code style
- `npm run typecheck` - Check TypeScript types (if applicable)
- `vercel dev` - Test locally
- `vercel --prod` - Deploy to production

### Environment Variables Required
- `OPENAI_API_KEY` - For OpenAI models
- `ANTHROPIC_API_KEY` - For Claude models
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` - For database (optional)

### Debugging Tips
- Check Vercel logs: `vercel logs <deployment-url>`
- Look for `[SDK]` prefixed logs for game logic debugging
- Board state is logged on every 5th move
- Full response objects logged for reasoning models