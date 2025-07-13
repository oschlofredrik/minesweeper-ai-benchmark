#!/bin/bash

# Quick script to open Render logs in browser

SERVICE_ID="${1:-srv-d1prptqdbo4c73bs9jkg}"
LOGS_URL="https://dashboard.render.com/web/$SERVICE_ID/logs"

echo "🔍 Opening Render logs in browser..."
echo "Service: $SERVICE_ID"
echo "URL: $LOGS_URL"
echo ""

# Check which command is available to open URLs
if command -v open &> /dev/null; then
    # macOS
    open "$LOGS_URL"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "$LOGS_URL"
elif command -v start &> /dev/null; then
    # Windows
    start "$LOGS_URL"
else
    echo "Could not detect browser command. Please open this URL manually:"
    echo "$LOGS_URL"
fi

echo "✅ Logs should now be open in your browser"