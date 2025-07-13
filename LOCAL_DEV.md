# Local Development Guide

## Quick Start

1. **Run the local server**:
   ```bash
   ./run-local.sh
   ```

2. **Access the application**:
   - Main UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Summary pages: http://localhost:8000/summary/{job_id}

## Development Workflow

### Making Changes

1. **Frontend changes** (HTML/CSS/JS):
   - Edit files in `src/api/static/`
   - Refresh browser to see changes immediately
   - No server restart needed

2. **Backend changes** (Python):
   - Edit Python files
   - Server auto-reloads with `--reload` flag
   - Check terminal for any errors

3. **Testing changes**:
   - Use the UI at http://localhost:8000
   - Test API endpoints at http://localhost:8000/docs
   - Check logs in terminal

### Common Tasks

**Run a test evaluation**:
```bash
# In another terminal
curl -X POST http://localhost:8000/api/play \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt-3.5-turbo",
    "model_provider": "openai",
    "num_games": 2,
    "difficulty": "expert"
  }'
```

**Check logs**:
- Terminal shows all server logs
- Check `data/logs/` for structured logs

**Clear test data**:
```bash
rm -rf data/results/*
```

## Troubleshooting

**Port already in use**:
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

**Module not found errors**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**API key issues**:
- Check `.env` file has valid keys
- Restart server after changing `.env`

## Hot Reload

The server runs with `--reload` flag, which means:
- Python changes trigger automatic restart
- Static files (HTML/CSS/JS) update without restart
- Just save file and refresh browser

## Deployment

When ready to deploy:
```bash
git add -A
git commit -m "Your changes"
git push origin main
```

Render will automatically deploy from GitHub.