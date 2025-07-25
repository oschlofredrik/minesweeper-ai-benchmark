#!/bin/bash

# Deploy Tilts Frontend to Vercel

set -e

echo "🚀 Deploying Tilts Frontend to Vercel..."

cd serverless/frontend

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the project
echo "🔨 Building frontend..."
npm run build

# Deploy based on environment
if [ "$1" == "production" ]; then
    echo "🌍 Deploying to production..."
    vercel --prod
else
    echo "🔍 Deploying to preview..."
    vercel
fi

echo "✅ Deployment complete!"