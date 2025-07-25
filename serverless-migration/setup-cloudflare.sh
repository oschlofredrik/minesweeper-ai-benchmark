#!/bin/bash

echo "Setting up Cloudflare Workers for Tilts API..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "Installing Wrangler CLI..."
    npm i -g wrangler
fi

# Login to Cloudflare
echo "Logging in to Cloudflare..."
wrangler login

# Create KV namespace for sessions
echo "Creating KV namespace..."
wrangler kv:namespace create "SESSIONS" --preview

# Create R2 bucket for storage
echo "Creating R2 bucket..."
wrangler r2 bucket create tilts-storage

# Create worker
mkdir -p src
cat > src/worker.js << 'EOF'
import { Router } from 'itty-router';
import { createClient } from '@supabase/supabase-js';
import Pusher from 'pusher';

const router = Router();

// Initialize services
const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY);
const pusher = new Pusher({
  appId: env.PUSHER_APP_ID,
  key: env.PUSHER_KEY,
  secret: env.PUSHER_SECRET,
  cluster: env.PUSHER_CLUSTER,
});

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// Health check
router.get('/health', () => {
  return new Response(JSON.stringify({ status: 'healthy' }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
});

// Session endpoints
router.post('/api/sessions/create', async (request, env) => {
  const body = await request.json();
  
  // Generate session ID and join code
  const sessionId = crypto.randomUUID();
  const joinCode = Math.random().toString(36).substring(2, 8).toUpperCase();
  
  // Store in KV
  await env.SESSIONS.put(sessionId, JSON.stringify({
    ...body,
    id: sessionId,
    join_code: joinCode,
    created_at: new Date().toISOString(),
  }));
  
  // Store in Supabase for persistence
  const { data, error } = await supabase
    .from('sessions')
    .insert([{ id: sessionId, join_code: joinCode, ...body }]);
  
  // Notify via Pusher
  await pusher.trigger('tilts-global', 'session-created', {
    sessionId,
    joinCode,
  });
  
  return new Response(JSON.stringify({ id: sessionId, join_code: joinCode }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
});

// Handle all requests
export default {
  async fetch(request, env, ctx) {
    return router.handle(request, env, ctx);
  },
};
EOF

# Create package.json
cat > package.json << 'EOF'
{
  "name": "tilts-api-worker",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler publish",
    "tail": "wrangler tail"
  },
  "dependencies": {
    "itty-router": "^4.0.0",
    "@supabase/supabase-js": "^2.0.0",
    "pusher": "^5.0.0"
  }
}
EOF

npm install

echo "Cloudflare Workers setup complete!"
echo "Deploy with: wrangler publish"