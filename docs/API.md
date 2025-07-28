# API Reference

## Base URL
- Production: `https://tilts.vercel.app/api`
- Local: `http://localhost:3000/api`

## Endpoints

### Game Management

#### POST /api/play
Start a new AI evaluation session.

**Request Body:**
```json
{
  "game": "minesweeper",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "num_games": 10,
  "difficulty": "medium"
}
```

**Response:**
```json
{
  "job_id": "play_123abc",
  "status": "running",
  "message": "Evaluation started"
}
```

#### GET /api/play/games
List all active game sessions.

**Response:**
```json
[
  {
    "job_id": "play_123abc",
    "model_name": "gpt-4",
    "progress": 0.5,
    "status": "running",
    "games_completed": 5,
    "games_total": 10
  }
]
```

### Competition System

#### POST /api/sessions/create
Create a new competition session.

**Request Body:**
```json
{
  "name": "Friday AI Challenge",
  "game_type": "minesweeper",
  "format": "single_round",
  "max_players": 20
}
```

**Response:**
```json
{
  "session_id": "sess_123",
  "join_code": "PLAY123",
  "status": "waiting"
}
```

#### POST /api/sessions/join
Join an existing competition.

**Request Body:**
```json
{
  "join_code": "PLAY123",
  "player_name": "Alice",
  "ai_model": "gpt-4"
}
```

### Leaderboard

#### GET /api/leaderboard
Get global leaderboard rankings.

**Query Parameters:**
- `metric`: Ranking metric (default: "global_score")
- `limit`: Number of results (default: 20)

**Response:**
```json
[
  {
    "rank": 1,
    "model_name": "gpt-4",
    "global_score": 0.875,
    "win_rate": 0.82,
    "total_games": 150
  }
]
```

### Model Configuration

#### GET /api/models/{provider}
Get available models for a provider.

**Response:**
```json
{
  "models": {
    "gpt-4": {
      "name": "GPT-4",
      "supports_functions": true
    },
    "gpt-3.5-turbo": {
      "name": "GPT-3.5 Turbo",
      "supports_functions": true
    }
  },
  "has_api_key": true
}
```

### System Status

#### GET /api/stats
Get platform statistics.

**Response:**
```json
{
  "total_evaluations": 1523,
  "unique_models": 12,
  "best_win_rate": 0.875,
  "active_games": 3
}
```