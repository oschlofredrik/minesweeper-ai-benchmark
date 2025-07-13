#!/bin/bash

# Render API Log Streaming Script
# Uses the Render API directly to stream logs

SERVICE_ID="${1:-srv-d1prptqdbo4c73bs9jkg}"
OWNER_ID="tea-csp7rjrgbbvc73d1n1mg"

# Check if RENDER_API_KEY is set
if [ -z "$RENDER_API_KEY" ]; then
    echo "❌ Error: RENDER_API_KEY environment variable is not set"
    echo ""
    echo "To get your API key:"
    echo "1. Go to: https://dashboard.render.com/account/api-keys"
    echo "2. Create a new API key or copy an existing one"
    echo "3. Export it: export RENDER_API_KEY='your-key-here'"
    echo ""
    echo "Example:"
    echo "  export RENDER_API_KEY='rnd_xxxxxxxxxxxxxx'"
    echo "  ./render-api-logs.sh"
    exit 1
fi

echo "🔍 Minesweeper AI Benchmark - Render Logs"
echo "Service: $SERVICE_ID"
echo "Press Ctrl+C to stop"
echo "----------------------------------------"

# Function to format and clean log messages
format_log() {
    local timestamp="$1"
    local message="$2"
    
    # Convert timestamp to readable format
    timestamp_clean=$(echo "$timestamp" | cut -d'.' -f1 | sed 's/T/ /')
    
    # Remove ANSI color codes from message
    message_clean=$(echo "$message" | sed 's/\x1b\[[0-9;]*m//g')
    
    echo "[$timestamp_clean] $message_clean"
}

# Initial fetch of recent logs
echo "Fetching recent logs..."
RESPONSE=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/logs?ownerId=$OWNER_ID&resource=$SERVICE_ID&limit=50")

# Check if the response is valid
if [ -z "$RESPONSE" ] || [ "$RESPONSE" = "null" ]; then
    echo "❌ Error: Could not fetch logs. Please check:"
    echo "  - Your API key is valid"
    echo "  - The service ID is correct: $SERVICE_ID"
    exit 1
fi

# Check for API errors
if echo "$RESPONSE" | jq -e '.message' >/dev/null 2>&1; then
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.message')
    echo "❌ API Error: $ERROR_MSG"
    exit 1
fi

# Display initial logs
echo "$RESPONSE" | jq -r '.logs[] | "\(.timestamp)|\(.message)"' 2>/dev/null | while IFS='|' read -r timestamp message; do
    format_log "$timestamp" "$message"
done || {
    echo "❌ Error parsing logs."
    exit 1
}

# Get the last timestamp for continuous streaming
LAST_TIMESTAMP=$(echo "$RESPONSE" | jq -r '.logs[-1].timestamp' 2>/dev/null)

# Continuous streaming
echo ""
echo "Streaming new logs..."

while true; do
    sleep 2
    
    # Fetch new logs since last timestamp
    if [ -n "$LAST_TIMESTAMP" ] && [ "$LAST_TIMESTAMP" != "null" ]; then
        NEW_LOGS=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
             "https://api.render.com/v1/logs?ownerId=$OWNER_ID&resource=$SERVICE_ID&startTime=$LAST_TIMESTAMP&limit=100")
        
        # Process and display new logs (skip the first one as it's the last from previous batch)
        if [ -n "$NEW_LOGS" ] && echo "$NEW_LOGS" | jq -e '.logs | length > 1' >/dev/null 2>&1; then
            echo "$NEW_LOGS" | jq -r '.logs[1:] | .[] | "\(.timestamp)|\(.message)"' 2>/dev/null | while IFS='|' read -r timestamp message; do
                format_log "$timestamp" "$message"
            done
            
            # Update last timestamp
            NEW_TIMESTAMP=$(echo "$NEW_LOGS" | jq -r '.logs[-1].timestamp' 2>/dev/null)
            if [ -n "$NEW_TIMESTAMP" ] && [ "$NEW_TIMESTAMP" != "null" ]; then
                LAST_TIMESTAMP="$NEW_TIMESTAMP"
            fi
        fi
    fi
done