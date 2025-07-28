# Tilts Platform Serverless Deployment Guide

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Vercel CDN    │────▶│  Cloudflare  │────▶│  Supabase   │
│  (Frontend)     │     │  Workers API │     │  (Database) │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                      │                     │
         └──────────────────────┴─────────────────────┘
                               │
                        ┌──────────────┐
                        │   Pusher     │
                        │ (WebSockets) │
                        └──────────────┘
```

## Prerequisites

1. Install required CLIs:
   ```bash
   # Vercel
   npm i -g vercel
   
   # Cloudflare
   npm i -g wrangler
   
   # Supabase
   brew install supabase/tap/supabase
   ```

2. Create accounts:
   - [Vercel](https://vercel.com) - Frontend hosting
   - [Cloudflare](https://cloudflare.com) - Workers for API
   - [Supabase](https://supabase.com) - Database
   - [Pusher](https://pusher.com) - WebSockets

## Step 1: Initial Setup

```bash
cd serverless-migration
chmod +x setup-all.sh
./setup-all.sh
```

Select option 5 to set up all services.

## Step 2: Configure Services

### Vercel Setup
1. Run `./setup-vercel.sh`
2. Login when prompted
3. Create new project "tilts-platform"
4. Set environment variables:
   - `VITE_API_URL`: Your Cloudflare Workers URL
   - `VITE_PUSHER_KEY`: From Pusher dashboard
   - `VITE_PUSHER_CLUSTER`: Usually "us2"

### Cloudflare Workers Setup
1. Run `./setup-cloudflare.sh`
2. Login when prompted
3. Update `wrangler.toml` with:
   - KV namespace ID (from output)
   - Supabase credentials
   - Pusher credentials

### Supabase Setup
1. Run `./setup-supabase.sh`
2. Create new project "tilts-platform"
3. Note your:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon Key: `eyJ...`
   - Database URL: `postgresql://...`

### Pusher Setup
1. Create account at pusher.com
2. Create new Channels app
3. Note credentials:
   - App ID
   - Key
   - Secret
   - Cluster

## Step 3: Update Configuration

Create `.env` file:
```bash
# Vercel
VITE_API_URL=https://tilts-api.workers.dev
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=us2

# Cloudflare
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
PUSHER_APP_ID=123456
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret

# Migration
RENDER_DATABASE_URL=postgresql://...
```

## Step 4: Deploy

### Deploy API (Cloudflare Workers)
```bash
cd api
npm install
wrangler publish --env production
```

Note the API URL (e.g., `https://tilts-api.workers.dev`)

### Deploy Frontend (Vercel)
```bash
cd ../frontend
vercel --prod
```

Note the frontend URL (e.g., `https://tilts-platform.vercel.app`)

## Step 5: Migrate Data

```bash
cd ..
python3 migrate-data.py
```

## Step 6: Update DNS (Optional)

1. In Cloudflare DNS, add:
   - `A` record: `@` → Vercel IP
   - `CNAME` record: `www` → `cname.vercel-dns.com`
   - `CNAME` record: `api` → Workers route

2. In Vercel, add custom domain

## Monitoring & Logs

### Vercel Logs
```bash
vercel logs --follow
```

### Cloudflare Workers Logs
```bash
wrangler tail --env production
```

### Supabase Logs
Access via Supabase dashboard → Logs

## Cost Estimates

| Service | Free Tier | Estimated Monthly |
|---------|-----------|------------------|
| Vercel | 100GB bandwidth | $0-20 |
| Cloudflare | 100k requests/day | $0-5 |
| Supabase | 500MB DB, 2GB bandwidth | $0-25 |
| Pusher | 200k messages/day | $0-49 |
| **Total** | | **$0-99** |

## Troubleshooting

### CORS Issues
Add to Cloudflare Worker:
```javascript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};
```

### WebSocket Connection Failed
Check Pusher cluster matches in frontend and backend.

### Database Connection Issues
Ensure Supabase project is not paused (free tier pauses after 7 days).

## Next Steps

1. Set up monitoring (e.g., Sentry)
2. Configure custom domain
3. Enable Cloudflare caching rules
4. Set up CI/CD with GitHub Actions
5. Configure rate limiting