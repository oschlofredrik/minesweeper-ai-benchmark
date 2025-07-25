#!/bin/bash

echo "==================================="
echo "Tilts Platform Serverless Migration"
echo "==================================="

# Make all scripts executable
chmod +x setup-*.sh

# Check for required tools
echo "Checking required tools..."
required_tools=("node" "npm" "git")
for tool in "${required_tools[@]}"; do
    if ! command -v $tool &> /dev/null; then
        echo "❌ $tool is required but not installed"
        exit 1
    fi
done
echo "✅ All required tools found"

# Create .env template
cat > .env.example << 'EOF'
# Vercel
VITE_API_URL=https://api.tilts.workers.dev
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=us2

# Cloudflare
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret

# Supabase
DATABASE_URL=postgresql://user:pass@host:5432/db
EOF

echo ""
echo "Setup Options:"
echo "1. Vercel (Frontend hosting)"
echo "2. Cloudflare Workers (API)"
echo "3. Supabase (Database + Real-time)"
echo "4. Pusher (WebSocket events)"
echo "5. All services"
echo ""
read -p "Select option (1-5): " choice

case $choice in
    1) ./setup-vercel.sh ;;
    2) ./setup-cloudflare.sh ;;
    3) ./setup-supabase.sh ;;
    4) ./setup-pusher.sh ;;
    5) 
        echo "Setting up all services..."
        ./setup-vercel.sh
        ./setup-cloudflare.sh
        ./setup-supabase.sh
        ./setup-pusher.sh
        ;;
    *) echo "Invalid option" ;;
esac

echo ""
echo "==================================="
echo "Next Steps:"
echo "1. Copy .env.example to .env and fill in credentials"
echo "2. Deploy frontend: cd frontend && vercel --prod"
echo "3. Deploy API: cd api && wrangler publish"
echo "4. Test the platform at your Vercel URL"
echo "==================================="