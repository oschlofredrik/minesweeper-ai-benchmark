# Deployment Guide - Tilts Platform

This guide covers deploying the Tilts platform to Vercel with the latest AI SDK integration.

## Prerequisites

1. [Vercel account](https://vercel.com)
2. [GitHub account](https://github.com) with repository access
3. API keys for AI providers
4. [Supabase account](https://supabase.com) for database

## Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-org/tilts)

## Manual Deployment Steps

### 1. Prepare Your Repository

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Install Vercel CLI

```bash
pnpm install -g vercel
```

### 3. Configure Environment Variables

Create a `.env.production` file (do not commit this):

```bash
# AI Provider Keys (Required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (Required)
SUPABASE_URL=https://mgkprogfsjmazekeyquq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJ... # For server-side operations

# Optional AI Providers
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...
MISTRAL_API_KEY=...
TOGETHERAI_API_KEY=...

# Feature Flags
ENABLE_REASONING=true
ENABLE_STREAMING=true
ENABLE_COMPUTER_USE=false
ENABLE_EXTENDED_THINKING=true

# Performance
AI_REQUEST_TIMEOUT=300000  # 5 minutes for complex evaluations
MAX_CONCURRENT_GAMES=5
CACHE_TTL=3600

# Monitoring (Optional)
SENTRY_DSN=...
POSTHOG_API_KEY=...
```

### 4. Deploy to Vercel

#### Option A: Using Vercel CLI

```bash
# First deployment
vercel

# Follow prompts:
# - Link to existing project or create new
# - Select scope (personal or team)
# - Confirm project settings

# Production deployment
vercel --prod
```

#### Option B: Using GitHub Integration

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js (or Other if custom)
   - **Root Directory**: `./` (or your app directory)
   - **Build Command**: `pnpm build`
   - **Output Directory**: `.next` (or `dist`)

### 5. Configure Environment Variables in Vercel

```bash
# Using CLI
vercel env add OPENAI_API_KEY production
vercel env add ANTHROPIC_API_KEY production
vercel env add SUPABASE_URL production
vercel env add SUPABASE_ANON_KEY production

# Or in Dashboard:
# Settings → Environment Variables → Add all variables
```

### 6. Configure Vercel Project Settings

Update `vercel.json`:
```json
{
  "functions": {
    "api/*.py": {
      "runtime": "python3.9",
      "maxDuration": 300
    },
    "api/evaluate-sdk.py": {
      "maxDuration": 300,
      "memory": 1024
    },
    "api/stream-game.py": {
      "maxDuration": 300,
      "streaming": true
    }
  },
  "rewrites": [
    {
      "source": "/api/evaluate-sdk",
      "destination": "/api/evaluate-sdk.py"
    },
    {
      "source": "/api/evaluation/:path*/status",
      "destination": "/api/evaluation_status.py"
    }
  ],
  "env": {
    "DB_POOL_SIZE": "5",
    "DB_TIMEOUT": "30",
    "CACHE_TTL": "300"
  }
}
```

## Database Setup (Supabase)

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

### 3. Create Indexes for Performance
```sql
CREATE INDEX idx_games_job_id ON games(job_id);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_created_at ON games(created_at DESC);
CREATE INDEX idx_games_model ON games(model_name, model_provider);
```

## Post-Deployment Verification

### 1. Test Core Endpoints
```bash
# Health check
curl https://tilts.vercel.app/api/stats

# AI SDK availability
curl https://tilts.vercel.app/api/evaluate-sdk

# Leaderboard
curl https://tilts.vercel.app/api/leaderboard
```

### 2. Test AI Evaluation
```bash
curl -X POST https://tilts.vercel.app/api/evaluate-sdk \
  -H "Content-Type: application/json" \
  -d '{
    "game": "minesweeper",
    "provider": "openai",
    "model": "gpt-4",
    "num_games": 1,
    "use_sdk": true
  }'
```

### 3. Monitor Logs
```bash
# Real-time logs
vercel logs --follow

# Filter by function
vercel logs --filter="api/evaluate-sdk"
```

## Production Optimizations

### 1. Enable Edge Functions
Convert latency-sensitive endpoints to Edge Runtime:

```typescript
// api/leaderboard-edge.ts
export const config = {
  runtime: 'edge',
};

export default async function handler(request: Request) {
  // Edge-optimized code
}
```

### 2. Implement Caching

```typescript
// Use Vercel KV for caching
import { kv } from '@vercel/kv';

const cached = await kv.get('leaderboard');
if (cached) return cached;

const data = await fetchLeaderboard();
await kv.set('leaderboard', data, { ex: 300 }); // 5 min cache
```

### 3. Add Rate Limiting

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { kv } from '@vercel/kv';

const ratelimit = new Ratelimit({
  redis: kv,
  limiter: Ratelimit.slidingWindow(10, '10 s'),
});
```

### 4. Enable Analytics

```typescript
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/next';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
```

## Troubleshooting

### API Keys Not Working
```bash
# Verify environment variables
vercel env ls

# Pull latest env vars
vercel env pull

# Redeploy after changes
vercel --prod
```

### Function Timeouts
Increase timeout in `vercel.json`:
```json
{
  "functions": {
    "api/evaluate-sdk.py": {
      "maxDuration": 300 // 5 minutes
    }
  }
}
```

### Database Connection Issues
```python
# Add connection pooling
import os
from supabase import create_client, Client

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    return create_client(url, key, options={
        "db": {"pool_size": 5}
    })
```

### Build Failures
```bash
# Check build logs
vercel logs --type=build

# Common fixes:
# 1. Update dependencies: pnpm update
# 2. Clear cache: vercel --force
# 3. Check Python version in vercel.json
```

## Security Best Practices

1. **Environment Variables**: Never commit secrets to repository
2. **API Authentication**: Implement API key validation
3. **CORS Configuration**: Restrict allowed origins
4. **Input Validation**: Validate all user inputs
5. **Rate Limiting**: Protect against abuse

## Monitoring & Maintenance

### Set Up Alerts
```javascript
// api/_monitoring.js
export async function checkHealth() {
  const checks = [
    { name: 'Database', fn: checkDatabase },
    { name: 'AI APIs', fn: checkAIProviders },
    { name: 'Cache', fn: checkCache },
  ];
  
  const results = await Promise.all(
    checks.map(async (check) => ({
      name: check.name,
      status: await check.fn(),
    }))
  );
  
  return results;
}
```

### Regular Updates
```bash
# Update AI SDK
pnpm add ai@beta @ai-sdk/openai@beta @ai-sdk/anthropic@beta

# Update all dependencies
pnpm update

# Deploy updates
vercel --prod
```

## Scaling Strategies

### 1. Use Vercel Functions Concurrency
```json
{
  "functions": {
    "api/evaluate-sdk.py": {
      "maxDuration": 300,
      "memory": 1024,
      "concurrency": 100
    }
  }
}
```

### 2. Implement Job Queue
For long-running evaluations:
```typescript
// Use Vercel KV as job queue
import { kv } from '@vercel/kv';

export async function queueEvaluation(job) {
  await kv.lpush('evaluation-queue', JSON.stringify(job));
  return job.id;
}
```

### 3. Multi-Region Deployment
```json
{
  "regions": ["iad1", "sfo1", "sin1", "fra1"]
}
```

## CI/CD Pipeline

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: pnpm/action-setup@v2
        with:
          version: 8
          
      - name: Install dependencies
        run: pnpm install
        
      - name: Run tests
        run: pnpm test
        
      - name: Type check
        run: pnpm type-check
        
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: ${{ github.ref == 'refs/heads/main' && '--prod' || '' }}
```

## Custom Domain Setup

1. Add domain in Vercel Dashboard
2. Update DNS records:
   - A: 76.76.21.21
   - AAAA: 2606:4700:3033::6815:3a7b
   - CNAME: cname.vercel-dns.com

## Rollback Strategy

```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback

# Rollback to specific deployment
vercel rollback [deployment-url]
```

## Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Support](https://vercel.com/support)
- [AI SDK Documentation](https://sdk.vercel.ai/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Project Issues](https://github.com/your-org/tilts/issues)

## Cost Optimization

1. **Choose appropriate models**: Use GPT-3.5 for simple tasks
2. **Enable caching**: Cache repeated queries
3. **Optimize function size**: Remove unused dependencies
4. **Monitor usage**: Track API calls and costs
5. **Use Edge functions**: Lower latency and cost