# Vercel Deployment Guide

## Current Status ✅
- Game engines implemented (Minesweeper, Risk)
- AI model integration (OpenAI, Anthropic with function calling)
- Supabase database connected (project: mgkprogfsjmazekeyquq)
- Migration script ready
- Vercel configuration updated
- Live at: https://tilts.vercel.app/

## Prerequisites

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Create a Vercel account at https://vercel.com

## Environment Variables

These are already set in your Vercel project:

- `SUPABASE_URL` - https://mgkprogfsjmazekeyquq.supabase.co
- `SUPABASE_ANON_KEY` - Your Supabase anon key
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key

## Deployment Steps

1. **Deploy Latest Changes**:
```bash
git add .
git commit -m "Complete Vercel migration with game engines and AI integration"
git push origin main
```

Vercel will automatically deploy from your GitHub repository.

2. **Run Data Migration** (if you have data in Render):
```bash
# First, add RENDER_DATABASE_URL to your .env file
# Get it from: Render Dashboard > Your Database > Connection String

# Then run the migration
python scripts/migrate_render_to_supabase.py
```

3. **Test the Deployment**:
Visit https://tilts.vercel.app/ and test:
- Playing games (Minesweeper and Risk)
- Viewing leaderboard
- Admin panel functionality

## What's New in This Migration

### Real Game Engines
- **Minesweeper**: Full implementation with proper mine placement and win/loss detection
- **Risk**: Simplified 22-territory version with all game phases
- Both games provide function schemas for AI models

### AI Integration
- **OpenAI**: Uses native function calling API
- **Anthropic**: Uses tool use for structured responses
- No more regex parsing - all moves come as structured JSON
- Automatic game chaining for multi-game sessions

### Serverless Architecture
- Each game runs as a separate function invocation
- Games chain automatically (one triggers the next)
- Handles Vercel's 10-second timeout gracefully
- All state stored in Supabase

### Database
- Supabase PostgreSQL with automatic fallback to JSON
- All game data, moves, and transcripts stored
- Real-time leaderboard updates

## API Endpoints
- `/api/play` - Start new games
- `/api/run_game` - Execute individual games (NEW)
- `/api/sessions` - Competition sessions
- `/api/evaluations` - Custom evaluations
- `/api/admin` - Admin functions
- `/api/events` - SSE for real-time updates
- `/` - Main web interface

## Monitoring
Games now include:
- Full move history with reasoning
- Token usage tracking
- Error messages and stack traces
- Performance metrics

## Next Steps
1. Monitor initial deployment
2. Run data migration if needed
3. Update DNS if using custom domain
4. Decommission Render instance once verified

## Troubleshooting

1. **Games Not Running**: 
   - Check that API keys are set in Vercel environment
   - Verify Supabase connection is working
   - Check browser console for errors

2. **Timeout Issues**:
   - Games are designed to chain automatically
   - Each game runs in its own function invocation
   - Check `/api/run_game` endpoint logs

3. **Database Issues**:
   - Verify Supabase credentials are correct
   - Check that migrations were applied
   - System falls back to JSON if Supabase fails