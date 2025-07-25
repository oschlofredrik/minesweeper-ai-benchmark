# Quick Deploy Steps for Tilts Serverless

## 1. Vercel Setup (Frontend)

```bash
# Login to Vercel
vercel login

# Select "Continue with GitHub" or your preferred method

# After login, in the serverless-migration directory:
vercel link

# When prompted:
# - Set up and deploy: Y
# - Which scope: Select your account
# - Link to existing project? N
# - Project name: tilts-platform
# - In which directory: . (current)
# - Override settings? N

# Deploy
vercel --prod
```

## 2. Supabase Setup (Database)

Go to https://supabase.com and:
1. Click "Start your project"
2. Sign in with GitHub
3. Click "New Project"
4. Name: tilts-platform
5. Database Password: Generate a strong one (save it!)
6. Region: Select closest to you

Once created, get your credentials:
- Click "Settings" → "API"
- Copy:
  - Project URL
  - anon public key

## 3. Pusher Setup (WebSockets)

Go to https://pusher.com and:
1. Sign up for free account
2. Create new app
3. Name: tilts-platform
4. Cluster: us2 (or closest)
5. Front-end: React
6. Back-end: Node.js

Get credentials from "App Keys" tab

## 4. Cloudflare Workers Setup

```bash
# Login to Cloudflare
wrangler login

# Create KV namespace
wrangler kv:namespace create "SESSIONS"

# Note the namespace ID from output

# Update wrangler.toml with all credentials
```

## 5. Create .env file

```bash
cat > .env << 'EOF'
# Vercel
VITE_API_URL=https://tilts-api.YOUR-SUBDOMAIN.workers.dev
VITE_PUSHER_KEY=YOUR_PUSHER_KEY
VITE_PUSHER_CLUSTER=us2

# Cloudflare
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_ANON_KEY
PUSHER_APP_ID=YOUR_APP_ID
PUSHER_KEY=YOUR_PUSHER_KEY
PUSHER_SECRET=YOUR_PUSHER_SECRET
EOF
```

## 6. Deploy Everything

```bash
# Deploy API to Cloudflare
wrangler publish

# Deploy Frontend to Vercel
vercel --prod
```

Your platform will be live at the Vercel URL!