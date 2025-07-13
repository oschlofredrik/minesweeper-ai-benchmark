# Viewing Render Logs

Since the Render CLI requires workspace configuration even for direct service access, here are your options:

## Option 1: Set up Workspace (Recommended)

1. Run the workspace setup:
   ```bash
   render workspace set
   ```
   This will open a browser to select your workspace.

2. Once set, run:
   ```bash
   ./stream-render-logs.sh srv-d1prptqdbo4c73bs9jkg
   ```

## Option 2: View in Browser

Direct link to your logs:
https://dashboard.render.com/web/srv-d1prptqdbo4c73bs9jkg/logs

## Option 3: Use Render API Directly

If you need programmatic access without workspace setup:

```bash
# Get your API key from https://dashboard.render.com/account/api-keys
export RENDER_API_KEY='your-api-key'

# Fetch recent logs
curl -H "Authorization: Bearer $RENDER_API_KEY" \
     "https://api.render.com/v1/services/srv-d1prptqdbo4c73bs9jkg/logs?tail=100" \
     | jq -r '.[] | "[\(.timestamp)] \(.message)"'

# Continuous streaming (polls every 2 seconds)
while true; do
  curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
       "https://api.render.com/v1/services/srv-d1prptqdbo4c73bs9jkg/logs?tail=50" \
       | jq -r '.[] | "[\(.timestamp)] \(.message)"'
  sleep 2
done
```

## Why Workspace is Required

The Render CLI is designed to work within the context of a workspace (team/organization). Even when you provide a specific service ID, it validates that the service belongs to your current workspace for security reasons.

This is why you're getting the "no workspace set" error even with a direct service ID.