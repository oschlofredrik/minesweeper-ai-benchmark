#!/bin/bash

echo "🚀 Render API Logs Setup"
echo "========================"
echo ""
echo "This will help you set up API-based log streaming for your Render deployment."
echo ""

# Check if API key is already set
if [ -n "$RENDER_API_KEY" ]; then
    echo "✅ RENDER_API_KEY is already set"
    echo ""
    echo "Ready to stream logs! Run:"
    echo "  ./render-api-logs.sh"
    echo ""
    echo "Or stream a specific service:"
    echo "  ./render-api-logs.sh srv-YOUR-SERVICE-ID"
    exit 0
fi

echo "📋 Steps to get your Render API key:"
echo ""
echo "1. Open in your browser:"
echo "   https://dashboard.render.com/account/api-keys"
echo ""
echo "2. Click 'Create API Key'"
echo ""
echo "3. Give it a name (e.g., 'Log Viewer')"
echo ""
echo "4. Copy the key (starts with 'rnd_')"
echo ""
echo "5. Run this command with your key:"
echo "   export RENDER_API_KEY='rnd_YOUR_KEY_HERE'"
echo ""
echo "6. Then run:"
echo "   ./render-api-logs.sh"
echo ""
echo "💡 Tip: Add the export command to your ~/.bashrc or ~/.zshrc to make it permanent"