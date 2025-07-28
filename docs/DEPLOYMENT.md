# Deployment Guide

## Prerequisites
- Vercel account
- Supabase account  
- GitHub repository

## Environment Setup

### 1. Create `.env` file
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://mgkprogfsjmazekeyquq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Configure Vercel Environment
```bash
vercel env add OPENAI_API_KEY
vercel env add ANTHROPIC_API_KEY
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
```

## Deploy to Production

### Automatic (GitHub)
1. Push to main branch
2. Vercel auto-deploys

### Manual Deploy
```bash
vercel --prod
```

## Database Setup

### 1. Apply Migrations
```bash
cd supabase
supabase db push
```

### 2. Enable Realtime
```sql
ALTER PUBLICATION supabase_realtime 
ADD TABLE games, sessions, leaderboard_entries;
```

## Post-Deployment

### Verify Endpoints
- Health: https://tilts.vercel.app/api/stats
- Models: https://tilts.vercel.app/api/models/openai
- Leaderboard: https://tilts.vercel.app/api/leaderboard

### Monitor Logs
```bash
vercel logs --follow
```

## Troubleshooting

### API Keys Not Working
- Verify in Vercel dashboard: Settings > Environment Variables
- Redeploy after adding variables

### Database Connection Failed
- Check Supabase status
- Verify connection string
- System falls back to JSON storage automatically