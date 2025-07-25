#!/bin/bash

echo "Testing Tilts Serverless Deployment"
echo "==================================="

# Test Vercel deployment
if [ -f ".vercel/project.json" ]; then
    echo "✅ Vercel project linked"
    VERCEL_URL=$(cat .vercel/project.json | grep -o '"name":"[^"]*' | cut -d'"' -f4)
    echo "   Project: $VERCEL_URL"
else
    echo "❌ Vercel not set up yet"
fi

# Test environment file
if [ -f ".env" ]; then
    echo "✅ Environment file exists"
else
    echo "❌ Environment file missing"
    echo "   Run: cp .env.example .env"
fi

# Test Cloudflare config
if [ -f "wrangler.toml" ]; then
    echo "✅ Cloudflare config exists"
else
    echo "❌ Cloudflare config missing"
fi

# Test node modules
if [ -d "node_modules" ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Dependencies not installed"
    echo "   Run: npm install"
fi

echo ""
echo "Next Steps:"
echo "1. vercel login"
echo "2. Create accounts on Supabase and Pusher"
echo "3. Update .env with credentials"
echo "4. vercel --prod"