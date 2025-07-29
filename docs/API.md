# API Reference

## Base URL
- Production: `https://tilts.vercel.app/api`
- Local: `http://localhost:3000/api`

## Authentication
Most read endpoints are public. Write operations may require API keys in future versions.

## Endpoints

### AI SDK Evaluation

#### POST /api/evaluate-sdk
Start a new AI evaluation using Vercel AI SDK with advanced features.

**Request Body:**
```json
{
  "game": "minesweeper",
  "provider": "openai",
  "model": "gpt-4.5-preview",
  "num_games": 10,
  "difficulty": "medium",
  "use_sdk": true,
  "features": {
    "streaming": true,
    "reasoning": true,
    "multiStep": true,
    "maxSteps": 50
  }
}
```

**Response:**
```json
{
  "evaluation_id": "eval_123abc",
  "status": "started",
  "message": "SDK evaluation started",
  "endpoint": "/api/evaluation/eval_123abc",
  "streamEndpoint": "/api/evaluation/eval_123abc/stream"
}
```

**Supported Models:**
- OpenAI: `gpt-4.5-preview`, `gpt-4`, `o1`, `o3-mini`, `gpt-3.5-turbo`
- Anthropic: `claude-4-sonnet-20250514`, `claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-opus`
- DeepSeek: `deepseek-reasoner`
- Groq: `llama-3.1-70b-versatile`

#### GET /api/evaluation/{id}/status
Get real-time evaluation progress.

**Response:**
```json
{
  "evaluation_id": "eval_123abc",
  "status": "running",
  "progress": 0.5,
  "games_completed": 5,
  "games_total": 10,
  "currentGame": {
    "id": "game_5",
    "status": "in_progress",
    "moves": 23,
    "reasoning": "Analyzing corner patterns for safe moves..."
  },
  "games": [
    {
      "id": "game_1",
      "status": "won",
      "moves": 42,
      "duration": 15.3,
      "minesIdentified": 10
    }
  ]
}
```

#### GET /api/evaluation/{id}/stream
Server-sent events stream for real-time updates.

**Event Format:**
```
event: move
data: {"move": {"action": "reveal", "row": 5, "col": 7}, "reasoning": "Safe based on adjacent numbers"}

event: game-complete
data: {"gameId": "game_1", "won": true, "moves": 42}

event: evaluation-complete
data: {"evaluationId": "eval_123", "results": {...}}
```

### Game Management

#### POST /api/play
Start a new AI evaluation session (legacy endpoint, prefer `/api/evaluate-sdk`).

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

**Query Parameters:**
- `status`: Filter by status (`running`, `completed`, `error`)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset

**Response:**
```json
{
  "games": [
    {
      "job_id": "play_123abc",
      "model_name": "gpt-4",
      "model_provider": "openai",
      "progress": 0.5,
      "status": "running",
      "games_completed": 5,
      "games_total": 10,
      "started_at": "2024-01-20T10:30:00Z"
    }
  ],
  "total": 45,
  "hasMore": true
}
```

### Structured AI Endpoints

#### POST /api/analyze-game
Analyze a game state using structured output.

**Request Body:**
```json
{
  "gameState": {
    "board": [[0,1,0],[1,2,1],[0,1,0]],
    "revealed": [[true,true,true],[true,false,true],[true,true,true]],
    "flagged": [[false,false,false],[false,false,false],[false,false,false]]
  },
  "model": "gpt-4.5-preview"
}
```

**Response:**
```json
{
  "safeSquares": [
    {"row": 1, "col": 1, "confidence": 0.0}
  ],
  "mineLocations": [
    {"row": 1, "col": 1, "confidence": 1.0}
  ],
  "strategy": "The center cell must be a mine based on surrounding numbers",
  "riskAssessment": "low",
  "winProbability": 0.95
}
```

#### POST /api/generate-move
Generate a single move with reasoning.

**Request Body:**
```json
{
  "gameState": {...},
  "provider": "openai",
  "model": "o3-mini",
  "reasoningEffort": "high"
}
```

**Response:**
```json
{
  "action": "flag",
  "row": 3,
  "col": 5,
  "reasoning": "Based on the pattern analysis, this cell has a 98% probability of containing a mine",
  "confidence": 0.98,
  "alternativeMoves": [
    {"action": "reveal", "row": 2, "col": 4, "confidence": 0.85}
  ]
}
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
  "max_players": 20,
  "settings": {
    "difficulty": "expert",
    "time_limit": 300,
    "allow_reasoning_models": true
  }
}
```

**Response:**
```json
{
  "session_id": "sess_123",
  "join_code": "PLAY123",
  "status": "waiting",
  "created_at": "2024-01-20T10:30:00Z",
  "expires_at": "2024-01-20T11:30:00Z"
}
```

#### POST /api/sessions/join
Join an existing competition.

**Request Body:**
```json
{
  "join_code": "PLAY123",
  "player_name": "Alice",
  "ai_config": {
    "provider": "anthropic",
    "model": "claude-4-sonnet-20250514",
    "features": {
      "extendedThinking": true,
      "thinkingBudget": 15000
    }
  }
}
```

### Leaderboard

#### GET /api/leaderboard
Get global leaderboard rankings.

