# Supabase Setup Guide for Tilts Platform

## Quick Setup

### 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Enter:
   - Project name: `tilts-platform`
   - Database password: (save this securely)
   - Region: Choose closest to your users
5. Click "Create new project"

### 2. Apply Database Schema

Once your project is created:

1. Go to SQL Editor (left sidebar)
2. Click "New Query"
3. Copy and paste the contents of `supabase/migrations/001_initial_schema.sql`
4. Click "Run"

### 3. Get Your API Keys

1. Go to Settings > API (left sidebar)
2. Copy these values:
   - **Project URL**: `https://YOUR_PROJECT.supabase.co`
   - **Anon/Public Key**: `eyJhbGc...` (long string)

### 4. Configure Vercel

1. Go to your Vercel project dashboard
2. Navigate to Settings > Environment Variables
3. Add these variables:

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=eyJhbGc... (your anon key)
OPENAI_API_KEY=sk-... (if using OpenAI)
ANTHROPIC_API_KEY=sk-ant-... (if using Anthropic)
```

### 5. Deploy

Push your changes to trigger a new deployment:

```bash
git add .
git commit -m "Add Supabase integration"
git push
```

## Local Development

For local testing:

1. Create `.env` file:
```bash
cp .env.vercel.example .env
```

2. Fill in your Supabase credentials

3. Install Supabase CLI:
```bash
brew install supabase/tap/supabase
```

4. Link to your project:
```bash
supabase link --project-ref YOUR_PROJECT_REF
```

## Testing the Connection

Once deployed, test these endpoints:

```bash
# Check if Supabase is connected
curl https://your-app.vercel.app/api/admin/stats

# Get leaderboard (should return data from Supabase)
curl https://your-app.vercel.app/api/leaderboard

# Create a test session
curl -X POST https://your-app.vercel.app/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Session", "game_type": "minesweeper"}'
```

## Troubleshooting

### "No Supabase connection" errors
- Check environment variables are set in Vercel
- Verify SUPABASE_URL includes `https://`
- Ensure anon key is complete (very long string)

### Database not updating
- Check Row Level Security policies
- Verify migrations were applied
- Check Supabase dashboard for errors

### Fallback to JSON
The platform automatically falls back to JSON file storage if Supabase is not configured. This is useful for:
- Local development without Supabase
- Testing without database
- Graceful degradation

## Data Migration

To migrate existing JSON data to Supabase:

```python
# Run the migration script (create this if needed)
python migrate-to-supabase.py
```

## Security Notes

1. **Never commit API keys** - Use environment variables
2. **Use RLS policies** - Current schema has open policies for development
3. **Secure in production** - Tighten policies before going live
4. **Regular backups** - Enable Supabase automatic backups

## Next Steps

1. **Enable Realtime** - For live updates
2. **Add Authentication** - Supabase Auth integration
3. **Storage Buckets** - For game replays and assets
4. **Edge Functions** - For complex game logic

## Monitoring

Check your Supabase dashboard for:
- Database size and usage
- API request counts
- Performance metrics
- Error logs