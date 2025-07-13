#!/bin/bash

# Render CLI Log Streaming Script
# This script streams logs from your Render deployment

set -e

# Check if logged in to Render CLI
if ! render whoami --output json >/dev/null 2>&1; then
    echo "❌ Error: Not logged in to Render CLI"
    echo ""
    echo "Please log in first:"
    echo "  render login"
    exit 1
fi

# If SERVICE_ID is provided as argument, skip workspace checks
if [ -n "$1" ]; then
    SERVICE_ID="$1"
    echo "Using provided service ID: $SERVICE_ID"
else
    # Check if workspace is set
    if ! render workspace current --output json >/dev/null 2>&1; then
        echo "❌ Error: No workspace set"
        echo ""
        echo "Please set your workspace first:"
        echo "  1. Run: render workspace set"
        echo "  2. Select your workspace from the list"
        echo ""
        echo "Alternative: Provide service ID directly"
        echo "  1. Go to https://dashboard.render.com"
        echo "  2. Find your service ID (srv-xxxxx) in the URL"
        echo "  3. Run: ./stream-render-logs.sh srv-YOUR-SERVICE-ID"
        exit 1
    fi

    echo "🔍 Fetching Render services..."

    # Get services in JSON format (non-interactive)
    SERVICES=$(render services --output json --confirm 2>/dev/null || echo "[]")

    if [ "$SERVICES" = "[]" ]; then
        echo "❌ No services found"
        echo ""
        echo "This could mean:"
        echo "  - No services in the current workspace"
        echo "  - Wrong workspace selected"
        echo ""
        echo "Alternative: Get logs directly with service ID"
        echo "  1. Find your service ID from https://dashboard.render.com"
        echo "  2. Run: ./stream-render-logs.sh srv-YOUR-SERVICE-ID"
        exit 1
    fi

    # Parse and display services
    echo ""
    echo "Available services:"
    echo "$SERVICES" | jq -r '.[] | "- \(.name) (\(.type)) - ID: \(.id)"' 2>/dev/null || {
        echo "Error parsing services. Raw output:"
        echo "$SERVICES"
        exit 1
    }

    # Extract the first service ID from workspace
    SERVICE_ID=$(echo "$SERVICES" | jq -r '.[0].id' 2>/dev/null)
    
    if [ -z "$SERVICE_ID" ] || [ "$SERVICE_ID" = "null" ]; then
        echo ""
        echo "❌ Could not extract service ID"
        echo "Please provide the service ID as an argument:"
        echo "  ./stream-render-logs.sh srv-YOUR-SERVICE-ID"
        exit 1
    fi
fi

echo ""
echo "📋 Fetching logs for service: $SERVICE_ID"
echo "Press Ctrl+C to stop"
echo "----------------------------------------"

# Since --tail only works in interactive mode, we'll poll for new logs
# Start with the last 100 logs
LAST_TIMESTAMP=""

while true; do
    # Fetch logs using render CLI in non-interactive mode
    if [ -z "$LAST_TIMESTAMP" ]; then
        # First run - get last 100 logs
        LOGS=$(render logs --resources "$SERVICE_ID" --output json --confirm --limit 100 2>/dev/null || echo "[]")
    else
        # Subsequent runs - get logs after last timestamp
        LOGS=$(render logs --resources "$SERVICE_ID" --output json --confirm --start "$LAST_TIMESTAMP" 2>/dev/null || echo "[]")
    fi
    
    # Process and display logs
    if [ "$LOGS" != "[]" ] && [ -n "$LOGS" ]; then
        # Display logs and update last timestamp
        echo "$LOGS" | jq -r '.[] | "[\(.timestamp)] \(.message)"' 2>/dev/null || {
            echo "Error parsing logs"
        }
        
        # Get the timestamp of the last log for next query
        NEW_TIMESTAMP=$(echo "$LOGS" | jq -r '.[-1].timestamp' 2>/dev/null)
        if [ -n "$NEW_TIMESTAMP" ] && [ "$NEW_TIMESTAMP" != "null" ]; then
            LAST_TIMESTAMP="$NEW_TIMESTAMP"
        fi
    fi
    
    # Wait before next poll
    sleep 2
done