**Query Parameters:**
- `metric`: Ranking metric (`global_score`, `win_rate`, `speed`, `efficiency`)
- `timeframe`: Time period (`all`, `month`, `week`, `today`)
- `game_type`: Filter by game (`minesweeper`, `risk`)
- `model_class`: Filter by model type (`reasoning`, `standard`, `fast`)
- `limit`: Number of results (default: 20)

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "model_name": "o3-mini",
      "model_provider": "openai",
      "model_class": "reasoning",
      "global_score": 0.925,
      "win_rate": 0.88,
      "avg_moves": 45.2,
      "total_games": 150,
      "last_played": "2024-01-20T09:15:00Z"
    }
  ],
  "metadata": {
    "total_entries": 45,
    "updated_at": "2024-01-20T10:30:00Z",
    "timeframe": "all"
  }
}
```

### Model Configuration

#### GET /api/models
Get all available models across providers.

**Response:**
```json
{
  "providers": {
    "openai": {
      "models": {
        "gpt-4.5-preview": {
          "name": "GPT-4.5 Preview",
          "class": "standard",
          "features": ["streaming", "tools", "vision"],
          "context_window": 128000
        },
        "o3-mini": {
          "name": "O3 Mini",
          "class": "reasoning",
          "features": ["reasoning", "structured_output"],
          "reasoning_effort": ["low", "medium", "high"]
        }
      },
      "has_api_key": true
    },
    "anthropic": {
      "models": {
        "claude-4-sonnet-20250514": {
          "name": "Claude 4 Sonnet",
          "class": "extended_thinking",
          "features": ["extended_thinking", "interleaved_thinking"],
          "thinking_budget": 20000
        }
      },
      "has_api_key": true
    }
  }
}
```

#### GET /api/models/{provider}
Get available models for a specific provider.

**Response:**
```json
{
  "provider": "openai",
  "models": {
    "gpt-4.5-preview": {
      "name": "GPT-4.5 Preview",
      "supports_functions": true,
      "supports_streaming": true,
      "max_tokens": 128000
    }
  },
  "has_api_key": true,
  "features": ["reasoning", "vision", "tools"]
}
```

### System Status

#### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "services": {
    "database": "connected",
    "ai_providers": {
      "openai": "available",
      "anthropic": "available",
      "deepseek": "available"
    },
    "cache": "ready"
  },
  "version": "2.0.0"
}
```

#### GET /api/stats
Get platform statistics.

**Response:**
```json
{
  "total_evaluations": 1523,
  "unique_models": 24,
  "games_played": 15230,
  "best_win_rate": 0.925,
  "active_games": 3,
  "models_by_class": {
    "reasoning": 5,
    "standard": 12,
    "extended_thinking": 3,
    "fast": 4
  },
  "popular_models": [
    {"name": "gpt-4.5-preview", "usage": 450},
    {"name": "claude-4-sonnet", "usage": 380},
    {"name": "o3-mini", "usage": 220}
  ],
  "last_updated": "2024-01-20T10:30:00Z"
}
```

### Streaming Endpoints

#### GET /api/stream/{evaluation_id}
WebSocket endpoint for real-time game updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://tilts.vercel.app/api/stream/eval_123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.payload);
};
```

**Message Types:**
- `move`: Individual move made
- `state`: Game state update
- `reasoning`: AI reasoning text
- `game-complete`: Game finished
- `evaluation-complete`: All games finished

## Error Responses

All endpoints use standard HTTP status codes and return errors in this format:

```json
{
  "error": {
    "code": "INVALID_MODEL",
    "message": "Model 'gpt-5' is not available",
    "details": {
      "available_models": ["gpt-4.5-preview", "gpt-4", "o3-mini"]
    }
  }
}
```

**Common Error Codes:**
- `400` - Bad Request: Invalid parameters
- `401` - Unauthorized: Missing or invalid API key
- `404` - Not Found: Resource doesn't exist
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server-side error
- `503` - Service Unavailable: AI provider unavailable

## Rate Limits

- **Public endpoints**: 100 requests per minute
- **Evaluation endpoints**: 10 concurrent evaluations
- **Streaming endpoints**: 5 concurrent connections

## SDK Examples

### JavaScript/TypeScript
```typescript
// Using fetch
const response = await fetch('https://tilts.vercel.app/api/evaluate-sdk', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    game: 'minesweeper',
    provider: 'openai',
    model: 'gpt-4.5-preview',
    num_games: 5,
    use_sdk: true
  })
});

const { evaluation_id } = await response.json();
```

### Python
```python
import requests

response = requests.post(
    'https://tilts.vercel.app/api/evaluate-sdk',
    json={
        'game': 'minesweeper',
        'provider': 'anthropic',
        'model': 'claude-4-sonnet-20250514',
        'num_games': 5,
        'use_sdk': True
    }
)

evaluation = response.json()
```

### cURL
```bash
curl -X POST https://tilts.vercel.app/api/evaluate-sdk \
  -H "Content-Type: application/json" \
  -d '{
    "game": "minesweeper",
    "provider": "openai",
    "model": "o3-mini",
    "num_games": 5,
    "use_sdk": true
  }'
```

## Changelog

### v2.0.0 (Latest)
- Added Vercel AI SDK integration
- New `/api/evaluate-sdk` endpoint
- Support for reasoning models (o1, o3, R1)
- Extended thinking for Claude 4
- Real-time streaming updates
- Structured output with Zod schemas

### v1.5.0
- Added competition system
- Improved leaderboard metrics
- Database optimization

### v1.0.0
- Initial release
- Basic evaluation API
- Leaderboard functionality