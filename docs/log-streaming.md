# Log Streaming Guide

This guide explains how to monitor your Minesweeper AI Benchmark deployment logs in real-time.

## Overview

The platform provides multiple ways to view logs from your Render deployment:

1. **Render API** (Recommended) - Stream logs directly to your terminal
2. **Render CLI** - Official CLI tool (requires workspace setup)
3. **Web Browser** - Quick access via Render dashboard

## Method 1: Render API Log Streaming (Recommended)

### Setup

1. Get your Render API key:
   - Go to https://dashboard.render.com/account/api-keys
   - Create a new API key
   - Copy the key (starts with `rnd_`)

2. Set the environment variable:
   ```bash
   export RENDER_API_KEY='rnd_your_key_here'
   ```

3. Run the log streaming script:
   ```bash
   ./render-api-logs.sh
   ```

### Features

- Shows last 50 log entries on startup
- Continuously streams new logs every 2 seconds
- Removes ANSI color codes for better readability
- Formats timestamps in human-readable format

### Custom Service ID

To stream logs from a different service:
```bash
./render-api-logs.sh srv-YOUR-SERVICE-ID
```

## Method 2: Render CLI

### Setup

1. Install Render CLI:
   ```bash
   brew install render/render/render
   # or download from https://render.com/docs/cli#installation
   ```

2. Login to Render:
   ```bash
   render login
   ```

3. Set your workspace:
   ```bash
   render workspace set
   # Select your workspace from the list
   ```

4. Stream logs:
   ```bash
   render logs --resources srv-d1prptqdbo4c73bs9jkg --tail
   ```

### Notes

- The CLI requires interactive workspace setup
- Cannot pass workspace ID as parameter
- Best for users who regularly use Render CLI

## Method 3: Browser Access

### Quick Access

Run the browser viewer script:
```bash
./view-logs-browser.sh
```

Or directly visit:
https://dashboard.render.com/web/srv-d1prptqdbo4c73bs9jkg/logs

### Features

- Full Render dashboard interface
- Advanced filtering options
- Download logs
- Search functionality

## Log Format

The application uses structured JSON logging with the following fields:

```json
{
  "timestamp": "2025-07-13T19:30:00.000Z",
  "level": "INFO",
  "logger": "api.play",
  "message": "Play session completed",
  "job_id": "play_abc123",
  "duration": 120.5,
  "games_played": 10,
  "win_rate": 0.7
}
```

## Common Log Patterns

### Game Evaluation
```
INFO [httpx] HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
```

### API Requests
```
INFO: 10.201.239.193:33224 - "GET /api/play/games HTTP/1.1" 200 OK
```

### Play Sessions
```
INFO [api.play] Play session completed {job_id: play_abc123, games_played: 10}
```

## Troubleshooting

### No logs appearing
- Verify your API key is correct
- Check the service ID matches your deployment
- Ensure the service is running (check Render dashboard)

### Permission errors
- Make sure your API key has read permissions
- Verify you're using the correct owner/workspace ID

### Connection issues
- Check your internet connection
- Verify Render API is accessible
- Try the browser method as fallback

## Production Considerations

- API rate limits apply based on your Render plan
- Logs are retained based on your Render tier
- Consider log aggregation services for long-term storage
- Use structured logging queries for debugging

## Environment Variables

```bash
# Required for API-based streaming
export RENDER_API_KEY='rnd_your_key'

# Optional: Set default service ID
export RENDER_SERVICE_ID='srv-d1prptqdbo4c73bs9jkg'
```

## Scripts Reference

| Script | Purpose | Requirements |
|--------|---------|--------------|
| `render-api-logs.sh` | Stream logs via API | RENDER_API_KEY |
| `stream-render-logs.sh` | Stream via CLI | Render CLI + workspace |
| `view-logs-browser.sh` | Open logs in browser | None |
| `setup-render-logs.sh` | Setup helper | None |