# Web Interface Documentation

The Minesweeper AI Benchmark includes a web interface for viewing results and exploring the leaderboard.

## Features

- **Live Leaderboard**: Real-time rankings of all evaluated models
- **Metric Filtering**: Sort by different metrics (global score, win rate, accuracy, etc.)
- **Task Type Filtering**: View results for static or interactive tasks
- **Platform Statistics**: Total evaluations, unique models, and task counts
- **Game Replays**: Visualize individual game sessions (coming soon)
- **API Access**: RESTful API for programmatic access

## Starting the Web Server

### Using the CLI

```bash
# Start the web server on default port (8000)
python -m src.cli.main serve

# Start on a custom port
python -m src.cli.main serve --port 8080

# Start and open browser automatically
python -m src.cli.main serve --open-browser
```

### Using the Script

```bash
./scripts/run_web.sh
```

The web interface will be available at `http://localhost:8000`

## Web Interface Sections

### Leaderboard

The main leaderboard shows:
- Model rankings by selected metric
- Key performance metrics for each model
- Number of games evaluated
- Statistical significance indicators (when available)

### Metrics

Detailed explanation of all evaluation metrics:
- **Global Score**: Weighted geometric mean across task types
- **Win Rate**: Percentage of games won
- **Accuracy**: Correct predictions on static tasks
- **Coverage**: Average board cells revealed
- **Reasoning Score**: Quality of logical explanations (0-1)

### About

Information about the benchmark:
- Task types and difficulty levels
- Evaluation methodology
- Links to documentation and code

## API Endpoints

The web interface exposes several API endpoints:

### GET /api/leaderboard
Get current leaderboard data.

**Query Parameters:**
- `task_type`: Filter by task type (static/interactive)
- `metric`: Metric to sort by (default: global_score)
- `limit`: Number of entries to return (default: 50)

**Example:**
```bash
curl "http://localhost:8000/api/leaderboard?metric=win_rate&limit=10"
```

### GET /api/models/{model_id}/results
Get detailed results for a specific model.

### GET /api/models/{model_id}/games
Get list of games played by a model.

### GET /api/games/{game_id}/replay
Get replay data for a specific game.

### GET /api/stats
Get platform statistics.

### GET /api/metrics
Get list of available metrics with descriptions.

## CLI Integration

Additional CLI commands for web interface:

```bash
# Open web interface in browser (if running)
python -m src.cli.main open-web

# Export leaderboard data
python -m src.cli.main export-leaderboard
```

## Customization

### Adding New Metrics

To display new metrics in the leaderboard:

1. Add metric calculation in `src/evaluation/metrics.py`
2. Include in API response in `src/api/database.py`
3. Add column in web interface `src/api/static/index.html`

### Styling

The web interface uses a clean, modern design with:
- CSS variables for easy theming
- Responsive layout for mobile devices
- Color-coded score badges

To customize styling, edit `src/api/static/rams-design.css` and `src/api/static/rams-components.css`

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install uvicorn[standard] --upgrade

# Run with auto-reload
uvicorn src.api.main:app --reload
```

### Adding New Pages

1. Create HTML file in `src/api/static/`
2. Add route in `src/api/main.py`
3. Update navigation in `index.html`

## Deployment

For production deployment:

1. Use a production ASGI server:
```bash
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. Set up reverse proxy (nginx):
```nginx
location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

3. Enable HTTPS with SSL certificates

## Troubleshooting

### Server won't start
- Check if port is already in use
- Ensure all dependencies are installed
- Check for Python import errors

### Leaderboard is empty
- Run some evaluations first
- Check if results are saved in `data/results/`
- Verify file permissions

### API errors
- Check server logs for detailed errors
- Ensure proper JSON formatting
- Verify API endpoint URLs