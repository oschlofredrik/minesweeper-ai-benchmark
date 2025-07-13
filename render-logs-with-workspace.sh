#!/bin/bash

# Render logs viewer with workspace configuration
# This script sets up the workspace configuration temporarily

WORKSPACE_ID="tea-csp7rjrgbbvc73d1n1mg"
SERVICE_ID="${1:-srv-d1prptqdbo4c73bs9jkg}"

# Create render config directory
mkdir -p ~/.config/render

# Create workspace configuration
cat > ~/.config/render/config.json << EOF
{
  "workspace": {
    "id": "$WORKSPACE_ID",
    "name": "Fredrik Evjen Ekli",
    "email": "fredrik@oschlo.co"
  }
}
EOF

echo "📋 Fetching logs for service: $SERVICE_ID"
echo "Workspace: Fredrik Evjen Ekli ($WORKSPACE_ID)"
echo "----------------------------------------"

# Now fetch logs
render logs --resources "$SERVICE_ID" --output text --confirm --limit 100

# For continuous streaming, uncomment this:
# render logs --resources "$SERVICE_ID" --output text --confirm --tail