# Supabase Realtime Setup for Serverless

## Overview
Since Vercel serverless functions can't maintain WebSocket connections, we've implemented a polling-based realtime system using Supabase tables.

## How It Works

1. **Backend Broadcasting**: 
   - Game moves are written to `realtime_events` table
   - Each event has a channel name (e.g., `game:bench_abc123`)
   - Events include move data, board state, and game state

2. **Frontend Polling**:
   - JavaScript polls the `realtime_events` table every 500ms
   - Only fetches new events since last poll
   - Updates UI in real-time as moves arrive

## Setup Steps

### 1. Apply Database Migration
```bash
# If using Supabase CLI
./apply-realtime-migration.sh

# Or manually in Supabase SQL editor:
# Copy contents of supabase/migrations/002_realtime_events.sql
```

### 2. Verify Environment Variables
Make sure these are set in Vercel:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

### 3. Deploy to Vercel
```bash
git add .
git commit -m "Add Supabase Realtime for live game updates"
git push
```

## Testing

1. Start a benchmark evaluation
2. Open browser console
3. You should see:
   - "Started polling for game events: game:bench_xxx"
   - "Event received: move" messages as the game progresses
   - Board updates in real-time

## Architecture Benefits

- **No WebSocket Requirements**: Works in serverless environment
- **Reliable**: Events stored in database, won't be lost
- **Scalable**: Supabase handles thousands of concurrent polls
- **Simple**: No complex WebSocket management

## Cleanup

Old events are automatically deleted after 5 minutes to keep the table small. You can also manually run:

```sql
SELECT cleanup_old_realtime_events();
```

## Troubleshooting

1. **No events appearing**: Check Supabase logs for insert errors
2. **Polling errors**: Verify RLS policies allow public SELECT
3. **Missing moves**: Check backend logs for broadcast failures