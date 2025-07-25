#!/bin/bash

echo "Setting up Vercel for Tilts Platform..."

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm i -g vercel
fi

# Copy static files
echo "Preparing static files..."
mkdir -p src/api/static
cp -r ../src/api/static/* src/api/static/

# Create package.json for Vercel
cat > package.json << 'EOF'
{
  "name": "tilts-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vercel dev",
    "deploy": "vercel --prod"
  }
}
EOF

# Login to Vercel
echo "Logging in to Vercel..."
vercel login

# Link to project
echo "Linking to Vercel project..."
vercel link

# Set environment variables
echo "Setting environment variables..."
vercel env add VITE_API_URL production
vercel env add VITE_PUSHER_KEY production
vercel env add VITE_PUSHER_CLUSTER production

echo "Vercel setup complete!"
echo "Deploy with: vercel --prod"